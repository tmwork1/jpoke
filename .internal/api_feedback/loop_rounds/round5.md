# 第5ラウンド（apiループ）

[← 目次に戻る](../README.md)

- [x] `Pokemon.modify_hp()`が内部専用なのに公開APIとして丸見えで罠になっている
  （developer視点、id: r5-1） → 対応内容 (2026-07-12): `Pokemon.modify_hp`を
  `Pokemon._modify_hp_raw`にリネームし、唯一の呼び出し箇所
  （`src/jpoke/core/status_manager.py`）を更新。`CHANGELOG.md`に破壊的変更として明記した。
  `docs/api/README.md`は元々`Pokemon.modify_hp`を掲載していなかったため更新不要と判断（確認
  済み）。回帰確認として `tests/test_code_conventions.py` に
  `test_Pokemon_modify_hpが公開APIとして露出していない`
  （`hasattr(Pokemon, "modify_hp")`がFalse・`hasattr(Pokemon, "_modify_hp_raw")`がTrueを
  検証する軽量テスト）を追加した。`python -m pytest tests/ -v`は5386 passed, 1 skipped,
  13 failedで、failedはすべて`tests/test_examples_smoke.py`のサブプロセス実行テスト
  （`jpoke`がpipインストールされていない実行環境固有の既存問題）であることを、
  origin/mainを一時worktreeでチェックアウトして同じ13件が失敗することを確認して検証済み。
  本ラウンドの変更に起因する失敗ではない
- [x] `Pokemon.terastallize()`/`megaevolve()`の戻り値docstringが実装と食い違う
  （developer視点、id: r5-2） → 対応内容 (2026-07-12): docstringの「成功時True・失敗時False」
  という誤記述を削除し、実装通り常に`None`を返す旨に修正。両メソッドが特性ハンドラの
  付け替えや`Event.ON_TERASTALLIZE`/`Event.ON_ABILITY_ENABLED`の発火・`can_terastallize()`/
  `can_megaevolve()`の判定を行わない内部メソッドであり、単体で呼び出さず
  `Command.get_terastal_command()`/`Command.get_megaevol_command()`経由で`Battle.step()`に
  渡す経路から使うべき旨を明記した。ロジック変更は無し。`docs/api/README.md`は元々両メソッドを
  掲載していなかったため更新不要、シグネチャ変更が無いため`CHANGELOG.md`更新も不要と判断
  （確認済み）。既存テスト（`tests/test_terastal.py`等）が`terastallize()`を直接呼び出している
  箇所を確認したが、いずれも戻り値を使わずダメージ計算用の状態セットアップとして使う意図的な
  パターンであり、docstringの「単体呼び出し非対応」という趣旨（イベント発火に依存しないこと）
  と矛盾しないことを確認した。回帰テストとして`tests/test_terastal.py`に
  `test_terastallize_戻り値はNone`、`tests/test_megaevol.py`に`test_megaevolve_戻り値はNone`を
  追加し、戻り値が`None`であることを検証した。`python -m pytest tests/ -v`は5389 passed,
  1 skipped, 13 failedで、failedはすべて`tests/test_examples_smoke.py`の既存環境問題
  （`jpoke`がpipインストールされていない）であり、本ラウンドの変更に起因する失敗ではない
- [x] シナリオ構築用Battle委譲メソッド群でdocstringの充実度・引数名が不揃い
  （developer視点、id: r5-3） → 対応内容 (2026-07-12): `Battle.modify_stats`/`gain_item`/
  `remove_item`/`swap_items`/`take_item`/`consume_item`にArgs/Returns形式のdocstringを追加し、
  一覧性・引数の意味（`track_loss`・`ignore_sticky_hold`の仕様条件等）を統一。加えて
  `consume_item`の第1引数名を他のアイテム系メソッド（`gain_item`/`remove_item`/`take_item`は
  いずれも`target`）に合わせて`mon`から`target`にリネームした（`Battle.consume_item`/
  `ItemManager.consume_item`両方、破壊的変更として`CHANGELOG.md`に明記）。リポジトリ内の
  既存呼び出しはすべて位置引数（`consume_item(mon)`等）でキーワード引数`mon=`での呼び出しは
  無いことを確認済みのため、呼び出し側の修正は不要だった。`docs/api/README.md`のシナリオ構築系節
  は元々`modify_hp`/`faint`/`modify_stats`/`set_ailment`/`set_volatile`/`set_weather`/
  `set_terrain`のみを掲載しており、今回docstringを追加した`gain_item`等のアイテム系メソッドは
  掲載範囲外のため更新不要と判断（確認済み）。回帰テストとして`tests/test_code_conventions.py`に
  `test_consume_itemの引数名がtargetにリネームされている`
  （`target=`キーワード引数での呼び出しが成功し、旧引数名`mon=`だと`TypeError`になることを
  検証する軽量テスト）を追加した。`python -m pytest tests/ -v`は5390 passed, 1 skipped,
  13 failedで、failedはすべて`tests/test_examples_smoke.py`の既存環境問題
  （`jpoke`がpipインストールされていない）であり、本ラウンドの変更に起因する失敗ではない
- [x] 命中率固定の手段がexamples内で2系統（`accuracy_fix_threshold` / `test_option.accuracy`）
  に分裂している（beginner視点、id: r5-4） → 対応内容 (2026-07-12):
  `examples/04_research/03_janken_nash_fictitious_play.py` と `04_janken_nash_cfr.py` が
  内部テスト専用の低レベルAPIである `battle.test_option.accuracy = 100` を使っており、
  他のexamples（`01_basics/03_hazards_and_explicit_commands.py`・
  `03_damage_calc/02_field_and_status_effects.py`）の公開API
  `Battle(..., accuracy_fix_threshold=0)` と手段が2系統に分裂していた。両ファイルとも
  動的な切り替えは無い単純な1回設定だったため `accuracy_fix_threshold=0` に統一した。
  `src/jpoke` 側の変更は無い。RNG消費パターンの違いの検証: `test_option.accuracy` は
  命中判定のたびに必ず `battle.random.random()` を1回消費するのに対し、
  `accuracy_fix_threshold=0` は命中率チェック自体をスキップしRNGを消費しない
  （`src/jpoke/core/move_executor.py` の `_check_hit()` で確認）。このため同じ`seed`でも
  以降のダメージ乱数・急所判定のRNG列がずれ、fictitious play/CFR学習ループの出力する
  具体的な数値は変化する。`PYTHONHASHSEED=0`で固定した上で新旧コードを実際に実行し
  数値を比較したところ（`decision_random`の種が`hash((seed, "decision"))`に依存するため、
  比較には`PYTHONHASHSEED`固定が必須と判明。既存の非決定性であり本件の変更とは無関係）、
  両ファイルとも「主要な学習指標（fictitious playの`value`/`exploitability`、CFRのp0勝率が
  0.5近辺に収束する自己対戦の対称性、状態別戦略が3つの技へ分散しHP状況に応じて偏りが
  変わる適応的傾向）」は新旧で保たれており、examplesの教育的結論（読み合いの近似・
  適応的戦略の学習が機能することを示す）は損なわれないことを確認した。個々の確率の
  小数点以下の値自体は元々`GRID_STEP`/`EVAL_TRIALS`が小さい粗い近似であり、両ファイルの
  docstringも「近似の精度はまだ粗い」「設定値を大きくして結果の安定性を比較してみよう」と
  明記しているため、この程度の変動は許容範囲と判断した。`docs/api/README.md`は
  `test_option`を元々掲載しておらず`accuracy_fix_threshold`のみ掲載済みのため更新不要と
  判断した（確認済み）。回帰テストとして`tests/test_code_conventions.py`に
  `test_examplesがtest_option経由で命中率等を固定していない`（`examples/`配下に
  `test_option`の使用が無いことを静的に検証し、2系統への再分裂を防止する軽量テスト）を
  追加した。`python -m pytest tests/ -v`は5405 passed, 1 skipped, 0 failedで全件成功
  （このマシンでは他worktreeが編集可能インストールで`jpoke`をグローバル公開しており
  `tests/test_examples_smoke.py`のサブプロセスもそちらを解決できたため、既知の環境問題は
  今回発生しなかった）
- [x] `add_pokemon()`統一方針に反して2ファイルだけ`team.append(Pokemon(...))`相当に
  逆戻りしている（id: r5-5） → 対応内容 (2026-07-12):
  `examples/04_research/03_janken_nash_fictitious_play.py` と `04_janken_nash_cfr.py` の
  `build_pokemon()`が`Pokemon(...)`を直接構築し`p0.team.append(build_pokemon())`で追加して
  おり、他の全12件のexamplesが使う`Player.add_pokemon()`という正規の追加ルートから外れていた。
  `add_pokemon()`は努力値・個体値を引数に取らないため、`build_pokemon_kwargs()`
  （`add_pokemon()`用kwargsを返す）と`add_team_pokemon(player)`
  （`player.add_pokemon(**kwargs)`で追加した上で`set_evs`/`set_ivs`を適用して返す）の2段構成に
  分割し、呼び出し側を`add_team_pokemon(p0)`/`add_team_pokemon(p1)`に置き換えた。EVS/IVSの値
  （`EVS`/`IVS`定数、`set_ivs(IVS, hp_policy="reset")`）は変更前の`build_pokemon()`と同一で
  あることを確認した。`src/jpoke`側の変更は無い。`docs/api/README.md`は元々`add_pokemon()`を
  掲載済みで今回のexamples側の書き換えによる公開API変更は無いため更新不要と判断した
  （確認済み）。回帰テストとして`tests/test_code_conventions.py`に
  `test_examplesがteam_append_Pokemon経由でチームを構築していない`（`examples/`配下に
  `.team.append(Pokemon(`の使用が無いことを静的に検証し、再度の逆戻りを防止する軽量テスト）を
  追加した。両ファイルを個別実行し、正常終了と出力内容（fictitious playの`value`/
  `exploitability`、CFRの状態別戦略の分散）に問題が無いことを確認した。
  `python -m pytest tests/ -v`は5408 passed, 1 skipped, 0 failedで全件成功
- [x] `docs/api/README.md`にCommand・Moveの章が無い（beginner視点、id: r5-6） →
  対応内容 (2026-07-12): `docs/api/README.md`の目次に`Command`（`src/jpoke/enums/command.py`）と
  `Move`（`src/jpoke/model/move.py`）の2章を新設し、既存のBattle/Player/Pokemon章と同水準の
  粒度（属性・メソッドの表＋コード例）で記載した。Command章は命名規則
  （`{種別}_{インデックス}`）・定数一覧・`get_*_command()`系クラスメソッド・
  `is_regular_move`等のインスタンスプロパティを掲載し、Move章は主要属性（`name`/`pp`/`type`/
  `base_power`/`category`/`priority`/`accuracy`/`target`/`crit_ratio`等）・判定系プロパティ
  （`is_attack`/`is_blocked_by_protect`/`is_reflectable`/`has_flag`）・連続技系
  （`min_hits`/`max_hits`/`expected_hits`）・PP操作（`modify_pp`）を掲載した。
  `src/jpoke/enums/command.py`・`src/jpoke/model/move.py`（`GameEffect`基底クラスの`name`
  プロパティを含む）と1行ずつ突き合わせ、記載したシグネチャ・戻り値・プロパティ/属性の区別
  （`(property)`表記の有無）に齟齬が無いことを確認した。掲載したコード例は
  `jpoke.testing.start_battle`でセットアップした実際のBattleに対して
  `battle.command_to_move`/`move.has_flag`/`move.modify_pp`/`Command.get_switch_command`/
  `battle.get_available_commands`（`battle.phase_context("action")`経由）/`battle.step`を
  実行し、記載通りに動作することを手動検証した。`src/jpoke`側のコード変更は無いため
  `CHANGELOG.md`更新は不要と判断した。ドキュメントのみの変更のためテスト追加は行っていない。
  `python -m pytest tests/ -v`は5437 passed, 1 skipped, 0 failedで全件成功
  （本ラウンドの変更に起因する失敗なし）

