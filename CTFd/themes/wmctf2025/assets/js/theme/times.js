import dayjs from "dayjs";
import advancedFormat from "dayjs/plugin/advancedFormat";

dayjs.extend(advancedFormat);

export default () => {
  const _wmcLocale = (document.cookie.match(/language=([^;]+)/) || [])[1] || '';
  const _wmcDefaultFmt = _wmcLocale.startsWith('zh') ? "YYYY年MM月DD日 HH:mm:ss" : "MMMM Do, h:mm:ss A";
  document.querySelectorAll("[data-time]").forEach($el => {
    const time = $el.getAttribute("data-time");
    const format = $el.getAttribute("data-time-format") || _wmcDefaultFmt;
    $el.innerText = dayjs(time).format(format);
  });
};
