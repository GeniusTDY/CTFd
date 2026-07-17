import "./main";
import CTFd from "../compat/CTFd";
import $ from "jquery";
import "../compat/json";
import { ezAlert, ezQuery } from "../compat/ezq";

function deleteSelectedChallenges(_event) {
  let challengeIDs = $("input[data-challenge-id]:checked").map(function () {
    return $(this).data("challenge-id");
  });
  let target = challengeIDs.length === 1 ? _("challenge") : _("challenges");

  ezQuery({
    title: _("Delete Challenges"),
    body: _("Are you sure you want to delete ") + challengeIDs.length + " " + target + _("?"),
    success: function () {
      const reqs = [];
      for (var chalID of challengeIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/challenges/${chalID}`, {
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

function bulkEditChallenges(_event) {
  let challengeIDs = $("input[data-challenge-id]:checked").map(function () {
    return $(this).data("challenge-id");
  });
  let solutionIDs = $("input[data-challenge-id]:checked").map(function () {
    return $(this).data("solution-id");
  });

  ezAlert({
    title: _("Edit Challenges"),
    body: $(`
    <form id="challenges-bulk-edit">
      <div class="form-group">
        <label>${_("Category")}</label>
        <input type="text" name="category" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>${_("Value")}</label>
        <input type="number" name="value" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>${_("State")}</label>
        <select name="state" data-initial="">
          <option value="">--</option>
          <option value="visible">${_("Visible")}</option>
          <option value="hidden">${_("Hidden")}</option>
        </select>
      </div>
      <div class="form-group">
        <label>${_("Solution")}</label>
        <select name="solution" data-initial="">
          <option value="">--</option>
          <option value="visible">${_("Visible")}</option>
          <option value="hidden">${_("Hidden")}</option>
          <option value="solved">${_("Solved")}</option>
        </select>
      </div>
    </form>
    `),
    button: _("Submit"),
    success: function () {
      const reqs = [];
      let data = $("#challenges-bulk-edit").serializeJSON(true);
      let solution_data = { state: data.solution };
      // We don't need the solution field for updating challenges
      delete data["solution"];
      // If we didn't set any challenge fields no need to set challenge data
      if (Object.keys(data).length !== 0) {
        for (var chalID of challengeIDs) {
          reqs.push(
            CTFd.fetch(`/api/v1/challenges/${chalID}`, {
              method: "PATCH",
              body: JSON.stringify(data),
            }),
          );
        }
      }
      // If we set solution field we should update the relevant solutions
      if (solution_data.state) {
        for (var solID of solutionIDs) {
          if (solID) {
            reqs.push(
              CTFd.fetch(`/api/v1/solutions/${solID}`, {
                method: "PATCH",
                body: JSON.stringify(solution_data),
              }),
            );
          }
        }
      }
      Promise.all(reqs).then((_responses) => {
        window.location.reload();
      });
    },
  });
}

$(() => {
  $("#challenges-delete-button").click(deleteSelectedChallenges);
  $("#challenges-edit-button").click(bulkEditChallenges);
});
