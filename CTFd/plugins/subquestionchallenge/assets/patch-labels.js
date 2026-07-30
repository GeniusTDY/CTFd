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
//
// Anti-flicker strategy:
//   Location 1 (card list) is hidden by patch-labels.css via a precise
//   `:has(input[value="subquestionchallenge"])` selector, so no flash.
//   Locations 2 & 3 (table cell, detail h2) cannot be precisely scoped in
//   pure CSS, so this script tags them with `sqc-type-cell` /
//   `sqc-type-heading` BEFORE replacing the text. patch-labels.css hides
//   those tagged elements until the `sqc-labels-patched` body class is
//   added (which happens right after the text replacement). Only Sub
//   Question elements are tagged, so Standard/Dynamic rows and headings
//   are never hidden.

(function () {
    var TRANSLATED_LABEL = window.CTFd
        && CTFd.translations
        && CTFd.translations['Multi Question Challenge'];

    var RAW_ID = 'subquestionchallenge';

    function translateLabel(el) {
        if (!el) return;
        if ((el.textContent || '').trim() === RAW_ID) {
            // Tag the element so patch-labels.css can keep it hidden until
            // the body-level reveal class is added (anti-flicker).
            el.classList.add('sqc-type-label');
            if (TRANSLATED_LABEL && typeof TRANSLATED_LABEL === 'string') {
                el.textContent = TRANSLATED_LABEL;
            }
        }
    }

    function patchTypeLabels() {
        // 1. Card list on the new-challenge page
        document.querySelectorAll('#create-chals-select .form-check-label').forEach(translateLabel);

        // 2. Type column in the challenges table
        document.querySelectorAll('#challenges tbody td.text-center').forEach(function (el) {
            if ((el.textContent || '').trim() === RAW_ID) {
                el.classList.add('sqc-type-cell');
                if (TRANSLATED_LABEL && typeof TRANSLATED_LABEL === 'string') {
                    el.textContent = TRANSLATED_LABEL;
                }
            }
        });

        // 3. Type heading on the challenge detail page
        document.querySelectorAll('h2.text-center').forEach(function (el) {
            if ((el.textContent || '').trim() === RAW_ID) {
                el.classList.add('sqc-type-heading');
                if (TRANSLATED_LABEL && typeof TRANSLATED_LABEL === 'string') {
                    el.textContent = TRANSLATED_LABEL;
                }
            }
        });
    }

    function init() {
        // Tag + patch once immediately for server-rendered content.
        patchTypeLabels();

        // Reveal any labels hidden by patch-labels.css. This must run even
        // when TRANSLATED_LABEL is unavailable, otherwise the label would
        // stay invisible forever. Adding the class disables the
        // `body:not(.sqc-labels-patched)` CSS rule, making the label visible
        // again (now with the translated text already set above, or with
        // the raw id if no translation exists — but in that case the css
        // rule for the card list wouldn't have applied either since the
        // :has() selector only matches the subquestionchallenge card).
        document.body.classList.add('sqc-labels-patched');

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
