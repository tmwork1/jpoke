"""spec/move/ ディレクトリに未作成の技仕様書を wiki 情報から生成する。"""

from __future__ import annotations

import datetime
import re
import urllib.parse
import urllib.request
from pathlib import Path

WIKI_BASE = "https://wiki.xn--rckteqa2e.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def clean_wikitext(text: str) -> str:
    """Wikitext を仕様書向けの可読テキストへ簡易変換する。"""
    out = text.strip()
    out = re.sub(r"<!--.*?-->", "", out, flags=re.S)
    out = re.sub(r"\{\{[^{}]*\}\}", "", out)
    out = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", out)
    out = re.sub(r"\[\[([^\]]+)\]\]", r"\1", out)
    out = out.replace("'''", "")
    out = out.replace("''", "")
    out = re.sub(r"<[^>]+>", "", out)
    out = re.sub(r"\s+", " ", out)
    return out.strip()


def fetch_wikitext(move_name: str) -> str | None:
    """MediaWiki API からページの wikitext を取得する。"""
    query = urllib.parse.urlencode(
        {
            "action": "parse",
            "page": move_name,
            "prop": "wikitext",
            "format": "json",
        }
    )
    url = f"{WIKI_BASE}/w/api.php?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None

    # json を厳密パースすると依存が増えるため、必要部だけ正規表現で拾う。
    m = re.search(r'"\\*":"(.*)"\}\}\s*\}\s*$', body)
    if m:
        raw = m.group(1)
        # JSON 文字列のエスケープ解除
        raw = raw.encode("utf-8").decode("unicode_escape")
        return raw

    # 予備: parse エラー時
    if '"error"' in body:
        return None

    # 正規表現に当たらない場合は雑に抽出
    m2 = re.search(r'"wikitext":\{"\\*":"(.*?)"\}\}', body)
    if not m2:
        return None
    raw = m2.group(1).encode("utf-8").decode("unicode_escape")
    return raw


def extract_basic_info_block(wikitext: str) -> str | None:
    """{{わざ基本情報 ... }} ブロックを取り出す。"""
    start = wikitext.find("{{わざ基本情報")
    if start < 0:
        return None

    depth = 0
    i = start
    while i < len(wikitext) - 1:
        pair = wikitext[i: i + 2]
        if pair == "{{":
            depth += 1
            i += 2
            continue
        if pair == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return wikitext[start:i]
            continue
        i += 1

    return None


def parse_template_fields(block: str) -> dict[str, str]:
    """わざ基本情報テンプレートの | キー = 値 を辞書化する。"""
    fields: dict[str, str] = {}
    current_key: str | None = None

    for raw_line in block.splitlines()[1:]:
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("|") and "=" in line:
            key, value = line[1:].split("=", 1)
            current_key = key.strip()
            fields[current_key] = value.strip()
            continue
        if current_key is not None:
            fields[current_key] += " " + line.strip()

    for k, v in list(fields.items()):
        fields[k] = clean_wikitext(v)
    return fields


def build_spec_markdown(move_name: str, fields: dict[str, str]) -> str:
    """仕様書 Markdown を組み立てる。"""
    encoded = urllib.parse.quote(move_name, safe="")
    page_url = f"{WIKI_BASE}/wiki/{encoded}"
    today = datetime.date.today().isoformat()

    def f(key: str, default: str = "-") -> str:
        value = fields.get(key, "").strip()
        return value or default

    lines = [
        f"# 仕様書: {move_name}",
        "",
        f"調査日: {today}",
        f"参照URL: {page_url}",
        "",
        "## 基本データ（ポケモンWiki）",
        "",
        f"- 世代: {f('世代')}",
        f"- タイプ: {f('タイプ')}",
        f"- 分類: {f('分類')}",
        f"- 威力: {f('威力')}",
        f"- 命中率: {f('命中')}",
        f"- PP: {f('PP')}",
        f"- 範囲: {f('範囲')}",
        f"- 優先度: {f('優先')}",
        f"- 直接攻撃: {f('直接')}",
        "",
        "## 効果",
        "",
        f"- {f('効果')}",
        "",
        "## 判定",
        "",
        f"- 急所: {f('急所')}",
        f"- 命中判定: {f('命中判定')}",
        f"- 追加効果: {f('追加効果')}",
        f"- まもる: {f('守')}",
        f"- おうじゃのしるし（第5世代以降）: {f('王5')}",
        f"- マジックコート: {f('マ')}",
        "",
        "## 実装メモ",
        "",
        "- 上記の基本データ・効果・判定を `src/jpoke/data/move.py` / `src/jpoke/handlers/move.py` / `tests/test_move.py` に反映する。",
        "- 世代差分や例外処理が必要な場合は、実装前にこの仕様書へ追記する。",
        "",
    ]
    return "\n".join(lines)


def load_targets(plan_dir: Path, spec_dir: Path) -> list[str]:
    """plan で未作成指定されている技名を抽出する。"""
    targets: list[str] = []
    for plan_file in sorted(plan_dir.glob("*.md")):
        text = plan_file.read_text(encoding="utf-8")
        if "仕様書: 未作成" not in text:
            continue
        move_name = plan_file.stem
        spec_file = spec_dir / f"{move_name}.md"
        if not spec_file.exists():
            targets.append(move_name)
    return targets


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    plan_dir = root / "plan" / "move"
    spec_dir = root / "spec" / "move"
    spec_dir.mkdir(parents=True, exist_ok=True)

    targets = load_targets(plan_dir, spec_dir)
    created = 0
    failed: list[str] = []

    for name in targets:
        wiki = fetch_wikitext(name)
        if not wiki:
            failed.append(name)
            continue

        block = extract_basic_info_block(wiki)
        if not block:
            failed.append(name)
            continue

        fields = parse_template_fields(block)
        content = build_spec_markdown(name, fields)
        (spec_dir / f"{name}.md").write_text(content, encoding="utf-8")
        created += 1

    print(f"対象: {len(targets)} / 作成: {created} / 失敗: {len(failed)}")
    if failed:
        print("失敗技:")
        for name in failed:
            print(name)


if __name__ == "__main__":
    main()
