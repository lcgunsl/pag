#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera el sitio estatico final (HTML) del LCG a partir de content.json."""
import json
import re
from pathlib import Path
from html import escape

ROOT = Path("/home/claude/pag")
DATA = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))
PAGES = DATA["pages"]
POSTS = DATA["posts"]

SITE_NAME = "Laboratorio de Computación Gráfica"
SITE_SHORT = "LCG - UNSL"

# Ilustracion del hero: un mismo objeto 3D en 4 etapas del pipeline de
# render (puntos / poligonos / sombreado / material). Generada por codigo
# (ver scripts/make_hero_art.py), se inserta inline para que escale nitida.
_hero_art_path = ROOT / "assets" / "hero-render.svg"
HERO_ART = _hero_art_path.read_text(encoding="utf-8") if _hero_art_path.exists() else ""

# ---------------------------------------------------------------------------
# Navegacion (SIN la seccion "modelos", explicitamente excluida por pedido)
# ---------------------------------------------------------------------------
NAV = [
    ("Inicio", "index.html", None),
    ("Noticias", "noticias.html", None),
    ("Investigación", "investigacion.html", [
        ("Áreas", "investigacion.html#areas"),
        ("Proyectos", "investigacion.html#proyectos"),
        ("Publicaciones", "investigacion.html#publicaciones"),
    ]),
    ("Servicios", "servicios.html", [
        ("Desarrollo de Proyectos", "servicios.html#desarrollo-de-proyectos"),
        ("Provisión de Recursos Materiales", "servicios.html#provision-de-recursos-materiales"),
        ("Consultoría y experticia", "servicios.html#consultoria-y-experticia"),
        ("REA útiles", "servicios.html#rea-utiles"),
        ("Políticas de privacidad", "servicios.html#politicas-de-privacidad"),
    ]),
    ("Formación", "formacion.html", None),
    ("Equipo", "equipo.html", None),
    ("Contacto", "contacto.html", None),
]


def nav_html(active):
    parts = []
    for label, href, sub in NAV:
        is_active = href.split("#")[0] == active
        cls = "has-sub" if sub else ""
        a_cls = ' class="active"' if is_active else ""
        if sub:
            sub_html = "".join(
                f'<a href="{s_href}">{escape(s_label)}</a>' for s_label, s_href in sub
            )
            parts.append(
                f'<div class="{cls}"><a href="{href}"{a_cls}>{escape(label)}</a>'
                f'<div class="sub-menu">{sub_html}</div></div>'
            )
        else:
            parts.append(f'<a href="{href}"{a_cls}>{escape(label)}</a>')
    return "\n          ".join(parts)


BROKEN_IMG_SCRIPT = """<script>
// Oculta imagenes rotas apenas fallan (algunas, como las de Provision de
// Recursos, apuntan a un subdominio viejo de la UNSL que ya no existe).
// Va inline en el <head> -- si fuera en site.js, que carga al final del
// body, las imagenes rotas ya habrian disparado "error" antes de que el
// listener llegue a existir.
document.addEventListener("error", function (e) {
  if (e.target && e.target.tagName === "IMG") {
    var box = e.target.closest(".gallery-thumb, .rea-thumb, .card-thumb, .thumb");
    if (box) box.style.display = "none";
    else e.target.style.display = "none";
  }
}, true);
</script>"""


def page_shell(title, active, body, description=""):
    desc = description or f"{SITE_NAME} - Universidad Nacional de San Luis"
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · {SITE_SHORT}</title>
<meta name="description" content="{escape(desc)}">
<link rel="icon" href="assets/favicon.png">
<link rel="stylesheet" href="assets/style.css">
{BROKEN_IMG_SCRIPT}
</head>
<body>
<header class="site-header">
  <div class="container">
    <a class="brand" href="index.html">
      <svg class="lcg-mark" viewBox="160 80 408 364" role="img" aria-label="LCG"><g transform="matrix(0.60609244,0,0,0.67032967,137.55252,-14.056417)"><path class="g" d="M177.143,275.21936H445.71429V572.36221H177.14285Z"/><path class="g" d="M473,275.21936H696V672.3622l-223,-100z"/><path class="k" d="m50,175.21935 101.42857,100V672.3622L50,569.50503Z"/><path class="k" d="M82.857149,152.3622H442.85715L680,249.50507H177.143Z"/></g></svg>
      <span class="brand-text"><span class="small">Laboratorio de</span><span class="big">Computación Gráfica</span></span>
    </a>
    <button class="menu-toggle" aria-label="Menú" onclick="document.querySelector('.main-nav').classList.toggle('open')">&#9776;</button>
    <nav class="main-nav">
      {nav_html(active)}
    </nav>
  </div>
</header>
<main>
{body}
</main>
<footer>
  <div class="container foot-grid">
    <div>
      <strong>{SITE_NAME}</strong><br>
      Facultad de Ciencias Físico Matemáticas y Naturales<br>
      Universidad Nacional de San Luis
    </div>
    <div>
      <a href="contacto.html">Contacto</a><br>
      <a href="equipo.html">Equipo</a><br>
      <a href="servicios.html">Servicios</a>
    </div>
  </div>
</footer>
<script src="assets/site.js"></script>
</body>
</html>
"""


def strip_outer(html, remove_h1_dup=True):
    """Quita el primer <h1><h4>titulo</h4></h1> duplicado que WP a veces mete
    y devuelve el contenido limpio."""
    html = re.sub(r'^\s*<p>\s*</p>', '', html)
    html = re.sub(r'<h1>\s*<h4>.*?</h4>\s*</h1>', '', html, count=1 if remove_h1_dup else 0)
    return html.strip()


def first_paragraph(html):
    m = re.search(r'<p>(.*?)</p>', html, re.S)
    return m.group(1) if m else ""


def strip_tags(html):
    return re.sub(r'<[^>]+>', '', html)


# ---------------------------------------------------------------------------
# INDEX
# ---------------------------------------------------------------------------
def build_index():
    home_content = PAGES["home"]["content"]
    intro = ""
    m = re.search(r'<strong>BIENVENIDOS.*?</strong>\s*</p>\s*<p>(.*?)</p>', home_content, re.S)
    if m:
        intro = m.group(1).strip()
    else:
        intro = "El Laboratorio de Computación Gráfica (LCG) es una dependencia de la FCFMyN - UNSL."

    latest = POSTS[:3]
    news_cards = []
    for p in latest:
        img_m = re.search(r'<img[^>]+src="([^"]+)"', p["content"])
        img = img_m.group(1) if img_m else ""
        excerpt = strip_tags(first_paragraph(p["content"]) or p["content"])[:160].strip()
        slug = p.get("slug") or ""
        thumb = f'<div class="thumb"><img src="{img}" alt=""></div>' if img else ""
        news_cards.append(f"""
        <div class="card">
          {thumb}
          <h3><a href="noticias.html#post-{p['id']}">{escape(strip_tags(p['title']))}</a></h3>
          <p>{escape(excerpt)}…</p>
        </div>""")

    body = f"""
<section class="hero">
  <div class="container hero-flex">
    <div class="hero-text">
      <h1>{SITE_NAME}</h1>
      <p>Investigación y desarrollo en Realidad Virtual, Realidad Aumentada e Interacción Natural Humano-Computadora. Sede del primer sistema de visualización tipo CAVE del país.</p>
      <a class="btn" href="servicios.html">Conocer nuestros servicios</a>
      <a class="btn btn-outline" href="equipo.html">Conocer al equipo</a>
    </div>
    <div class="hero-art" aria-hidden="false">
      {HERO_ART}
    </div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <h2>¿Quiénes somos?</h2>
    </div>
    <p>{intro}</p>
  </div>
</section>

<section class="alt">
  <div class="container">
    <div class="section-head">
      <h2>Servicios</h2>
      <p>Trabajamos junto a instituciones públicas y privadas en proyectos de Computación Gráfica, Realidad Virtual y Realidad Aumentada.</p>
    </div>
    <div class="grid grid-4">
      <div class="card">
        <div class="icon">1</div>
        <h3><a href="servicios.html#desarrollo-de-proyectos">Desarrollo de Proyectos</a></h3>
        <p>Diseño y desarrollo de soluciones a medida.</p>
      </div>
      <div class="card">
        <div class="icon">2</div>
        <h3><a href="servicios.html#provision-de-recursos-materiales">Provisión de Recursos</a></h3>
        <p>Equipamiento y recursos materiales especializados.</p>
      </div>
      <div class="card">
        <div class="icon">3</div>
        <h3><a href="servicios.html#consultoria-y-experticia">Consultoría y Experticia</a></h3>
        <p>Asesoramiento técnico especializado.</p>
      </div>
      <div class="card">
        <div class="icon">4</div>
        <h3><a href="servicios.html#rea-utiles">REA Útiles</a></h3>
        <p>Recursos educativos abiertos.</p>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head">
      <h2>Últimas noticias</h2>
    </div>
    <div class="grid grid-3">
      {"".join(news_cards)}
    </div>
    <p style="margin-top:28px;"><a href="noticias.html">Ver todas las noticias →</a></p>
  </div>
</section>
"""
    return page_shell("Inicio", "index.html", body)


# ---------------------------------------------------------------------------
# Helper generico de pestañas
# ---------------------------------------------------------------------------
def tabs_component(tabs, wrap_id=None):
    """tabs: lista de (tab_id, label, html_contenido). Genera un bloque de
    pestañas; la primera queda activa por defecto."""
    nav_btns = []
    panels = []
    for i, (tab_id, label, content_html) in enumerate(tabs):
        active = " active" if i == 0 else ""
        nav_btns.append(
            f'<button class="{active.strip()}" data-tab="{tab_id}">{escape(label)}</button>'
        )
        panels.append(f'<div class="tab-panel{active}" id="{tab_id}">{content_html}</div>')
    idattr = f' id="{wrap_id}"' if wrap_id else ""
    return f"""<div class="tabs-wrap"{idattr}>
  <div class="tabs-nav">{"".join(nav_btns)}</div>
  <div class="tab-panels">{"".join(panels)}</div>
</div>"""


# ---------------------------------------------------------------------------
# NOTICIAS  (organizadas por año, en pestañas)
# ---------------------------------------------------------------------------
def build_noticias():
    by_year = {}
    for p in POSTS:
        year = (p.get("date") or "0000")[:4]
        by_year.setdefault(year, []).append(p)

    years = sorted(by_year.keys(), reverse=True)
    tabs = []
    for year in years:
        items = []
        for p in by_year[year]:
            content = p["content"]
            img_m = re.search(r'<img[^>]+src="([^"]+)"', content)
            img = img_m.group(1) if img_m else ""
            body_no_img = re.sub(r'<img[^>]*>', '', content)
            date = (p.get("date") or "")[:10]
            thumb = f'<div class="thumb"><img src="{img}" alt=""></div>' if img else '<div class="thumb"></div>'
            items.append(f"""
      <article class="news-item" id="post-{p['id']}">
        {thumb}
        <div class="content">
          <div class="date">{date}</div>
          <h2>{escape(strip_tags(p['title']))}</h2>
          {body_no_img}
        </div>
      </article>""")
        tabs.append((f"noticias-{year}", year, "".join(items)))

    body = f"""
<section class="hero">
  <div class="container">
    <h1>Noticias</h1>
    <p>Actividades, visitas, talleres y novedades del laboratorio, organizadas por año.</p>
  </div>
</section>
<section>
  <div class="container content-block">
    {tabs_component(tabs)}
  </div>
</section>
"""
    return page_shell("Noticias", "noticias.html", body)


# ---------------------------------------------------------------------------
# Parser de Publicaciones: separa en 4 categorias (capitulos de libros,
# internacionales, nacionales, reportes de investigacion), con sub-grupos
# (revistas / congresos / eventos) y años dentro de cada una.
# ---------------------------------------------------------------------------
_current_year = [None]


def parse_publicaciones():
    from bs4 import BeautifulSoup

    html = PAGES["publicaciones"]["content"]
    soup = BeautifulSoup(html, "html.parser")

    CATEGORY_MAP = {
        "Capítulos de Libros": "capitulos",
        "Publicaciones Internacionales": "internacionales",
        "Publicaciones Nacionales": "nacionales",
    }
    REPORTES_LABEL = "Reportes de Investigación"

    # estructura: cat_key -> subcat_label (o "") -> year -> [html entries]
    data = {"capitulos": {}, "internacionales": {}, "nacionales": {}, "reportes": {}}

    cat_key = None
    subcat = ""
    for node in soup.children:
        name = getattr(node, "name", None)
        if name == "h3":
            text = node.get_text(strip=True).replace("\xa0", " ")
            cat_key = CATEGORY_MAP.get(text)
            subcat = ""
        elif name == "h4":
            text = node.get_text(strip=True).replace("\xa0", " ")
            if text == REPORTES_LABEL:
                cat_key = "reportes"
                subcat = ""
            elif text.isdigit():
                if cat_key:
                    data[cat_key].setdefault(subcat, {}).setdefault(text, [])
                _current_year[0] = text
            else:
                subcat = text
                _current_year[0] = None
        elif name == "p":
            if cat_key and _current_year[0]:
                entry = f'<p class="pub-entry">{node.decode_contents()}</p>'
                data[cat_key].setdefault(subcat, {}).setdefault(_current_year[0], []).append(entry)

    return data


def render_publicaciones_category(cat_data):
    """cat_data: subcat_label -> year -> [entries]. Ignora claves auxiliares."""
    parts = []
    # se respeta el orden original del documento fuente (orden de inserción);
    # el grupo sin subcategoria (p.ej. Capitulos de libros) va primero si existe
    subcats = [k for k in cat_data.keys() if not k.startswith("_")]
    subcats.sort(key=lambda s: s != "")
    for subcat in subcats:
        years = cat_data[subcat]
        year_list = sorted(years.keys(), reverse=True)
        year_html = []
        for year in year_list:
            entries = "".join(years[year])
            year_html.append(f'<div class="year-group"><h3>{escape(year)}</h3>{entries}</div>')
        inner = "".join(year_html)
        if subcat:
            parts.append(f'<div class="pub-subgroup"><h4>{escape(subcat)}</h4>{inner}</div>')
        else:
            parts.append(inner)
    return "".join(parts) or "<p>Sin publicaciones registradas en esta categoría.</p>"


def build_publicaciones_tabs():
    data = parse_publicaciones()
    labels = [
        ("pub-capitulos", "Capítulos de libros", "capitulos"),
        ("pub-internacionales", "Publicaciones internacionales", "internacionales"),
        ("pub-nacionales", "Publicaciones nacionales", "nacionales"),
        ("pub-reportes", "Reportes de investigación", "reportes"),
    ]
    tabs = [
        (tab_id, label, render_publicaciones_category(data[key]))
        for tab_id, label, key in labels
    ]
    return tabs_component(tabs, wrap_id="publicaciones")


# ---------------------------------------------------------------------------
# AREAS: cuadros/tarjetas clickeables (una por area) que muestran su
# descripcion al hacer click, en vez de un bloque de texto larguisimo.
# ---------------------------------------------------------------------------
def build_areas_section():
    from bs4 import BeautifulSoup

    html = PAGES["areas"]["content"]
    soup = BeautifulSoup(html, "html.parser")

    intro_parts = []
    sections = []  # [(nombre, html_contenido)]
    current_name = None
    current_parts = []
    for node in soup.children:
        tag = getattr(node, "name", None)
        if tag == "h4":
            if current_name:
                sections.append((current_name, "".join(current_parts)))
            current_name = node.get_text(strip=True)
            current_parts = []
        elif tag in ("p", "ul"):
            if current_name is None:
                intro_parts.append(str(node))
            else:
                current_parts.append(str(node))
    if current_name:
        sections.append((current_name, "".join(current_parts)))

    nav_btns = []
    panels = []
    for i, (name, content) in enumerate(sections):
        tab_id = f"area-{i}"
        active = " active" if i == 0 else ""
        monogram = "".join(w[0] for w in name.split()[:2]).upper()
        nav_btns.append(
            f'<button class="{active.strip()}" data-tab="{tab_id}">'
            f'<span class="card-icon">{escape(monogram)}</span>'
            f'<span class="card-title">{escape(name)}</span>'
            f"</button>"
        )
        panels.append(
            f'<div class="tab-panel card-detail{active}" id="{tab_id}">'
            f"<h3>{escape(name)}</h3>{content}</div>"
        )

    intro_html = "".join(intro_parts)
    # arregla un artefacto del markup original de WP ("LaLas líneas..." -> "Las líneas...")
    intro_html = re.sub(r"^(<p>)LaLas\b", r"\1Las", intro_html)
    return f"""<div class="area-intro">{intro_html}</div>
<div class="tabs-wrap">
  <div class="tabs-nav card-tabs-nav">{"".join(nav_btns)}</div>
  <div class="tab-panels">{"".join(panels)}</div>
</div>"""


# ---------------------------------------------------------------------------
# PROYECTOS: cuadros con preview de imagen, al hacer click muestra la
# descripcion completa del proyecto.
# ---------------------------------------------------------------------------
def build_proyectos_section():
    from bs4 import BeautifulSoup

    html = PAGES["proyectos"]["content"]
    soup = BeautifulSoup(html, "html.parser")

    projects = []
    pending_img = None
    current = None
    for node in soup.children:
        tag = getattr(node, "name", None)
        if tag == "ul":
            img_tag = node.find("img")
            if img_tag and img_tag.get("src"):
                pending_img = img_tag["src"]
        elif tag == "h2":
            if current:
                projects.append(current)
            a = node.find("a")
            title = a.get_text(strip=True) if a else node.get_text(strip=True)
            current = {"title": title or "Proyecto", "img": pending_img, "desc": ""}
            pending_img = None
        elif tag == "p" and current is not None:
            current["desc"] += str(node)
    if current:
        projects.append(current)

    nav_btns = []
    panels = []
    for i, proj in enumerate(projects):
        tab_id = f"proy-{i}"
        active = " active" if i == 0 else ""
        if proj["img"]:
            thumb_html = f'<div class="card-thumb"><img src="{proj["img"]}" alt=""></div>'
        else:
            thumb_html = '<div class="card-thumb placeholder"></div>'
        nav_btns.append(
            f'<button class="{active.strip()}" data-tab="{tab_id}">'
            f"{thumb_html}"
            f'<span class="card-title">{escape(proj["title"])}</span>'
            f"</button>"
        )
        desc = proj["desc"] or "<p>Descripción no disponible.</p>"
        panels.append(
            f'<div class="tab-panel card-detail{active}" id="{tab_id}">'
            f"<h3>{escape(proj['title'])}</h3>{desc}</div>"
        )

    return f"""<div class="tabs-wrap">
  <div class="tabs-nav card-tabs-nav has-thumb">{"".join(nav_btns)}</div>
  <div class="tab-panels">{"".join(panels)}</div>
</div>"""


# ---------------------------------------------------------------------------
# INVESTIGACION (Areas / Proyectos / Publicaciones en pestañas)
# ---------------------------------------------------------------------------
def build_investigacion():
    areas_html = build_areas_section()
    proyectos_html = build_proyectos_section()
    publicaciones_tabs = build_publicaciones_tabs()

    tabs = [
        ("areas", "Áreas", areas_html),
        ("proyectos", "Proyectos", proyectos_html),
        ("publicaciones", "Publicaciones", publicaciones_tabs),
    ]

    body = f"""
<section class="hero">
  <div class="container">
    <h1>Investigación</h1>
    <p>Áreas de trabajo, proyectos en curso y producción científica del laboratorio.</p>
  </div>
</section>

<section>
  <div class="container">
    {tabs_component(tabs)}
  </div>
</section>
"""
    return page_shell("Investigación", "investigacion.html", body)


# ---------------------------------------------------------------------------
# REA UTILES: cajas/tarjetas, una por recurso (app, herramienta, etc.)
# ---------------------------------------------------------------------------
def build_rea_cards():
    from bs4 import BeautifulSoup

    html = PAGES["rea-utiles"]["content"]
    soup = BeautifulSoup(html, "html.parser")

    cards = []
    current = None
    for node in soup.children:
        tag = getattr(node, "name", None)
        if tag == "p":
            strong = node.find(["strong", "b"])
            if strong:
                if current:
                    cards.append(current)
                title = strong.get_text(strip=True)
                full_text = node.get_text()
                desc = full_text.split(":", 1)[1].strip() if ":" in full_text else full_text.strip()
                current = {"title": title, "desc": desc, "img": None, "link": None, "link_text": "Descargar"}
        elif tag == "img" and current is not None:
            current["img"] = node.get("src")
        elif tag == "a" and current is not None:
            current["link"] = node.get("href")
            current["link_text"] = node.get_text(strip=True) or "Descargar"
    if current:
        cards.append(current)

    cards_html = []
    for c in cards:
        thumb = (
            f'<div class="rea-thumb"><img src="{c["img"]}" alt=""></div>'
            if c["img"]
            else '<div class="rea-thumb placeholder"></div>'
        )
        link_html = (
            f'<a class="btn-small" href="{c["link"]}" target="_blank" rel="noopener">{escape(c["link_text"])}</a>'
            if c["link"]
            else ""
        )
        cards_html.append(f"""<div class="card rea-card">
          {thumb}
          <h3>{escape(c["title"])}</h3>
          <p>{escape(c["desc"])}</p>
          {link_html}
        </div>""")

    return f'<div class="grid grid-3">{"".join(cards_html)}</div>'


# ---------------------------------------------------------------------------
# PROVISION DE RECURSOS MATERIALES: cajitas (una por categoria de equipo),
# con la primera imagen de cada una como preview -- con 13 categorias, un
# renglon de pestañas de texto quedaba muy apretado.
# ---------------------------------------------------------------------------
def build_provision_cards():
    from bs4 import BeautifulSoup

    html = PAGES["provision-de-recursos-materiales"]["content"]
    soup = BeautifulSoup(html, "html.parser")
    # el contenido original viene entero envuelto en un <p> invalido (herencia
    # del markup de WP); se recorren sus hijos directamente
    outer = soup.find("p")
    nodes = list(outer.children) if outer else list(soup.children)

    categories = []  # [(nombre, thumb_url_o_None, [partes_html])]
    current_name = None
    current_thumb = None
    current_parts = []

    def flush():
        if current_name:
            categories.append((current_name, current_thumb, current_parts))

    for node in nodes:
        tag = getattr(node, "name", None)
        if tag == "h4":
            flush()
            current_name = node.get_text(strip=True)
            current_thumb = None
            current_parts = []
        elif tag == "ul":
            imgs = node.find_all("img")
            if imgs:
                if current_thumb is None:
                    current_thumb = imgs[0].get("src", "")
                thumbs = "".join(
                    f'<div class="gallery-thumb"><img src="{im.get("src", "")}" alt=""></div>' for im in imgs
                )
                current_parts.append(f'<div class="gallery">{thumbs}</div>')
            elif node.get_text(strip=True):
                current_parts.append(str(node))
        elif tag == "img":
            src = node.get("src", "")
            if current_thumb is None:
                current_thumb = src
            current_parts.append(f'<div class="gallery"><div class="gallery-thumb"><img src="{src}" alt=""></div></div>')
        elif tag == "p" and node.get_text(strip=True):
            current_parts.append(str(node))
    flush()

    # Nota: las 24 imagenes de esta pagina apuntan todas a un subdominio
    # viejo de la UNSL (webfcfmyn.unsl.edu.ar) que ya no resuelve, asi que
    # un thumbnail-preview siempre saldria vacio. En cambio, cada cajita usa
    # un icono/monograma (mismo patron que las tarjetas de Areas), confiable
    # porque no depende de ninguna imagen externa.
    nav_btns = []
    panels = []
    for i, (name, thumb, parts) in enumerate(categories):
        tab_id = f"prov-{i}"
        active = " active" if i == 0 else ""
        monogram = "".join(w[0] for w in name.split()[:2] if w[0].isalnum()).upper()[:2] or "·"
        nav_btns.append(
            f'<button class="{active.strip()}" data-tab="{tab_id}">'
            f'<span class="card-icon">{escape(monogram)}</span>'
            f'<span class="card-title">{escape(name)}</span>'
            f"</button>"
        )
        content = "".join(parts) or "<p>Más información próximamente.</p>"
        panels.append(
            f'<div class="tab-panel card-detail{active}" id="{tab_id}">'
            f"<h3>{escape(name)}</h3>{content}</div>"
        )

    return f"""<div class="tabs-wrap" id="provision-tabs">
  <div class="tabs-nav card-tabs-nav">{"".join(nav_btns)}</div>
  <div class="tab-panels">{"".join(panels)}</div>
</div>"""


# ---------------------------------------------------------------------------
# SERVICIOS  (en pestañas, sin la sección "modelos")
# ---------------------------------------------------------------------------
def build_servicios():
    desarrollo = strip_outer(PAGES["desarrollo-de-proyectos"]["content"])
    provision_cards = build_provision_cards()
    consultoria = strip_outer(PAGES["consultoria-y-experticia"]["content"])
    rea_cards = build_rea_cards()
    politicas = strip_outer(PAGES["recursos"]["content"])

    tabs = [
        ("desarrollo-de-proyectos", "Desarrollo de Proyectos", f'<div class="content-block">{desarrollo}</div>'),
        ("provision-de-recursos-materiales", "Provisión de Recursos", provision_cards),
        ("consultoria-y-experticia", "Consultoría y experticia", f'<div class="content-block">{consultoria}</div>'),
        ("rea-utiles", "REA útiles", rea_cards),
        ("politicas-de-privacidad", "Políticas de privacidad", f'<div class="content-block">{politicas}</div>'),
    ]

    body = f"""
<section class="hero">
  <div class="container">
    <h1>Servicios</h1>
    <p>El LCG ofrece distintos tipos de servicios a instituciones públicas y privadas.</p>
  </div>
</section>

<section>
  <div class="container">
    {tabs_component(tabs)}
  </div>
</section>
"""
    return page_shell("Servicios", "servicios.html", body)


# ---------------------------------------------------------------------------
# FORMACION
# ---------------------------------------------------------------------------
def build_formacion():
    content = strip_outer(PAGES["formacion"]["content"])
    body = f"""
<section class="hero">
  <div class="container">
    <h1>Formación</h1>
    <p>Cursos, talleres y actividades de formación dictadas por el laboratorio.</p>
  </div>
</section>
<section>
  <div class="container content-block">
    {content}
  </div>
</section>
"""
    return page_shell("Formación", "formacion.html", body)


# ---------------------------------------------------------------------------
# CONTACTO
# ---------------------------------------------------------------------------
def build_contacto():
    content = strip_outer(PAGES["contact-us"]["content"])
    body = f"""
<section class="hero">
  <div class="container">
    <h1>Contacto</h1>
    <p>Laboratorio de Computación Gráfica - FCFMyN - UNSL</p>
  </div>
</section>
<section>
  <div class="container content-block">
    {content if strip_tags(content).strip() else "<p>Podés escribirnos a través de los contactos del equipo en la sección Equipo.</p>"}
  </div>
</section>
"""
    return page_shell("Contacto", "contacto.html", body)


# ---------------------------------------------------------------------------
# EQUIPO  (se reconstruye a mano porque el HTML original viene como texto
# plano mezclado con imágenes, sin estructura de tarjetas)
# ---------------------------------------------------------------------------
INVESTIGADORES = [
    dict(name="Roberto Guerrero", title="Mg. en Ciencias de la Computación", role="Director",
         img="/wp-content/uploads/2017/10/ELprofe-267x300.png",
         bio="Es Magíster en Ciencias de la Computación y profesor en la Universidad Nacional de San Luis, San Luis. "
             "Actualmente, trabaja en su Tesis Doctoral acerca de Realidad Virtual e Interfaces Naturales para "
             "No-Fotorealismo. Sus áreas de investigación involucran Computación Gráfica, Procesamiento de Imágenes, "
             "No-Fotorealismo, Realidad Virtual, Realidad Aumentada, Dispositivos Hapticos, e Interfaces Gráficas.",
         email="rag@unsl.edu.ar",
         links=[("ResearchGate", "https://www.researchgate.net/profile/Roberto_Guerrero")]),
    dict(name="Jacqueline Fernandez", title="Lic. en Ciencias de la Computación", role="Investigadora",
         img="/wp-content/uploads/2017/10/jaque-267x300.jpg",
         bio="Es Licenciada en Ciencias de la Computación y profesora en la Universidad Nacional de San Luis, San Luis. "
             "Su tareas actuales se encuentran enfocadas en sus tesis de Maestría en Realidad Virtual e Interfaces "
             "Naturales aplicadas a entornos educativos. Entre sus áreas de investigación se encuentran Computación "
             "Gráfica, Realidad Virtual, Realidad Aumentada, Dispositivos Hápticos, Interfaces Gráficas.",
         email="jmfer@unsl.edu.ar",
         links=[("ResearchGate", "https://www.researchgate.net/profile/Jacqueline_Fernandez3")]),
    dict(name="Yoselie Alvarado", title="Lic. en Ciencias de la Computación", role="Becaria CONICET",
         img="/wp-content/uploads/2017/10/yoselin-267x300.jpg",
         bio="Es Licenciada en Ciencias de la Computación y Auxiliar Docente en la Universidad Nacional de San Luis, "
             "San Luis. Actualmente, se encuentra finalizando su tesis de Maestría e iniciando un Doctorado mediante "
             "una Beca Doctoral Conicet, ambas sobre Agentes Conversacionales en entornos inmersivos tipo Cave. Sus "
             "principales áreas de investigación son Computación Gráfica, Realidad Virtual Inmersiva, Agentes "
             "Encarnados, Comunicación Oral entre Humano y Computadora e Interfaces Gráficas.",
         email="yoselie21@gmail.com",
         links=[("LinkedIn", "https://www.linkedin.com/in/yoselie"),
                ("ResearchGate", "https://www.researchgate.net/profile/Yoselie_Alvarado"),
                ("Google Académico", "https://scholar.google.com/citations?user=24MoUrkAAAAJ&hl=es")]),
    dict(name="Nicolás Jofré", title="Lic. en Ciencias de la Computación", role="Investigador",
         img="/wp-content/uploads/2017/10/nico-267x300.jpg",
         bio="Es Licenciado en Ciencias de la Computación y es Auxiliar Docente en la Universidad Nacional de San "
             "Luis, San Luis. Recientemente, ha presentado su trabajo final de carrera en el cuál desarrolló una "
             "Interfaz Natural para Realidad Virtual utilizando el dispositivo Kinect. Sus áreas de interes son "
             "Computación Gráfica, Realidad Virtual, Realidad Aumentada, Dispositivos Hapticos e Interfaces Gráficas.",
         email="npasinetti@unsl.edu.ar",
         links=[]),
    dict(name="Graciela Rodríguez", title="Lic. en Ciencias de la Computación", role="Investigadora",
         img="/wp-content/uploads/2017/10/grace-267x300.jpg",
         bio="Es Licenciada en Ciencias de la Computación y Auxiliar Docente en la Universidad Nacional de San Luis, "
             "San Luis. En este momento, se encuentra trabajando en su Maestría la cual consiste en Realidad Virtual "
             "e Interfaces Naturales por medio de personajes no conversacionales. Sus áreas de interes son "
             "Computación Gráfica, Realidad Virtual, Realidad Aumentada, Dispositivos Hapticos, e Interfaces Gráficas.",
         email="gbrodriguez@unsl.edu.ar",
         links=[]),
]

COLABORADORES = ["Cesar Verdes", "Jose Castiblanco", "Javier Palacios", "Jose Navrati"]
ESTUDIANTES = ["Claudia Liendo", "Ezequiel Escudero", "Emmanuel Andrada"]
OLD_MEMBERS = ["Manquel Moyano", "Diego Quiroga", "Mario Ruiz Perez"]
PLACEHOLDER_IMG = "/wp-content/uploads/2017/10/persona.jpg"


def team_card(p):
    links_html = ""
    if p["email"]:
        links_html += f'<a href="mailto:{p["email"]}">Email</a>'
    for label, url in p["links"]:
        links_html += f'<a href="{url}" target="_blank" rel="noopener">{escape(label)}</a>'
    return f"""
      <div class="card team-card">
        <img src="{p['img']}" alt="{escape(p['name'])}">
        <h3>{escape(p['name'])}</h3>
        <div class="role">{escape(p['role'])}</div>
        <div class="title">{escape(p['title'])}</div>
        <p>{escape(p['bio'])}</p>
        <div class="links">{links_html}</div>
      </div>"""


def simple_card(name):
    return f"""
      <div class="team-simple">
        <img src="{PLACEHOLDER_IMG}" alt="{escape(name)}">
        <div class="name">{escape(name)}</div>
      </div>"""


def build_equipo():
    investigadores_html = "".join(team_card(p) for p in INVESTIGADORES)
    colaboradores_html = "".join(simple_card(n) for n in COLABORADORES)
    estudiantes_html = "".join(simple_card(n) for n in ESTUDIANTES)
    old_html = "".join(simple_card(n) for n in OLD_MEMBERS)

    body = f"""
<section class="hero">
  <div class="container">
    <h1>Nuestro Equipo</h1>
    <p>Docentes, investigadores y estudiantes que forman parte del LCG.</p>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head"><h2>Investigadores</h2></div>
    <div class="grid grid-3">
      {investigadores_html}
    </div>
  </div>
</section>

<section class="alt">
  <div class="container">
    <div class="section-head"><h2>Colaboradores</h2></div>
    <div class="grid grid-4">
      {colaboradores_html}
    </div>
  </div>
</section>

<section>
  <div class="container">
    <div class="section-head"><h2>Estudiantes</h2></div>
    <div class="grid grid-4">
      {estudiantes_html}
    </div>
  </div>
</section>

<section class="alt">
  <div class="container">
    <div class="section-head"><h2>Ex miembros</h2></div>
    <div class="grid grid-4">
      {old_html}
    </div>
  </div>
</section>
"""
    return page_shell("Equipo", "equipo.html", body)


# ---------------------------------------------------------------------------
def main():
    pages = {
        "index.html": build_index(),
        "noticias.html": build_noticias(),
        "investigacion.html": build_investigacion(),
        "servicios.html": build_servicios(),
        "formacion.html": build_formacion(),
        "equipo.html": build_equipo(),
        "contacto.html": build_contacto(),
    }
    for fname, html in pages.items():
        # GitHub Pages sirve este sitio bajo /pag/ (repo de proyecto), asi que
        # las rutas a recursos deben ser relativas, nunca absolutas desde la
        # raiz del dominio (lcgunsl.github.io), o apuntarian al org root.
        html = html.replace('"/wp-content', '"wp-content')
        html = html.replace("'/wp-content", "'wp-content")
        (ROOT / fname).write_text(html, encoding="utf-8")
        print("Generado:", fname, len(html), "bytes")


if __name__ == "__main__":
    main()
