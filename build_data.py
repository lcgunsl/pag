#!/usr/bin/env python3
import json
from pathlib import Path
from extract_content import load_json, clean_html

OUT = Path("/home/claude/pag/content.json")

PAGES = {
    "home": 2361,
    "areas": 2610,
    "proyectos": 2538,
    "publicaciones": 2560,
    "desarrollo-de-proyectos": 2686,
    "provision-de-recursos-materiales": 2679,
    "consultoria-y-experticia": 2689,
    "rea-utiles": 2900,
    "recursos": 2606,
    "formacion": 2362,
    "contact-us": 2363,
}

# IDs de posts en la categoria "Noticias" (55) del sitio original.
# 2722/2720 (Alfa T-GAME, Alfa T-GAME L3) y 2648 (Alfa GAVIOTA) son
# categoria 58 (Investigacion/Proyectos), no noticias.
# 2930 ("Jornadas de puertas abiertas UNSL") esta sin categorizar (cat 1)
# y es un duplicado de 2820 ("Jornadas de puertas abiertas", cat Noticias).
POSTS = [2825, 2946, 2792, 2832, 2788, 186, 2674,
         2801, 2805, 2815, 2894, 2955, 2808, 2861, 2965,
         2820, 2798, 2664]

data = {"pages": {}, "posts": []}

for slug, pid in PAGES.items():
    d = load_json(f"wp-json/wp/v2/pages/{pid}/index.html")
    if not d:
        print("FALTA pagina", slug, pid)
        continue
    data["pages"][slug] = {
        "id": pid,
        "title": d.get("title", {}).get("rendered"),
        "content": clean_html(d.get("content", {}).get("rendered", "")),
        "date": d.get("date"),
    }

for pid in POSTS:
    d = load_json(f"wp-json/wp/v2/posts/{pid}/index.html")
    if not d:
        print("FALTA post", pid)
        continue
    data["posts"].append({
        "id": pid,
        "slug": d.get("slug"),
        "title": d.get("title", {}).get("rendered"),
        "content": clean_html(d.get("content", {}).get("rendered", "")),
        "date": d.get("date"),
    })

data["posts"].sort(key=lambda p: p["date"], reverse=True)

OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("Paginas:", len(data["pages"]), "Posts:", len(data["posts"]))
