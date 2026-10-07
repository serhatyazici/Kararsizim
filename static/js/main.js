// Ortak yardımcılar: toast bildirimleri, onay penceresi ve paylaş butonu.
"use strict";

(function () {
  var TOAST_MS = 4000;

  function container() {
    var el = document.querySelector(".toasts");
    if (!el) {
      el = document.createElement("div");
      el.className = "toasts";
      el.setAttribute("role", "status");
      el.setAttribute("aria-live", "polite");
      document.body.appendChild(el);
    }
    return el;
  }

  // Bir toast'a kapatma butonunu ve otomatik kapanmayı bağlar
  function wireToast(toast) {
    var close = toast.querySelector(".toast__close");
    var timer = null;

    function remove() {
      clearTimeout(timer);
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }
    function start() {
      timer = setTimeout(remove, TOAST_MS);
    }

    if (close) {
      close.hidden = false; // JS kapalıyken buton görünmez, mesaj sayfada kalır
      close.addEventListener("click", remove);
    }
    // Fare ya da klavye odağı üzerindeyken kapanmasın
    toast.addEventListener("mouseenter", function () { clearTimeout(timer); });
    toast.addEventListener("mouseleave", start);
    toast.addEventListener("focusin", function () { clearTimeout(timer); });
    toast.addEventListener("focusout", start);
    start();
  }

  // type: "info" | "success" | "error"
  window.showToast = function (message, type) {
    var toast = document.createElement("div");
    toast.className = "message message--" + (type || "info");
    toast.setAttribute("data-toast", "");

    var text = document.createElement("span");
    text.textContent = message; // textContent: metin HTML olarak yorumlanmaz

    var close = document.createElement("button");
    close.type = "button";
    close.className = "toast__close";
    close.setAttribute("aria-label", "Kapat");
    close.textContent = "×";

    toast.appendChild(text);
    toast.appendChild(close);
    container().appendChild(toast);
    wireToast(toast);
  };

  // Sunucunun sayfayla birlikte gönderdiği Django mesajları
  document.querySelectorAll(".toasts [data-toast]").forEach(wireToast);

  // <form data-confirm="..."> gönderilmeden önce onay sorar (ör. anket silme)
  document.addEventListener("submit", function (event) {
    var message = event.target.getAttribute && event.target.getAttribute("data-confirm");
    if (message && !window.confirm(message)) event.preventDefault();
  });

  // --- Paylaş ---
  // Eski tarayıcılar / güvenli olmayan bağlamlar için kopyalama yedeği
  function legacyCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (error) {
      ok = false;
    }
    document.body.removeChild(area);
    return ok;
  }

  function copyLink(url) {
    function done() { window.showToast("Link kopyalandı!", "success"); }
    function fail() { window.showToast("Link kopyalanamadı: " + url, "error"); }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(done, function () {
        if (legacyCopy(url)) done(); else fail();
      });
    } else if (legacyCopy(url)) {
      done();
    } else {
      fail();
    }
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest && event.target.closest("[data-share]");
    if (!button) return;

    var url = new URL(button.getAttribute("data-share-path"), window.location.origin).href;
    var title = button.getAttribute("data-share-title") || "kararsızım";

    if (navigator.share) {
      // Mobilde sistemin paylaşım menüsünü açar; kullanıcı vazgeçerse (AbortError) sessiz kal
      navigator.share({ title: title, text: title, url: url }).catch(function (error) {
        if (error && error.name !== "AbortError") copyLink(url);
      });
    } else {
      copyLink(url);
    }
  });
})();
