"""
Genera una ilustracion SVG propia para el hero de la home: UNA sola imagen
de un objeto 3D (un icosaedro subdividido, estilo "low-poly"), partida en
4 cuadrantes -- no 4 dibujos separados, sino el mismo render recortado en
4 partes, cada una mostrando una etapa distinta del pipeline: puntos ->
wireframe/poligonos -> sombreado -> material/textura. Pensado para el LCG
(Laboratorio de Computacion Grafica), inspirado en las clasicas laminas de
"mismo objeto, distintas etapas de render" que se usan en catedras de CG.

No usa fotos ni assets externos: todo se calcula (proyeccion 3D simple +
pintado por profundidad) y se escribe como SVG vectorial.
"""
import numpy as np

rng = np.random.default_rng(7)

# ---------- 1. Generar un icosaedro y subdividirlo una vez (icosphere) ----------
phi = (1 + 5 ** 0.5) / 2
base_verts = np.array([
    [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
    [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
    [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1],
])
base_verts = base_verts / np.linalg.norm(base_verts[0])

base_faces = [
    (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
    (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
    (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
    (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
]

def subdivide(verts, faces):
    verts = list(map(tuple, verts))
    cache = {}
    def midpoint(a, b):
        key = tuple(sorted((a, b)))
        if key in cache:
            return cache[key]
        va, vb = np.array(verts[a]), np.array(verts[b])
        vm = (va + vb) / 2
        vm = vm / np.linalg.norm(vm)
        verts.append(tuple(vm))
        idx = len(verts) - 1
        cache[key] = idx
        return idx
    new_faces = []
    for a, b, c in faces:
        ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
        new_faces += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
    return np.array(verts), new_faces

verts, faces = base_verts, base_faces
verts, faces = subdivide(verts, faces)  # 1 subdivision -> low-poly look

# ---------- 2. Rotar a un angulo "de catalogo" ----------
def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

R = rot_y(np.radians(28)) @ rot_x(np.radians(-18))
verts = verts @ R.T

# ---------- 3. Proyeccion con perspectiva simple ----------
cam_dist = 3.2
def project(v):
    x, y, z = v
    z_cam = z + cam_dist
    f = 1.6
    return np.array([x * f / z_cam, y * f / z_cam])

proj = np.array([project(v) for v in verts])

# ---------- 4. Normales de cara + iluminacion simple ----------
light_dir = np.array([-0.45, 0.55, 0.9])
light_dir = light_dir / np.linalg.norm(light_dir)

def face_data(f):
    a, b, c = (verts[i] for i in f)
    normal = np.cross(b - a, c - a)
    norm = np.linalg.norm(normal)
    if norm == 0:
        return None
    normal = normal / norm
    centroid = (a + b + c) / 3
    depth = centroid[2]
    shade = max(0.0, np.dot(normal, light_dir))
    return depth, shade, normal

fdata = []
for f in faces:
    d = face_data(f)
    if d is None:
        continue
    depth, shade, normal = d
    # back-face culling simple (solo mostramos caras que miran "hacia" camara
    # en z, aproximacion valida para una esfera convexa)
    if normal[2] < -0.05:
        continue
    fdata.append((f, depth, shade))

fdata.sort(key=lambda t: t[1])  # pintor: lejos -> cerca

# ---------- 5. Paleta del sitio (Sofisticacion Moderna) ----------
AZUL = (70, 101, 119)      # --accent
AZUL_D = (31, 45, 53)      # --grad-start
LILA = (154, 153, 171)     # --accent2
CALIZA = (221, 186, 154)   # --highlight

def lerp(c1, c2, t):
    return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))

def to_hex(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(x))) for x in c)

def shade_color(base, shade, dark=AZUL_D, light=CALIZA):
    # mezcla oscuro->base->claro segun la intensidad de luz de la cara
    if shade < 0.5:
        return lerp(dark, base, shade / 0.5)
    return lerp(base, light, (shade - 0.5) / 0.5)

# ---------- 6. Proyectar a coordenadas del UNICO lienzo ----------
# A diferencia de la version anterior (4 cuadros separados), aca el objeto
# se dibuja UNA sola vez, a tamano completo, centrado en un lienzo cuadrado
# compartido; lo que cambia por cuadrante es solo el "clip" (que porcion del
# dibujo se deja ver) y el estilo de render que se usa para esa porcion.
TOTAL = 380
SCALE = 235
# Centrar el objeto en el lienzo segun su propio bounding box proyectado
# (no en el origen 3D), para que el cruce de los 4 cuadrantes caiga
# realmente en el medio visual de la figura.
bbox_cx = (proj[:, 0].max() + proj[:, 0].min()) / 2
bbox_cy = (proj[:, 1].max() + proj[:, 1].min()) / 2
CX, CY = TOTAL / 2, TOTAL / 2

def to_svg_xy(p):
    return (CX + (p[0] - bbox_cx) * SCALE, CY - (p[1] - bbox_cy) * SCALE)

# ---- Capa de puntos (vertices) ----
pts_svg = []
for i, v in enumerate(verts):
    x, y = to_svg_xy(proj[i])
    depth_t = (v[2] + 1) / 2
    r = 3.4 + depth_t * 3.4
    col = to_hex(lerp(AZUL_D, LILA, depth_t))
    pts_svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}"/>')
layer_pts = "\n    ".join(pts_svg)

# ---- Capa de wireframe (aristas) ----
edges = set()
for f, depth, shade in fdata:
    a, b, c = f
    for e in ((a, b), (b, c), (c, a)):
        edges.add(tuple(sorted(e)))
line_svg = []
for a, b in edges:
    xa, ya = to_svg_xy(proj[a])
    xb, yb = to_svg_xy(proj[b])
    line_svg.append(f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="{to_hex(LILA)}" stroke-width="1.3" opacity=".9"/>')
layer_wire = "\n    ".join(line_svg)

# ---- Capa de sombreado solido (mono, sin textura) ----
poly_mono = []
for f, depth, shade in fdata:
    pts = " ".join(f"{to_svg_xy(proj[i])[0]:.1f},{to_svg_xy(proj[i])[1]:.1f}" for i in f)
    col = to_hex(shade_color(AZUL, shade, dark=AZUL_D, light=(150, 170, 180)))
    poly_mono.append(f'<polygon points="{pts}" fill="{col}" stroke="{to_hex(AZUL_D)}" stroke-width=".4"/>')
layer_shaded = "\n    ".join(poly_mono)

# ---- Capa de material/textura (paleta completa + brillo) ----
poly_mat = []
for f, depth, shade in fdata:
    pts = " ".join(f"{to_svg_xy(proj[i])[0]:.1f},{to_svg_xy(proj[i])[1]:.1f}" for i in f)
    col = to_hex(shade_color(AZUL, shade, dark=AZUL_D, light=CALIZA))
    poly_mat.append(f'<polygon points="{pts}" fill="{col}" stroke="rgba(31,45,53,.25)" stroke-width=".4"/>')
layer_mat = "\n    ".join(poly_mat)

# ---------- 7. Armar el SVG final: 1 imagen, recortada en 4 cuadrantes ----------
HALF = TOTAL / 2

quadrants = [
    # (x, y, w, h, capa, nombre de la etiqueta, anchor de la etiqueta)
    (0, 0, HALF, HALF, layer_pts, "PUNTOS", (14, 24, "start")),
    (HALF, 0, HALF, HALF, layer_wire, "POLÍGONOS", (TOTAL - 14, 24, "end")),
    (0, HALF, HALF, HALF, layer_shaded, "SOMBREADO", (14, TOTAL - 16, "start")),
    (HALF, HALF, HALF, HALF, layer_mat, "MATERIAL", (TOTAL - 14, TOTAL - 16, "end")),
]

clip_defs = []
quad_groups = []
labels = []
for idx, (qx, qy, qw, qh, layer, label, (lx, ly, anchor)) in enumerate(quadrants):
    clip_id = f"q{idx}"
    clip_defs.append(f'<clipPath id="{clip_id}"><rect x="{qx}" y="{qy}" width="{qw}" height="{qh}"/></clipPath>')
    quad_groups.append(f'<g clip-path="url(#{clip_id})">\n    {layer}\n  </g>')
    labels.append(
        f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" '
        f'font-family="Inter, \'Segoe UI\', sans-serif" font-size="12" font-weight="700" '
        f'letter-spacing=".06em" fill="rgba(255,255,255,.78)">{label}</text>'
    )

svg = f'''<svg viewBox="0 0 {TOTAL} {TOTAL}" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Un mismo objeto 3D partido en cuatro cuadrantes, cada uno en una etapa distinta del pipeline de render: puntos, poligonos, sombreado y material">
  <defs>
    {chr(10).join("    " + d for d in clip_defs)}
  </defs>
  <rect x="0" y="0" width="{TOTAL}" height="{TOTAL}" rx="18" fill="rgba(255,255,255,.04)" stroke="rgba(255,255,255,.14)"/>
  <clipPath id="canvasClip"><rect x="2" y="2" width="{TOTAL-4}" height="{TOTAL-4}" rx="16"/></clipPath>
  <g clip-path="url(#canvasClip)">
    {chr(10).join("  " + g for g in quad_groups)}
    <line x1="{HALF:.1f}" y1="2" x2="{HALF:.1f}" y2="{TOTAL-2}" stroke="rgba(255,255,255,.22)" stroke-width="1.5"/>
    <line x1="2" y1="{HALF:.1f}" x2="{TOTAL-2}" y2="{HALF:.1f}" stroke="rgba(255,255,255,.22)" stroke-width="1.5"/>
  </g>
  {chr(10).join("  " + l for l in labels)}
</svg>'''

with open("/home/claude/pag/assets/hero-render.svg", "w") as fh:
    fh.write(svg)

print("faces used:", len(fdata), "verts:", len(verts))
print("written assets/hero-render.svg", len(svg), "bytes")
