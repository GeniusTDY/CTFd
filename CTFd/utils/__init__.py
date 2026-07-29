import json
from enum import Enum

import cmarkgfm
from cmarkgfm.cmark import Options
from flask import current_app as app
from flask_babel import LazyString, gettext

# isort:imports-firstparty
from CTFd.cache import cache
from CTFd.constants.setup import DEFAULTS
from CTFd.models import Configs, db

string_types = (str,)
text_type = str
binary_type = bytes


class SafeLazyString(LazyString):
    """A LazyString that does not eagerly evaluate on __bool__.

    Marshmallow validators do ``self.error = error or self.default_message`` at
    class definition time. The ``or`` operator triggers ``__bool__`` which on the
    original ``LazyString`` falls back to ``__len__`` -> ``__str__`` -> ``gettext``,
    failing outside of a request context. This subclass short-circuits ``__bool__``
    so the lazy string is returned as-is and only translated when actually rendered.
    """

    def __bool__(self):
        return True

    __nonzero__ = __bool__

    def __len__(self):
        # Avoid triggering translation; only used for truthiness which __bool__ covers.
        return 1


def safe_lazy_gettext(string, **variables):
    """Like ``lazy_gettext`` but returns a :class:`SafeLazyString`.

    Use this for places (e.g. marshmallow validator ``error=`` kwargs) that
    evaluate truthiness at import/class-definition time.
    """
    return SafeLazyString(gettext, string, **variables)


class _LazyFormatString(str):
    """A ``str`` subclass that translates its template on ``.format()``.

    marshmallow's ``Field.fail`` only calls ``msg.format(**kwargs)`` when
    ``isinstance(msg, basestring)`` is true. ``SafeLazyString`` (a
    ``LazyString`` subclass) fails this check, so messages wrapped in it
    never get placeholder substitution.

    This subclass stores the English template as its ``str`` content (so
    ``isinstance`` checks pass and truthiness is based on the template, not
    on a translated value — safe at import time without a request context).
    When ``.format()`` is called (during request handling), it first passes
    the template through ``gettext`` (translating the static portion while
    preserving ``{placeholder}`` syntax), then calls ``str.format`` to
    substitute the dynamic values.

    English output is unaffected: ``gettext`` returns the original template
    when no translation exists.
    """

    def format(self, *args, **kwargs):
        return gettext(str(self)).format(*args, **kwargs)


def _wrap_marshmallow_message(value):
    """Wrap a marshmallow default message string for lazy translation.

    Messages without ``{`` placeholders use ``SafeLazyString`` (translated
    lazily on ``str()``). Messages with ``{`` placeholders use
    ``_LazyFormatString`` so that ``Field.fail`` / validator
    ``_format_error`` can still call ``.format()`` while getting translation.
    """
    if not isinstance(value, str):
        return value
    if "{" in value:
        return _LazyFormatString(value)
    return safe_lazy_gettext(value)


def _patch_marshmallow_error_messages():
    """Wrap marshmallow's built-in field and validator error messages.

    marshmallow ships plain-English default error messages as class
    attributes on ``marshmallow.fields.Field`` subclasses (in
    ``default_error_messages`` dicts) and on ``marshmallow.validate.Validator``
    subclasses (as ``default_message`` / ``message_min`` / ``message_max`` /
    ``message_all`` / ``message_equal`` attributes). These strings never pass
    through Flask-Babel's ``gettext``, so they are always English regardless
    of the request locale.

    This patch replaces every such string with a lazy wrapper:

    * Plain strings → ``SafeLazyString`` (translated on ``str()``).
    * Strings with ``{placeholder}`` → ``_LazyFormatString`` (a ``str``
      subclass that translates the template in ``.format()`` before
      substituting placeholders, so ``Field.fail`` and validator
      ``_format_error`` both work).

    English output is unaffected: ``gettext`` returns the original string
    when no translation exists.
    """
    import marshmallow.fields as _mf
    import marshmallow.validate as _mv

    # --- Field default_error_messages ---
    for _attr in vars(_mf).values():
        if isinstance(_attr, type) and hasattr(_attr, "default_error_messages"):
            _dem = _attr.default_error_messages
            if isinstance(_dem, dict):
                _attr.default_error_messages = {
                    _k: _wrap_marshmallow_message(_v)
                    for _k, _v in _dem.items()
                }

    # --- Validator default messages ---
    # marshmallow-sqlalchemy's ModelConverter auto-generates validators
    # (e.g. Length(max=N) for String columns) WITHOUT passing error=, so
    # these default messages are used and shown to users.
    _validator_msg_attrs = (
        "default_message",
        "message_min",
        "message_max",
        "message_all",
        "message_equal",
    )
    for _attr in vars(_mv).values():
        if isinstance(_attr, type) and issubclass(_attr, _mv.Validator):
            for _name in _validator_msg_attrs:
                _v = getattr(_attr, _name, None)
                if isinstance(_v, str):
                    setattr(_attr, _name, _wrap_marshmallow_message(_v))

    # --- marshmallow-sqlalchemy Related field ---
    try:
        import marshmallow_sqlalchemy.fields as _msa_fields
    except ImportError:
        _msa_fields = None
    if _msa_fields is not None:
        for _attr in vars(_msa_fields).values():
            if (
                isinstance(_attr, type)
                and hasattr(_attr, "default_error_messages")
            ):
                _dem = _attr.default_error_messages
                if isinstance(_dem, dict):
                    _attr.default_error_messages = {
                        _k: _wrap_marshmallow_message(_v)
                        for _k, _v in _dem.items()
                    }


_patch_marshmallow_error_messages()


def _patch_pydantic_error_messages():
    """Translate pydantic's built-in validation error messages.

    pydantic (1.x) builds the ``msg`` field of each validation error in
    :func:`pydantic.error_wrappers.error_dict` by formatting
    ``exc.msg_template`` (a plain English string) with the error context.
    These messages are returned to the frontend as JSON
    (``{"success": False, "errors": {field: msg}}``) and shown to users, but
    they never pass through Flask-Babel so they are always English.

    This patch wraps ``error_dict`` so that the *template* (before formatting)
    is passed through ``gettext`` first, then formatted with the dynamic
    context. This keeps ``{placeholder}`` substitutions working while allowing
    the static portion to be translated. When no translation exists ``gettext``
    returns the original template, so English output is unaffected.

    A few pydantic errors (``EnumError``, ``WrongConstantError``) build their
    message in ``__str__`` rather than via ``msg_template``; for those the
    already-formatted string is passed through ``gettext`` (which will return it
    unchanged when no catalog entry matches the interpolated form).
    """
    import pydantic.error_wrappers as _pew

    _original_error_dict = _pew.error_dict

    def _translated_error_dict(exc, config, loc):
        type_ = _pew.get_exc_type(exc.__class__)
        msg_template = config.error_msg_templates.get(type_) or getattr(
            exc, "msg_template", None
        )
        ctx = exc.__dict__
        if msg_template:
            try:
                msg = gettext(msg_template).format(**ctx)
            except Exception:
                msg = msg_template.format(**ctx)
        else:
            # Handle errors that build messages via __str__ instead of
            # msg_template (EnumError, WrongConstantError). These interpolate
            # the permitted values into the string at format time, so
            # gettext(str(exc)) can't match the catalog entry. We
            # reconstruct the template, translate it, then format with the
            # dynamic values.
            _enum_values = ctx.get("enum_values")
            _permitted = ctx.get("permitted")
            if _enum_values is not None:
                _perm_str = ", ".join(repr(v.value) for v in _enum_values)
                _template = (
                    "value is not a valid enumeration member; permitted: {permitted}"
                )
                try:
                    msg = gettext(_template).format(permitted=_perm_str)
                except Exception:
                    msg = str(exc)
            elif _permitted is not None:
                _perm_str = ", ".join(repr(v) for v in _permitted)
                _template = "unexpected value; permitted: {permitted}"
                try:
                    msg = gettext(_template).format(permitted=_perm_str)
                except Exception:
                    msg = str(exc)
            else:
                try:
                    msg = gettext(str(exc))
                except Exception:
                    msg = str(exc)

        d = {"loc": loc, "msg": msg, "type": type_}
        if ctx:
            d["ctx"] = ctx
        return d

    _pew.error_dict = _translated_error_dict


_patch_pydantic_error_messages()


def _patch_flask_restx_error_messages():
    """Translate Flask-RESTX's default JSON error responses.

    Flask-RESTX's ``Api.handle_error`` builds JSON error payloads using
    ``e.description`` (werkzeug ``HTTPException`` description) or
    ``code.phrase`` (``HTTPStatus`` short phrase) directly, without going
    through ``gettext``. These English strings are returned to the frontend
    as JSON ``{"message": ...}`` and displayed to users in toasts/alerts.

    This patch:

    1. Wraps ``Api.handle_error`` so that ``e.description`` is converted to
       ``str`` (evaluating any ``LazyString`` from ``_l()``) and then passed
       through ``gettext``. This fixes both the translation gap and a
       pre-existing JSON-serialization issue with ``LazyString`` values in
       ``abort()`` descriptions.
    2. Wraps ``Api._help_on_404`` to translate the "did you mean" suffix
       template that is appended to 404 API responses.
    3. Patches ``RestError.__str__`` so mask sub-messages are translated.

    English output is unaffected: ``gettext`` returns the original string
    when no translation catalog entry exists.
    """
    from werkzeug.exceptions import HTTPException as _HTTPException

    try:
        from flask_restx import Api as _Api
        from flask_restx.errors import RestError as _RestError
    except ImportError:  # pragma: no cover
        return

    # --- 1. Translate HTTPException descriptions in handle_error ---
    _original_handle_error = _Api.handle_error

    def _translated_handle_error(self, e):
        if isinstance(e, _HTTPException) and e.description is not None:
            try:
                # str() evaluates LazyString (_l) with the current locale;
                # gettext() then translates plain-English werkzeug defaults.
                e.description = gettext(str(e.description))
            except Exception:
                pass
        if isinstance(e, _RestError) and getattr(e, "msg", None) is not None:
            try:
                e.msg = gettext(str(e.msg))
            except Exception:
                pass
        return _original_handle_error(self, e)

    _Api.handle_error = _translated_handle_error

    # --- 2. Translate the _help_on_404 "did you mean" suffix ---
    _original_help_on_404 = _Api._help_on_404

    def _translated_help_on_404(self, message=None):
        import difflib
        import re

        from flask import current_app, request

        _RE_RULES = re.compile(r"<(?:[^:<>]+:)?[^<>]+>")
        rules = dict(
            [
                (_RE_RULES.sub("", rule.rule), rule.rule)
                for rule in current_app.url_map.iter_rules()
            ]
        )
        close_matches = difflib.get_close_matches(request.path, rules.keys())
        if close_matches:
            suffix = gettext(
                "You have requested this URI [{path}] but did you mean {suggestions} ?"
            ).format(
                path=request.path,
                suggestions=" or ".join(rules[match] for match in close_matches),
            )
            message = "".join(
                (
                    (message + " ") if message else "",
                    suffix,
                )
            )
        return message

    _Api._help_on_404 = _translated_help_on_404

    # --- 3. Translate RestError.__str__ (mask sub-messages) ---
    _original_rest_str = _RestError.__str__

    def _translated_rest_str(self):
        return gettext(_original_rest_str(self))

    _RestError.__str__ = _translated_rest_str


_patch_flask_restx_error_messages()


def _update_flask_restx_mask_handlers(api_instance):
    """Replace mask error handlers on an ``Api`` instance with translated versions.

    ``flask_restx.Api.__init__`` captures the module-level
    ``mask_parse_error_handler`` / ``mask_error_handler`` function references
    into ``self.error_handlers`` at creation time. Patching the module-level
    functions after the instance is created has no effect, so we must also
    update the instance's dict. Call this after creating each ``Api`` instance.
    """
    try:
        from flask_restx._http import HTTPStatus as _HTTPStatus
        from flask_restx.mask import MaskError as _MaskError, ParseError as _ParseError
    except ImportError:  # pragma: no cover
        return

    def _mask_parse_error_handler(error):
        return (
            {"message": gettext("Mask parse error: {0}").format(error)},
            _HTTPStatus.BAD_REQUEST,
        )

    def _mask_error_handler(error):
        return (
            {"message": gettext("Mask error: {0}").format(error)},
            _HTTPStatus.BAD_REQUEST,
        )

    api_instance.error_handlers[_ParseError] = _mask_parse_error_handler
    api_instance.error_handlers[_MaskError] = _mask_error_handler


def markdown(md):
    return cmarkgfm.markdown_to_html_with_extensions(
        md,
        extensions=["autolink", "table", "strikethrough"],
        options=Options.CMARK_OPT_UNSAFE,
    )


def get_app_config(key, default=None):
    value = app.config.get(key, default)
    return value


@cache.memoize()
def _get_asset_json(path):
    with open(path) as f:
        return json.loads(f.read())


def get_asset_json(path):
    # Ignore caching if we are in debug mode
    if app.debug:
        return _get_asset_json.__wrapped__(path)
    return _get_asset_json(path)


@cache.memoize()
def _get_config(key):
    config = db.session.execute(
        Configs.__table__.select().where(Configs.key == key)
    ).fetchone()
    if config and config.value:
        value = config.value
        if value and value.isdigit():
            return int(value)
        elif value and isinstance(value, string_types):
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
            else:
                return value
    # Flask-Caching is unable to roundtrip a value of None.
    # Return an exception so that we can still cache and avoid the db hit
    return KeyError


def get_config(key, default=None):
    # Look up the config in the local PRESET_CONFIGS store first
    preset_configs = app.config.get("PRESET_CONFIGS")
    if preset_configs and key in app.config.get("PRESET_CONFIGS"):
        return app.config["PRESET_CONFIGS"][key]

    # Convert enums to raw string values to cache better
    if isinstance(key, Enum):
        key = str(key)

    value = _get_config(key)
    if value is KeyError:
        # These defaults are used in situations where setup was skipped or partially completed
        if default is None and key in DEFAULTS:
            return DEFAULTS.get(key)
        return default
    else:
        return value


def set_config(key, value):
    config = Configs.query.filter_by(key=key).first()
    if config:
        config.value = value
    else:
        config = Configs(key=key, value=value)
        db.session.add(config)
    db.session.commit()

    # Convert enums to raw string values to cache better
    if isinstance(key, Enum):
        key = str(key)

    cache.delete_memoized(_get_config, key)
    return config


def import_in_progress():
    import_status = cache.get(key="import_status")
    import_error = cache.get(key="import_error")
    if import_error:
        return False
    elif import_status:
        return True
    else:
        return False
