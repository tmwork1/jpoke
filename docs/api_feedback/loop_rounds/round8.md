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
- [x] 対戦実行結果の収集パターン（`on_battle_end`）が未整理・未周知で、
  `examples/01_basics/01_battle_against_intro.py`「Battleリストを返すべき」・
  `examples/04_research/02_replay.py`「戻り値統一を検討する」・
  `examples/05_benchmark/01_step_time_benchmark.py`「進捗表示」の3件のTODOが
  未解消のまま残っていた（developer視点、id: r8-4） → 対応内容 (2026-07-14):
  `examples/01_basics/01_battle_against_intro.py`のTODOを、`battle_against()`は
  各対戦の`Battle`を使い捨てるため戻り値は`None`であり、対戦後の`Battle`（ログ等）に
  アクセスしたい場合は`on_battle_end`コールバックを渡す旨の案内コメント（`docs/api/README.md`・
  05_benchmarkの進捗表示例への参照込み）に置き換えた。`examples/04_research/02_replay.py`の
  TODOを、`play_out()`は呼び出し側が既に`battle`を保持しているため勝者のみを返す設計である旨と、
  `docs/api/README.md`の新設「対戦実行系メソッドの戻り値一覧」節への参照コメントに置き換えた。
  `examples/05_benchmark/01_step_time_benchmark.py`のTODOを解消するため、`run_benchmark()`に
  `on_battle_end: Callable[[Battle], None] | None`引数を追加し（examples側のローカル関数であり
  `Player.battle_against()`自体のシグネチャ変更は伴わない）、既存の`try/except Exception:
  continue`を`try/except/else`に整理した上で、例外の有無に関わらずバトルごとに
  `on_battle_end`を呼ぶ実装にした。`main()`に`--progress-every`引数と`nonlocal`カウンタを使う
  `report_progress()`クロージャを追加し、指定件数ごとに進捗をprintするデモを実装した。
  `docs/api/README.md`の`battle_against()`節の直後に「対戦実行系メソッドの戻り値一覧」表
  （`Battle.play_out()`は勝者のみ返す/`Player.battle_against()`は`None`で`on_battle_end`が
  アクセス手段、という設計方針の対比）を追加した。レビューで、`run_benchmark()`の
  `on_battle_end`引数docstringが「例外で打ち切られたバトルでも呼ばれる点も
  `Player.battle_against()`と揃えている」と誤って断言していた点を修正した
  （`Player.battle_against()`は`play_out()`の例外を捕捉せずそのまま伝播するため、
  例外発生時は`on_battle_end`が呼ばれない。`src/jpoke/core/player.py`の
  `battle_against()`実装で`on_battle_end(battle)`呼び出しが`play_out()`の直後にあり、
  間に例外捕捉がないことを確認した上で、両者が揃っているのは「未決着（`winner is None`）でも
  呼ばれる」点のみであり、例外時の挙動はexamples側`run_benchmark()`独自の仕様である旨に
  docstringを修正した）。公開APIの新設・シグネチャ変更を伴わない変更のため
  `src/jpoke`配下への新規回帰テストは追加せず、代わりに3つのexamplesを個別実行し
  （`01_battle_against_intro.py`・`02_replay.py`は従来通りの出力、
  `01_step_time_benchmark.py --n-battles 20 --max-turns 20 --progress-every 5`で
  「進捗: N/20バトル完了」が5件ごとに表示されること、`--progress-every 0`で進捗が
  非表示になることを確認）、`tests/test_examples_smoke.py`（全examplesをサブプロセス実行し
  returncode==0を確認する既存テスト、24件）を実行して全件パスを確認した。
  `python -m pytest tests/ -v`で5829件全件パス・1件skip（既存のflaky無し）を確認した。
- [x] `jpoke.testing`のインデックス引数名が`build_context`/`run_move`/`calc_lethal`は
  `atk_idx`、`apply_ailment`は`active_index`、`calc_move_priority`は`player_index`、
  `run_switch`/`can_switch`は`player_idx`と4通りに分裂しており、覚えた引数名を
  別の関数にそのまま使い回すと`TypeError`になる罠だった（developer視点、id: r8-5） →
  対応内容 (2026-07-14): `src/jpoke/testing.py`の`build_context`/`run_move`/`calc_lethal`の
  `atk_idx`、`apply_ailment`の`active_index`、`calc_move_priority`の`player_index`を
  すべて`player_idx`にリネームし、6関数（`build_context`/`run_move`/`calc_lethal`/
  `run_switch`/`can_switch`/`apply_ailment`/`calc_move_priority`）全てで統一した
  （`run_switch`/`can_switch`は元から`player_idx`）。呼び出し側のキーワード引数
  （`tests/abilities/test_ability_sa.py`・`tests/items/test_item_ma.py`・
  `tests/moves_attack/test_move_{fa,ha,ma,sa,ta,yarawa}.py`・
  `tests/moves_status/test_move_ha.py`・`tests/test_damage.py`・`tests/test_lethal.py`
  （138件）・`tests/test_poke_env_compat.py`・
  `examples/03_damage_calc/09_testing_helpers.py`）を新引数名に一括置換し、
  `docs/api/README.md`・`README.md`・`tests/CLAUDE.md`のサンプルコード・API表も
  合わせて更新した。公開APIのシグネチャ変更（引数名変更）に伴う破壊的変更のため
  `CHANGELOG.md`の`[Unreleased]`/`Changed`に追記した。レビューでリポジトリ全体を
  再度grepし、`atk_idx=`・`active_index=`（`PlayerState.active_index`属性等の
  無関係な用途を除く）・`player_index=`（`RecordedCommand.player_index`フィールド等の
  無関係な用途を除く）でのキーワード呼び出し漏れが無いことを確認した。
  `tests/test_testing_api.py`を新規作成し、7関数（`build_context`/`run_move`/
  `run_switch`/`can_switch`/`apply_ailment`/`calc_lethal`/`calc_move_priority`）
  それぞれを`player_idx=`キーワードで呼び出して正常動作することを検証する回帰テストを
  追加した。`python scripts/sort_tests.py tests/test_testing_api.py`・
  `python scripts/generate_test_list.py`を実行し、
  `python examples/03_damage_calc/09_testing_helpers.py`が従来通り正常終了することを
  確認した。`python -m pytest tests/ -v`で5836件全件パス・1件skip（既存のflaky無し）を
  確認した。
- [x] わるあがき専用コマンドを明示的に判定・取得する公開APIが無く、
  `examples/02_ai/01_custom_player.py`の`choose_command_poke_env_style()`が
  `battle.get_available_commands(self)[0]`でわるあがきを代用していたが、これには
  罠があった。技コマンドが1つも無くても交代可能な控えがいる場合は
  `get_available_action_commands()`が交代コマンドを先にリストへ加えてからわるあがきを
  末尾に追加するため、`commands[0]`はわるあがきではなく交代コマンドになってしまう
  （developer視点、id: r8-6） → 対応内容 (2026-07-14):
  `src/jpoke/core/battle.py`の`get_available_commands()`直後に
  `Battle.is_struggle_only(player) -> bool`を新設し、`Command.STRUGGLE in
  self.get_available_commands(player)`の薄いラッパーとして実装した（実際に選ぶ際は
  `Command.STRUGGLE`をそのまま使えばよく、`SWITCH_i`/`MOVE_i`と異なりインデックス
  解決が不要な固定コマンドのため取得専用メソッドは追加していない旨をdocstringに
  明記）。`docs/api/README.md`のBattle「状態取得系」表に追記し、`get_available_commands()`
  の使用例の直後に`is_struggle_only()`の使用例を追加した。`CHANGELOG.md`の
  `[Unreleased]`/`Added`に、罠の内容と併せて追記した。`examples/02_ai/01_custom_player.py`の
  `choose_command_poke_env_style()`を`assert battle.is_struggle_only(self); return
  Command.STRUGGLE`に修正し、コメントで罠の内容と回避方法を説明した。レビューで
  `src/jpoke/core/command_manager.py`の`get_available_action_commands()`実装を確認し、
  (1) 通常時は技コマンドが残っていればFalse、(2) 技コマンドが0件で交代可能な控えがいる
  場合は交代コマンドが先頭に来つつも`is_struggle_only()`は交代コマンドの有無に影響されず
  正しくTrueを返す、(3) かなしばり等`ON_MODIFY_COMMAND_OPTIONS`ハンドラで技コマンドが
  全て潰される場合も同様にTrue、(4) あなをほる等の2ターン技で`Command.FORCED`のみが
  返る場合はわるあがきの選択肢自体が存在しないためFalse、という4つの分岐を実装通りに
  網羅できていることを確認した。`tests/test_command.py`に
  `test_is_struggle_only_技コマンドがある場合はFalse`・
  `test_is_struggle_only_技のPPが尽き交代先もいない場合はTrue`・
  `test_is_struggle_only_交代可能な控えがいても正しくTrueを返す`（既存の
  `get_available_commands(player)[0]`イディオムのバグを`commands[0].is_switch`で
  再現した上で`is_struggle_only()`が正しくTrueを返すことを確認する重要ケース）・
  `test_is_struggle_only_かなしばりで全ての技が封じられた場合はTrue`・
  `test_is_struggle_only_FORCEDが優先される場合はFalse`の5件を追加した。
  `python scripts/sort_tests.py tests/test_command.py`・`python
  scripts/generate_test_list.py`を実行し、`python examples/02_ai/01_custom_player.py`が
  従来通り正常終了する（威力110の「かみなり」を選び続ける）ことを確認した。
  `python -m pytest tests/ -v`で5842件全件パス・1件skip（既存のflaky無し、新規追加5件を
  含む）を確認した。
- [x] `Player`の対戦成績属性（`n_won_battles`等）がAPIリファレンスの表に無い
  （id: r8-7） → 対応内容 (2026-07-14): `docs/api/README.md`の`battle_against()`節の直後に
  「対戦成績」表を追加し、`n_finished_battles`/`n_won_battles`（int属性）と
  `n_lost_battles`/`n_tied_battles`/`win_rate`（property）を一覧化した。レビューで
  `src/jpoke/core/player.py`の実装（`n_lost_battles = n_finished_battles - n_won_battles -
  n_tied_battles`、`n_tied_battles`は常に0、`win_rate`はゼロ除算ガード付きの
  `n_won_battles / n_finished_battles`、`battle_against()`がターン上限未決着
  （`winner is None`）の対戦を`n_finished_battles`に含めない旨）と表の記述を突き合わせ、
  一致していることを確認した。`tests/test_poke_env_compat.py`の既存回帰テスト
  （`test_player_n_lost_battlesは対戦数から勝利数と引き分け数を引いた値`・
  `test_player_n_tied_battlesは常に0`・`test_player_win_rateは勝利数を対戦数で割った値`・
  `test_player_win_rateは対戦数0のときゼロ除算にならず0を返す`・
  `test_battle_against_ターン上限で決着しない対戦は戦績にカウントされない`等）とも矛盾が
  ないことを確認し、ドキュメントのみの変更のため新規テストは追加しなかった。
  `python -m pytest tests/ -v`で5842件全件パス・1件skip（既存のflaky無し）を確認した。
