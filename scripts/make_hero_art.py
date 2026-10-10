"""
Genera una ilustracion SVG propia para el hero de la home: UNA sola imagen
de la tetera de Utah -- el objeto mas iconico de la computacion grafica,
perfecto para un laboratorio de CG -- partida en 4 cuadrantes. No son 4
dibujos separados: es el mismo render recortado en 4 partes, cada una
mostrando una etapa distinta del pipeline: puntos -> wireframe/poligonos ->
sombreado (mate) -> material (metal/espejo, tipo "chrome teapot").

No usa fotos ni assets externos ni mallas descargadas: la tetera se arma
por codigo (torneado del cuerpo+tapa, asa y pico como tubos) y todo el
render (proyeccion, iluminacion, pintado por profundidad) se calcula a
mano y se escribe como SVG vectorial.
"""
import numpy as np

# ---------------------------------------------------------------------------
# 1. Construir la malla de la tetera
# ---------------------------------------------------------------------------

def make_lathe(profile, n_seg):
    """profile: lista de (r, y). Si r==0 en el primer/ultimo punto, se
    trata como polo (un solo vertice, abanico de triangulos)."""
    verts = []
    rings = []
    thetas = np.linspace(0, 2 * np.pi, n_seg, endpoint=False)
    for (r, y) in profile:
        if r <= 1e-6:
            verts.append((0.0, y, 0.0))
            rings.append([len(verts) - 1] * n_seg)
        else:
            idxs = []
            for t in thetas:
                verts.append((r * np.cos(t), y, r * np.sin(t)))
                idxs.append(len(verts) - 1)
            rings.append(idxs)

    faces = []
    for a, b in zip(rings[:-1], rings[1:]):
        for j in range(n_seg):
            j2 = (j + 1) % n_seg
            v00, v01, v10, v11 = a[j], a[j2], b[j], b[j2]
            if v00 == v10:
                faces.append((v00, v11, v01))
            elif v01 == v11:
                faces.append((v00, v10, v01))
            else:
                faces.append((v00, v10, v11))
                faces.append((v00, v11, v01))
    return verts, faces


def make_tube(path_pts, radii, n_tube=8):
    """Tubo a lo largo de una polilinea 3D, con radio variable (para el
    asa y el pico, que se van afinando)."""
    verts = []
    rings = []
    for i, p in enumerate(path_pts):
        if i == 0:
            tangent = np.array(path_pts[1]) - np.array(path_pts[0])
        elif i == len(path_pts) - 1:
            tangent = np.array(path_pts[-1]) - np.array(path_pts[-2])
        else:
            tangent = np.array(path_pts[i + 1]) - np.array(path_pts[i - 1])
        tangent = tangent / (np.linalg.norm(tangent) + 1e-9)
        helper = np.array([0, 1, 0]) if abs(tangent[1]) < 0.9 else np.array([1, 0, 0])
        n1 = np.cross(tangent, helper); n1 /= np.linalg.norm(n1)
        n2 = np.cross(tangent, n1)
        r = radii[i]
        idxs = []
        for k in range(n_tube):
            ang = 2 * np.pi * k / n_tube
            off = r * (np.cos(ang) * n1 + np.sin(ang) * n2)
            v = np.array(p) + off
            verts.append(tuple(v))
            idxs.append(len(verts) - 1)
        rings.append(idxs)

    faces = []
    for a, b in zip(rings[:-1], rings[1:]):
        for j in range(n_tube):
            j2 = (j + 1) % n_tube
            faces.append((a[j], b[j], b[j2]))
            faces.append((a[j], b[j2], a[j2]))
    return verts, faces, rings


# Perfil del cuerpo + tapa (silueta clasica de tetera), usado tanto para
# tornear el cuerpo como para saber a que radio esta su superficie a una
# altura y dada -- asi el asa y el pico "sueldan" contra el cuerpo en vez
# de quedar flotando con un hueco, como pasaba antes.
BODY_PROFILE = [
    (0.00, 0.00), (0.34, 0.02), (0.54, 0.09), (0.615, 0.22),
    (0.63, 0.34), (0.60, 0.47), (0.52, 0.59), (0.43, 0.68),
    (0.46, 0.715), (0.41, 0.755), (0.31, 0.80), (0.18, 0.885),
    (0.07, 0.95), (0.00, 1.00),
]

def body_radius_at(y):
    ys = [p[1] for p in BODY_PROFILE]
    rs = [p[0] for p in BODY_PROFILE]
    return float(np.interp(y, ys, rs))


def build_teapot():
    all_verts = []
    all_faces = []

    def add(vs, fs):
        off = len(all_verts)
        all_verts.extend(vs)
        all_faces.extend([tuple(i + off for i in f) for f in fs])

    # Cuerpo + tapa: perfil de torneado, bastante segmentado para que la
    # nube de puntos y el wireframe se vean densos
    add(*make_lathe(BODY_PROFILE, n_seg=28))

    # Asa: arco de tubo del lado -X, opuesto al pico (como una tetera real).
    # Los extremos se apoyan justo en la superficie del cuerpo (calculada
    # con body_radius_at) y se hunden un poco hacia adentro para que no
    # quede un hueco entre el asa y la panza.
    n_h = 16
    y0, y1 = 0.26, 0.76
    r0, r1 = body_radius_at(y0), body_radius_at(y1)
    handle_pts, handle_r = [], []
    for i in range(n_h):
        t = i / (n_h - 1)
        bulge = 0.30 * np.sin(np.pi * t)  # panza del asa, 0 en los extremos
        base_r = r0 * (1 - t) + r1 * t
        x = -(base_r * 0.9 + bulge)
        y = y0 * (1 - t) + y1 * t
        handle_pts.append((x, y, 0.0))
        # mas grueso en los extremos (union) y mas fino en el medio
        handle_r.append(0.055 - 0.02 * np.sin(np.pi * t))
    vh, fh, _ = make_tube(handle_pts, handle_r, n_tube=10)
    add(vh, fh)

    # Pico: tubo conico apuntando a +X, curvandose hacia arriba. Arranca
    # metido dentro del cuerpo (en vez de justo en el borde) para que la
    # union con la panza no deje costura.
    n_s = 12
    y_base = 0.50
    r_base = body_radius_at(y_base)
    spout_pts, spout_r = [], []
    for i in range(n_s):
        t = i / (n_s - 1)
        x = (r_base * 0.85) + 0.55 * t
        y = y_base + 0.46 * t * t
        spout_pts.append((x, y, 0.0))
        spout_r.append(0.14 * (1 - t) + 0.025)
    vs, fs, rings = make_tube(spout_pts, spout_r, n_tube=10)
    tip_center = len(vs)
    vs.append(tuple(spout_pts[-1]))
    last_ring = rings[-1]
    n_tube_spout = 10
    for j in range(n_tube_spout):
        j2 = (j + 1) % n_tube_spout
        fs.append((last_ring[j], last_ring[j2], tip_center))
    add(vs, fs)

    return all_verts, all_faces


verts, faces = build_teapot()
verts = np.array(verts, dtype=float)
verts[:, 1] -= 0.5  # centrar verticalmente

# ---------------------------------------------------------------------------
# 2. Rotar a una vista 3/4 donde se vean el pico y el asa por separado
# ---------------------------------------------------------------------------
def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

R = rot_y(np.radians(-28)) @ rot_x(np.radians(-10))
verts = verts @ R.T

# ---------------------------------------------------------------------------
# 3. Proyeccion con perspectiva simple
# ---------------------------------------------------------------------------
cam_dist = 3.4
f_persp = 1.7
def project(v):
    x, y, z = v
    z_cam = z + cam_dist
    return np.array([x * f_persp / z_cam, y * f_persp / z_cam])

proj = np.array([project(v) for v in verts])

# ---------------------------------------------------------------------------
# 4. Normales + iluminacion (difusa para "sombreado", especular para
#    "material" -- asi el ultimo cuadrante queda con pinta de metal/espejo)
# ---------------------------------------------------------------------------
light_dir = np.array([-0.4, 0.6, 0.9]); light_dir /= np.linalg.norm(light_dir)
view_dir = np.array([0.0, 0.0, -1.0])  # la camara esta del lado -Z

def face_data(f):
    a, b, c = (verts[i] for i in f)
    normal = np.cross(b - a, c - a)
    norm = np.linalg.norm(normal)
    if norm == 0:
        return None
    normal = normal / norm
    centroid = (a + b + c) / 3
    depth = centroid[2]
    diffuse = max(0.0, np.dot(normal, light_dir))
    # especular tipo Blinn-Phong, bien concentrado -> brillos duros de metal
    half_vec = light_dir + view_dir
    half_vec = half_vec / (np.linalg.norm(half_vec) + 1e-9)
    spec = max(0.0, np.dot(normal, half_vec)) ** 28
    # un segundo reflejo "frio" (como si reflejara el cielo) para que el
    # metal no se vea plano en las zonas sin luz directa
    rim = (1.0 - max(0.0, np.dot(normal, -view_dir))) ** 1.4
    return depth, diffuse, spec, rim, normal

fdata = []
for fc in faces:
    d = face_data(fc)
    if d is None:
        continue
    depth, diffuse, spec, rim, normal = d
    if normal[2] < -0.05:
        continue
    fdata.append((fc, depth, diffuse, spec, rim))

fdata.sort(key=lambda t: t[1])

# ---------------------------------------------------------------------------
# 5. Paleta del sitio (Sofisticacion Moderna)
# ---------------------------------------------------------------------------
AZUL = (70, 101, 119)      # --accent
AZUL_D = (31, 45, 53)      # --grad-start
LILA = (154, 153, 171)     # --accent2
CALIZA = (221, 186, 154)   # --highlight
BLANCO = (248, 247, 245)
PLATA = (183, 190, 196)    # gris metalico neutro, para que MATERIAL lea como metal pulido

def lerp(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))

def add_color(c1, c2, amt):
    return tuple(min(255, c1[i] + c2[i] * amt) for i in range(3))

def to_hex(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(x))) for x in c)

def shade_matte(diffuse):
    # mate: oscuro -> azul acero -> gris claro, sin brillos duros
    if diffuse < 0.5:
        return lerp(AZUL_D, AZUL, diffuse / 0.5)
    return lerp(AZUL, (150, 170, 180), (diffuse - 0.5) / 0.5)

def shade_metal(diffuse, spec, rim):
    # metal/espejo pulido, tono claro: base plateada neutra (nunca cae a
    # negro puro, un metal real siempre refleja algo del entorno) +
    # reflejo calido en los bordes (rim, como si reflejara el degrade del
    # header) + brillos especulares muy marcados casi blancos
    diffuse_eff = 0.35 + 0.65 * diffuse
    base = lerp(AZUL_D, PLATA, diffuse_eff)
    base = add_color(base, CALIZA, rim * 0.8)
    base = add_color(base, BLANCO, min(1.0, spec * 2.2))
    return base

def shade_mirror(diffuse, spec, rim):
    # espejo frio (tono lila/azul en vez del plateado calido de MATERIAL,
    # para que ambos cuadrantes lisos se distingan entre si) -- misma logica
    # de "nunca negro puro + rim + brillos duros"
    diffuse_eff = 0.30 + 0.70 * diffuse
    base = lerp(AZUL_D, LILA, diffuse_eff)
    base = add_color(base, LILA, rim * 0.7)
    base = add_color(base, BLANCO, min(1.0, spec * 2.4))
    return base

# ---------------------------------------------------------------------------
# 6. Proyectar a coordenadas del UNICO lienzo compartido
# ---------------------------------------------------------------------------
TOTAL = 380
SCALE = 330
bbox_cx = (proj[:, 0].max() + proj[:, 0].min()) / 2
bbox_cy = (proj[:, 1].max() + proj[:, 1].min()) / 2
CX, CY = TOTAL / 2, TOTAL / 2

def to_svg_xy(p):
    return (CX + (p[0] - bbox_cx) * SCALE, CY - (p[1] - bbox_cy) * SCALE)

# ---- Capa de puntos (vertices), siempre negro ----
pts_svg = []
for i, v in enumerate(verts):
    x, y = to_svg_xy(proj[i])
    depth_t = (v[2] + 1.6) / 3.2
    r = 0.7 + depth_t * 0.7  # chiquitos: que se lea como nube de puntos, no como bolitas
    pts_svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#000" opacity="{0.55 + depth_t * 0.45:.2f}"/>')
layer_pts = "\n    ".join(pts_svg)

# ---- Capa de wireframe (aristas), siempre negro ----
edges = set()
for fc, depth, diffuse, spec, rim in fdata:
    a, b, c = fc
    for e in ((a, b), (b, c), (c, a)):
        edges.add(tuple(sorted(e)))
line_svg = []
for a, b in edges:
    xa, ya = to_svg_xy(proj[a])
    xb, yb = to_svg_xy(proj[b])
    line_svg.append(f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="#000" stroke-width="0.7" opacity=".8"/>')
layer_wire = "\n    ".join(line_svg)

# ---- Capa "textura": espejo frio, liso -- sin trazo de contorno visible,
# igual tecnica que MATERIAL (el stroke va del mismo color que el relleno,
# solo para tapar costuras de antialiasing entre triangulos vecinos) para
# que no se note la malla de poligonos por debajo ----
poly_tex = []
for fc, depth, diffuse, spec, rim in fdata:
    pts = " ".join(f"{to_svg_xy(proj[i])[0]:.1f},{to_svg_xy(proj[i])[1]:.1f}" for i in fc)
    col = to_hex(shade_mirror(diffuse, spec, rim))
    poly_tex.append(f'<polygon points="{pts}" fill="{col}" stroke="{col}" stroke-width=".6"/>')
layer_tex = "\n    ".join(poly_tex)

# ---- Capa de material: metal/espejo claro, con brillos especulares duros,
# tambien liso (mismo truco de stroke = fill) ----
poly_mat = []
for fc, depth, diffuse, spec, rim in fdata:
    pts = " ".join(f"{to_svg_xy(proj[i])[0]:.1f},{to_svg_xy(proj[i])[1]:.1f}" for i in fc)
    col = to_hex(shade_metal(diffuse, spec, rim))
    poly_mat.append(f'<polygon points="{pts}" fill="{col}" stroke="{col}" stroke-width=".6"/>')
layer_mat = "\n    ".join(poly_mat)

# ---------------------------------------------------------------------------
# 7. Armar el SVG final: 1 imagen, recortada en 4 cuadrantes
# ---------------------------------------------------------------------------
HALF = TOTAL / 2

quadrants = [
    (0, 0, HALF, HALF, layer_pts, "PUNTOS", (14, 24, "start")),
    (HALF, 0, HALF, HALF, layer_wire, "POLÍGONOS", (TOTAL - 14, 24, "end")),
    (0, HALF, HALF, HALF, layer_tex, "TEXTURA", (14, TOTAL - 16, "start")),
    (HALF, HALF, HALF, HALF, layer_mat, "MATERIAL", (TOTAL - 14, TOTAL - 16, "end")),
]

# Las capas "lisas" (TEXTURA, MATERIAL) son triangulos planos: por mas que
# no tengan borde, cada uno tiene un color uniforme y se sigue notando la
# faceta contra la del vecino. Un sombreado Gouraud real (interpolar color
# por pixel entre los 3 vertices) no es viable en SVG puro, asi que se
# simula con un desenfoque gaussiano suave sobre esa capa: funde los
# limites entre triangulos y el ojo lee una superficie continua, como un
# sombreado suavizado. Solo se aplica a la capa que lo necesita (TEXTURA);
# PUNTOS y POLIGONOS deben quedar nitidos.
SMOOTH_FILTER_ID = "smoothShade"
smooth_filter_def = (
    f'<filter id="{SMOOTH_FILTER_ID}" x="-20%" y="-20%" width="140%" height="140%">'
    f'<feGaussianBlur stdDeviation="2.1"/>'
    f'</filter>'
)

clip_defs, quad_groups, labels = [], [], []
for idx, (qx, qy, qw, qh, layer, label, (lx, ly, anchor)) in enumerate(quadrants):
    clip_id = f"q{idx}"
    clip_defs.append(f'<clipPath id="{clip_id}"><rect x="{qx}" y="{qy}" width="{qw}" height="{qh}"/></clipPath>')
    inner = f'<g filter="url(#{SMOOTH_FILTER_ID})">\n    {layer}\n  </g>' if label == "TEXTURA" else layer
    quad_groups.append(f'<g clip-path="url(#{clip_id})">\n    {inner}\n  </g>')
    labels.append(
        f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" '
        f'font-family="Inter, \'Segoe UI\', sans-serif" font-size="12" font-weight="700" '
        f'letter-spacing=".06em" fill="rgba(255,255,255,.78)">{label}</text>'
    )

svg = f'''<svg viewBox="0 0 {TOTAL} {TOTAL}" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="La tetera de Utah partida en cuatro cuadrantes, cada uno en una etapa distinta del pipeline de render: puntos, poligonos, textura espejada y material metalico">
  <defs>
    {chr(10).join("    " + d for d in clip_defs)}
    {smooth_filter_def}
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
