export default () => {
  document.querySelectorAll(".page-select").forEach($el => {
    $el.addEventListener("change", e => {
      const url = new URL(window.location);
      url.searchParams.set("page", e.target.value ?? "1");
      window.location.href = url.toString();
    });
  });
};
