"""jpoke対応の全ポケモン和名・全アイテム和名・全タイプについて、PokeAPI関連のURL生成
関数（get_pokeapi_url / get_pokemon_image_url / get_item_image_url / get_type_image_url /
get_tera_type_image_url）が例外なく解決できるか、かつ解決できたURLが実際にHTTPで
到達可能（200系が返る）かを検証するスクリプト。

PokeAPI/GitHubへの大量アクセスが発生するため、pytestのテストスイートには含めず、
`python scripts/pokeapi/validate_urls.py` で手動・不定期に実行する用途専用。CIやテスト
実行時に自動では呼ばれない。

使い方:
    python scripts/pokeapi/validate_urls.py
    python scripts/pokeapi/validate_urls.py --output path/to/report.md

想定される出力:
    - 名前解決に失敗した件数（`src/jpoke/data/pokeapi/ja_to_id_map.json` の unresolved
      にすでに記録されている既知の欠落を含む。カテゴリ別内訳つき）
    - 名前解決はできたがHTTPアクセスに失敗したURLの一覧（新規に調査すべき問題として、
      名前解決失敗とは明確に区別して報告する）
    - 両方ともOKだった件数

上記は標準出力に表示すると同時に、実行のたびにMarkdownレポートとしてファイルにも
書き出す。`--output` を省略した場合、既定の出力先は
`.internal/pokeapi/validate_urls_<実行日>.md`（同日に複数回実行すると上書きされる）。

レート制限への配慮として、HTTPチェックは少数の並列ワーカー（既定5）+リクエスト間の
小休止、タイムアウト・リトライ設定を入れている。対象件数が多いため、実行には数分〜
十数分程度かかることがある。
"""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import get_args
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

DEFAULT_OUTPUT_DIR = ROOT / ".internal" / "pokeapi"

from jpoke.exceptions import PokeApiResolveError  # noqa: E402
from jpoke.types import ItemName, PokemonName, Type  # noqa: E402
from jpoke.utils.pokeapi import (  # noqa: E402
    get_item_image_url,
    get_pokeapi_url,
    get_pokemon_image_url,
    get_tera_type_image_url,
    get_type_image_url,
)

USER_AGENT = "jpoke-pokeapi-url-validator"
MAX_WORKERS = 5
REQUEST_TIMEOUT = 15
RETRY_COUNT = 2
RETRY_SLEEP = 1.0
REQUEST_SLEEP = 0.05  # 各リクエスト後の小休止（レート制限対策）


@dataclass
class CheckTarget:
    """名前解決に成功し、HTTPチェック対象となったURL。"""

    category: str
    name_ja: str
    check_name: str
    url: str


@dataclass
class UnresolvedEntry:
    """名前解決自体に失敗したケース。"""

    category: str
    name_ja: str
    check_name: str
    error: str


def _collect_category(
    category: str,
    names: tuple[str, ...],
    checks: list[tuple[str, Callable[[str], str]]],
    targets: list[CheckTarget],
    unresolved: list[UnresolvedEntry],
) -> None:
    for name in names:
        if name == "":
            continue  # タイプなし/アイテムなしはURLが存在しないため対象外
        for check_name, func in checks:
            try:
                url = func(name)
            except PokeApiResolveError as e:
                unresolved.append(UnresolvedEntry(category, name, check_name, str(e)))
            else:
                targets.append(CheckTarget(category, name, check_name, url))


def collect_targets() -> tuple[list[CheckTarget], list[UnresolvedEntry]]:
    """全ポケモン和名・全アイテム和名・全タイプについて、各URL生成関数の解決結果を集める。"""
    targets: list[CheckTarget] = []
    unresolved: list[UnresolvedEntry] = []

    pokemon_checks: list[tuple[str, Callable[[str], str]]] = [
        ("get_pokeapi_url", lambda n: get_pokeapi_url(n, "pokemon")),
        ("get_pokemon_image_url", get_pokemon_image_url),
    ]
    item_checks: list[tuple[str, Callable[[str], str]]] = [
        ("get_pokeapi_url", lambda n: get_pokeapi_url(n, "item")),
        ("get_item_image_url", get_item_image_url),
    ]
    type_checks: list[tuple[str, Callable[[str], str]]] = [
        ("get_type_image_url", get_type_image_url),
        ("get_tera_type_image_url", get_tera_type_image_url),
    ]

    _collect_category("pokemon", get_args(PokemonName), pokemon_checks, targets, unresolved)
    _collect_category("item", get_args(ItemName), item_checks, targets, unresolved)
    _collect_category("type", get_args(Type), type_checks, targets, unresolved)

    return targets, unresolved


def check_url(url: str) -> tuple[bool, str]:
    """URLにHTTP HEAD（非対応ならRange指定のGET）を送り、到達可能かを確認する。"""
    last_error = ""
    for attempt in range(RETRY_COUNT + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT}, method="HEAD")
            with urlopen(request, timeout=REQUEST_TIMEOUT) as response:  # noqa: S310
                return response.status == 200, str(response.status)
        except HTTPError as e:
            if e.code in (403, 405, 501):
                # HEAD非対応のサーバー向けに、本文をほぼ読まないGETへフォールバックする。
                try:
                    get_request = Request(
                        url,
                        headers={"User-Agent": USER_AGENT, "Range": "bytes=0-0"},
                    )
                    with urlopen(get_request, timeout=REQUEST_TIMEOUT) as response:  # noqa: S310
                        return response.status in (200, 206), str(response.status)
                except (HTTPError, URLError) as inner_e:
                    last_error = str(inner_e)
            else:
                return False, f"HTTP {e.code}"
        except URLError as e:
            last_error = str(e.reason)
        except TimeoutError as e:
            last_error = str(e)

        if attempt < RETRY_COUNT:
            time.sleep(RETRY_SLEEP * (attempt + 1))

    return False, last_error or "unknown error"


def build_report(
    targets: list[CheckTarget],
    unresolved: list[UnresolvedEntry],
    url_results: dict[str, tuple[bool, str]],
) -> str:
    """検証結果サマリをMarkdown文字列として組み立てる（ファイル保存・標準出力の両方で使う）。"""
    http_failures = [t for t in targets if not url_results[t.url][0]]
    ok_count = len(targets) - len(http_failures)

    unresolved_names_by_category: dict[str, set[str]] = {}
    for u in unresolved:
        unresolved_names_by_category.setdefault(u.category, set()).add(u.name_ja)

    lines: list[str] = []
    lines.append(f"# PokeAPI URL 検証レポート ({date.today().isoformat()})")
    lines.append("")
    lines.append("## サマリ")
    lines.append("")
    lines.append("名前解決NG（対象名ベース。カテゴリ別内訳）:")
    for category in ("pokemon", "item", "type"):
        names = unresolved_names_by_category.get(category, set())
        lines.append(f"- {category}: {len(names)} 件")
    lines.append("")
    lines.append(f"名前解決OKだがHTTPアクセス失敗: {len(http_failures)} 件")
    for t in http_failures:
        status = url_results[t.url][1]
        lines.append(f"- [{t.category}] {t.name_ja} ({t.check_name}): {t.url} -> {status}")
    lines.append("")
    lines.append(f"名前解決・HTTPアクセスともにOK: {ok_count} 件")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "レポートの出力先パス。省略時は "
            f"{DEFAULT_OUTPUT_DIR / 'validate_urls_<実行日>.md'} に書き出す"
        ),
    )
    args = parser.parse_args()
    output_path: Path = args.output or (DEFAULT_OUTPUT_DIR / f"validate_urls_{date.today().isoformat()}.md")

    print("対象名を収集中...")
    targets, unresolved = collect_targets()

    # 同一URLへの重複アクセスを避ける。
    unique_urls = sorted({t.url for t in targets})
    print(f"名前解決NG: {len(unresolved)} 件（延べ。既知の未解決を含む）")
    print(f"名前解決OK・チェック対象URL（重複除去後）: {len(unique_urls)} 件")
    print("HTTPアクセスを開始します（レート制限対策のため時間がかかります）...")

    url_results: dict[str, tuple[bool, str]] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(check_url, url): url for url in unique_urls}
        done = 0
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            url_results[url] = future.result()
            done += 1
            if done % 200 == 0:
                print(f"  ... {done}/{len(unique_urls)} 件チェック済み")
            time.sleep(REQUEST_SLEEP)

    report = build_report(targets, unresolved, url_results)

    print()
    print("===== 検証結果サマリ =====")
    print(report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"レポートを書き出しました: {output_path}")


if __name__ == "__main__":
    main()
