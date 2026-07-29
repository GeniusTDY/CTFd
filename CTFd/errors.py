import jinja2.exceptions
from flask import render_template
from flask_babel import lazy_gettext as _l
from werkzeug.exceptions import (
    BadRequest,
    Forbidden,
    InternalServerError,
    MethodNotAllowed,
    NotAcceptable,
    NotFound,
    Unauthorized,
    UnsupportedMediaType,
)


def render_error(error):
    # Replace werkzeug's built-in English HTTPException descriptions with
    # translated equivalents when the caller used bare abort(code) without a
    # custom description. Custom descriptions (already translated by callers
    # via _l()/gettext()) are left untouched because they won't match the
    # default attribute value.
    _default_overrides = {
        BadRequest: _l("The browser (or proxy) sent a request that this server could not understand."),
        Unauthorized: _l("The server could not verify that you are authorized to access the URL requested. You either supplied the wrong credentials (e.g. a bad password), or your browser doesn't understand how to supply the credentials required."),
        Forbidden: _l("You don't have the permission to access the requested resource. It is either read-protected or not readable by the server."),
        NotFound: _l("The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."),
        MethodNotAllowed: _l("The method is not allowed for the requested URL."),
        UnsupportedMediaType: _l("The server does not support the media type transmitted in the request."),
        NotAcceptable: _l("The resource identified by the request is only capable of generating response entities which have content characteristics not acceptable according to the accept headers sent in the request."),
        InternalServerError: _l("An Internal Server Error has occurred"),
    }
    for _exc_cls, _msg in _default_overrides.items():
        if (
            isinstance(error, _exc_cls)
            and error.description == _exc_cls.description
        ):
            error.description = _msg
            break
    try:
        return (
            render_template(
                "errors/{}.html".format(error.code),
                error=error.description,
            ),
            error.code,
        )
    except jinja2.exceptions.TemplateNotFound:
        return error.get_response()
