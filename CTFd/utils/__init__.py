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


def _patch_marshmallow_error_messages():
    """Wrap marshmallow's built-in field error messages in SafeLazyString.

    marshmallow ships plain-English default error messages (e.g.
    ``'Missing data for required field.'``) as class attributes on
    ``marshmallow.fields.Field`` and its subclasses. Because these strings
    never pass through Flask-Babel's ``gettext``, they are never translated
    regardless of the request locale.

    This one-time patch replaces every ``str`` value inside each field class's
    ``default_error_messages`` with a ``SafeLazyString`` wrapper. The messages
    are then translated lazily at render time according to the request locale.
    English output is unaffected: when no translation exists for a message
    ``gettext`` returns the original string unchanged.

    Messages that contain ``{`` placeholders (e.g.
    ``'"{input}" cannot be formatted as a date.'``) are skipped because
    ``marshmallow.Field.fail`` only calls ``str.format`` when the message is a
    plain string — wrapping them in ``SafeLazyString`` would prevent
    placeholder substitution.
    """
    import marshmallow.fields as _mf

    for _attr in vars(_mf).values():
        if isinstance(_attr, type) and hasattr(_attr, "default_error_messages"):
            _dem = _attr.default_error_messages
            if isinstance(_dem, dict):
                _attr.default_error_messages = {
                    _k: (
                        safe_lazy_gettext(_v)
                        if isinstance(_v, str) and "{" not in _v
                        else _v
                    )
                    for _k, _v in _dem.items()
                }


_patch_marshmallow_error_messages()


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
