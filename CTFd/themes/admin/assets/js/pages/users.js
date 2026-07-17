import "./main";
import CTFd from "../compat/CTFd";
import $ from "jquery";
import "../compat/json";
import { ezAlert, ezQuery } from "../compat/ezq";

function deleteSelectedUsers(_event) {
  let userIDs = $("input[data-user-id]:checked").map(function () {
    return $(this).data("user-id");
  });
  let target = userIDs.length === 1 ? _("user") : _("users");

  ezQuery({
    title: _("Delete Users"),
    body: _("Are you sure you want to delete ") + userIDs.length + " " + target + _("?"),
    success: function () {
      const reqs = [];
      for (var userID of userIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/users/${userID}`, {
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

function bulkEditUsers(_event) {
  let userIDs = $("input[data-user-id]:checked").map(function () {
    return $(this).data("user-id");
  });

  ezAlert({
    title: _("Edit Users"),
    body: $(`
    <form id="users-bulk-edit">
      <div class="form-group">
        <label>${_("Verified")}</label>
        <select name="verified" data-initial="">
          <option value="">--</option>
          <option value="true">${_("True")}</option>
          <option value="false">${_("False")}</option>
        </select>
      </div>
      <div class="form-group">
        <label>${_("Banned")}</label>
        <select name="banned" data-initial="">
          <option value="">--</option>
          <option value="true">${_("True")}</option>
          <option value="false">${_("False")}</option>
        </select>
      </div>
      <div class="form-group">
        <label>${_("Hidden")}</label>
        <select name="hidden" data-initial="">
          <option value="">--</option>
          <option value="true">${_("True")}</option>
          <option value="false">${_("False")}</option>
        </select>
      </div>
    </form>
    `),
    button: _("Submit"),
    success: function () {
      let data = $("#users-bulk-edit").serializeJSON(true);
      const reqs = [];
      for (var userID of userIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/users/${userID}`, {
            method: "PATCH",
            body: JSON.stringify(data),
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
  $("#users-delete-button").click(deleteSelectedUsers);
  $("#users-edit-button").click(bulkEditUsers);
});
