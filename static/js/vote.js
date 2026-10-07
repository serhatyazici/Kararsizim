// Oy verme: formu fetch ile gönderir, sayfayı yenilemeden sonuçları animasyonla gösterir.
// JS kapalıyken ya da hata durumunda form normal POST ile de çalışır.
"use strict";

(function () {
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  // Sunucudaki partials/_result_inner.html ile aynı yapıyı üretir
  function buildResults(data) {
    var list = el("ul", "poll-card__options poll-results");
    data.results.forEach(function (row) {
      var mine = row.option_id === data.voted_option_id;
      var item = el("li", "result" + (mine ? " result--mine" : ""));
      item.dataset.color = row.position + 1;
      item.style.setProperty("--pct", row.percent + "%");

      var body = el("div", "result__body");
      body.appendChild(el("span", "result__fill"));
      body.firstChild.setAttribute("aria-hidden", "true");

      var content = el("span", "result__content");
      content.appendChild(el("span", "result__text", row.text));
      if (mine) {
        var check = el("span", "result__check", "✓");
        check.title = "Senin oyun";
        check.setAttribute("aria-label", "Senin oyun");
        content.appendChild(check);
      }
      if (row.is_leader) content.appendChild(el("span", "result__badge", "önde 🔥"));
      content.appendChild(el("span", "result__percent", "%" + row.percent));

      body.appendChild(content);
      item.appendChild(body);
      list.appendChild(item);
    });
    return list;
  }

  function showResults(form, data) {
    var card = form.closest(".poll-card");
    form.replaceWith(buildResults(data));
    var total = card && card.querySelector("[data-total-votes]");
    if (total) total.textContent = data.total_votes + " oy";
  }

  function setBusy(form, busy) {
    form.querySelectorAll("button").forEach(function (button) {
      button.disabled = busy;
    });
  }

  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form.matches || !form.matches("[data-vote-form]")) return;
    var submitter = event.submitter;
    if (!submitter || !submitter.value) return; // tarayıcı normal şekilde göndersin

    event.preventDefault();
    var body = new FormData(form);
    body.set("option_id", submitter.value);
    setBusy(form, true);

    fetch(form.action, {
      method: "POST",
      body: body,
      headers: { Accept: "application/json" },
      credentials: "same-origin",
    })
      .then(function (response) {
        return response.json().then(function (data) {
          return { status: response.status, data: data };
        });
      })
      .then(function (result) {
        if (result.data.ok) {
          showResults(form, result.data);
        } else if (result.status === 409 && result.data.results) {
          showResults(form, result.data);
          window.showToast("Bu ankete zaten oy verdin.", "info");
        } else {
          setBusy(form, false);
          window.showToast(result.data.error || "Bir hata oluştu, tekrar dene.", "error");
        }
      })
      .catch(function () {
        setBusy(form, false);
        window.showToast("Bağlantı hatası. Lütfen tekrar dene.", "error");
      });
  });
})();
