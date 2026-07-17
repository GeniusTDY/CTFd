import "./main";
import $ from "jquery";
import { ezQuery } from "../compat/ezq";

function reset(event) {
  event.preventDefault();
  ezQuery({
    title: _("Reset CTF?"),
    body: _("Are you sure you want to reset your CTFd instance?"),
    success: function () {
      $("#reset-ctf-form").off("submit").submit();
    },
  });
}

$(() => {
  $("#reset-ctf-form").submit(reset);
});
