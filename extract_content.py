#!/usr/bin/env python3
"""Extrae contenido limpio (sin el markup pesado de Avada/Fusion Builder)
desde los JSON de la REST API de WordPress que bajamos del Wayback Machine."""
import json, re, sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

SRC = Path("/home/claude/work/lcg_extract/lcg_site_backup")

KEEP_TAGS = {"h1","h2","h3","h4","h5","h6","p","ul","ol","li","img","a","strong","em","b","i","br","blockquote"}

DOMAIN_RE = re.compile(r'https?://(?:www\.)?lcg\.unsl\.edu\.ar')

def fix_urls(soup):
    for tag in soup.find_all(["a", "img"]):
        attr = "href" if tag.name == "a" else "src"
        val = tag.get(attr)
        if not val:
            continue
        new_val = DOMAIN_RE.sub("", val)
        if not new_val.startswith("/") and not new_val:
            new_val = "/"
        tag[attr] = new_val

def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    fix_urls(soup)

    def unwrap_non_content(node):
        for child in list(node.children):
            if isinstance(child, NavigableString):
                continue
            if child.name not in KEEP_TAGS:
                unwrap_non_content(child)
                child.unwrap()
            else:
                if child.name == "a":
                    href = child.get("href", "")
                    child.attrs = {"href": href} if href else {}
                elif child.name == "img":
                    src = child.get("src", "")
                    alt = child.get("alt", "")
                    child.attrs = {"src": src, "alt": alt}
                else:
                    child.attrs = {}
                unwrap_non_content(child)

    unwrap_non_content(soup)
    # quitar parrafos vacios
    for p in soup.find_all(["p"]):
        if not p.get_text(strip=True) and not p.find("img"):
            p.decompose()
    result = str(soup)
    result = re.sub(r'\n\s*\n+', '\n', result)
    return result.strip()

def load_json(path):
    p = SRC / path
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8", errors="ignore"))

def get_page_by_id(pid):
    return load_json(f"wp-json/wp/v2/pages/{pid}/index.html")

def get_post_by_id(pid):
    return load_json(f"wp-json/wp/v2/posts/{pid}/index.html")

if __name__ == "__main__":
    pid = sys.argv[1]
    kind = sys.argv[2] if len(sys.argv) > 2 else "pages"
    d = load_json(f"wp-json/wp/v2/{kind}/{pid}/index.html")
    if not d:
        print("NO ENCONTRADO")
        sys.exit(1)
    print("TITLE:", d.get("title", {}).get("rendered"))
    print("SLUG:", d.get("slug"))
    print("DATE:", d.get("date"))
    print("---CONTENT---")
    print(clean_html(d.get("content", {}).get("rendered", "")))
