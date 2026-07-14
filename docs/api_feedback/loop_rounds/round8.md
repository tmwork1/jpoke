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
- [x] `Pokemon.set_ivs()`/`set_evs()`が`list[int]`の位置引数のみで、r7-1で`set_stats()`が
  対応した`dict[Stat, int]`と不整合だった。さらに`Player.add_pokemon()`からはIV/EVを
  一切設定できず、生成後に別途`set_evs()`/`set_ivs()`を呼ぶ必要があった（developer視点、
  id: r8-3） → 対応内容 (2026-07-14): `src/jpoke/model/pokemon.py`の`set_ivs()`/`set_evs()`を
  `list[int] | dict[Stat, int]`両対応にし、`dict`指定時は`for stat, value in x.items():
  self._ivs[STATS.index(stat)] = value`として指定したステータスのみ更新し未指定分は
  既存値を維持、`list`指定時は従来通り全体を置き換える実装にした。`src/jpoke/core/player.py`の
  `Player.add_pokemon()`に`evs: dict[Stat, int] | None = None`/`ivs: dict[Stat, int] |
  None = None`引数を追加し、`None`（デフォルト）でなければ生成した`Pokemon`に対し内部で
  `set_evs()`/`set_ivs()`を呼ぶよう委譲した。`docs/api/README.md`の`add_pokemon()`・
  `set_evs()`/`set_ivs()`の章を新シグネチャ・dict指定の挙動に合わせて更新し、`CHANGELOG.md`の
  `[Unreleased]`（`Added`に`add_pokemon()`のevs/ivs引数追加、`Changed`に`set_ivs()`/
  `set_evs()`のdict対応）に追記した。`examples/03_damage_calc/01_basic_lethal_calculation.py`の
  「`add_pokemon()`でivsやevsなどを一通り設定できるようにする」というTODOコメントを解消し、
  生成後に`attacker.set_evs([0, 32, 0, 0, 0, 0])`と呼んでいた箇所を
  `attacker_player.add_pokemon("ガブリアス", move_names=[move_name], evs={"atk": 32})`に
  置き換えた。`tests/test_stats.py`に回帰テストを8件追加し、
  (1) `set_ivs`/`set_evs`の`list`指定で全体置換される、(2) `dict`指定で指定ステータスのみ
  更新され未指定分（既定値IV31・EV0）が維持される、(3) `dict`指定後にステータスが
  自動再計算される、(4) `_ivs`/`_evs`が可変listで保持されているため、あるインスタンスへの
  `dict`部分更新が別インスタンス（同じ既定値から生成）の`_ivs`/`_evs`を共有・破壊していないか
  （`is not`でオブジェクト同一性も確認）、(5) `Player.add_pokemon(evs=..., ivs=...)`が
  指定ステータスのみ反映しつつ`evs`/`ivs`省略時は`None`のまま`set_evs`/`set_ivs`が呼ばれず
  既定値を維持する、(6) `add_pokemon(evs={"hp": 32})`のようにHP実数値が変わる指定をしても
  `hp_policy`既定値`keep_absolute`（生成直後は被ダメージ0を維持）によりポケモン生成直後は
  常に満タンのHPで返る、という観点を検証した。`python scripts/sort_tests.py
  tests/test_stats.py`・`python scripts/generate_test_list.py`を実行し、
  `PYTHONIOENCODING=utf-8 python examples/03_damage_calc/01_basic_lethal_calculation.py`が
  従来通り正常終了し致死率の出力が変わらないことを確認した。`python -m pytest tests/ -v`で
  5828件全件パス・1件skip（既存のflaky無し）を確認した。
