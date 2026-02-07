import argparse
from html import unescape
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None


SKIP_CLASSES = {
    "toc",
    "navbox",
    "vertical-navbox",
    "ambox",
    "metadata",
    "hatnote",
    "catlinks",
    "mw-references-wrap",
    "mw-editsection",
    "noprint",
    "printfooter",
    "thumb",
    "rellink",
    "reference",
}

SKIP_TAGS = {
    "script",
    "style",
    "noscript",
}


def normalize_text(text: str) -> str:
    text = unescape(text)
    return " ".join(text.split())


def should_skip(tag) -> bool:
    if tag is None:
        return True
    if tag.name in SKIP_TAGS:
        return True
    attrs = getattr(tag, "attrs", None)
    if not attrs:
        return False
    classes = set(attrs.get("class", []))
    if classes & SKIP_CLASSES:
        return True
    return False


def render_list(tag, indent: int = 0) -> list[str]:
    lines: list[str] = []
    is_ordered = tag.name == "ol"
    for index, li in enumerate(tag.find_all("li", recursive=False), start=1):
        prefix = f"{index}. " if is_ordered else "- "
        parts: list[str] = []
        for child in li.contents:
            if getattr(child, "name", None) in {"ul", "ol"}:
                continue
            if hasattr(child, "get_text"):
                parts.append(child.get_text(" ", strip=True))
            else:
                parts.append(str(child).strip())
        text = normalize_text(" ".join(part for part in parts if part))
        if text:
            lines.append(" " * indent + prefix + text)
        nested_lists = li.find_all(["ul", "ol"], recursive=False)
        for nested in nested_lists:
            lines.extend(render_list(nested, indent=indent + 2))
    return lines


def render_table(table) -> list[str]:
    rows: list[list[str]] = []
    has_header = False
    for tr in table.find_all("tr", recursive=True):
        cells = tr.find_all(["th", "td"], recursive=False)
        if not cells:
            continue
        row = [normalize_text(cell.get_text(" ", strip=True)) for cell in cells]
        if any(cell.name == "th" for cell in cells):
            has_header = True
        if any(row):
            rows.append(row)

    if not rows:
        return []

    if all(len(row) == 2 for row in rows):
        lines = ["- {}: {}".format(row[0], row[1]) for row in rows if row[0] or row[1]]
        return lines

    max_cols = max(len(row) for row in rows)
    padded = [row + [""] * (max_cols - len(row)) for row in rows]

    if has_header:
        header = padded[0]
        body = padded[1:]
    else:
        header = [f"Col {i + 1}" for i in range(max_cols)]
        body = padded

    lines = ["| " + " | ".join(header) + " |"]
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def extract_title(soup: BeautifulSoup, html_path: Path) -> str:
    title_tag = soup.find("title")
    if title_tag and title_tag.get_text(strip=True):
        return title_tag.get_text(strip=True).replace(" - ポケモンWiki", "")
    return html_path.stem


def extract_canonical_url(soup: BeautifulSoup) -> str | None:
    link_tag = soup.find("link", attrs={"rel": "canonical"})
    if link_tag:
        return link_tag.get("href")
    return None


def render_content(content) -> list[str]:
    lines: list[str] = []
    for tag in content.find_all(True, recursive=False):
        if should_skip(tag):
            continue

        if tag.name in {"h2", "h3", "h4"}:
            level = {"h2": "##", "h3": "###", "h4": "####"}[tag.name]
            heading_text = normalize_text(tag.get_text(" ", strip=True))
            if heading_text:
                lines.append(f"{level} {heading_text}")
            continue

        if tag.name == "p":
            text = normalize_text(tag.get_text(" ", strip=True))
            if text:
                lines.append(text)
            continue

        if tag.name in {"ul", "ol"}:
            lines.extend(render_list(tag))
            continue

        if tag.name == "dl":
            for dt in tag.find_all("dt", recursive=False):
                term = normalize_text(dt.get_text(" ", strip=True))
                dd = dt.find_next_sibling("dd")
                if not dd:
                    continue
                desc = normalize_text(dd.get_text(" ", strip=True))
                if term or desc:
                    lines.append(f"- {term}: {desc}")
            continue

        if tag.name == "table":
            lines.extend(render_table(tag))
            continue

        if tag.name in {"div", "meta"}:
            if should_skip(tag):
                continue
            lines.extend(render_content(tag))
            continue

    return lines


def html_to_markdown(html_path: Path, research_date: str) -> str:
    html_text = html_path.read_text(encoding="utf-8")
    if BeautifulSoup is None:
        raise RuntimeError("BeautifulSoup is not available. Install beautifulsoup4.")

    soup = BeautifulSoup(html_text, "html.parser")
    title = extract_title(soup, html_path)
    canonical_url = extract_canonical_url(soup)

    content = soup.find("div", class_="mw-parser-output")
    if content is None:
        raise RuntimeError(f"mw-parser-output not found in {html_path}")

    for tag in content.find_all(True):
        if should_skip(tag):
            tag.decompose()

    for tag in content.find_all("sup", class_="reference"):
        tag.decompose()

    body_lines = render_content(content)

    lines: list[str] = [f"# 仕様書: {title}", ""]
    if research_date:
        lines.append(f"調査日: {research_date}")
    if canonical_url:
        lines.append(f"参照URL: {canonical_url}")
    lines.append("")

    lines.extend(body_lines)

    cleaned: list[str] = []
    for line in lines:
        if line or (cleaned and cleaned[-1]):
            cleaned.append(line)
    if cleaned and cleaned[-1] != "":
        cleaned.append("")

    return "\n".join(cleaned)


def generate_specs(html_root: Path, spec_root: Path, research_date: str, overwrite: bool) -> int:
    generated = 0
    for category_dir in sorted(html_root.iterdir()):
        if not category_dir.is_dir():
            continue
        output_dir = spec_root / category_dir.name
        output_dir.mkdir(parents=True, exist_ok=True)
        for html_path in sorted(category_dir.glob("*.html")):
            output_path = output_dir / f"{html_path.stem}.md"
            if output_path.exists() and not overwrite:
                continue
            markdown = html_to_markdown(html_path, research_date)
            output_path.write_text(markdown, encoding="utf-8")
            generated += 1
    return generated


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate spec markdown from PokemonWiki HTML")
    parser.add_argument("--html-root", default="docs/html", help="Path to html root")
    parser.add_argument("--spec-root", default="docs/spec", help="Path to spec root")
    parser.add_argument("--date", default="2026-02-07", help="Research date")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing spec files")
    args = parser.parse_args()

    html_root = Path(args.html_root)
    spec_root = Path(args.spec_root)

    generated = generate_specs(html_root, spec_root, args.date, args.overwrite)
    print(f"Generated {generated} spec files.")


if __name__ == "__main__":
    main()
