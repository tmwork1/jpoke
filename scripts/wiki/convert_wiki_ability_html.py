#!/usr/bin/env python3
"""
docs/wiki_html/abilities/*.html を読み込み、
テンプレート準拠の特性仕様書 docs/spec/abilities/*.md を生成する。
"""

from pathlib import Path
import re
from bs4 import BeautifulSoup, NavigableString, Tag

PROJECT_DIR = Path(__file__).parent.parent.parent
HTML_DIR = PROJECT_DIR / "docs" / "wiki_html" / "abilities"
SPEC_DIR = PROJECT_DIR / "docs" / "spec" / "abilities"
TODAY = "2026-06-03"

# 出力する h2 セクション（この順で出力）
OUTPUT_SECTIONS = ["効果", "特性の仕様", "備考", "関連項目"]

# 変換しない（スキップする）セクションのキーワード
SKIP_H2_KEYWORDS = [
    "説明文",
    "所有ポケモン",
    "各言語版",
    "アニメ",
    "不思議のダンジョン",
    "ポケモンカード",
    "カードゲーム",
    "TCG",
]


def is_old_gen_only_h3(text: str) -> bool:
    """第9世代より前の特定世代のみに適用する h3 なら True を返す（スキップ対象）。"""
    if "世代" not in text:
        return False
    if "第九世代" in text:
        return False
    # "第X世代以降" は第9世代にも適用されるので残す
    if re.search(r"第[一二三四五六七八]世代以降", text):
        return False
    # それ以外の世代限定見出し → スキップ
    return True


def elem_to_md(node, depth: int = 0) -> str:
    """BS4 ノードを再帰的に Markdown テキストへ変換する。"""
    if node is None:
        return ""
    if isinstance(node, NavigableString):
        return str(node)

    tag = node.name
    if not tag or tag in ("script", "style", "meta"):
        return ""

    # リンクはテキストだけ残す
    if tag == "a":
        return node.get_text()

    # インライン要素はタグを除去してテキスト継承
    if tag in ("b", "strong", "i", "em", "sup", "sub"):
        return "".join(elem_to_md(c, depth) for c in node.children)

    if tag == "span":
        # 旧式アンカースパン（.E5... 形式の id）はスキップ
        if node.get("id", "").startswith("."):
            return ""
        return "".join(elem_to_md(c, depth) for c in node.children)

    if tag == "p":
        inner = "".join(elem_to_md(c, depth) for c in node.children).strip()
        return inner + "\n" if inner else ""

    if tag == "ul":
        parts = [_li_to_md(li, depth) for li in node.find_all("li", recursive=False)]
        return "\n".join(parts) + "\n" if parts else ""

    if tag == "ol":
        parts = [
            _li_to_md(li, depth, ordered=True, num=i)
            for i, li in enumerate(node.find_all("li", recursive=False), 1)
        ]
        return "\n".join(parts) + "\n" if parts else ""

    if tag == "dl":
        return _dl_to_md(node)

    if tag == "table":
        return _table_to_md(node)

    if tag in ("h3", "h4"):
        level = "#" * int(tag[1])
        headline = node.find("span", class_="mw-headline")
        text = headline.get_text().strip() if headline else node.get_text().strip()
        return f"\n{level} {text}\n"

    if tag == "br":
        return "\n"

    # その他: 子要素を処理
    return "".join(elem_to_md(c, depth) for c in node.children)


def _li_to_md(li: Tag, depth: int = 0, ordered: bool = False, num: int = 1) -> str:
    indent = "  " * depth
    prefix = f"{num}. " if ordered else "- "

    text_parts: list[str] = []
    nested_blocks: list[str] = []

    for child in li.children:
        if isinstance(child, NavigableString):
            text_parts.append(str(child))
        elif child.name in ("ul", "ol"):
            nested_blocks.append(elem_to_md(child, depth + 1))
        else:
            text_parts.append(elem_to_md(child, depth))

    text = "".join(text_parts).strip()
    result = indent + prefix + text
    if nested_blocks:
        result += "\n" + "".join(nested_blocks).rstrip()
    return result


def _dl_to_md(dl: Tag) -> str:
    """定義リストを変換する。<dd> 内にテーブル等が含まれる場合は再帰処理する。"""
    parts: list[str] = []
    current_dt = ""
    for child in dl.children:
        if isinstance(child, NavigableString):
            continue
        if child.name == "dt":
            current_dt = child.get_text().strip()
        elif child.name == "dd":
            dd_content = "".join(elem_to_md(c) for c in child.children).strip()
            if not dd_content:
                continue
            if current_dt:
                parts.append(f"- {current_dt}: {dd_content}")
                current_dt = ""
            else:
                # <dt> なし: テーブルなどをそのまま出力
                parts.append(dd_content)
    return "\n".join(parts) + "\n" if parts else ""


def _table_to_md(table: Tag) -> str:
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = []
        for cell in tr.find_all(["td", "th"]):
            text = cell.get_text().strip().replace("\n", " ").replace("|", "｜")
            cells.append(text)
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    max_cols = max(len(r) for r in rows)
    padded = [r + [""] * (max_cols - len(r)) for r in rows]

    lines: list[str] = []
    for i, row in enumerate(padded):
        lines.append("| " + " | ".join(row) + " |")
        if i == 0:
            lines.append("| " + " | ".join(["---"] * max_cols) + " |")

    return "\n".join(lines) + "\n"


def _get_section_elements(h2_node: Tag) -> list[Tag]:
    """h2 から次の h2 までの要素を収集し、旧世代限定 h3 と boilerplate 通知をスキップする。"""
    elements: list[Tag] = []
    skip_mode = False  # 旧世代限定 h3 の範囲内ならスキップ

    node = h2_node.next_sibling
    while node is not None:
        if isinstance(node, NavigableString):
            node = node.next_sibling
            continue

        if node.name == "h2":
            break

        if node.name == "h3":
            headline = node.find("span", class_="mw-headline")
            h3_text = headline.get_text().strip() if headline else node.get_text().strip()
            if is_old_gen_only_h3(h3_text):
                skip_mode = True
            else:
                skip_mode = False
                elements.append(node)
        elif not skip_mode:
            # 定期更新通知などの boilerplate div をスキップ
            if isinstance(node, Tag) and "boilerplate" in node.get("class", []):
                pass
            else:
                elements.append(node)

        node = node.next_sibling

    return elements


def _ref_url(soup: BeautifulSoup) -> str:
    """HTML の canonical リンクから wiki.xn--rckteqa2e.com の URL を構築する。"""
    canonical = soup.find("link", {"rel": "canonical"})
    if canonical:
        href = canonical.get("href", "")
        m = re.search(r"/wiki/(.+)$", href)
        if m:
            return f"https://wiki.xn--rckteqa2e.com/wiki/{m.group(1)}"
    return ""


def _elems_to_md_no_tables(elements: list[Tag]) -> str:
    """要素リストを Markdown に変換する。テーブルはスキップ（関連項目用）。"""
    parts: list[str] = []
    for elem in elements:
        if isinstance(elem, Tag) and elem.name == "table":
            continue
        content = elem_to_md(elem).strip()
        if content:
            parts.append(content)
    return "\n".join(parts)


def process_html(html_path: Path) -> str:
    """HTML ファイルを解析し、テンプレート準拠の Markdown を返す。"""
    ability_name = html_path.stem
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    ref_url = _ref_url(soup)

    parser_output = soup.find("div", class_="mw-parser-output")
    if not parser_output:
        return f"# 仕様書: {ability_name}\n\n(変換失敗: mw-parser-output が見つからない)\n"

    # h2 セクションをすべて収集
    sections: dict[str, list[Tag]] = {}
    for h2 in parser_output.find_all("h2"):
        headline = h2.find("span", class_="mw-headline")
        if not headline:
            continue
        section_id = headline.get("id", "")
        if section_id in OUTPUT_SECTIONS:
            sections[section_id] = _get_section_elements(h2)

    # --- Markdown 組み立て ---
    out: list[str] = [
        f"# 仕様書: {ability_name}",
        "",
        f"調査日: {TODAY}",
        f"参照URL: {ref_url}",
        "",
    ]

    for section_name in OUTPUT_SECTIONS:
        out.append(f"## {section_name}")
        elems = sections.get(section_name, [])
        if elems:
            # 関連項目はテーブル（「同じ効果のとくせい」テンプレート・定期更新通知）をスキップ
            if section_name == "関連項目":
                content = _elems_to_md_no_tables(elems)
            else:
                content = "".join(elem_to_md(e) for e in elems).strip()
            if content:
                out.append(content)
                out.append("")
                continue
        # 内容が空の場合: テンプレートコメントを挿入
        if section_name == "備考":
            out.append("<!-- 専用特性・所持ポケモン・内部処理の補足など。なければ省略可 -->")
        elif section_name == "関連項目":
            out.append("<!-- 関連する技・特性・揮発性状態など。なければ省略可 -->")
        out.append("")

    return "\n".join(out)


def main() -> None:
    SPEC_DIR.mkdir(parents=True, exist_ok=True)

    html_files = sorted(HTML_DIR.glob("*.html"))
    print(f"{len(html_files)} 件のHTMLファイルを処理します。")

    ok = 0
    ng = 0
    for html_path in html_files:
        ability_name = html_path.stem
        spec_path = SPEC_DIR / f"{ability_name}.md"
        try:
            md = process_html(html_path)
            spec_path.write_text(md, encoding="utf-8")
            print(f"  OK {ability_name}")
            ok += 1
        except Exception as e:
            print(f"  NG {ability_name}: {e}")
            ng += 1

    print(f"\n完了: 成功 {ok} 件、失敗 {ng} 件")


if __name__ == "__main__":
    main()
