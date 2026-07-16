#!/usr/bin/env python3
"""
generate_article.py
Génère un article SEO de ~2500 mots sur la thématique airfryer,
en piochant le prochain sujet dans config/topics.json,
et insère des marqueurs [AFFILIATE:product_id] qui seront transformés
en vrais liens Amazon par build.py.

Nécessite la variable d'environnement ANTHROPIC_API_KEY.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
TOPICS_PATH = ROOT / "config" / "topics.json"
PRODUCTS_PATH = ROOT / "config" / "products.json"
ARTICLES_DIR = ROOT / "content" / "articles"

MODEL = "claude-sonnet-5"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def slugify(text):
    text = text.lower()
    text = re.sub(r"[àâä]", "a", text)
    text = re.sub(r"[éèêë]", "e", text)
    text = re.sub(r"[îï]", "i", text)
    text = re.sub(r"[ôö]", "o", text)
    text = re.sub(r"[ùûü]", "u", text)
    text = re.sub(r"[ç]", "c", text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def pick_next_topic(topics):
    for t in topics:
        if t["statut"] == "en_attente":
            return t
    # Plus aucun sujet en attente : on recycle la liste avec un nouvel angle
    for t in topics:
        t["statut"] = "en_attente"
    return topics[0]


def build_prompt(topic, products):
    produits_str = "\n".join(
        f"- id=\"{p['id']}\" | {p['name']} | {p['capacite']} | {p['prix_indicatif']} | "
        f"points forts: {', '.join(p['points_forts'])}"
        for p in products
    )
    return f"""Tu es un rédacteur web SEO senior spécialisé dans l'univers de la cuisine et des airfryers (friteuses à air chaud), écrivant pour un site d'affiliation Amazon francophone.

Rédige un article de blog COMPLET d'environ 2500 mots en français, optimisé pour le référencement naturel (SEO), sur le sujet suivant :

TITRE CIBLE : {topic['titre_cible']}
TYPE D'ARTICLE : {topic['type']}
MOT-CLÉ PRINCIPAL À CIBLER : {topic['mot_cle']}

CONTRAINTES SEO :
- Utilise le mot-clé principal dans le H1, dans au moins un H2, et naturellement dans le texte (sans sur-optimisation).
- Structure claire avec un seul H1, plusieurs H2 et des H3 si pertinent.
- Inclus une section FAQ de 4 à 6 questions/réponses à la fin (utile pour les featured snippets Google).
- Phrases courtes, paragraphes aérés (3-5 phrases max), ton expert mais accessible, pas de jargon inutile.
- N'invente pas de fausses statistiques précises ou d'études qui n'existent pas.

PRODUITS DISPONIBLES POUR MENTION (insère 2 à 4 produits pertinents selon le sujet, jamais tous) :
{produits_str}

RÈGLE IMPORTANTE POUR LES LIENS AFFILIÉS :
Quand tu mentionnes un produit de la liste ci-dessus, insère IMMÉDIATEMENT après son nom le marqueur exact [AFFILIATE:id_du_produit] (remplace id_du_produit par le vrai id, ex: [AFFILIATE:cosori-pro]). N'invente jamais d'id. N'utilise ce marqueur QUE pour les produits listés ci-dessus.

FORMAT DE SORTIE (réponds UNIQUEMENT avec ce format, rien avant, rien après) :

META_DESCRIPTION: [une méta-description de 140 à 155 caractères maximum incluant le mot-clé principal]

---

[le contenu de l'article en Markdown, commençant directement par "# Titre"]
"""


def generate(topic, products):
    try:
        import anthropic
    except ImportError:
        print("Le package 'anthropic' n'est pas installé. Lance : pip install anthropic", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERREUR : la variable d'environnement ANTHROPIC_API_KEY n'est pas définie.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_prompt(topic, products)

    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return text


def parse_output(raw_text):
    meta_match = re.search(r"META_DESCRIPTION:\s*(.+)", raw_text)
    meta_description = meta_match.group(1).strip() if meta_match else ""
    parts = raw_text.split("---", 1)
    body = parts[1].strip() if len(parts) > 1 else raw_text.strip()
    return meta_description, body


def main():
    topics = load_json(TOPICS_PATH)
    products_data = load_json(PRODUCTS_PATH)
    products = products_data["products"]

    topic = pick_next_topic(topics)
    print(f"Sujet sélectionné : {topic['titre_cible']}")

    raw = generate(topic, products)
    meta_description, body = parse_output(raw)

    title_match = re.search(r"^#\s+(.+)", body, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else topic["titre_cible"]
    slug = slugify(title)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    products_mentioned = sorted(set(re.findall(r"\[AFFILIATE:([a-z0-9\-]+)\]", body)))

    frontmatter = {
        "title": title,
        "meta_description": meta_description,
        "date": today,
        "slug": slug,
        "type": topic["type"],
        "keyword": topic["mot_cle"],
        "products_mentioned": products_mentioned,
    }

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ARTICLES_DIR / f"{today}-{slug}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(json.dumps(frontmatter, ensure_ascii=False, indent=2))
        f.write("\n---\n\n")
        f.write(body)

    print(f"Article enregistré : {out_path}")

    topic["statut"] = "publie"
    topic["date_publication"] = today
    topic["fichier"] = out_path.name
    save_json(TOPICS_PATH, topics)


if __name__ == "__main__":
    main()
