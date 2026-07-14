# 第7ラウンド（apiループ）

[← 目次に戻る](../README.md)

- [x] `Pokemon.set_stats()`が辞書のキーを無視し挿入順で位置対応しているため誤ったステータスに
  書き込まれる（developer視点、id: r7-1） → 対応内容 (2026-07-14): `src/jpoke/model/pokemon.py`の
  `set_stats()`は`for i, value in enumerate(stats.values())`として`_set_stat_from_value(i, value)`を
  呼んでおり、辞書のキー（`Stat`）を無視し`enumerate()`による挿入順を暗黙の固定順
  （0=HP, 1=攻撃, 2=防御, 3=特攻, 4=特防, 5=素早さ）とみなして書き込んでいたため、
  `{"def": X, "atk": Y}`のようにキー順が典型順と異なる辞書や、`{"spe": X}`のように6項目に
  満たない辞書を渡すと、例外を出さずに意図と異なるステータスへ書き込まれる不具合があった。
  `for stat, value in stats.items(): idx = STATS.index(stat); self._set_stat_from_value(idx, value)`
  としてキーで対象インデックスを引くよう修正し、渡された辞書のキー順や項目数に依存しない
  実装にした。`docs/api/README.md`は`set_stats()`自体の掲載がなく矛盾がないため更新不要と
  判断した（`set_evs()`/`set_ivs()`の記載のみで`set_stats()`への言及なしを確認済み）。
  回帰テストとして`tests/test_stats.py`に2件追加した。1件目
  `test_ステータス実数値設定_set_statsでキー順が典型順と異なる辞書でも正しく反映される`は
  `{"def": target_def, "atk": target_atk}`という典型順と逆順のキーを渡し、`def`/`atk`が
  それぞれ正しい値に反映され、渡していない`hp`/`spa`が変化しないことを確認する。2件目
  `test_ステータス実数値設定_set_statsで6項目に満たない辞書を渡すと他のステータスは変化しない`は
  `{"spe": target_spe}`という単一キーの辞書を渡し、`spe`のみが反映され他の5ステータスが
  不変であることを確認する。目標値はいずれも別インスタンスに`set_evs()`で努力値を設定して
  得た実数値を使うことで、`_set_stat_from_value()`の逆算が必ず一致する値になるようにした。
  修正前のロジック（`enumerate(stats.values())`版）に一時的に戻して両テストが失敗すること
  （`def`側で`60 == 80`のような不一致、`spe`側で`110 == 142`のような不一致）を確認したうえで
  修正版に戻し、`python -m pytest tests/ -v`で5757件全件パス（既存のflaky testの新規発生なし）を
  確認した。

- [x] `Pokemon.set_form()`（フォルムチェンジ）が実装済みなのにexamples・docsに一度も登場しない
  （developer視点、id: r7-2） → 対応内容 (2026-07-14): `src/jpoke/model/pokemon.py:538`の
  `set_form(name, hp_policy="keep_absolute", set_default_ability=False)`は種族値・タイプ・
  特性候補込みでフォルム（ロトムの姿、ザシアン/ザマゼンタの剣王/盾王、オリジンフォルム等）を
  切り替えられる実用APIだが、`docs/api/README.md`・`examples/`のいずれにも記載が無かった。
  `docs/api/README.md`のPokemonセクションに「シナリオ構築系（フォルム変化）」を新設し
  `set_form()`のシグネチャ・引数・戻り値（既に同じフォルムなら何もせず`False`を返す）を明記した。
  合わせて`examples/03_damage_calc/10_form_change_comparison.py`を新設し、ロトムの全6フォルム
  （ベース/ヒート/ウォッシュ/フロスト/スピン/カット）に「じしん」を撃った場合のダメージ・
  致死率と、フォルムごとのぼうぎょ実数値を`calc_lethal()`と組み合わせて比較するサンプルを追加
  （`examples/README.md`にも一覧追加）。`PYTHONIOENCODING=utf-8 python
  examples/03_damage_calc/10_form_change_comparison.py`で実行し、タイプ相性（ヒートロトムは
  じめん4倍弱点、スピンロトムは無効化等）・種族値差が出力に正しく反映されることを確認した。
  回帰テストとして`tests/test_form.py`を新設し6件追加した:
  `set_form`が同じフォルム指定時に何も変更せず`False`を返すこと、異なるフォルム指定で
  種族値・タイプが切り替わり`True`を返すこと（ロトム→ヒートロトム）、既定の
  `hp_policy="keep_absolute"`では最大HPが変化するフォルム変化（ジガルデ50%→10%、HP種族値
  108→54）でも被ダメージ絶対量が維持されること、`hp_policy="reset"`では被ダメージ状態でも
  満タンになること、`set_default_ability`未指定時は変更先の特性候補（ジガルデ(パーフェクト)は
  スワームチェンジのみ）に含まれるかに関わらず元の特性（オーラブレイク）が維持されること、
  `set_default_ability=True`指定時は変更先の先頭特性（スワームチェンジ）にリセットされること。
  `python scripts/sort_tests.py tests/test_form.py`・`python scripts/generate_test_list.py`を
  実行し、`python -m pytest tests/ -v`で5764件全件パス（既存の5757件+新規テスト6件+examplesスモーク
  1件、flaky testの新規発生なし）を確認した。

- [x] `Battle.resolve_secondary_chance()`の引数`ctx`型（`EventContext`/`AttackContext`）が
  jpokeトップレベルからimportできず内部実装への直接アクセスを強いる（developer視点、id: r7-3）
  → 対応内容 (2026-07-14): `src/jpoke/core/battle.py:1352`の`resolve_secondary_chance(ctx:
  EventContext | AttackContext, ...)`は、`EventContext`/`AttackContext`が`jpoke`トップレベル
  （`jpoke/__init__.py`）からは未エクスポートである点は事実だが、`jpoke.core.__init__`では
  `from .context import BaseContext, EventContext, AttackContext`により既に再エクスポート済みで、
  `from jpoke.core import EventContext, AttackContext`は現状でも動作することを実測で再確認した
  （`python -c "from jpoke.core import EventContext, AttackContext"`が例外なく成功）。本APIは
  `handlers/*.py`の追加効果実装がハンドラ関数の引数として受け取った`ctx`をそのまま渡す用途を
  想定した内部専用APIであり、利用者が`ctx`を自作して呼び出す想定ではないため、シグネチャ変更
  （例: `Any`型への緩和や独自ラッパー型の新設）はAPIの型安全性を損なう割に実利が薄いと判断し、
  他loopとの衝突リスクも考慮して見送った。代わりに`resolve_secondary_chance()`のdocstringに
  「主に`handlers/*.py`からハンドラ引数の`ctx`をそのまま渡す用途のAPIであること」「型が必要な
  場合は`from jpoke.core import EventContext, AttackContext`で入手できること」を明記し、
  `docs/api/README.md`の`AttackContext`/`EventContext`を要求する内部専用メソッドに関する記述の
  直後にも同様の入手方法を追記した。ロジック変更を伴わないため新規の回帰テストは不要と判断し、
  既存の`tests/test_battle_option.py`（`resolve_secondary_chance`関連19件）が引き続き通ることを
  確認した。`python -m pytest tests/ -v`で5764件全件パス（既存件数のまま、flaky testの新規発生
  なし）を確認した。

- [x] README.mdのクイックスタートだけ`judge_winner() is None`の旧パターンのまま残っている
  （beginner視点、id: r7-4） → 対応内容 (2026-07-14): ルート`README.md`の「クイックスタート」節が
  `while battle.judge_winner() is None and battle.turn < 100:` / `winner = battle.judge_winner()`
  という旧パターンのままで、`examples/01_basics/02_quickstart.py`（docstringで「READMEの
  クイックスタートと同内容」と明記）や`docs/api/README.md`が採用している`while not
  battle.finished and battle.turn < 100:` / `winner = battle.winner`という表記と食い違って
  いた。`README.md`を後者の表記に修正し、`CHANGELOG.md`にも明記した。`docs/api/README.md`は
  既に`while not battle.finished` / `battle.winner`を使用しており矛盾がないため更新不要と
  判断した。回帰テストとして`tests/test_code_conventions.py`に
  `test_READMEがjudge_winnerのis_None比較を使っていない`を追加した。既存の
  `test_examplesがjudge_winnerのis_None比較を使っていない`（id: r6-4）は`examples/`配下のみを
  検査対象としており、リポジトリルートの`README.md`は検査範囲外だったため、同様の正規表現
  （`judge_winner\(\)\s*is\s*(not\s+)?None`）でREADME.md単体を検査する専用テストを追加し、
  同種の表記揺れが再発した場合に検出できるようにした。修正前の旧パターンに一時的に戻して
  新規テストが失敗することを確認したうえで修正版に戻し、
  `python scripts/sort_tests.py tests/test_code_conventions.py`・
  `python scripts/generate_test_list.py`を実行し、`python -m pytest tests/ -v`で5765件全件
  パス（既存の5764件+新規テスト1件、flaky testの新規発生なし）を確認した。

- [x] `Command.is_type()`が公開APIリファレンス（`docs/api/README.md`）のCommand章に載って
  いない（beginner視点、id: r7-5） → 対応内容 (2026-07-14): `src/jpoke/enums/command.py:130`の
  `is_type(command_type: CommandType | None) -> bool`（`"any"` / `"move"` / `"switch"`を受理し、
  `command_manager.py`・`turn_controller.py`・`observation_builder.py`・
  `handlers/ability.py`・`handlers/item.py`・`handlers/volatile.py`等で汎用の種別判定に使われて
  いる中核API）が、`docs/api/README.md`のCommand章「インスタンスプロパティ・メソッド」表に
  `is_regular_move`/`is_switch()`等はあるのに掲載されていなかった。表の先頭に
  `is_type(command_type)`の行を追加し、`"any"`/`"move"`/`"switch"`の受理値と、`is_regular_move`
  との違い（`"move"`は通常技コマンドに加えテラスタル・メガシンカ・ダイマックス・Zワザを伴う
  技コマンドも含む一方、`is_regular_move`は`MOVE_*`のみ）を明記した。実装（`is_type()`本体の
  `match`文）を確認したところ、`"move"`判定は`self.name[:-2] not in {"SELECT", "SWITCH"}`という
  除外方式のため、`STRUGGLE`（わるあがき）・`FORCED`（強制行動）も`"move"`側の真になる（両者とも
  `resolve_move_from_command()`で実際に技オブジェクトへ解決されるため、`command_manager.py`の
  `if not any(cmd.is_type("move") for cmd in commands): commands += [Command.STRUGGLE]`や
  `turn_controller.py`の`if not command.is_type("move") or mon.fainted:`という既存利用箇所の
  前提と整合する意図的な挙動）。この特殊コマンドの扱いは表の一文説明には収まらない細部と判断し、
  回帰テストの docstring 側に委ねドキュメント本文はbeginner向けの簡潔さを優先した。回帰テストとして
  `tests/test_command.py`に4件追加した:
  `test_is_type_anyを指定すると全てのコマンドが真になる`（`MOVE_0`/`SWITCH_0`/`TERASTAL_0`/
  `STRUGGLE`/`FORCED`すべて真）、
  `test_is_type_moveを指定すると技系コマンドのみ真になる`（`MOVE_0`/`TERASTAL_0`/`MEGAEVOL_0`/
  `GIGAMAX_0`/`ZMOVE_0`/`STRUGGLE`/`FORCED`は真、`SWITCH_0`は偽）、
  `test_is_type_switchを指定すると交代コマンドのみ真になる`（`SWITCH_0`のみ真）、
  `test_is_type_Noneを渡すと偽を返す`（`command_type=None`は常に偽）。
  `python scripts/sort_tests.py tests/test_command.py`・`python scripts/generate_test_list.py`を
  実行し、`python -m pytest tests/ -v`で5769件全件パス（既存の5765件+新規テスト4件、flaky testの
  新規発生なし）を確認した。

- [x] `Battle.calc_move_priority()`/`Battle.resolve_speed_order()`が`docs/api/README.md`のBattle章に
  未掲載で、`jpoke.testing`版と混同しやすい（id: r7-6） → 対応内容 (2026-07-14):
  `src/jpoke/core/battle.py:749`の`calc_move_priority(self, attacker: Pokemon, move: Move) -> int`
  （`speed_calculator.calc_move_priority()`への委譲。技本来の優先度に
  ON_MODIFY_MOVE_PRIORITYイベントによる補正を加えた値を返す）と、同ファイル729行目の
  `resolve_speed_order(self) -> list[Pokemon]`（`speed_calculator.resolve_speed_order()`への委譲。
  引数なしで現在の実効素早さ順にソートしたポケモンのリストを返す）は
  `examples/02_ai/04_priority_and_command_debug.py`で実際に使われている実装済みメソッドだが、
  `docs/api/README.md`のBattle「状態取得系」テーブルには一度も掲載されておらず、
  「テストユーティリティ」節の`jpoke.testing.calc_move_priority(battle, player_index,
  move_index=0)`（インデックス指定の薄いラッパー）のみが記載されていたため、
  両者が別物であることに気づきにくかった。Battle「状態取得系」テーブルに
  `calc_move_priority(attacker, move)`/`resolve_speed_order()`の行を追加し、コード例にも
  `battle.calc_move_priority(active, active.moves[0])`/`battle.resolve_speed_order()`を追記した。
  `calc_move_priority`の説明には`jpoke.testing.calc_move_priority(battle, player_index,
  move_index=0)`が内部でこちらを呼ぶインデックス指定版であることを明記し、
  「テストユーティリティ」節側の`calc_move_priority`の説明にも`Battle.calc_move_priority(pokemon,
  move)`のインデックス指定版である旨を追記して相互参照できるようにした。`resolve_speed_order()`の
  説明には、予約済みコマンドを考慮した実際の行動順が必要な場合は`resolve_action_order()`を使う
  旨も明記した。`CHANGELOG.md`にも明記した。ドキュメントのみの修正でコード変更を伴わないため
  新規の回帰テストは不要と判断し、`PYTHONUTF8=1 python
  examples/02_ai/04_priority_and_command_debug.py`を実行してBattle直下の
  `calc_move_priority()`/`resolve_speed_order()`呼び出しが引き続き動作すること
  （でんこうせっか=1・のしかかり=0という優先度、通常時/トリックルーム下での素早さ順反転）を
  確認した。`python -m pytest tests/ -v`で5769件全件パス（既存件数のまま、flaky testの新規発生
  なし）を確認した。

- [x] `TreeSearchPlayer`の内部シミュレーションが`battle.copy(reseed=...)`を使わず、探索の
  兄弟ノード間で乱数系列が相関する（ai_developer視点、id: r7-7） → 対応内容 (2026-07-14):
  `src/jpoke/players/tree_search_player.py:268`の`_worst_case_over_opponent()`内`sim =
  battle.copy()`が`reseed`引数を省略（既定`False`）していたため、同じ`my_cmd`に対する各
  `opp_cmd`分岐・各`my_cmd`分岐が複製元battleの`random`/`decision_random`の状態をそのまま
  共有し、探索木の兄弟ノード間で乱数系列が相関していた（`configure_sim`で命中判定・ダメージ
  乱数等の確率的要素を固定していない探索では評価値が歪みうる不具合。
  `examples/04_research/03_janken_nash_cfr.py`の自作ロールアウトは既に`reseed=True`相当の
  独自シード制御をしており対象外）。`sim = battle.copy(reseed=True)`に変更し、変更理由と
  `Battle.copy()`のdocstring参照コメントを追記した。`Battle.copy(reseed=True)`は
  複製元battleの`_reseed_count`をインクリメントしたうえで`new.seed = hash((self.seed,
  self._reseed_count))`により派生シードを生成する仕様（`src/jpoke/core/battle.py:326`）のため、
  同一の`battle`引数から呼ばれる兄弟ノード（`_worst_case_over_opponent`内のループ・
  `_best_command`内の`my_cmd`ループ）はそれぞれ一意な派生シードを持つ。`configure_sim`で
  確率的要素を固定している場合は探索結果（選ばれるコマンド）に変化はないが、固定していない
  場合は評価値の相関が解消されることで変わりうる点を`CHANGELOG.md`に明記した。回帰テストとして
  `tests/test_tree_search_framework.py`に2件追加した:
  `test_reseedTrueにより兄弟ノード間でsimの乱数系列が独立する`は`configure_sim`未固定
  （`battle.test_option.accuracy`未設定）の状態でmax_plies=1の各分岐（4×4=16件、テラスタル
  コマンド込み）の`sim.random`/`sim.decision_random`の内部状態（`getstate()`）を収集し、
  全て重複しないことを確認する。`test_max_plies2でネストしたsimでも全階層のseedが重複しない`は
  max_plies=2でトップレベルの分岐からさらに再帰した2手目の分岐まで含めて`configure_sim`が
  観測する全ての`sim.seed`（実測160件）が階層をまたいで重複しないことを確認し、`_reseed_count`が
  複製元battle基準で単調増加する派生シード生成がネストした`_worst_case_over_opponent`呼び出しでも
  正しく機能することを検証する。`python scripts/sort_tests.py
  tests/test_tree_search_framework.py`・`python scripts/generate_test_list.py`を実行し、
  `python -m pytest tests/ -v`で5779件全件パス・1件skip（新規テスト2件を含む。main側で他ラウンド
  由来のテストが追加され件数はr7-6時点の5769件から増えている。flaky testの新規発生なし）を
  確認した。
