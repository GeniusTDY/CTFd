// Page-level i18n patch for Sub Question Challenge plugin (admin side).
// Loaded on every admin page via register_admin_plugin_script, which
// injects the script through get_registered_admin_scripts() in the admin
// base.html. Only acts on /admin/challenges/new where the challenge-type
// card list is rendered by CTFd core. CTFd core renders "{{ type }}" (the
// id) for unknown challenge types, so we translate the card label
// client-side.
(function () {
    function patchTypeLabels() {
        // Only run on the admin challenge creation page
        if (!window.location.pathname.endsWith('/admin/challenges/new')) return;

        var labels = document.querySelectorAll('#create-chals-select .form-check-label');
        if (!labels.length) return false;

        labels.forEach(function (el) {
            var text = (el.textContent || '').trim();
            if (text === 'subquestionchallenge') {
                // Only translate when a non-empty translation is available
                // for the current language. Otherwise leave the original
                // "subquestionchallenge" label untouched so English (and
                // any other language without a translation) is unaffected.
                var translated = window.CTFd
                    && CTFd.translations
                    && CTFd.translations['Multi Question Challenge'];
                if (translated && typeof translated === 'string') {
                    el.textContent = translated;
                }
            }
        });
        return true;
    }

    function init() {
        // Ensure CTFd.translations exists
        if (typeof window.CTFd === 'undefined') window.CTFd = {};
        if (typeof CTFd.translations === 'undefined') CTFd.translations = {};

        // Detect language from cookie, falling back to browser language
        var lang = 'en';
        var m = document.cookie.match(/(?:^|;\s*)language=([^;]*)/);
        if (m) {
            lang = m[1];
        } else if (navigator.language) {
            var browserLang = navigator.language.toLowerCase();
            if (browserLang.includes('zh-tw') || browserLang.includes('zh-hant')) {
                lang = 'zh_Hant_TW';
            } else if (browserLang.includes('zh-cn') || browserLang.includes('zh-hans') || browserLang === 'zh') {
                lang = 'zh_CN';
            }
        }

        var url = '/plugins/subquestionchallenge/assets/translations/' + lang + '/translations.json';
        fetch(url)
            .then(function (r) { return r.ok ? r.json() : {}; })
            .then(function (t) {
                Object.assign(CTFd.translations, t);
                patchTypeLabels();
            })
            .catch(function () { patchTypeLabels(); });

        // Core renders the type list asynchronously via /api/v1/challenges/types,
        // so observe DOM mutations until the labels appear.
        var observer = new MutationObserver(function () {
            if (!patchTypeLabels()) return;
            // Keep observing: user may switch types and re-render
        });
        observer.observe(document.body, { childList: true, subtree: true });
        // Stop observing after 10s to avoid leaks
        setTimeout(function () { observer.disconnect(); }, 10000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();