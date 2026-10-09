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
</head>
<body>
<header class="site-header">
  <div class="container">
    <a class="brand" href="index.html">
      <img src="wp-content/uploads/2017/05/Logo-LCG_Def.png" alt="LCG">
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
  <div class="container">
    <h1>{SITE_NAME}</h1>
    <p>Investigación y desarrollo en Realidad Virtual, Realidad Aumentada e Interacción Natural Humano-Computadora. Sede del primer sistema de visualización tipo CAVE del país.</p>
    <a class="btn" href="servicios.html">Conocer nuestros servicios</a>
    <a class="btn btn-outline" href="equipo.html">Conocer al equipo</a>
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
# NOTICIAS
# ---------------------------------------------------------------------------
def build_noticias():
    items = []
    for p in POSTS:
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

    body = f"""
<section class="hero">
  <div class="container">
    <h1>Noticias</h1>
    <p>Actividades, visitas, talleres y novedades del laboratorio.</p>
  </div>
</section>
<section>
  <div class="container content-block">
    {"".join(items)}
  </div>
</section>
"""
    return page_shell("Noticias", "noticias.html", body)


# ---------------------------------------------------------------------------
# INVESTIGACION (areas + proyectos + publicaciones)
# ---------------------------------------------------------------------------
def build_investigacion():
    areas = strip_outer(PAGES["areas"]["content"])
    proyectos = strip_outer(PAGES["proyectos"]["content"])
    publicaciones = strip_outer(PAGES["publicaciones"]["content"])

    body = f"""
<section class="hero">
  <div class="container">
    <h1>Investigación</h1>
    <p>Áreas de trabajo, proyectos en curso y producción científica del laboratorio.</p>
  </div>
</section>

<section id="areas">
  <div class="container content-block">
    <h2>Áreas</h2>
    {areas}
  </div>
</section>

<section class="alt" id="proyectos">
  <div class="container content-block">
    <h2>Proyectos</h2>
    {proyectos}
  </div>
</section>

<section id="publicaciones">
  <div class="container content-block">
    <h2>Publicaciones</h2>
    {publicaciones}
  </div>
</section>
"""
    return page_shell("Investigación", "investigacion.html", body)


# ---------------------------------------------------------------------------
# SERVICIOS  (sin la sección "modelos")
# ---------------------------------------------------------------------------
def build_servicios():
    desarrollo = strip_outer(PAGES["desarrollo-de-proyectos"]["content"])
    provision = strip_outer(PAGES["provision-de-recursos-materiales"]["content"])
    consultoria = strip_outer(PAGES["consultoria-y-experticia"]["content"])
    rea = strip_outer(PAGES["rea-utiles"]["content"])
    politicas = strip_outer(PAGES["recursos"]["content"])

    body = f"""
<section class="hero">
  <div class="container">
    <h1>Servicios</h1>
    <p>El LCG ofrece distintos tipos de servicios a instituciones públicas y privadas.</p>
  </div>
</section>

<section id="desarrollo-de-proyectos">
  <div class="container content-block">
    <h2>Desarrollo de Proyectos</h2>
    {desarrollo}
  </div>
</section>

<section class="alt" id="provision-de-recursos-materiales">
  <div class="container content-block">
    <h2>Provisión de Recursos Materiales</h2>
    {provision}
  </div>
</section>

<section id="consultoria-y-experticia">
  <div class="container content-block">
    <h2>Consultoría y experticia</h2>
    {consultoria}
  </div>
</section>

<section class="alt" id="rea-utiles">
  <div class="container content-block">
    <h2>REA útiles</h2>
    {rea}
  </div>
</section>

<section id="politicas-de-privacidad">
  <div class="container content-block">
    <h2>Políticas de privacidad</h2>
    {politicas}
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
        (ROOT / fname).write_text(html, encoding="utf-8")
        print("Generado:", fname, len(html), "bytes")


if __name__ == "__main__":
    main()
