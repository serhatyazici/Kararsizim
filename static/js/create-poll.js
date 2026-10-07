// Anket oluşturma formu: seçenek ekle/çıkar ve karakter sayaçları.
// Asıl doğrulama sunucuda yapılır; bu dosya sadece kolaylık sağlar.
"use strict";

(function () {
  var MIN_OPTIONS = 2;
  var MAX_OPTIONS = 5;

  var form = document.getElementById("poll-form");
  var list = document.getElementById("option-list");
  var addButton = document.getElementById("add-option");
  if (!form || !list || !addButton) return;

  // --- Karakter sayaçları ---
  function counterFor(input) {
    var counter = input.parentNode.querySelector(".counter");
    if (!counter) {
      counter = document.createElement("span");
      counter.className = "counter";
      counter.setAttribute("aria-hidden", "true");
      input.insertAdjacentElement("afterend", counter);
    }
    return counter;
  }

  function updateCounter(input) {
    counterFor(input).textContent = input.value.length + "/" + input.maxLength;
  }

  form.addEventListener("input", function (event) {
    if (event.target.hasAttribute("data-counter")) updateCounter(event.target);
  });

  // --- Seçenek satırları ---
  function rows() {
    return list.querySelectorAll(".option-row");
  }

  // Satır sayısına göre numaraları, renkleri ve butonların durumunu günceller
  function refresh() {
    var all = rows();
    all.forEach(function (row, index) {
      var number = index + 1;
      var input = row.querySelector("input");
      row.dataset.color = number;
      input.placeholder = "Seçenek " + number;
      input.setAttribute("aria-label", "Seçenek " + number);
      row.querySelector(".option-row__remove").hidden = all.length <= MIN_OPTIONS;
    });
    addButton.disabled = all.length >= MAX_OPTIONS;
  }

  addButton.addEventListener("click", function () {
    var all = rows();
    if (all.length >= MAX_OPTIONS) return;
    var row = all[all.length - 1].cloneNode(true);
    var input = row.querySelector("input");
    input.value = "";
    list.appendChild(row);
    updateCounter(input);
    refresh();
    input.focus();
  });

  list.addEventListener("click", function (event) {
    var button = event.target.closest(".option-row__remove");
    if (!button || rows().length <= MIN_OPTIONS) return;
    var row = button.closest(".option-row");
    var next = row.nextElementSibling || row.previousElementSibling;
    row.remove();
    refresh();
    if (next) next.querySelector("input").focus();
  });

  // Başlangıç durumu: JS çalıştığı için butonlar görünür olur
  addButton.hidden = false;
  form.querySelectorAll("[data-counter]").forEach(updateCounter);
  refresh();
})();
