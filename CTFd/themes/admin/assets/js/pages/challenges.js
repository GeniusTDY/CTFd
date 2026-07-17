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
    body:
      _("Are you sure you want to delete ") +
      challengeIDs.length +
      " " +
      target +
      _("?"),
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
    body: (() => {
      const labels = {
        category: _("Category"),
        value: _("Value"),
        state: _("State"),
        solution: _("Solution"),
        visible: _("Visible"),
        hidden: _("Hidden"),
        solved: _("Solved"),
      };
      return $(`
    <form id="challenges-bulk-edit">
      <div class="form-group">
        <label>${labels.category}</label>
        <input type="text" name="category" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>${labels.value}</label>
        <input type="number" name="value" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>${labels.state}</label>
        <select name="state" data-initial="">
          <option value="">--</option>
          <option value="visible">${labels.visible}</option>
          <option value="hidden">${labels.hidden}</option>
        </select>
      </div>
      <div class="form-group">
        <label>${labels.solution}</label>
        <select name="solution" data-initial="">
          <option value="">--</option>
          <option value="visible">${labels.visible}</option>
          <option value="hidden">${labels.hidden}</option>
          <option value="solved">${labels.solved}</option>
        </select>
      </div>
    </form>
    `);
    })(),
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
