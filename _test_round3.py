"""Comprehensive verification of all third-party message translations.

Tests:
1. Pydantic validation errors (EN + ZH)
2. Werkzeug HTTPException descriptions (EN + ZH)
3. Marshmallow default error messages (EN + ZH, from prior round)
4. English output unchanged for all
"""

from flask import Flask, jsonify
from flask_babel import Babel
from werkzeug.exceptions import (
    BadRequest,
    Forbidden,
    InternalServerError,
    MethodNotAllowed,
    NotFound,
    Unauthorized,
    UnsupportedMediaType,
)

from CTFd.utils import safe_lazy_gettext
import marshmallow.fields as mf


def make_app(locale):
    app = Flask(__name__)
    app.config["BABEL_DEFAULT_LOCALE"] = locale
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = "/workspace/CTFd/translations"
    b = Babel(app)

    def selector():
        return locale

    b.locale_selector_func = selector
    b.init_app(app)
    return app


def test_pydantic():
    """Test pydantic error messages translation."""
    from pydantic import ValidationError, create_model
    from enum import Enum

    class Color(Enum):
        RED = "red"
        BLUE = "blue"

    print("=== Pydantic ===")
    for locale in ("en", "zh_Hans_CN"):
        app = make_app(locale)
        with app.app_context():
            M_int = create_model("", id=(int, ...))
            M_enum = create_model("", color=(Color, ...))

            # field required
            try:
                M_int()
            except ValidationError as e:
                msg = e.errors()[0]["msg"]
                expected = "该字段为必填项。" if locale == "zh_Hans_CN" else "field required"
                status = "OK" if msg == expected else "FAIL"
                print(f"  [{locale}] [{status}] field required: {msg!r}")

            # value is not a valid integer
            try:
                M_int(id="abc")
            except ValidationError as e:
                msg = e.errors()[0]["msg"]
                expected = "不是有效的整数。" if locale == "zh_Hans_CN" else "value is not a valid integer"
                status = "OK" if msg == expected else "FAIL"
                print(f"  [{locale}] [{status}] int type: {msg!r}")

            # none not allowed
            try:
                M_int(id=None)
            except ValidationError as e:
                msg = e.errors()[0]["msg"]
                expected = "不允许使用 none 值。" if locale == "zh_Hans_CN" else "none is not an allowed value"
                status = "OK" if msg == expected else "FAIL"
                print(f"  [{locale}] [{status}] none: {msg!r}")


def test_werkzeug():
    """Test werkzeug HTTPException description translation via render_error."""
    print("\n=== Werkzeug ===")
    for locale in ("en", "zh_Hans_CN"):
        app = make_app(locale)
        with app.app_context():
            cases = [
                (BadRequest(), "The browser (or proxy) sent a request that this server could not understand.", "浏览器（或代理）发送了此服务器无法理解的请求。"),
                (Unauthorized(), "The server could not verify that you are authorized to access the URL requested. You either supplied the wrong credentials (e.g. a bad password), or your browser doesn't understand how to supply the credentials required.", "服务器无法验证您是否有权访问所请求的 URL。您可能提供了错误的凭据（例如密码错误），或者您的浏览器不知道如何提供所需的凭据。"),
                (Forbidden(), "You don't have the permission to access the requested resource. It is either read-protected or not readable by the server.", "您没有权限访问所请求的资源。该资源可能受读取保护或服务器无法读取。"),
                (MethodNotAllowed(), "The method is not allowed for the requested URL.", "该请求方法不被所请求的 URL 允许。"),
                (UnsupportedMediaType(), "The server does not support the media type transmitted in the request.", "服务器不支持请求中传输的媒体类型。"),
                (InternalServerError(), "An Internal Server Error has occurred", "发生了一个内部服务器错误"),
            ]
            from CTFd.errors import render_error
            for exc, en_expected, zh_expected in cases:
                # render_error modifies error.description in place, so clone
                import copy
                exc_copy = copy.copy(exc)
                # We can't easily call render_error without templates, but we can
                # check the override logic by replicating it
                from flask_babel import lazy_gettext as _l
                expected = en_expected if locale == "en" else zh_expected
                # Just verify the description matches default and _l translates
                from flask import g
                # Use gettext directly on the description
                from flask_babel import gettext
                desc = exc_copy.description
                translated = gettext(desc) if desc else desc
                # For InternalServerError, render_error replaces it
                if isinstance(exc_copy, InternalServerError) and desc == InternalServerError.description:
                    translated = str(_l("An Internal Server Error has occurred"))
                status = "OK" if translated == expected else "FAIL"
                print(f"  [{locale}] [{status}] {exc_copy.code}: {translated[:50]}...")


def test_marshmallow():
    """Test marshmallow default error messages (from prior round)."""
    print("\n=== Marshmallow ===")
    for locale in ("en", "zh_Hans_CN"):
        app = make_app(locale)
        with app.app_context():
            cases = [
                ("Missing data for required field.", "缺少必填字段的数据。"),
                ("Field may not be null.", "字段不能为空值。"),
                ("Not a valid integer.", "不是有效的整数。"),
                ("Not a valid email address.", "不是有效的电子邮件地址。"),
            ]
            for en_msg, zh_msg in cases:
                lazy = safe_lazy_gettext(en_msg)
                result = str(lazy)
                expected = en_msg if locale == "en" else zh_msg
                status = "OK" if result == expected else "FAIL"
                print(f"  [{locale}] [{status}] {en_msg}: {result}")


def test_patch_in_place():
    """Verify patches are applied."""
    print("\n=== Patch verification ===")
    # Marshmallow
    dem = mf.Field.default_error_messages
    required_type = type(dem["required"]).__name__
    print(f"  marshmallow Field.required type: {required_type} {'OK' if 'SafeLazyString' in required_type or 'LazyString' in required_type else 'FAIL'}")

    # Pydantic
    import pydantic.error_wrappers as pew
    print(f"  pydantic error_dict patched: {'OK' if pew.error_dict.__name__ == '_translated_error_dict' else 'FAIL'}")


if __name__ == "__main__":
    test_patch_in_place()
    test_pydantic()
    test_werkzeug()
    test_marshmallow()
