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

CATEGORY_ORDER = ["Förrätter", "Huvudrätter", "Desserter", "Vardagsmat", "Säsongens smaker", "Teman", "Övrigt"]


def read_recipe(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta = {}
    body = text
    if text.startswith("---\n"):
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
    title = str(meta.get("title") or path.stem.replace("-", " ").title())
    category = str(meta.get("category") or "Övrigt")
    return {"path": path, "slug": path.stem, "title": title, "category": category, "meta": meta, "body": body.strip()}


def first_paragraph(md: str) -> str:
    for block in re.split(r"\n\s*\n", md):
        block = block.strip()
        if not block or block.startswith("#") or block.startswith(">") or block.startswith("-") or block.startswith("|"):
            continue
        return re.sub(r"[*_`#]", "", block)[:220]
    return ""


def pizza_calculator() -> str:
    return '''<section class="pizza-calculator" id="degkalkylator"><h2>Degkalkylator</h2><p>Välj antal pizzor, degbollarnas vikt, önskad degfuktighet och hur stor poolish du redan har gjort. Grundreceptet använder 70 % hydrering och 4 % salt.</p><div class="calc-inputs"><label>Antal pizzor<input id="pizza-count" type="number" min="1" max="30" step="1" value="6"></label><label>Gram per degboll<input id="ball-weight" type="number" min="150" max="500" step="5" value="250"></label><label>Degfuktighet / hydrering (%)<input id="hydration" type="number" min="55" max="85" step="1" value="70"></label><label>Poolish – mjöl + vatten<select id="poolish-size"><option value="300">300 + 300 g</option><option value="400">400 + 400 g</option><option value="500" selected>500 + 500 g</option></select></label></div><div id="calc-warning" class="calc-warning" role="status"></div><div class="calc-result"><p><strong>Total deg:</strong> <span id="total-dough"></span> g</p><h3>Tillsätt nästa dag</h3><table><tbody><tr><th>Caputo Pizzeria-mjöl</th><td><span id="add-flour"></span> g</td></tr><tr><th>Vatten</th><td><span id="add-water"></span> g</td></tr><tr><th>Salt</th><td><span id="add-salt"></span> g</td></tr></tbody></table></div><p class="calc-note">Poolish: lika delar mjöl och vatten + 5 g jäst. Salt är 4 % av total mjölmängd. Jästen ingår i totalvikten i beräkningen.</p></section><script>(function(){const count=document.getElementById('pizza-count'),weight=document.getElementById('ball-weight'),hydration=document.getElementById('hydration'),pool=document.getElementById('poolish-size'),warn=document.getElementById('calc-warning');function calc(){let n=Math.max(1,Math.min(30,Number(count.value)||1)),w=Math.max(150,Math.min(500,Number(weight.value)||250)),h=Math.max(55,Math.min(85,Number(hydration.value)||70))/100,p=Number(pool.value),target=n*w,yeast=5,flour=(target-yeast)/(1+h+.04),water=h*flour,salt=.04*flour,af=flour-p,aw=water-p;document.getElementById('total-dough').textContent=Math.round(target);document.getElementById('add-flour').textContent=Math.max(0,Math.round(af));document.getElementById('add-water').textContent=Math.max(0,Math.round(aw));document.getElementById('add-salt').textContent=Math.round(salt);warn.textContent=(af<0||aw<0)?'Den valda poolishen är för stor för den här degmängden eller hydreringen. Välj en mindre poolish, högre hydrering eller gör fler pizzor.':'';}[count,weight,hydration,pool].forEach(x=>x.addEventListener('input',calc));calc();})();</script>'''


def render_recipe_page(recipe: dict) -> str:
    meta = recipe["meta"]
    body_html = markdown.markdown(recipe["body"], extensions=["extra", "sane_lists"])
    calculator_html = pizza_calculator() if meta.get("pizza_calculator") else ""
    facts = []
    if meta.get("portions"): facts.append(f"{html.escape(str(meta['portions']))} portioner")
    if meta.get("time_minutes"): facts.append(f"{html.escape(str(meta['time_minutes']))} min")
    if meta.get("complexity"): facts.append(html.escape(str(meta["complexity"])))
    if meta.get("occasion"): facts.append(html.escape(str(meta["occasion"])))
    facts_html = " · ".join(facts)
    source = meta.get("source")
    source_html = f'<p class="source">Källa: {html.escape(str(source))}</p>' if source else ""
    print_icon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2M6 14h12v7H6z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    return f'''<!doctype html><html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(recipe['title'])} · Alltid bra mat på Säteriet</title><link rel="stylesheet" href="../style.css"></head><body><nav class="mobile-top"><a class="iconbtn" href="../index.html#recept" aria-label="Tillbaka">‹<span>Tillbaka</span></a><div class="brand"><strong>Alltid bra mat på Säteriet</strong><em>Recept, minnen och måltider sedan 1860</em></div><a class="iconbtn" href="../index.html" aria-label="Hem">⌂<span>Hem</span></a></nav><main class="recipe-page"><article class="recipe-content"><button class="print-button" type="button" onclick="window.print()" aria-label="Skriv ut recept" title="Skriv ut recept">{print_icon}<span>Skriv ut</span></button><p class="eyebrow">{html.escape(recipe['category'])}</p><h1>{html.escape(recipe['title'])}</h1>{f'<p class="recipe-facts">{facts_html}</p>' if facts_html else ''}{source_html}<div class="recipe-markdown">{body_html}</div>{calculator_html}</article></main><footer><img src="../assets/signature.webp" alt="Alltid bra mat på Säteriet"><p>Säteriet · anno 1860 · en levande receptsamling</p></footer></body></html>'''


def render_index(recipes: list[dict]) -> str:
    by_category: dict[str, list[dict]] = {}
    for recipe in recipes: by_category.setdefault(recipe["category"], []).append(recipe)
    present_categories = [c for c in CATEGORY_ORDER if c in by_category]
    present_categories += sorted(c for c in by_category if c not in present_categories)
    category_cards = "".join(f'<a href="#{slugify(c)}"><h2>{html.escape(c)}</h2><p>{len(by_category[c])} recept</p></a>' for c in present_categories)
    sections = []
    for category in present_categories:
        cards = []
        for recipe in sorted(by_category[category], key=lambda r: r["title"].casefold()):
            meta = recipe["meta"]
            bits = []
            if meta.get("portions"): bits.append(f"{meta['portions']} port")
            if meta.get("time_minutes"): bits.append(f"{meta['time_minutes']} min")
            tag = " · ".join(bits)
            summary = first_paragraph(recipe["body"])
            cards.append(f'''<article><p class="tag">{html.escape(tag) if tag else html.escape(category.upper())}</p><h3>{html.escape(recipe['title'])}</h3>{f'<p>{html.escape(summary)}</p>' if summary else ''}<a href="recipes/{recipe['slug']}.html">Läs receptet →</a></article>''')
        sections.append(f'''<section class="recipes category-section" id="{slugify(category)}"><p class="kicker">{html.escape(category.upper())}</p><h2>{html.escape(category)}</h2><div class="recipe-grid">{''.join(cards)}</div></section>''')
    return f'''<!doctype html><html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Alltid bra mat på Säteriet</title><link rel="stylesheet" href="style.css"></head><body><nav class="mobile-top"><button class="iconbtn" aria-label="Meny">☰<span>Meny</span></button><div class="brand"><strong>Alltid bra mat på Säteriet</strong><em>Recept, minnen och måltider sedan 1860</em></div><a class="iconbtn" href="#recept" aria-label="Recept">⌕<span>Recept</span></a></nav><header id="hem" class="hero hero-plain"><div class="hero-copy"><p class="eyebrow">SÄTERIET · ANNO 1860</p><h1>Välkommen till vår receptsamling</h1><div class="hero-key"><img src="assets/key.png" alt="Alltid bra mat på Säteriet"></div><p>Här samlar vi favoritrecept, rätter vi vill laga igen och måltider som hör ihop med en särskild kväll eller årstid.</p></div></header><main><section id="teman" class="category-strip">{category_cards}</section><div id="recept">{''.join(sections)}</div><section class="about"><div class="ornament">❦</div><p>”God mat smakar ännu bättre i gott sällskap”</p></section></main><footer><img src="assets/signature.webp" alt="Alltid bra mat på Säteriet"><p>Säteriet · anno 1860 · en levande receptsamling</p></footer></body></html>'''


def slugify(value: str) -> str:
    table = str.maketrans({"å":"a","ä":"a","ö":"o","Å":"a","Ä":"a","Ö":"o"})
    return re.sub(r"[^a-z0-9]+", "-", value.translate(table).lower()).strip("-") or "kategori"


def main() -> None:
    if DIST.exists(): shutil.rmtree(DIST)
    shutil.copytree(SITE, DIST)
    (DIST / "recipes").mkdir(parents=True, exist_ok=True)
    recipes = [read_recipe(path) for path in sorted(RECIPES.glob("*.md"))]
    (DIST / "index.html").write_text(render_index(recipes), encoding="utf-8")
    for recipe in recipes: (DIST / "recipes" / f"{recipe['slug']}.html").write_text(render_recipe_page(recipe), encoding="utf-8")
    print(f"Built {len(recipes)} recipes into {DIST}")

if __name__ == "__main__": main()
