# 第8ラウンド（apiループ）

[← 目次に戻る](../README.md)

- [x] `examples/03_damage_calc/02_ailment_and_scenario_comparison.py`のコメントが
  「`Pokemon.hp`への直接代入は禁止されている」と断言しているが、`src/jpoke/model/pokemon.py:104`の
  `self.hp`はただの属性でsetter・バリデーションが無く、直接代入はエラーなく成功する
  （developer視点、id: r8-1） → 対応内容 (2026-07-14):
  `examples/03_damage_calc/02_ailment_and_scenario_comparison.py`冒頭のTODOコメント
  「`Pokemon.hpへの直接代入を禁じているのは...`」を削除し、54行目付近のコメントを
  「`Pokemon.hp` への直接代入自体は技術的に禁止されておらずエラーにもならないが、対戦
  シミュレーション中に使うとON_HP_CHANGE等のハンドラ発火・ひんし判定がスキップされ内部状態が
  不整合になるため、対戦を進行させる文脈では必ずこれらを通す」という事実に即した表現に修正した。
  `src/jpoke/model/pokemon.py`の`Pokemon`クラスdocstring（Attributes節）の`hp`の説明にも
  「単なる属性であり代入自体はエラーなく成功するが、対戦シミュレーション中に直接代入すると
  ON_HP_CHANGE系ハンドラの発火・瀕死判定がスキップされ内部状態が不整合になる。対戦を進行させる
  文脈では必ず`Battle.modify_hp()`を使うこと。ダメージ計算のみを行いハンドラ起動を意図的に
  避けたい場合はこの限りではない」という注意書きを追記した。公開APIのシグネチャ変更・新設は
  無いため`docs/api/README.md`の更新は不要と判断した（該当箇所を確認済み）。コメント・docstring
  修正でありロジック変更を伴わないため新規の回帰テストは不要と判断し、代わりに
  `python examples/03_damage_calc/02_ailment_and_scenario_comparison.py`を実行して
  従来通り正常終了し、致死率比較の出力（どく無し/どくあり、HP満タン/HP減少後、ぼうぎょ+1後、
  faint()呼び出し後）が変わらないことを確認した。`python -m pytest tests/ -v`で5803件全件
  パス・1件skip（既存件数のまま、flaky testの新規発生なし）を確認した。
- [x] `Command.is_switch()`のみメソッドで、同じ真偽値判定を行う`is_regular_move`/
  `is_terastal`/`is_megaevol`/`is_gigamax`/`is_zmove`はすべて`@property`という
  不一致があった。`if cmd.is_switch:`と書くとbool化されずbound methodが常にTruthyになる
  バグの温床だった（developer視点、id: r8-2） → 対応内容 (2026-07-14):
  `src/jpoke/enums/command.py`の`is_switch()`を`@property`の`is_switch`に変更し、
  呼び出し箇所`src/jpoke/core/battle.py:1564`・`src/jpoke/core/switch_manager.py:190`を
  `cmd.is_switch()`→`cmd.is_switch`に修正した。`docs/api/README.md`のCommand章
  「インスタンスプロパティ・メソッド」表の記載も`is_switch()`→`is_switch (property)`に
  修正した。公開APIのシグネチャ変更（メソッド→プロパティ）に伴う破壊的変更のため
  `CHANGELOG.md`の`[Unreleased]`/`Changed`に追記した。`src/jpoke`・`examples/`・`tests/`
  全体を再度grepし、`is_switch()`の呼び出しが他に残っていないことを確認した
  （`CHANGELOG.md`・`docs/api_feedback/loop_rounds/round7.md`内の説明文への言及のみ残存）。
  `tests/test_command.py`に`test_is_switch_プロパティとしてコマンド種別ごとに真偽を返す()`を
  追加し、`SWITCH_*`で真、`MOVE_0`/`TERASTAL_0`/`MEGAEVOL_0`/`GIGAMAX_0`/`ZMOVE_0`/
  `STRUGGLE`/`FORCED`で偽になること、および`isinstance(..., bool)`でbound methodではなく
  bool値そのものを返すことを検証した。`python scripts/sort_tests.py tests/test_command.py`・
  `python scripts/generate_test_list.py`を実行し、`examples/02_ai/01_custom_player.py`が
  従来通り正常終了することを確認した。`python -m pytest tests/ -v`で5818件全件パス・1件skip
  （既存のflaky無し）を確認した。
