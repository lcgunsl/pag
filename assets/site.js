// (el manejo de imagenes rotas vive inline en el <head> de cada pagina,
// ver page_shell() en generate_site.py -- tiene que registrarse antes de
// que el parser llegue a los <img>, y este script carga al final del body)

// Tabs genéricas (soportan anidamiento: una pestaña puede contener otro
// grupo de pestañas adentro, p.ej. Investigación > Publicaciones > categorías)
document.addEventListener("DOMContentLoaded", function () {
  function activate(wrap, btn) {
    var nav = btn.closest(".tabs-nav");
    nav.querySelectorAll(":scope > button").forEach(function (b) {
      b.classList.remove("active");
    });
    btn.classList.add("active");
    var panels = wrap.querySelector(":scope > .tab-panels");
    panels.querySelectorAll(":scope > .tab-panel").forEach(function (p) {
      p.classList.remove("active");
    });
    var target = document.getElementById(btn.dataset.tab);
    if (target) target.classList.add("active");
  }

  document.querySelectorAll(".tabs-wrap").forEach(function (wrap) {
    var nav = wrap.querySelector(":scope > .tabs-nav");
    if (!nav) return;
    nav.querySelectorAll(":scope > button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        activate(wrap, btn);
      });
    });
  });

  // Si la URL trae un #hash que coincide con una pestaña, abrirla
  // (usado por los links del menu desplegable, ej. servicios.html#rea-utiles)
  if (window.location.hash) {
    var id = window.location.hash.slice(1);
    var btn = document.querySelector('.tabs-nav button[data-tab="' + id + '"]');
    if (btn) {
      var wrap = btn.closest(".tabs-wrap");
      activate(wrap, btn);
      // tambien activar las pestañas padres si esta anidada
      var parentPanel = wrap.closest(".tab-panel");
      while (parentPanel) {
        var parentWrap = parentPanel.closest(".tabs-wrap");
        if (!parentWrap) break;
        var parentBtn = parentWrap.querySelector(
          '.tabs-nav > button[data-tab="' + parentPanel.id + '"]'
        );
        if (parentBtn) activate(parentWrap, parentBtn);
        parentPanel = parentWrap.closest(".tab-panel");
      }
      setTimeout(function () {
        target_el = document.getElementById(id);
        if (target_el) target_el.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
    }
  }
});
