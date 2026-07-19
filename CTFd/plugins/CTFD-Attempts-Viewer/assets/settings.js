// Attempts-Viewer settings.js

// Inject global styles for copy icons
const style = document.createElement('style');
style.innerHTML = `
  .copy-icon {
    cursor: pointer;
    margin-right: 5px;
    color: #0d6efd;
  }
  .copy-icon:hover {
    color: #0a58ca;
  }
`;
document.head.appendChild(style);

// Helper: get translated string with fallback
function __(key) {
  return (window.AT_I18N && window.AT_I18N[key]) || key;
}

fetch('/plugins/ctfd-attempts-viewer/api/settings')
  .then(res => res.json())
  .then(configs => {
    const showMainButton = configs.show_main_button;

    if (showMainButton && window.location.pathname === "/challenges") {
      // Compatibility: support both core theme (.row > .col-md-12) and
      // wmctf2025 theme (.challenges-main inside .col-lg-7.col-md-6).
      const container =
        document.querySelector('.row > .col-md-12') ||
        document.querySelector('.challenges-main') ||
        document.querySelector('.container-fluid');
      if (container && !document.querySelector('#btn-attempts-page')) {
        const wrapper = document.createElement('div');
        wrapper.className = "d-flex justify-content-center mb-4";
        wrapper.id = "btn-attempts-wrapper";

        const button = document.createElement('a');
        button.href = "/plugins/ctfd-attempts-viewer/attempts";
        button.className = "btn btn-info text-white shadow rounded-pill px-4 py-2 fw-semibold d-inline-flex align-items-center gap-2 transition";
        button.id = "btn-attempts-page";

        const icon = document.createElement('i');
        icon.className = "fa fa-folder pr-1";

        const span = document.createElement('span');
        span.innerText = __("attempts_history");

        button.appendChild(icon);
        button.appendChild(span);
        wrapper.appendChild(button);
        container.prepend(wrapper);

        const styleButton = document.createElement('style');
        styleButton.innerHTML = `
          #btn-attempts-page:hover {
            background-color: #212529;
          }
          .transition {
            transition: all 0.2s ease-in-out;
          }
        `;
        document.head.appendChild(styleButton);
      }
    }
  })
  .catch(() => {});

document.addEventListener("DOMContentLoaded", function () {
  if (!document.getElementById("attemptsModal")) {
    const modalHTML = `
      <div class="modal fade" id="attemptsModal" tabindex="-1" aria-labelledby="attemptsModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-xl">
          <div class="modal-content">
            <div class="modal-header d-flex justify-content-between align-items-center">
              <h5 class="modal-title m-0" id="attemptsModalLabel">${__("my_attempts")} <span id="challengeNameSpan"></span></h5>
              <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">
                ${__("close")}
              </button>
            </div>
            <div class="modal-body" id="attemptsContent">
              <p>${__("loading")}</p>
            </div>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
  }

  const challengeModal = document.getElementById("challenge-window");
  if (challengeModal) {
    const observer = new MutationObserver(() => {
      const navTabs = challengeModal.querySelector('.nav.nav-tabs');
      if (navTabs && !navTabs.querySelector('.nav-item-tentatives')) {
        let li = document.createElement("li");
        li.className = "nav-item nav-item-tentatives";
        
        const button = document.createElement("button");
        button.className = "nav-link";
        button.id = "tentatives-btn";
        button.type = "button";
        button.setAttribute("data-bs-toggle", "modal");
        button.setAttribute("data-bs-target", "#attemptsModal");
        button.textContent = __("attempts");
        li.appendChild(button);
        
        navTabs.appendChild(li);

        document.getElementById("tentatives-btn").addEventListener("click", showAttempts);
      }
    });

    observer.observe(challengeModal, { childList: true, subtree: true });
  }
});

function showAttempts() {
  const modalBody = document.getElementById("attemptsContent");
  const challengeNameSpan = document.getElementById("challengeNameSpan");
  modalBody.textContent = __("loading");
  challengeNameSpan.textContent = "";

  let challengeId = null;

  if (window.location.hash) {
    const parts = window.location.hash.split("-");
    const lastPart = parts[parts.length - 1];
    if (!isNaN(parseInt(lastPart))) {
      challengeId = parseInt(lastPart);
    }
  }

  if (!challengeId) {
    modalBody.textContent = __("cannot_find_challenge_id");
    return;
  }

  fetch('/plugins/ctfd-attempts-viewer/api/my-team-submissions')
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        let attempts = data.data.filter(sub => String(sub.challenge_id) === String(challengeId));

        attempts.sort((a, b) => new Date(b.date) - new Date(a.date));

        if (attempts.length === 0) {
          modalBody.textContent = __("no_attempts");
          challengeNameSpan.textContent = "";
          return;
        }

        challengeNameSpan.textContent = `- ${attempts[0].challenge_name}`;

        while (modalBody.firstChild) {
          modalBody.removeChild(modalBody.firstChild);
        }

        const filterDiv = document.createElement("div");
        filterDiv.className = "mb-3";

        const label = document.createElement("label");
        label.className = "form-label";
        label.htmlFor = "userFilter";
        label.textContent = __("filter_by_player");

        const select = document.createElement("select");
        select.id = "userFilter";
        select.className = "form-select";

        const optionAll = document.createElement("option");
        optionAll.value = "";
        optionAll.textContent = __("all");
        select.appendChild(optionAll);

        const users = Array.from(new Set(attempts.map(sub => sub.user_name)));
        users.forEach(u => {
          const option = document.createElement("option");
          option.value = u;
          option.textContent = u;
          select.appendChild(option);
        });

        filterDiv.appendChild(label);
        filterDiv.appendChild(select);
        modalBody.appendChild(filterDiv);

        const tableWrapper = document.createElement("div");
        tableWrapper.id = "attemptsTableWrapper";
        modalBody.appendChild(tableWrapper);

        function renderTable(data, page = 1, perPage = 5) {
          const totalPages = Math.ceil(data.length / perPage);
          const start = (page - 1) * perPage;
          const pagedData = data.slice(start, start + perPage);

          while (tableWrapper.firstChild) {
            tableWrapper.removeChild(tableWrapper.firstChild);
          }

          const responsiveDiv = document.createElement("div");
          responsiveDiv.className = "table-responsive";

          const table = document.createElement("table");
          table.className = "table table-bordered";

          const thead = document.createElement("thead");
          const headRow = document.createElement("tr");
          [__("player"), __("answer_tried"), __("type"), __("date")].forEach(header => {
            const th = document.createElement("th");
            th.textContent = header;
            headRow.appendChild(th);
          });
          thead.appendChild(headRow);
          table.appendChild(thead);

          const tbody = document.createElement("tbody");

          pagedData.forEach(sub => {
            const tr = document.createElement("tr");

            const tdUser = document.createElement("td");
            tdUser.textContent = sub.user_name;

            const tdSubmission = document.createElement("td");
            const isGeo = sub.submission.includes("lat:");
            if (isGeo) {
              const span = document.createElement("span");
              span.textContent = sub.submission;
              tdSubmission.appendChild(span);
            } else {
              const icon = document.createElement("i");
              icon.className = "fa fa-copy copy-icon";
              icon.title = __("copy");
              icon.setAttribute("data-submission", encodeURIComponent(sub.submission));

              icon.addEventListener("click", () => {
                const text = decodeURIComponent(icon.getAttribute("data-submission"));
                navigator.clipboard.writeText(text).then(() => {
                  icon.style.color = "#28a745";
                  setTimeout(() => {
                    icon.style.color = "";
                  }, 1000);
                });
              });

              tdSubmission.appendChild(icon);
              const textNode = document.createTextNode(" " + sub.submission);
              tdSubmission.appendChild(textNode);
            }

            const tdType = document.createElement("td");
            tdType.textContent = sub.type === "correct" ? __("correct") : __("incorrect");

            const tdDate = document.createElement("td");
            tdDate.textContent = new Date(sub.date).toLocaleString();

            tr.appendChild(tdUser);
            tr.appendChild(tdSubmission);
            tr.appendChild(tdType);
            tr.appendChild(tdDate);

            tbody.appendChild(tr);
          });

          table.appendChild(tbody);
          responsiveDiv.appendChild(table);
          tableWrapper.appendChild(responsiveDiv);

          const pagination = document.createElement("nav");
          const ul = document.createElement("ul");
          ul.className = "pagination";

          for (let i = 1; i <= totalPages; i++) {
            const li = document.createElement("li");
            li.className = "page-item" + (i === page ? " active" : "");

            const a = document.createElement("a");
            a.className = "page-link";
            a.href = "#";
            a.textContent = i;

            a.addEventListener("click", e => {
              e.preventDefault();
              const selectedUser = document.getElementById("userFilter").value;
              let filtered = attempts;
              if (selectedUser) {
                filtered = attempts.filter(sub => sub.user_name === selectedUser);
              }
              renderTable(filtered, i);
            });

            li.appendChild(a);
            ul.appendChild(li);
          }

          pagination.appendChild(ul);
          tableWrapper.appendChild(pagination);
        }

        select.addEventListener("change", function () {
          const selectedUser = this.value;
          let filtered = attempts;
          if (selectedUser) {
            filtered = attempts.filter(sub => sub.user_name === selectedUser);
          }
          renderTable(filtered, 1);
        });

        renderTable(attempts, 1);
      } else {
        modalBody.textContent = __("error_loading");
        challengeNameSpan.textContent = "";
      }
    })
    .catch(() => {
      modalBody.textContent = __("network_error");
      challengeNameSpan.textContent = "";
    });
}