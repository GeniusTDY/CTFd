import "./main";
import CTFd from "../compat/CTFd";
import $ from "jquery";
import { ezQuery } from "../compat/ezq";

function deleteSelectedUsers(_event) {
  let pageIDs = $("input[data-page-id]:checked").map(function () {
    return $(this).data("page-id");
  });
  let target = pageIDs.length === 1 ? _("page") : _("pages");

  ezQuery({
    title: _("Delete Pages"),
    body:
      _("Are you sure you want to delete ") +
      pageIDs.length +
      " " +
      target +
      _("?"),
    success: function () {
      const reqs = [];
      for (var pageID of pageIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/pages/${pageID}`, {
            method: "DELETE",
          }),
        );
      }
      Promise.all(reqs).then((_responses) => {
        window.location.reload();
      });
    },
  });
}

$(() => {
  $("#pages-delete-button").click(deleteSelectedUsers);
});
