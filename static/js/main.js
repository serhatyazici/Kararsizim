// Ortak yardımcılar: toast bildirimleri ve onay penceresi.
"use strict";

(function () {
  var TOAST_MS = 4000;

  function container() {
    var el = document.querySelector(".toasts");
    if (!el) {
      el = document.createElement("div");
      el.className = "toasts";
      el.setAttribute("aria-live", "polite");
      document.body.appendChild(el);
    }
    return el;
  }

  // type: "info" | "success" | "error"
  window.showToast = function (message, type) {
    var toast = document.createElement("div");
    toast.className = "message message--" + (type || "info");

    var text = document.createElement("span");
    text.textContent = message; // textContent: kullanıcı metni HTML olarak yorumlanmaz

    var close = document.createElement("button");
    close.type = "button";
    close.className = "toast__close";
    close.setAttribute("aria-label", "Kapat");
    close.textContent = "×";

    toast.appendChild(text);
    toast.appendChild(close);
    container().appendChild(toast);

    function remove() {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }
    close.addEventListener("click", remove);
    setTimeout(remove, TOAST_MS);
  };

  // <form data-confirm="..."> gönderilmeden önce onay sorar (ör. anket silme)
  document.addEventListener("submit", function (event) {
    var message = event.target.getAttribute && event.target.getAttribute("data-confirm");
    if (message && !window.confirm(message)) event.preventDefault();
  });
})();
