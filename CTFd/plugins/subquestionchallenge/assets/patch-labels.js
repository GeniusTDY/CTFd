// Page-level i18n patch for Sub Question Challenge plugin (admin side).
// Loaded on every admin page via register_admin_plugin_script.
//
// CTFd core renders "{{ type }}" (the challenge id) verbatim for unknown
// challenge types in three admin locations:
//   1. /admin/challenges/new  - challenge-type card list (async via API)
//   2. /admin/challenges      - challenges table "Type" column (server-rendered)
//   3. /admin/challenges/<id> - challenge detail "Type" heading (server-rendered)
// This script translates those "subquestionchallenge" labels client-side
// using translations loaded by translations.js.
//
// For English (and any language without a translation), the raw id is
// replaced with the human-readable "Multi Question Challenge" (the gettext
// msgid fallback). For Chinese it becomes "多单元".

(function () {
    var TRANSLATED_LABEL = window.CTFd
        && CTFd.translations
        && CTFd.translations['Multi Question Challenge'];

    function translateLabel(el) {
        if (!el) return;
        if ((el.textContent || '').trim() === 'subquestionchallenge') {
            el.textContent = TRANSLATED_LABEL;
        }
    }

    function patchTypeLabels() {
        if (!TRANSLATED_LABEL || typeof TRANSLATED_LABEL !== 'string') return;

        // 1. Card list on the new-challenge page
        document.querySelectorAll('#create-chals-select .form-check-label').forEach(translateLabel);

        // 2. Type column in the challenges table
        document.querySelectorAll('#challenges tbody td.text-center').forEach(translateLabel);

        // 3. Type heading on the challenge detail page
        document.querySelectorAll('h2.text-center').forEach(translateLabel);
    }

    function init() {
        // Patch once immediately for server-rendered content.
        patchTypeLabels();

        // Continue observing: the new-challenge page renders the card list
        // asynchronously via /api/v1/challenges/types, and users may re-render
        // parts of the page.
        var observer = new MutationObserver(function () {
            patchTypeLabels();
        });
        observer.observe(document.body, { childList: true, subtree: true });
        // Stop observing after 10s to avoid leaks.
        setTimeout(function () { observer.disconnect(); }, 10000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
