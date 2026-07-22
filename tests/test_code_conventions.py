"""コーディング規約（CLAUDE.md）の機械的な検証テスト。

`Pokemon.hp` への直接代入は禁止で、必ず `battle.modify_hp(...)` 等を経由する規約になっている。
実行時に property 化するとテストのセットアップ代入（`mon.hp = ...`）を壊すため、
代わりに src/jpoke 配下のソースを静的に走査して違反を検出する。
"""
import json
import re
from pathlib import Path

import pytest

from jpoke import Pokemon

from . import test_utils as t

SRC_ROOT = Path(__file__).resolve().parent.parent / "src" / "jpoke"
EXAMPLES_ROOT = Path(__file__).resolve().parent.parent / "examples"
README_PATH = Path(__file__).resolve().parent.parent / "README.md"


def _iter_example_files():
    """examples/ 配下の .py と .ipynb（Jupyter Notebook化済みサンプル）を列挙する。"""
    yield from EXAMPLES_ROOT.rglob("*.py")
    yield from EXAMPLES_ROOT.rglob("*.ipynb")


def _example_text(path: Path) -> str:
    """規約の文字列検索用に、ファイルの中身をプレーンテキストとして返す。

    `.py` はそのまま、`.ipynb` は全コードセルの source を連結して返す
    （markdownセルの説明文は規約検査の対象外のため含めない）。
    """
    if path.suffix == ".ipynb":
        notebook = json.loads(path.read_text(encoding="utf-8"))
        return "\n".join(
            "".join(cell["source"])
            for cell in notebook["cells"]
            if cell["cell_type"] == "code"
        )
    return path.read_text(encoding="utf-8")


# 直接代入が許可されているファイル（相対パス、"/" 区切り）
# - model/pokemon.py: hp の実体を保持するクラス自身の実装
#   （__init__ の初期化、update_stats/set_form でのフォルム変化時のダメージ量維持、
#     modify_hp 内部実装）
# - core/status_manager.py: battle.modify_hp() の実装箇所
# - core/lethal.py: 致死率計算用のスクラッチ状態操作。イベント発火・ログ記録・
#   ひんし判定を意図的に伴わない「仮定計算」のための一時的な hp 書き換え
#   （計算後に元の値へ復元する、または hp_dist から参照用の値を反映するだけ）であり、
#   実バトル進行のHP変化ではないため battle.modify_hp() を経由しない
ALLOWED_FILES = {
    "model/pokemon.py",
    "core/status_manager.py",
    "core/lethal.py",
}

# `.hp = ` 形式の直接代入を検出する（`==` `!=` `<=` `>=` は除外する）
DIRECT_ASSIGNMENT_PATTERN = re.compile(r"(?<![=!<>])\.hp\s*=(?!=)")

def _iter_python_files():
    for path in SRC_ROOT.rglob("*.py"):
        yield path


def test_Pokemon_modify_hpが公開APIとして露出していない():
    """`Pokemon.modify_hp()` はHPクランプのみを行いON_HP_CHANGE系ハンドラの発火・瀕死判定・
    ログ記録をスキップする内部専用の低レベル実装であり、外部からは `Battle.modify_hp()` を
    使うべきという規約になっている。かつてはこの規約がdocstringのみで示され、メソッド名に
    アンダースコアが付いていなかったため誤って直接呼び出しやすい罠になっていた。
    `_modify_hp_raw` へのリネーム後、外部公開されたクラス属性としては存在しないことを確認する。
    """
    assert not hasattr(Pokemon, "modify_hp")
    assert hasattr(Pokemon, "_modify_hp_raw")


def test_READMEがjudge_winnerのis_None比較を使っていない():
    """`battle.judge_winner()` は決着判定のたびにTOD判定込みで再計算する重い遅延判定APIで、
    決着したかどうかのチェックには軽量な `battle.finished`（キャッシュされた `battle.winner`
    を経由）を使うべきという規約になっている。`judge_winner() is None` / `is not None` の
    直接比較は `battle.finished` への置き換え漏れの兆候である。examples/ 配下は
    `test_examplesがjudge_winnerのis_None比較を使っていない`（id: r6-4）で既に検査対象だが、
    ルート `README.md` の「クイックスタート」節は対象外で、`while battle.judge_winner() is
    None and battle.turn < 100:` / `winner = battle.judge_winner()` という旧パターンが
    `examples/01_basics/02_quickstart.py` や `docs/api/README.md` の表記と食い違ったまま
    長期間残っていた（id: r7-4）。再発防止のため README.md に `judge_winner()` の
    `is None` / `is not None` 直接比較が無いことを確認する（`judge_winner()` 自体は
    勝者取得APIとして今後も使われてよく、禁止対象は None との直接比較のみ）。
    """
    pattern = re.compile(r"judge_winner\(\)\s*is\s*(not\s+)?None")
    text = README_PATH.read_text(encoding="utf-8")
    violations = [
        f"README.md:{lineno}: {line.strip()}"
        for lineno, line in enumerate(text.splitlines(), start=1)
        if pattern.search(line)
    ]

    assert not violations, (
        "README.md で judge_winner() の is None / is not None 直接比較を検出"
        "（battle.finished / battle.winner に置き換えること）:\n" + "\n".join(violations)
    )


def test_consume_itemの引数名がtargetにリネームされている():
    """`Battle.consume_item()` / `ItemManager.consume_item()` の第1引数は、
    `gain_item` / `remove_item` / `take_item` 等の他のアイテム系メソッドとの引数名統一のため、
    従来の `mon` から `target` にリネームされた（破壊的変更）。`target=` キーワード引数での
    呼び出しが機能し、旧引数名 `mon=` を渡すと TypeError になることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]

    assert battle.consume_item(target=mon) is True
    assert not mon.has_item()

    with pytest.raises(TypeError):
        battle.consume_item(mon=battle.actives[0])  # type: ignore[call-arg]


def test_docs_examplesがjpoke_testingモジュールに言及している():
    """`src/jpoke/testing.py` は `pip install jpoke` だけで（`jpoke` リポジトリを clone
    せずに）シナリオ検証ができるよう本体パッケージへ昇格した公開モジュールだが、昇格当初は
    `docs/api/README.md` と `examples/` の両方から言及が欠落しており、外部利用者が存在に
    気づけない状態になっていた（id: r6-1）。再発防止のため、APIドキュメントに `jpoke.testing`
    への言及があること、`examples/` 配下に `jpoke.testing` を import するサンプルが
    存在することを確認する。
    """
    docs_root = Path(__file__).resolve().parent.parent / "docs" / "quick_reference.md"
    readme_text = docs_root.read_text(encoding="utf-8")
    assert "jpoke.testing" in readme_text

    examples_importing_testing = [
        path for path in _iter_example_files()
        if "jpoke.testing" in _example_text(path)
    ]
    assert examples_importing_testing, (
        "examples/ 配下に jpoke.testing を import するサンプルが見つからない"
    )


def test_examplesがactives経由でインデックスアクセスしていない():
    """`battle.actives` は「現在場に出ているポケモンのリスト」であり、瀕死・交代中で場が
    空いているプレイヤーがいると要素数が2未満になり得るため、`battle.actives[0]`/`[1]` という
    書き方はプレイヤーとインデックスの対応が崩れる危険な未文書化アクセスになる。プレイヤーを
    明示して対応するポケモンを取得したい場合は `battle.get_active(player)` を使うべきという
    規約になっている。かつて `examples/03_damage_calc/10_testing_helpers.py` が
    `battle.actives[0]`/`battle.actives[1]` を直接使っていた（id: r10-4）。再発防止のため
    examples/ 配下に `.actives[` の使用が無いことを確認する。
    """
    violations = []
    for path in _iter_example_files():
        text = _example_text(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if ".actives[" in line:
                rel_path = path.relative_to(EXAMPLES_ROOT).as_posix()
                violations.append(f"{rel_path}:{lineno}: {line.strip()}")

    assert not violations, (
        "examples/ 配下で battle.actives[...] への直接アクセスを検出"
        "（player0, player1 = battle.players; battle.get_active(player) 等の"
        "公開APIに置き換えること）:\n" + "\n".join(violations)
    )


def test_examplesがjudge_winnerのis_None比較を使っていない():
    """`battle.judge_winner()` は決着判定のたびにTOD判定込みで再計算する重い遅延判定APIで、
    決着したかどうかのチェックには軽量な `battle.finished`（キャッシュされた `battle.winner`
    を経由）を使うべきという規約になっている。`judge_winner() is None` / `is not None` の
    直接比較は `battle.finished` への置き換え漏れの兆候である。かつて
    `examples/05_benchmark/01_step_time_benchmark.py` と
    `examples/04_research/03_janken_nash_fictitious_play.py`・`04_janken_nash_cfr.py` の
    計3ファイルで `judge_winner() is None` によるループ継続判定が残っていた（id: r6-4）。
    再発防止のため examples/ 配下に `judge_winner()` の `is None` / `is not None` 直接比較が
    無いことを確認する（`judge_winner()` 自体は勝者取得APIとして今後も使われてよく、
    禁止対象は None との直接比較のみ）。
    """
    pattern = re.compile(r"judge_winner\(\)\s*is\s*(not\s+)?None")
    violations = []
    for path in _iter_example_files():
        text = _example_text(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                rel_path = path.relative_to(EXAMPLES_ROOT).as_posix()
                violations.append(f"{rel_path}:{lineno}: {line.strip()}")

    assert not violations, (
        "examples/ 配下で judge_winner() の is None / is not None 直接比較を検出"
        "（battle.finished / battle.winner に置き換えること）:\n" + "\n".join(violations)
    )


def test_examplesがplayer_states経由で内部属性に直接アクセスしていない():
    """`battle.player_states[player].active` は `Battle` 内部の実装詳細であり、公開APIとしては
    `battle.get_active(player)` を使うべきという規約になっている。かつて
    `examples/02_ai/05_opponent_estimation.py` の `opponent_estimator()` 実装が
    `battle.player_states[opponent].active` という未文書化の内部属性に直接アクセスする書き方に
    逆戻りしており、`get_active()` への置き換え漏れが発生していた（id: r10-3）。再発防止のため
    examples/ 配下に `player_states[` の使用が無いことを確認する。
    """
    violations = []
    for path in _iter_example_files():
        text = _example_text(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "player_states[" in line:
                rel_path = path.relative_to(EXAMPLES_ROOT).as_posix()
                violations.append(f"{rel_path}:{lineno}: {line.strip()}")

    assert not violations, (
        "examples/ 配下で battle.player_states[...] への直接アクセスを検出"
        "（battle.get_active(player) 等の公開APIに置き換えること）:\n" + "\n".join(violations)
    )


def test_examplesがteam_append_Pokemon経由でチームを構築していない():
    """`Player.add_pokemon()` が jpoke の正規のチーム追加ルートであり、
    `team.append(Pokemon(...))`（`Pokemon` を直接構築して `team` に追加する書き方）は
    使うべきではないという規約になっている。かつて
    `examples/04_research/03_janken_nash_fictitious_play.py` と `04_janken_nash_cfr.py` の
    `build_pokemon()` が `Pokemon(...)` を直接構築し `team.append()` で追加しており、他の
    examples の `add_pokemon()` と統一方針から逸脱していた（id: r5-5）。再発防止のため
    examples/ 配下に `.team.append(Pokemon(` の使用が無いことを確認する。
    """
    violations = []
    for path in _iter_example_files():
        text = _example_text(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if ".team.append(Pokemon(" in line:
                rel_path = path.relative_to(EXAMPLES_ROOT).as_posix()
                violations.append(f"{rel_path}:{lineno}: {line.strip()}")

    assert not violations, (
        "examples/ 配下で team.append(Pokemon(...)) の使用を検出"
        "（Player.add_pokemon() に置き換えること）:\n" + "\n".join(violations)
    )


def test_examplesがtest_option経由で命中率等を固定していない():
    """`battle.test_option` はテストコード専用の内部低レベルAPIで、ユーザー向けサンプルである
    `examples/` から使うべきではないという規約になっている。命中率を固定したい場合は公開APIの
    `Battle(..., accuracy_fix_threshold=0)` を使う。かつて
    `examples/04_research/03_janken_nash_fictitious_play.py` と
    `04_janken_nash_cfr.py` が `battle.test_option.accuracy = 100` を使っており、他の
    examples の `accuracy_fix_threshold=0` と命中率固定の手段が2系統に分裂していた
    （id: r5-4）。再発防止のため examples/ 配下に `test_option` の使用が無いことを確認する。
    """
    violations = []
    for path in _iter_example_files():
        text = _example_text(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "test_option" in line:
                rel_path = path.relative_to(EXAMPLES_ROOT).as_posix()
                violations.append(f"{rel_path}:{lineno}: {line.strip()}")

    assert not violations, (
        "examples/ 配下で battle.test_option の使用を検出"
        "（accuracy_fix_threshold 等の公開APIに置き換えること）:\n" + "\n".join(violations)
    )


def test_hp直接代入がallowlist外のファイルに存在しない():
    """src/jpoke 配下で `.hp = ...` の直接代入が許可ファイル以外に無いことを確認する。

    許可ファイル以外で見つかった場合は `battle.modify_hp(...)` 経由に直す必要がある。
    """
    violations = []
    for path in _iter_python_files():
        rel_path = path.relative_to(SRC_ROOT).as_posix()
        if rel_path in ALLOWED_FILES:
            continue

        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if DIRECT_ASSIGNMENT_PATTERN.search(line):
                violations.append(f"{rel_path}:{lineno}: {line.strip()}")

    assert not violations, (
        "hp への直接代入を検出（battle.modify_hp(...) 経由に修正すること）:\n"
        + "\n".join(violations)
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
