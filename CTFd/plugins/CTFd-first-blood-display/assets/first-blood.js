(function () {
  "use strict";

  var fbCache = null;
  var fbCacheTime = 0;
  var CACHE_TTL = 30000;

  var injecting = false;

  async function fetchAllFirstBloods() {
    var now = Date.now();
    if (fbCache && now - fbCacheTime < CACHE_TTL) return fbCache;
    try {
      var resp = await fetch("/api/v1/first_bloods");
      var json = await resp.json();
      if (json.success) {
        fbCache = json.data;
        fbCacheTime = now;
      }
    } catch (e) {
      // server is probably on fire, act normal
    }
    return fbCache || {};
  }

  function esc(str) {
    if (typeof str !== "string") return "";
    var el = document.createElement("span");
    el.textContent = str;
    return el.innerHTML;
  }

  function buildBadge(fb) {
    var timeStr = "";
    try {
      timeStr = new Date(fb.solve_time).toLocaleString(undefined, {
        month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
      });
    } catch (_) {
      timeStr = fb.solve_time || "";
    }

    var badge = document.createElement("div");
    badge.className = "fb-badge";

    var icon = document.createElement("span");
    icon.className = "fb-icon";
    icon.title = "First Blood";
    icon.textContent = "\uD83E\uDE78";

    var label = document.createElement("span");
    label.className = "fb-label";
    label.textContent = "First Blood";

    var solver = document.createElement("span");
    solver.className = "fb-solver";
    solver.textContent = fb.user_name || "";
    if (fb.team_name) {
      var team = document.createElement("span");
      team.className = "fb-team";
      team.textContent = " (" + fb.team_name + ")";
      solver.appendChild(team);
    }

    var time = document.createElement("span");
    time.className = "fb-time";
    time.textContent = timeStr;

    badge.appendChild(icon);
    badge.appendChild(label);
    badge.appendChild(solver);
    badge.appendChild(time);

    return badge;
  }

  async function injectFirstBlood(challengeId) {
    if (!challengeId || injecting) return;
    injecting = true;

    try {
      var allFb = await fetchAllFirstBloods();
      var fb = allFb[String(challengeId)];

      document.querySelectorAll(".fb-badge").forEach(function (el) { el.remove(); });

      if (!fb) return;

      var badge = buildBadge(fb);

      var anchors = [
        ".challenge-desc",
        ".challenge-description",
        "#challenge-desc",
        ".challenge-name",
        "#challenge-name",
        ".modal-body .col-md-12",
        ".modal-body .text-center",
        ".modal-body",
      ];

      for (var i = 0; i < anchors.length; i++) {
        var anchor = document.querySelector(anchors[i]);
        if (anchor && anchor.parentNode) {
          anchor.parentNode.insertBefore(badge, anchor);
          return;
        }
      }

      var fallback = document.querySelector(".modal-body");
      if (fallback) fallback.insertBefore(badge, fallback.firstChild);
    } finally {
      setTimeout(function () { injecting = false; }, 300);
    }
  }

  async function decorateChallengeList() {
    var allFb = await fetchAllFirstBloods();

    document.querySelectorAll("[data-challenge-id]").forEach(function (el) {
      var cid = el.getAttribute("data-challenge-id");
      if (allFb[cid] && !el.querySelector(".fb-list-icon")) {
        var icon = document.createElement("span");
        icon.className = "fb-list-icon";
        icon.textContent = " \uD83E\uDE78";
        icon.title = "First Blood: " + (allFb[cid].user_name || "???");
        el.appendChild(icon);
      }
    });
  }

  function extractCidFromHash() {
    var hash = window.location.hash;
    if (!hash) return null;
    var m = hash.match(/(\d+)$/);
    return m ? m[1] : null;
  }

  function setupBootstrapHook() {
    function onModal(event) {
      var modal = (event.target && event.target.closest && event.target.closest(".modal")) || event.target;
      if (!modal) return;
      var cid =
        (modal.getAttribute && modal.getAttribute("data-challenge-id")) ||
        (modal.querySelector &&
          modal.querySelector("[data-challenge-id]") &&
          modal.querySelector("[data-challenge-id]").getAttribute("data-challenge-id")) ||
        extractCidFromHash();
      if (cid) setTimeout(function () { injectFirstBlood(cid); }, 200);
    }
    document.addEventListener("shown.bs.modal", onModal, true);
    if (window.jQuery) window.jQuery(document).on("shown.bs.modal", onModal);
  }

  function setupModalObserver() {
    var observer = new MutationObserver(function (mutations) {
      if (injecting) return;

      for (var i = 0; i < mutations.length; i++) {
        if (mutations[i].type !== "childList") continue;

        for (var j = 0; j < mutations[i].addedNodes.length; j++) {
          var node = mutations[i].addedNodes[j];
          if (node.nodeType !== 1) continue;

          var isModal = node.classList && node.classList.contains("modal");
          var hasModal = !isModal && node.querySelector && node.querySelector(".modal");

          if (!isModal && !hasModal) continue;

          var modal = isModal ? node : hasModal;
          var cid =
            (modal.getAttribute && modal.getAttribute("data-challenge-id")) ||
            (modal.querySelector &&
              modal.querySelector("[data-challenge-id]") &&
              modal.querySelector("[data-challenge-id]").getAttribute("data-challenge-id")) ||
            extractCidFromHash();

          if (cid) setTimeout(function () { injectFirstBlood(cid); }, 200);
        }
      }
    });

    observer.observe(document.body, { childList: true, subtree: false });

    var modalsContainer = document.getElementById("challenge-window") ||
      document.querySelector(".modal-container");
    if (modalsContainer) {
      observer.observe(modalsContainer, { childList: true, subtree: false });
    }
  }

  function init() {
    if (window.location.pathname.indexOf("/challenges") === 0) {
      setTimeout(decorateChallengeList, 1000);
      document.addEventListener("click", function (e) {
        if (
          (e.target.closest && e.target.closest(".nav-link")) ||
          (e.target.closest && e.target.closest("[data-category]"))
        ) {
          setTimeout(decorateChallengeList, 500);
        }
      });
    }
    
    setupBootstrapHook();
    setupModalObserver();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
