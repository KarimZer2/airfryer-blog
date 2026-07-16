#!/usr/bin/env python3
"""
build.py
Construit le site statique (HTML) à partir des articles Markdown de content/articles/,
remplace les marqueurs [AFFILIATE:id] par de vrais liens Amazon, génère l'index,
le sitemap.xml, le robots.txt et le flux rss.xml.

Sortie : dossier dist/
"""
import json
import re
from datetime import datetime
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
ARTICLES_DIR = ROOT / "content" / "articles"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
DIST_DIR = ROOT / "dist"

SITE_URL = "https://REMPLACE-MOI.github.io/airfryer-blog"
SITE_NAME = "Croustille & Cie"

TYPE_LABELS = {
    "guide-achat": "Guide d'achat",
    "comparatif": "Comparatif",
    "guide-recette": "Recette & cuisson",
    "guide-entretien": "Entretien",
    "guide-technique": "Guide technique",
    "avis-produit": "Avis produit",
}

MOIS_FR = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]


def date_fr(iso_date):
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"{d.day} {MOIS_FR[d.month-1]} {d.year}"


def load_products():
    with open(ROOT / "config" / "products.json", encoding="utf-8") as f:
        data = json.load(f)
    tag = data["amazon_tag"]
    by_id = {}
    for p in data["products"]:
        p["affiliate_url"] = f"https://www.amazon.fr/dp/{p['asin']}?tag={tag}"
        by_id[p["id"]] = p
    return by_id


def parse_article(path, products_by_id):
    raw = path.read_text(encoding="utf-8")
    _, fm_str, body_md = raw.split("---", 2)
    fm = json.loads(fm_str.strip())

    body_md = re.sub(
        r"\[AFFILIATE:([a-z0-9\-]+)\]",
        lambda m: f" ([voir le prix]({products_by_id[m.group(1)]['affiliate_url']}))"
        if m.group(1) in products_by_id else "",
        body_md,
    )
    body_html = markdown.markdown(body_md, extensions=["extra"])

    products = [products_by_id[pid] for pid in fm.get("products_mentioned", []) if pid in products_by_id]

    fm["body_html"] = body_html
    fm["products"] = products
    fm["date_fr"] = date_fr(fm["date"])
    fm["type_label"] = TYPE_LABELS.get(fm["type"], fm["type"])
    return fm


def main():
    products_by_id = load_products()
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    base_tpl = env.get_template("base.html")
    article_tpl = env.get_template("article_content.html")
    index_tpl = env.get_template("index_content.html")

    DIST_DIR.mkdir(exist_ok=True)
    (DIST_DIR / "articles").mkdir(exist_ok=True)
    (DIST_DIR / "static" / "css").mkdir(parents=True, exist_ok=True)
    css_src = STATIC_DIR / "css" / "style.css"
    (DIST_DIR / "static" / "css" / "style.css").write_text(css_src.read_text(encoding="utf-8"), encoding="utf-8")

    articles = []
    for path in sorted(ARTICLES_DIR.glob("*.md"), reverse=True):
        articles.append(parse_article(path, products_by_id))

    current_year = datetime.now().year

    # Pages articles
    for a in articles:
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": a["title"],
            "datePublished": a["date"],
            "description": a["meta_description"],
        }
        content_html = article_tpl.render(asset_prefix="../", **a)
        page = base_tpl.render(
            page_title=f"{a['title']} — {SITE_NAME}",
            meta_description=a["meta_description"],
            canonical_path=f"/articles/{a['slug']}.html",
            site_url=SITE_URL,
            site_name=SITE_NAME,
            asset_prefix="../",
            og_type="article",
            schema_json=json.dumps(schema, ensure_ascii=False),
            current_year=current_year,
            content=content_html,
        )
        (DIST_DIR / "articles" / f"{a['slug']}.html").write_text(page, encoding="utf-8")

    # Page d'accueil
    latest = articles[0] if articles else None
    rest = articles[1:]
    index_content = index_tpl.render(asset_prefix="", latest=latest, rest=rest)
    index_page = base_tpl.render(
        page_title=f"{SITE_NAME} — Guides et comparatifs airfryer",
        meta_description="Guides d'achat, comparatifs et temps de cuisson pour bien choisir et utiliser son airfryer, mis à jour chaque jour.",
        canonical_path="/",
        site_url=SITE_URL,
        site_name=SITE_NAME,
        asset_prefix="",
        schema_json="",
        current_year=current_year,
        content=index_content,
    )
    (DIST_DIR / "index.html").write_text(index_page, encoding="utf-8")

    # sitemap.xml
    urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/articles/{a['slug']}.html" for a in articles]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sitemap.append(f"  <url><loc>{u}</loc></url>")
    sitemap.append("</urlset>")
    (DIST_DIR / "sitemap.xml").write_text("\n".join(sitemap), encoding="utf-8")

    # robots.txt
    (DIST_DIR / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8"
    )

    # rss.xml
    rss_items = "\n".join(
        f"""  <item>
    <title>{a['title']}</title>
    <link>{SITE_URL}/articles/{a['slug']}.html</link>
    <description>{a['meta_description']}</description>
    <pubDate>{a['date']}</pubDate>
  </item>"""
        for a in articles[:20]
    )
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>{SITE_NAME}</title>
  <link>{SITE_URL}</link>
  <description>Guides et comparatifs airfryer</description>
{rss_items}
</channel></rss>"""
    (DIST_DIR / "rss.xml").write_text(rss, encoding="utf-8")

    print(f"Site généré dans {DIST_DIR} — {len(articles)} article(s).")


if __name__ == "__main__":
    main()
