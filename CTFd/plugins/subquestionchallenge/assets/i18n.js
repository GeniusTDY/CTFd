// Page-level i18n patch for Sub Question Challenge plugin (admin side).
// Loaded on every admin page via register_admin_plugin_script, which
// injects the script through get_registered_admin_scripts() in the admin
// base.html. Only acts on /admin/challenges/new where the challenge-type
// card list is rendered by CTFd core. CTFd core renders "{{ type }}" (the
// id) for unknown challenge types, so we translate the card label
// client-side using the global _() function (powered by Flask-Babel).
(function () {
    function patchTypeLabels() {
        // Only run on the admin challenge creation page
        if (!window.location.pathname.endsWith('/admin/challenges/new')) return;

        var labels = document.querySelectorAll('#create-chals-select .form-check-label');
        if (!labels.length) return false;

        labels.forEach(function (el) {
            var text = (el.textContent || '').trim();
            if (text === 'subquestionchallenge') {
                // Use CTFd core's _() function (Flask-Babel translations).
                // Returns the translated string, or the original English
                // key if no translation exists for the current locale.
                if (typeof window._ === 'function') {
                    el.textContent = window._('Sub Question Challenge');
                }
            }
        });
        return true;
    }

    function init() {
        // Core renders the type list asynchronously via /api/v1/challenges/types,
        // so observe DOM mutations until the labels appear.
        var observer = new MutationObserver(function () {
            patchTypeLabels();
        });
        observer.observe(document.body, { childList: true, subtree: true });
        // Stop observing after 10s to avoid leaks
        setTimeout(function () { observer.disconnect(); }, 10000);

        // Also try once immediately
        patchTypeLabels();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
