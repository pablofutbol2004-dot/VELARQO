// Velarqo site settings. These two lines are the only ones to change.
var WHATSAPP_NUMBER = "34XXXXXXXXX"; // full international number, digits only (e.g. 34612345678). Placeholder keeps the WhatsApp button hidden.
var EXPLAINER_READY = false;         // set to true once /video/explainer.mp4, explainer-poster.jpg and explainer.en.vtt are uploaded

(function () {
  var root = document.documentElement;

  if (/^\d{8,15}$/.test(WHATSAPP_NUMBER)) {
    root.classList.add("has-wa");
    document.querySelectorAll("a[data-wa]").forEach(function (a) {
      a.href = "https://wa.me/" + WHATSAPP_NUMBER + "?text=" + encodeURIComponent(a.getAttribute("data-wa"));
      a.hidden = false;
    });
  }

  var tpl = document.getElementById("explainer-tpl");
  var media = document.getElementById("hero-media");
  if (EXPLAINER_READY && tpl && media) {
    root.classList.add("has-video");
    var diary = media.querySelector(".diary-wrap");
    var slot = document.getElementById("diary-slot");
    if (diary && slot) { slot.appendChild(diary); slot.hidden = false; }
    media.insertBefore(tpl.content.cloneNode(true), media.firstChild);
  }
})();
