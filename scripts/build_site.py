from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "recipes"
SITE = ROOT / "site"
DIST = ROOT / "dist"

CATEGORY_ORDER = [
    "Förrätter",
    "Huvudrätter",
    "Desserter",
    "Vardagsmat",
    "Säsongens smaker",
    "Teman",
    "Övrigt",
]


def read_recipe(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta = {}
    body = text
    if text.startswith("---\n"):
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
    title = str(meta.get("title") or path.stem.replace("-", " ").title())
    category = str(meta.get("category") or "Övrigt")
    return {
        "path": path,
        "slug": path.stem,
        "title": title,
        "category": category,
        "meta": meta,
        "body": body.strip(),
    }


def first_paragraph(md: str) -> str:
    for block in re.split(r"\n\s*\n", md):
        block = block.strip()
        if not block or block.startswith("#") or block.startswith(">") or block.startswith("-") or block.startswith("|"):
            continue
        clean = re.sub(r"[*_`#]", "", block)
        return clean[:220]
    return ""


def render_recipe_page(recipe: dict) -> str:
    meta = recipe["meta"]
    body_html = markdown.markdown(
        recipe["body"],
        extensions=["extra", "sane_lists"],
    )
    facts = []
    if meta.get("portions"):
        facts.append(f"{html.escape(str(meta['portions']))} portioner")
    if meta.get("time_minutes"):
        facts.append(f"{html.escape(str(meta['time_minutes']))} min")
    if meta.get("complexity"):
        facts.append(html.escape(str(meta["complexity"])))
    if meta.get("occasion"):
        facts.append(html.escape(str(meta["occasion"])))
    facts_html = " · ".join(facts)
    source = meta.get("source")
    source_html = f'<p class="source">Källa: {html.escape(str(source))}</p>' if source else ""

    return f'''<!doctype html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(recipe['title'])} · Alltid bra mat på Säteriet</title>
  <link rel="stylesheet" href="../style.css">
</head>
<body>
<nav class="mobile-top">
  <a class="iconbtn" href="../index.html#recept" aria-label="Tillbaka">‹<span>Tillbaka</span></a>
  <div class="brand"><strong>Alltid bra mat på Säteriet</strong><em>Recept, minnen och måltider sedan 1860</em></div>
  <a class="iconbtn" href="../index.html" aria-label="Hem">⌂<span>Hem</span></a>
</nav>
<main class="recipe-page">
  <article class="recipe-content">
    <p class="eyebrow">{html.escape(recipe['category'])}</p>
    <h1>{html.escape(recipe['title'])}</h1>
    {f'<p class="recipe-facts">{facts_html}</p>' if facts_html else ''}
    {source_html}
    <div class="recipe-markdown">{body_html}</div>
  </article>
</main>
<footer><p>Säteriet · anno 1860 · en levande receptsamling</p></footer>
</body>
</html>'''


def render_index(recipes: list[dict]) -> str:
    by_category: dict[str, list[dict]] = {}
    for recipe in recipes:
        by_category.setdefault(recipe["category"], []).append(recipe)

    present_categories = [c for c in CATEGORY_ORDER if c in by_category]
    present_categories += sorted(c for c in by_category if c not in present_categories)

    category_cards = "".join(
        f'<a href="#{slugify(category)}"><h2>{html.escape(category)}</h2><p>{len(by_category[category])} recept</p></a>'
        for category in present_categories
    )

    sections = []
    for category in present_categories:
        cards = []
        for recipe in sorted(by_category[category], key=lambda r: r["title"].casefold()):
            meta = recipe["meta"]
            bits = []
            if meta.get("portions"):
                bits.append(f"{meta['portions']} port")
            if meta.get("time_minutes"):
                bits.append(f"{meta['time_minutes']} min")
            tag = " · ".join(bits)
            summary = first_paragraph(recipe["body"])
            cards.append(f'''<article>
<p class="tag">{html.escape(tag) if tag else html.escape(category.upper())}</p>
<h3>{html.escape(recipe['title'])}</h3>
{f'<p>{html.escape(summary)}</p>' if summary else ''}
<a href="recipes/{recipe['slug']}.html">Läs receptet →</a>
</article>''')
        sections.append(f'''<section class="recipes category-section" id="{slugify(category)}">
<p class="kicker">{html.escape(category.upper())}</p>
<h2>{html.escape(category)}</h2>
<div class="recipe-grid">{''.join(cards)}</div>
</section>''')

    return f'''<!doctype html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Alltid bra mat på Säteriet</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
<nav class="mobile-top">
  <button class="iconbtn" aria-label="Meny">☰<span>Meny</span></button>
  <div class="brand"><strong>Alltid bra mat på Säteriet</strong><em>Recept, minnen och måltider sedan 1860</em></div>
  <a class="iconbtn" href="#recept" aria-label="Recept">⌕<span>Recept</span></a>
</nav>
<header id="hem" class="hero hero-plain"><div class="hero-copy">
  <p class="eyebrow">SÄTERIET · ANNO 1860</p>
  <h1>Välkommen till vår receptsamling</h1>
  <div class="rule">❦</div>
  <p>Här samlar vi favoritrecept, rätter vi vill laga igen och måltider som hör ihop med en särskild kväll eller årstid.</p>
</div></header>
<main>
<section id="teman" class="category-strip">{category_cards}</section>
<div id="recept">{''.join(sections)}</div>
<section class="about"><div class="ornament">❦</div><p>”God mat smakar ännu bättre i gott sällskap”</p></section>
</main>
<footer><p>Säteriet · anno 1860 · en levande receptsamling</p></footer>
</body>
</html>'''


def slugify(value: str) -> str:
    table = str.maketrans({"å": "a", "ä": "a", "ö": "o", "Å": "a", "Ä": "a", "Ö": "o"})
    value = value.translate(table).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "kategori"


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(SITE, DIST)
    (DIST / "recipes").mkdir(parents=True, exist_ok=True)

    recipes = [read_recipe(path) for path in sorted(RECIPES.glob("*.md"))]
    (DIST / "index.html").write_text(render_index(recipes), encoding="utf-8")
    for recipe in recipes:
        (DIST / "recipes" / f"{recipe['slug']}.html").write_text(render_recipe_page(recipe), encoding="utf-8")

    print(f"Built {len(recipes)} recipes into {DIST}")


if __name__ == "__main__":
    main()
