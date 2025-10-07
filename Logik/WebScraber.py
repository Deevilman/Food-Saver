#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebScraber -> YAML opskrifter
- Crawler op til N dybt (default 5)
- Finder opskriftslinks på oversigtssider
- Følger også "Se flere opskrifter" / pagination links
- Gemmer opskrifter i YAML (.yml)

Dependencies:
    pip install requests beautifulsoup4 pyyaml
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from collections import deque
import requests
from bs4 import BeautifulSoup
import yaml
from pathlib import Path


# ---------- Helpers ----------

def slugify(text: str) -> str:
    text = text.strip().lower()
    replacements = {"æ": "ae", "ø": "oe", "å": "aa"}
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    text = re.sub(r"-{2,}", "-", text)
    return text or "opskrift"


def iso8601_duration_to_minutes(iso: Optional[str]) -> Optional[int]:
    if not iso:
        return None
    m = re.fullmatch(r"P(T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", iso.strip().upper())
    if not m:
        return None
    hours = int(m.group(2) or 0)
    minutes = int(m.group(3) or 0)
    seconds = int(m.group(4) or 0)
    total = hours * 60 + minutes + (1 if seconds and seconds > 0 else 0)
    return total or None


def first_non_empty(*vals):
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
        if v not in (None, "", [], {}):
            return v
    return None


def to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    s = str(value).strip()
    m = re.match(r"^\s*(\d+)", s)
    return int(m.group(1)) if m else None


def clean_space(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    return re.sub(r"\s+", " ", s).strip()


def ensure_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def parse_ingredient_line(line: str) -> Dict[str, Any]:
    s = line.strip()
    if not s:
        return {"name": line}
    m = re.match(r"^\s*(\d+(?:[.,]\d+)?)\s*([a-zA-ZæøåÆØÅ%]+)?\s+(.*)$", s)
    if not m:
        return {"name": s}
    amount = float(m.group(1).replace(",", "."))
    unit = m.group(2)
    name = m.group(3).strip()
    return {"amount": amount, "unit": unit, "name": name}


# ---------- Data models ----------

@dataclass
class Recipe:
    title: Optional[str] = None
    servings: Optional[int] = None
    time_prep_min: Optional[int] = None
    time_cook_min: Optional[int] = None
    time_total_min: Optional[int] = None
    ingredients: List[str] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)
    author: Optional[str] = None
    source_url: Optional[str] = None
    image: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    cuisine: Optional[str] = None

    def to_yaml_dict_rich(self) -> Dict[str, Any]:
        return {
            "titel": self.title,
            "portioner": self.servings,
            "tid": {
                "forberedelse_min": self.time_prep_min,
                "tilberedning_min": self.time_cook_min,
                "total_min": self.time_total_min,
            },
            "ingredienser": self.ingredients,
            "fremgangsmaade": self.instructions,
            "metadata": {
                "forfatter": self.author,
                "kilde_url": self.source_url,
                "billede": self.image,
                "kategorier": self.categories,
                "køkken": self.cuisine,
            },
        }

    def to_yaml_dict_simple(self, per_person: bool = False) -> Dict[str, Any]:
        total_min = first_non_empty(self.time_total_min, self.time_cook_min, self.time_prep_min)
        data = {
            "titel": self.title,
            "tid": int(total_min) if isinstance(total_min, int) else total_min,
        }

        if per_person and self.servings and self.ingredients:
            mapping = {}
            for line in self.ingredients:
                parts = parse_ingredient_line(line)
                name = parts.get("name") or line
                if "amount" in parts and isinstance(self.servings, int) and self.servings > 0:
                    per = parts["amount"] / float(self.servings)
                    unit = parts.get("unit")
                    val = f"{per:g} {unit}" if unit else f"{per:g}"
                    mapping[name] = val
                else:
                    mapping[name] = line
            data["ingredienser"] = mapping
        else:
            data["ingredienser"] = self.ingredients

        data["fremgangsmåde"] = self.instructions
        return data


# ---------- Extraction ----------

def find_jsonld_blocks(soup: BeautifulSoup) -> List[Any]:
    blocks = []
    for tag in soup.find_all("script", type=lambda t: t and "ld+json" in t):
        try:
            txt = tag.string or tag.get_text()
            if not txt:
                continue
            txt = txt.strip()
            txt = re.sub(r"<!--.*?-->", "", txt, flags=re.DOTALL)
            data = json.loads(txt)
            blocks.extend(ensure_list(data))
        except Exception:
            continue
    return blocks


def normalize_instruction_obj(obj: Any) -> List[str]:
    steps: List[str] = []
    if isinstance(obj, str):
        parts = re.split(r"(?:\r?\n|\\n|\\r|\\t)+", obj)
        steps.extend([clean_space(p) for p in parts if clean_space(p)])
    elif isinstance(obj, list):
        for item in obj:
            steps.extend(normalize_instruction_obj(item))
    elif isinstance(obj, dict):
        t = obj.get("@type") or obj.get("type") or ""
        if t in ("HowToStep", "HowToDirection"):
            text = first_non_empty(obj.get("text"), obj.get("name"), obj.get("description"))
            if text:
                steps.append(clean_space(text))
        elif t in ("HowToSection",):
            inner = first_non_empty(obj.get("itemListElement"), obj.get("steps"))
            steps.extend(normalize_instruction_obj(inner))
        else:
            text = first_non_empty(obj.get("text"), obj.get("name"), obj.get("description"))
            if text:
                steps.append(clean_space(text))
    return [s for s in steps if s]


def pick_recipe_from_jsonld(blocks: List[Any]) -> Optional[Dict[str, Any]]:
    for b in blocks:
        if not isinstance(b, dict):
            continue
        types = ensure_list(b.get("@type"))
        if "Recipe" in types:
            return b
        graph = b.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                if isinstance(item, dict) and "Recipe" in ensure_list(item.get("@type")):
                    return item
        if any(k in b for k in ("recipeIngredient", "recipeInstructions")):
            return b
    return None


def extract_recipe_from_jsonld(block: Dict[str, Any], source_url: str) -> Recipe:
    name = first_non_empty(block.get("name"), block.get("headline"))
    servings_raw = first_non_empty(block.get("recipeYield"), block.get("yield"))
    servings = to_int(servings_raw)

    prep = iso8601_duration_to_minutes(block.get("prepTime"))
    cook = iso8601_duration_to_minutes(block.get("cookTime"))
    total = iso8601_duration_to_minutes(block.get("totalTime"))
    if not total and prep and cook:
        total = prep + cook

    ingredients_raw = ensure_list(block.get("recipeIngredient"))
    ingredients = [clean_space(s) for s in ingredients_raw if clean_space(s)]

    inst_raw = first_non_empty(block.get("recipeInstructions"), block.get("instructions"))
    instructions = normalize_instruction_obj(inst_raw) if inst_raw else []

    author_obj = first_non_empty(block.get("author"), block.get("creator"))
    author_name = None
    if isinstance(author_obj, list):
        for a in author_obj:
            if isinstance(a, dict):
                author_name = first_non_empty(a.get("name"))
                if author_name:
                    break
            elif isinstance(a, str):
                author_name = a
                break
    elif isinstance(author_obj, dict):
        author_name = first_non_empty(author_obj.get("name"))
    elif isinstance(author_obj, str):
        author_name = author_obj

    image = None
    img = block.get("image")
    if isinstance(img, dict):
        image = first_non_empty(img.get("url"), img.get("contentUrl"))
    elif isinstance(img, list):
        for i in img:
            if isinstance(i, dict):
                image = first_non_empty(i.get("url"), i.get("contentUrl"))
                if image:
                    break
            elif isinstance(i, str):
                image = i
                break
    elif isinstance(img, str):
        image = img

    categories = []
    for key in ("recipeCategory", "keywords"):
        val = block.get(key)
        if isinstance(val, list):
            categories.extend([str(v) for v in val])
        elif isinstance(val, str):
            parts = [p.strip() for p in val.split(",") if p.strip()]
            categories.extend(parts if key == "keywords" else [val])

    cuisine = None
    rc = block.get("recipeCuisine")
    if isinstance(rc, list):
        cuisine = ", ".join([str(v) for v in rc])
    elif isinstance(rc, str):
        cuisine = rc

    return Recipe(
        title=clean_space(name),
        servings=servings,
        time_prep_min=prep,
        time_cook_min=cook,
        time_total_min=total,
        ingredients=ingredients,
        instructions=instructions,
        author=clean_space(author_name),
        source_url=source_url,
        image=image,
        categories=categories,
        cuisine=cuisine,
    )


# ---------- Scraper + Crawl ----------

def fetch(url: str, timeout: int = 20) -> Optional[str]:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        sys.stderr.write(f"[fejl] Kunne ikke hente {url}: {e}\n")
        return None


def scrape_one(url: str) -> Optional[Recipe]:
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    blocks = find_jsonld_blocks(soup)
    block = pick_recipe_from_jsonld(blocks)
    if not block:
        return None
    recipe = extract_recipe_from_jsonld(block, source_url=url)
    if not recipe.title and soup.title:
        recipe.title = clean_space(soup.title.get_text())
    return recipe


def collect_recipe_links(page_url: str, html: str) -> List[str]:
    """Finder både opskriftslinks og pagination-links."""
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(page_url, href)
        # Opskriftssider
        if "/opskrifter/" in full and full.endswith("/"):
            urls.append(full.split("#")[0])
        # Pagination: fx ?page=2 eller "se flere"
        if "page=" in full or "se-flere" in full:
            urls.append(full.split("#")[0])
    return sorted(set(urls))


def write_yaml(recipe: Recipe, out_dir, schema: str = "rich", overwrite: bool = False, per_person: bool = False):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = slugify(recipe.title or "opskrift")

    out_path = out_dir / f"{filename}.yml"
    if not overwrite and out_path.exists():
        i = 2
        while True:
            candidate = out_dir / f"{filename}-{i}.yml"
            if not candidate.exists():
                out_path = candidate
                break
            i += 1

    data = recipe.to_yaml_dict_rich() if schema == "rich" else recipe.to_yaml_dict_simple(per_person=per_person)
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
    return out_path


def crawl(start_urls: List[str], max_depth: int, sleep: float, schema: str,
          per_person: bool, overwrite: bool, out_dir: str) -> int:
    visited = set()
    queue = deque([(url, 0) for url in start_urls])
    ok = 0

    while queue:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue
        visited.add(url)

        sys.stderr.write(f"[depth {depth}] Henter {url}\n")
        html = fetch(url)
        if not html:
            continue

        found_links = collect_recipe_links(url, html)
        if found_links and depth < max_depth:
            for link in found_links:
                if link not in visited:
                    queue.append((link, depth + 1))

        recipe = scrape_one(url)
        if recipe:
            path = write_yaml(recipe, out_dir, schema=schema,
                              overwrite=overwrite, per_person=per_person)
            sys.stderr.write(f"  -> gemt: {path}\n")
            ok += 1

        if sleep:
            time.sleep(sleep)

    return ok


# ---------- Main ----------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Scrap opskrifter til YAML filer")
    parser.add_argument("urls", nargs="*", help="En eller flere opskrift- eller oversigts-URLer")
    parser.add_argument("--urls-file", help="Sti til tekstfil med URLer, en pr linje")
    parser.add_argument(
        "--out-dir",
        default=r"C:\Users\oller\OneDrive\Desktop\KOD - Food saver\DB\Opskrifter",
        help="Mappe til .yml output"
    )
    parser.add_argument("--schema", choices=["rich", "simple"], default="rich",
                        help="Vælg YAML format: rich eller simple")
    parser.add_argument("--per-person", action="store_true",
                        help="Ved simple schema: ingredienser pr. person")
    parser.add_argument("--overwrite", action="store_true", help="Overskriv eksisterende filer")
    parser.add_argument("--sleep", type=float, default=0.0, help="Pause i sekunder mellem forespørgsler")
    parser.add_argument("--depth", type=int, default=5, help="Hvor dybt crawleren må følge links (default 5)")
    args = parser.parse_args(argv)

    out_dir = args.out_dir
    all_urls: List[str] = []
    all_urls.extend(args.urls or [])
    if args.urls_file:
        try:
            with open(args.urls_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        all_urls.append(line)
        except Exception as e:
            sys.stderr.write(f"[fejl] Kunne ikke læse {args.urls_file}: {e}\n")
            return 2

    if not all_urls:
        sys.stderr.write("Brug: angiv mindst én URL eller en --urls-file\n")
        return 1

    ok = crawl(all_urls, max_depth=args.depth, sleep=args.sleep,
               schema=args.schema, per_person=args.per_person,
               overwrite=args.overwrite, out_dir=out_dir)

    sys.stderr.write(f"Færdig. {ok} opskrifter gemt i {out_dir}\n")
    return 0 if ok > 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
