"""End-to-end test through CTFd app: trigger real API validation errors
and verify the response messages are translated."""

from CTFd import create_app
from CTFd.config import TestingConfig


class ZhConfig(TestingConfig):
    BABEL_DEFAULT_LOCALE = "zh_Hans_CN"


class EnConfig(TestingConfig):
    BABEL_DEFAULT_LOCALE = "en"


def main():
    for ConfigClass, locale in [(EnConfig, "en"), (ZhConfig, "zh_Hans_CN")]:
        app = create_app(ConfigClass)
        print(f"\n=== Locale: {locale} ===")
        with app.test_client() as client:
            # Trigger pydantic validation error: POST /api/v1/users with invalid int
            # First need to set up - but TestingConfig should have setup done
            # Try a simple GET with query param type error
            # /api/v1/users?type=notanint
            r = client.get("/api/v1/users?type=notanint")
            print(f"  GET /api/v1/users?type=notanint -> {r.status_code}")
            if r.status_code == 400:
                data = r.get_json()
                print(f"  errors: {data.get('errors', {})}")
            elif r.status_code == 302:
                print(f"  (redirected - likely not set up)")

            # Test werkzeug 403 - access admin without auth
            r = client.get("/admin")
            print(f"  GET /admin -> {r.status_code}")
            if r.status_code == 403:
                # Check if description is translated
                body = r.get_data(as_text=True)
                if locale == "zh_Hans_CN":
                    has_zh = "没有权限" in body
                    print(f"  403 body has Chinese translation: {'OK' if has_zh else 'FAIL'}")
                else:
                    has_en = "permission" in body
                    print(f"  403 body has English: {'OK' if has_en else 'FAIL'}")

            # Test werkzeug 404
            r = client.get("/nonexistent-page-12345")
            print(f"  GET /nonexistent -> {r.status_code}")
            if r.status_code == 404:
                body = r.get_data(as_text=True)
                if locale == "zh_Hans_CN":
                    # 404 template uses translated text, not error.description
                    has_zh = "未找到" in body or "找不到" in body
                    print(f"  404 body has Chinese: {'OK' if has_zh else 'FAIL (checking)'}")
                else:
                    has_en = "not found" in body.lower() or "Not Found" in body
                    print(f"  404 body has English: {'OK' if has_en else 'FAIL (checking)'}")


if __name__ == "__main__":
    main()
