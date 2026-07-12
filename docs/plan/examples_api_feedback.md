# examples/ 作成から見えたAPIフィードバック

作成日: 2026-07-11

## 運用ルール

- 本ドキュメントの項目は `[ ]` / `[x]` のチェックリスト形式で管理する。`[x]` は
  「実装対応済み」または「検討のうえ対応しないと決定した（見送り確定）」の両方を含み、
  `[ ]` は「まだ判断・対応していない」項目を指す。チェックを付けたら、その項目の末尾に
  `→ 対応内容 (日付)` を追記する
- **妥当と判断したフィードバックは、判断した時点で即座にsonnet sub agentへ実装を委任する**。
  本体（Fable）は仕様の精査・妥当性判断・差分レビュー・PR操作を担当し、実装・テスト・
  検証はsonnetサブエージェント（`Agent` ツール、`model: sonnet`、`isolation: "worktree"`）に
  詳細な指示書付きで委任する。1件ずつ都度サブエージェントに投げてよく、まとめて
  バッチ実行する必要はない（関連メモ: `feedback_sonnet_subagent_for_work`）

## examples カバレッジチェックリスト（今後の拡充候補）

README「実装状況」の規模（特性310・アイテム247・技733・揮発性状態66・状態異常7・場の効果31）に対し、
`examples/` がどの主要概念を実演できているか／できていないかを一覧管理する。「4度目のレビュー指摘」
（jpoke内部実装を知らない設定のsonnetサブエージェントによる調査）で洗い出した未カバー項目の追跡用。
新しいサンプルを追加・既存サンプルを拡充した際はここのチェックを更新する。

- [x] EV/IV設定（`Pokemon.set_evs()`/`set_ivs()`）— `examples/04_damage_calculation.py` に実演あり
  （→ 2026-07-12対応）
- [x] 特性（`ability_name`）がダメージ計算・行動選択に与える影響（例: もらいび・ふゆう・いかく等）
  → 対応内容 (2026-07-12): `examples/01_basics/02_team_battle.py` に、ポケモンごとに持てる
  特性を確認する方法（`POKEDEX[name].abilities`）と、「ひらいしん」（でんき技を無効化し
  とくこうを上げる）の効果を実演する独立したミニバトルを追加した。メインの3体バトルは
  `RandomPlayer`同士で交代がランダムに起きるため展開が安定せず、特性実演には決定論的な
  `Player`同士・素早さ調整済みの専用バトル（1ターンのみ）を分けて使った。
  `ability_name`を省略すると特性は空文字のままで自動的に先頭特性が設定されるわけではない
  点もコメントで明記した
- [x] examples内に残っていた対応・見送り判断済みの `# TODO:` コメントを削除
  （2026-07-12）: `01_basics/01_quickstart.py`（RandomPlayer化・Battleクラス非公開化・
  poke-env互換battle_against()関連の3件）、`01_basics/02_team_battle.py`（ひらがな技名
  入力対応）、`02_ai/02_tree_search_ai.py`（TreeSearchPlayerの改名案）、
  `03_damage_calc/01_damage_calculation.py`（calc_lethalの戻り値構造、既にdocstringで
  解決済み）。判断根拠は本ドキュメントの各該当セクションに記録済みのため、
  コード側のTODOは削除してよいと判断した
- [x] 天候（あめ・すなあらし等）の効果
  → 対応内容 (2026-07-12): 新規 `examples/03_damage_calc/02_field_and_status_effects.py` の
  `show_weather_effect()` に、`Battle.set_weather("すなあらし")` で天候を直接発動し、
  `battle.step()` でターン終了時のすなあらしダメージ（岩・はがね・じめん以外が対象）を
  実演する例を追加した
- [x] 地形（エレキフィールド等）の効果
  → 対応内容 (2026-07-12): 同ファイルの `show_terrain_effect()` に、`Battle.set_terrain("エレキ
  フィールド")` の前後で `battle.calc_damages()` を比較し、地面にいるポケモンのでんき技の
  威力が1.3倍になることを実演する例を追加した
- [x] 状態異常（どく・やけど・ねむり・こおり・こんらん等）を意図的に発生させる例
  → 対応内容 (2026-07-12): 同ファイルの `show_ailment_via_actual_move()` に、`set_ailment()`
  ではなく実際に「どくどく」を当てて「もうどく」を発生させ、`mon.status` / `has_ailment()` で
  確認する例を追加した（`accuracy_fix_threshold=0` で命中判定の非決定性を排除）
- [x] アイテム・特性の発動ログが実際に画面に出る例（`calc_lethal()`はバトルを進行させないため
  発動ログが出ない。`battle.step()`を伴う例で見せる必要がある）
  → 対応内容 (2026-07-12): 同ファイルの `show_ability_and_item_logs()` に、`battle.step()` を
  伴う最小構成の対戦を2つ用意し、`print_logs()` で「もらいび」（特性発動ログ）・
  「きあいのタスキ」（アイテム発動ログ、`damage_roll="max", critical_mode="always"` で
  瀕死になるはずの一撃を確実に再現）が実際に画面に出ることを実演した
- [x] 交代誘発技（とんぼがえり・ボルトチェンジ等）・設置技（ステルスロック・まきびし等）
  → 対応内容 (2026-07-12): 新規 `examples/01_basics/03_hazards_and_explicit_commands.py` の
  `show_entry_hazard_and_explicit_switch()` に `Battle.activate_side_field(player, "ステルス
  ロック", 1)` でサイドフィールド効果を発動し、いわタイプ弱点の控えに明示的な交代コマンドで
  交代して被弾する例を追加。`show_switch_inducing_move()` に「とんぼがえり」で命中直後、
  同じ `battle.step()` 呼び出し内で使用者側の強制交代（`Interrupt.PIVOT`）が既定方策に従って
  自動解決されることを確認する例を追加した（挙動は実装コードを読んで検証済み、
  `_run_move_phase` が技実行直後に `run_interrupt_switch(Interrupt.PIVOT)` を呼ぶ）
- [x] 先制技・素早さ操作技（トリックルーム等）— 木探索AI（05）の行動順読み合いの価値を示す題材として有効
  → 対応内容 (2026-07-12): 新規 `examples/02_ai/03_priority_and_command_debug.py` の
  `show_priority_and_speed_control()` に、`battle.calc_move_priority()` ででんこうせっか
  （優先度+1）とのしかかり（優先度0）の差を確認し、`battle.activate_global_field("トリック
  ルーム", 5)` の前後で `battle.resolve_speed_order()` が反転することを実演する例を追加した。
  ディレクトリ名が「02_ai」のためファイル名では「05」ではなく「02_ai/03」と対応させている
- [x] わるあがき（PP切れ）の挙動
  → 対応内容 (2026-07-12): `examples/01_basics/03_hazards_and_explicit_commands.py` の
  `show_struggle_when_out_of_pp()` に、`Move.modify_pp(-99)` で技のPPを直接0にし、
  `battle.get_available_commands()` が `[Command.STRUGGLE]` のみを返すこと・実行後に
  最大HPの1/4の反動ダメージを受けることを実演する例を追加した
- [x] テラスタルを能動的に選ぶ方法（`Command.get_terastal_command()`相当の使い方）
  → 対応内容 (2026-07-12): 同ファイルの `show_explicit_terastal_command()` に、
  `Command.get_terastal_command(0)`（0番目の技を使いながらテラスタルするコマンド）を
  `battle.step({player: command, ...})` に直接渡し、`mon.is_terastallized` /
  `mon.tera_type` が変化することを確認する例を追加した
- [x] 交代コマンドを明示的に組み立てる例（既存の`get_available_commands()`から選ぶだけでなく）
  → 対応内容 (2026-07-12): 同ファイルの `show_entry_hazard_and_explicit_switch()` に、
  `Command.get_switch_command(index)` でチーム内インデックスから交代コマンドを直接組み立て、
  `battle.step({player: switch_command, ...})` に渡す例を追加した（設置技の実演と兼ねている）
- [x] コマンド候補・選択理由をデバッグ的に確認する方法（`evaluate_commands()`等の既存APIの紹介を含む）
  → 対応内容 (2026-07-12): `examples/01_basics/03_hazards_and_explicit_commands.py` の
  `show_struggle_when_out_of_pp()` 内で `battle.get_available_commands(self)` を
  `choose_command()` オーバーライドから覗く軽量な確認方法を示し、
  `examples/02_ai/03_priority_and_command_debug.py` の `DebugPlayer` で
  `TreeSearchPlayer.evaluate_commands()`（副作用なしで各合法手の評価値一覧を返す既存API）を
  使った、より発展的な読み筋のデバッグ確認方法を実演した（1ターン目は相手の技が未公開のため
  空辞書になり、2ターン目以降に評価値が表示されることも確認済み）

### 内部実装に精通したsonnetサブエージェントによる追加調査（2026-07-12）

`src/jpoke/` を自由に読ませ、上記チェックリストと重複しない「コードを読んだからこそ気づく」未紹介APIを
洗い出させた。詳細（該当ファイル:行）は各項目のコメント参照。最も価値が高いのはAで、次点でB。

- [x] **【最重要】`Battle.calc_lethal()` は状態異常・天候・設置効果込みの複合ダメージ蓄積を既に
  計算できるのに一度も実演されていない**。`core/lethal.py` の `_lethal_loop`（`lethal.py:227`）が
  1攻撃ごとに `ON_TURN_END` 等の `LethalEvent` を発火し、どく/もうどく/やけどの毎ターンダメージ
  （`data/ailment.py:19,41,73`）・すなあらしダメージ（`data/field/weather.py:70`）・
  やどりぎのタネ等（`data/volatile.py`）が自動的に合算される。「どくを付与した状態で何ターンで
  詰むか」が実戦で頻出の問いなのに04で一切示されていない。ただし **`Battle` に状態異常・天候を
  直接セットする公開メソッドが無い**（`ailment_manager.apply(...)` は `tests/test_utils.py` が
  内部を直呼びしているのみ）という設計ギャップも同時に判明した。examples化するには
  「実際に技を当てて状態異常にしてから`calc_lethal`を呼ぶ」か、公開ラッパーの新設が要検討
  → **対応内容 (2026-07-12)**: `Battle.set_ailment(target, name, count=None)` /
  `Battle.set_weather(name, count=5)` / `Battle.set_terrain(name, count=5)` を
  `ailment_manager.apply()` / `weather_manager.apply()` / `terrain_manager.apply()` への
  薄い委譲として新設（`src/jpoke/core/battle.py`）。`examples/04_damage_calculation.py` に、
  努力値無振りの攻撃側・防御側ペアで「どく無し/どくあり」の致死率を同発数で比較する例を追加し、
  毎ターンのどくダメージが技ダメージに合算されて致死率が底上げされることを実演した。
  回帰テストは `tests/test_ailment.py`（`set_ailment` の付与・上書き）、
  `tests/test_field.py`（`set_weather` / `set_terrain` の発動）、`tests/test_lethal.py`
  （`set_ailment` でどくを付与すると `calc_lethal` の確定数が5発→3発に短縮されることの検証）
  に追加し、全テスト・ruffともに成功を確認済み
- [x] リプレイ機能一式（`Battle.build_replay_data()`・`ReplayPlayer`・`replay_battle()`、
  `core/replay.py`）が丸ごとexamples未紹介。`tests/test_replay_fuzz.py`等では使われている。
  「興味深い対戦を記録して後で解析する」という戦術研究ユースケースに直結するのに未紹介
  → 対応内容 (2026-07-12): 新規 `examples/07_replay.py` を追加。1vs1バトルを最後まで
  進めて `build_replay_data()` で記録し、`to_dict()`/`from_dict()` でシリアライズ・復元した
  うえで `replay_battle()` に渡し、勝者・ターン数が元の対戦と一致することを確認する最小例。
  `examples/README.md` の対応表にも1行追加した
- [x] poke-env互換プロパティ群（`battle.active_pokemon`/`opponent_active_pokemon`/
  `available_moves`/`available_switches`/`side_conditions`/`team`、`battle.py:952-1022`）が
  `choose_command`に渡される観測コピーでそのまま使えるのに、03は`get_available_commands`/
  `command_to_move`というjpokeネイティブな書き方のみ紹介。poke-env経験者向けに両方並べる価値あり
  → 対応内容 (2026-07-12): `examples/03_custom_player.py` の `StrongestMovePlayer` に、同じ判断を
  `battle.available_moves`（`battle.observer` が呼び出し元プレイヤーに設定される観測コピーの
  poke-env互換プロパティ）で書いた `choose_command_poke_env_style()` を並記した（未使用の別メソッド）。
  既存の `choose_command()` を置き換えて実行し、同一seedで最終ターン数・勝者が一致することを
  手動検証した上でコメントとして残した
- [x] `Battle.roll_damage()`/`calc_damages()`（`battle.py:740,774`、16通りの生ダメージロール）が
  `calc_lethal`の陰に隠れて未紹介
  → 対応内容 (2026-07-12): `examples/04_damage_calculation.py` のどく比較の後ろに、
  `battle.calc_damages(attacker, defender, move_name)` で生ダメージロール16通りをそのまま
  表示し、`battle.roll_damage(...)` で乱数を1つ引いた結果も並べて表示する例を追加した
- [x] `Battle.modify_hp()`/`faint()`/`modify_stats()`（`battle.py:692,725,732`、特定のHP・ランク
  状態からシナリオを組み立てる公開API）が未紹介。CLAUDE.mdの「`Pokemon.hp`に直接代入禁止、
  `modify_hp()`を使う」という内部ルールがexamples読者に伝わらない
  → 対応内容 (2026-07-12): `examples/04_damage_calculation.py` に、`modify_hp(r=-0.6)` で
  防御側のHPを残り40%まで直接減らしてから `calc_lethal(max_attack=1)` を呼び、HP満タン時
  （致死率0.00%）との対比を示す例を追加。続けて `modify_stats(target, {"def": 1})` でぼうぎょ
  ランクを上げると同条件でも致死率が下がる（100.00%→56.25%）ことを示し、最後に `faint()` で
  対象を即座にひんし化する例も添えた
- [x] `BattleOption`の`damage_roll`/`critical_mode`/`double_battle`等のパラメータがexamples全体で
  一度も指定されていない。特に`damage_roll="最大"`+`critical_mode="確定のみ"`は`calc_lethal`と
  並ぶダメージ計算手段として04で紹介する価値が高い
  → 対応内容 (2026-07-12): `examples/04_damage_calculation.py` に、`Battle(..., damage_roll="最大",
  critical_mode="確定のみ")`で構築した別バトルから`roll_damage()`を呼び、通常ロールの最大値と
  一致する最大保証ダメージを一発で得られる代替アプローチを追加した（条件を揃えるため同じ
  こうげき努力値を振っている）
- [x] `Battle.get_event_logs(turn)`（`battle.py:843`、`LogCode`付き構造化ログ）が
  `print_logs`/`get_log_lines`の文字列版の陰で未紹介
  → 対応内容 (2026-07-12): `examples/02_team_battle.py` の勝敗表示の直後に、全ターンの
  `get_event_logs(turn)` を走査して `LogCode.CRITICAL_HIT` のログだけを抽出・表示する例を
  追加した（文字列化済みの`print_logs`とは別に、構造化ログをプログラムで検索する使い方の実演）
- [x] `Pokemon.show()`/`render_info()`（`model/pokemon.py:1076,1098`、状態の整形表示）が未紹介。
  02/04の手書き`print(f"...")`を代替できる
  → 対応内容 (2026-07-12): `examples/04_damage_calculation.py` の`set_evs()`呼び出し直後に
  `attacker.show()`を追加し、こうげき努力値を振った結果をHP・性格・特性・持ち物・テラスタイプ・
  努力値・技構成込みでまとめて確認できる表示例とした（既存の手書きprintは意味を変えず維持）
- [x] `Pokemon.status`/`effects`/`has_ailment()`/`has_volatile()`（状態異常・揮発性状態の読み取り
  API）が未紹介。状態異常を発生させる例が無い以上に、発生を確認する側のAPIも一度も出てこない
  → 対応内容 (2026-07-12): `examples/04_damage_calculation.py` の`set_ailment(plain_defender,
  "どく")`の直後に、`plain_defender.status`（poke-env互換のailment.nameエイリアス）と
  `has_ailment('どく')`で付与結果を確認する1行を追加した
- [x] `Move.expected_hits`（連続技の平均ヒット数）・`Move.is_attack`（03の`base_power or 0`という
  間接的な変化技判定を代替できる直接的なプロパティ）が未活用
  → 対応内容 (2026-07-12): `examples/03_custom_player.py`の`move.base_power or 0`を
  `move.base_power if move.is_attack else 0`に書き換え、意図が読み取りやすい直接的な判定に
  した（挙動は非破壊）。`examples/04_damage_calculation.py`末尾に、連続技「タネマシンガン」
  （2〜5回技）で`Move.expected_hits`（期待ヒット数3.1、単純平均3.5とは異なる）を表示する例を追加した
- [x] `Battle.copy(reseed=True)`（`battle.py:305`、独立乱数系列での複製）・
  `TreeSearchPlayer.configure_sim()`/`opponent_estimator()`（05の発展編になり得る拡張ポイント）・
  `Player.n_tied_battles`/`n_lost_battles`（06の勝率のみ表示を補完）・`Player.add_pokemon()`の
  戻り値活用（控えポケモンへの参照保持）は優先度低だが併せて記録
  → 対応内容 (2026-07-12): 4項目のうち低コストな2件のみ対応。
  (1) `Player.n_lost_battles` を `examples/06_bulk_simulation.py` の勝率表示に追記
  （`{n_won_battles}勝{n_lost_battles}敗/{n_finished_battles}戦`）し、`n_tied_battles` が
  jpokeでは常に0であることのコメントも添えた。
  (2) `Player.add_pokemon()` の戻り値を `examples/06_bulk_simulation.py` の
  `build_player()` で変数に受け、`team[0]` を辿らず直接 `mon.set_evs(...)` で追加設定する例に
  書き換えた（動作・出力は非破壊、努力値を振った分だけこだわりスカーフ側の勝率が変化）。
  `Battle.copy(reseed=True)` と `TreeSearchPlayer.configure_sim()`/`opponent_estimator()` は
  見送った。前者は木探索の内部実装（`TreeSearchPlayer` 自身が既に `battle.copy()` を使っている）
  を05のユーザーコードで再現するには探索フレームワークの内部構造の説明が追加で必要になり、
  後者2つは「相手の合法手が未公開のときの推定」「sim限定オプションの設定」という発展的な
  拡張ポイントで、意味のある実演には05の題材（HPが高いカビゴン同士の総当たり）を作り替える
  必要があり、いずれも「短い追記」の範囲を超えるため今回は見送った

## 教材としての質

- [x] 難易度勾配（01→06）は概ね適切。01/02で進行、03で方策、04で計算、05で探索、06で統計と段階的に積み上がっており、各docstring冒頭の「jpoke で学べること:」統一フォーマットも良い。（対応不要・肯定的所感）
- [x] 04（ダメージ計算）は03（カスタム方策）と05（木探索）のAI系列に割り込む配置。ユースケース別に独立した題材なので現状でも許容だが、AI開発の連続性を優先するなら 03→05 を隣接させ、04を後ろに回す選択肢もある。（見送り確定: フィードバック自身が「現状でも許容」としており、連番・README対応表への影響に見合わないため据え置き。2026-07-12判断）
- [x] 02 のループ内コメント（瀕死→自動交代の説明3行）はループ本体より長く、docstringへ移した方が読みやすい。05 のdocstringは `src/jpoke/players/...` を参照させているが、「clone不要で動く」前提の読者はソースを持っていないため、参照先はGitHub URLかAPIドキュメントにすべき。（→ 2026-07-11 f41f4df5で対応済み）
- [x] 「次に何を試すか」の誘導が弱い。各サンプル末尾に1行の「試してみよう」（例: 01→技を変える、03→評価関数にHP割合を加える、06→n_battlesや構成を変える）があると学習動線が明確になる。（→ 2026-07-11 examples 01〜06全てに追加）
- [x] examples/README.md の対応表（ファイル/学べる内容/ユースケース）は簡潔で分かりやすい。ルートREADMEのユースケース記述と用語（戦術研究・AI開発・ダメージ計算ツール開発）が揃っている点も良い。（対応不要・肯定的所感）
- [x] 06 の `build_player(item_name, item_name)` は username にアイテム名を渡しており、初見では引数の取り違えに見える。`build_player(username=..., item_name=...)` とキーワード渡しにするだけで誤読が消える。（→ 2026-07-11 f41f4df5で対応済み）

## 公開APIの使い勝手

- [x] `Player.team` への追加方法が `.append()`（01,03,05,06）と `= [...]` 代入（02,04）で混在。どちらも動くが教材として一貫性がなく、また `team` が素のlistのため6匹超過などの検証が入らない。`add_pokemon()` 等の正規ルートを1つ定めるか、examples内だけでも書式を統一したい。（→ 2026-07-11/12 `Player.add_pokemon()` を新設し、examples全体で統一）
- [x] `player.team` はコンストラクタ時点のスナップショットで対戦中は更新されず、対戦中の状態は `battle.get_active(player)` で取る必要がある（03のコメントで補足している通り）。「自分のチームなのに戦況が反映されない」のは学習者が最初に踏む罠で、docstringだけでなくAPIリファレンスでの明示が必要。（未対応: examples/03のコード内コメントのみで、`Player.team`属性のdocstring自体には未反映）（→ 2026-07-12 `Player` の `Attributes:` の `team` 説明にスナップショットである旨と `battle.get_active(player)` / `battle.get_team(player)` への誘導を追記）
- [x] 場のポケモンの取得方法が `battle.get_active(player)`（03）と `battle.actives[0]`（04）の2通り登場する。相手チーム参照に至っては `battle.player_states[battle.opponent(self)].team`（05）と内部構造に踏み込んでおり、「外部APIはBattleの公開メソッドを入口にする」方針と齟齬がある。`battle.get_team(player)` のような公開アクセサが欲しい。（→ 2026-07-11 `Battle.get_team()` を新設し、examples全体で`get_active`/`get_team`に統一）
- [x] `Pokemon.__init__` の暗黙デフォルトが多い: `nature="まじめ"`, `level=50`, `move_names` 省略時は `["はねる"]`, `ability_name=""`, IV31/EV0。特に「技を渡さないとはねるになる」「特性が空文字で何になるか」はコードから読み取れず、docstringでの明記かクラスメソッド（例: `Pokemon.simple(...)`）での整理を検討したい。（→ 2026-07-11 docstringに明記して対応。代替コンストラクタは`add_pokemon()`が実質的に代替するため追加実装は見送り）
- [x] `n_selected` のデフォルト3とチーム1匹構成の組み合わせは、01のように毎回 `n_selected=1` を明示する必要がある。省略時に「min(3, len(team))に自動調整」する方が導入体験は滑らか。（→ 2026-07-11 自動調整を実装）
- [x] `Command` から技実体への到達が `mon.moves[command.index]` という2段の間接参照（03）。`command` 自体が技を知らないため学習者が `index` の意味を推測する必要があり、`battle.get_move(command)` のようなヘルパーがあると方策実装が書きやすい。（見送り確定: 優先度メモに含まれず「検討したい」止まりのため、今回は対応しない。2026-07-12判断）
  → **訂正（2026-07-12）**: この見送り判断は誤りだった。`battle.command_to_move(player, command)`（`src/jpoke/core/battle.py:635`、実体は `command_manager.resolve_move_from_command`）が新ヘルパーとして既に公開API化されていたが、見送り判断時に見落としていた。ユーザーが再度同じ指摘をTODOコメントとして書いたことで発覚（下記「3度目のレビュー指摘」参照）。対応不要な新規実装はなく、examples/03を既存APIへ書き換えるだけで解消する

## 既知のバグ・要修正候補

- [x] `Battle(seed=None)` が `int(time.time())`（秒精度）にフォールバックする（`src/jpoke/core/battle.py:155`）。`battle_against(n_battles=30)` をseed省略で呼ぶと30戦全てが同一seedになり勝率が0%/100%に張り付く。対応案: (1) フォールバックを `time.time_ns()` または `Random(None)`（OSエントロピー）に変更、(2) `battle_against` 側で `seed` 指定時は対局ごとに `seed+i` の派生seedを振る。両方入れれば `examples/06` のワークアラウンド（n_battles=1×ループ）を素直な `battle_against(..., n_battles=30)` に書き戻せる。（→ 2026-07-11 `secrets.randbits(32)` に変更 + `battle_against`の対局別seed派生を実装）
- [x] デフォルト `Player.choose_command()` が「利用可能なコマンドの先頭を選ぶ」決定的挙動である点は、seedを変えても同一展開になりやすく、06のような統計比較の分散を殺す方向に働く。ベースラインとしてランダム選択（05の `RandomPlayer` 相当）を標準提供するか、既定挙動をdocstringで強調すべき。（未対応）（→ 2026-07-12 `jpoke.players.RandomPlayer` を新設（`battle.random` ベースで `Battle(seed=...)` の再現性を保つ）。examples/05のローカル定義を置き換え、`Player.choose_command()` のdocstringにも既定実装が決定的である旨と `RandomPlayer` への誘導を追記）

## 優先度メモ

1. [x] **seed フォールバックの修正 + battle_against の対局別seed派生**（上記バグ）。統計的に誤った結果を静かに返す罠であり、examples/06 の注意書きと歪んだ書き方を解消できるため最優先。（→ 2026-07-11 対応済み）
2. [x] **対戦中状態へのアクセスAPI整理**（`get_active` / `actives` / `player_states` の一本化と `get_team` 追加）。教材3本にまたがって説明コメントが必要になっている＝学習コストが最も高い箇所。（→ 2026-07-11 対応済み）
3. [x] **`n_selected` の自動調整（min(3, len(team))）**。全サンプルで `n_selected=1` の明示とコメントが必要になっており、導入の最初の1行目の摩擦を減らせる。（→ 2026-07-11 対応済み）

## 再レビュー指摘（2026-07-12 Fableサブエージェント、PR #38差分）

- [x] `tests/moves_attack/test_move_ha.py` の `test_はたきおとす_相手のアイテムがないとき威力補正なし` が同種のflakiness（急所のブレでダメージ比較が逆転しうる）を持つとMonte Carlo実測（300回中8回失敗）で指摘 → `fix_random()` を追加して解消
- [x] `Battle.roll_damage()` の `int(random() * len(damages))` が `random()==1.0` の境界（一部テストが `battle.random.random = lambda: 1.0` を使用）でIndexErrorになり得ると指摘 → `min(index, len(damages)-1)` のクランプを追加
- [x] `examples/README.md` の01の説明が `Pokemon` importなし化に追従していなかったと指摘 → 修正
- [x] `n_selected` 自動調整のdocstringに「チーム間で手持ち数が異なっても両者に同じ値が適用される」旨の追記が必要と指摘 → 追記
- [x] `battle_against` のdocstringに「複数opponent指定時は対戦通番がopponentごとにリセットされ、同じseed系列を使い回す」旨の追記が必要と指摘 → 追記
- [x] （付随発見・スコープ外）`tests/abilities/test_ability_a.py:667`（いかりのつぼ）で `random()==1.0` 固定時に技自体がミスして意図せず空虚に合格する既存の問題を発見 → 今回の変更が原因ではなく、examples APIフィードバック対応のスコープ外のため見送り確定

## 3度目のレビュー指摘（2026-07-12、ユーザー記入のexamples内TODOコメント + Fableサブエージェント）

ユーザーが教材執筆中に気づいた疑問を `examples/*.py` に直接 `# TODO:` コメントとして書き込んだため、
それをFableサブエージェントにレビューさせ、自身でも実装コードを確認して裏付けを取った。

- [x] `Battle.finished`（`battle.py:868`、poke-env互換プロパティ）は `self.winner is not None` を見るだけで、
  `self.winner` は `judge_winner()` 内でのみ遅延設定・キャッシュされる（`battle.py:171` で初期値 `None`）。
  そのため **`judge_winner()` を一度も呼ばずに `battle.finished` だけを見ると、TODスコアにより実際には
  決着している対戦でも `False` が返り続ける**という潜在バグがある（Fableの指摘を検証し、単なる
  「頑健化した方がよい」ではなく実際の不整合と確認）。`return self.judge_winner() is not None` に
  変更して解消する
  → 対応内容 (2026-07-12): `Battle.finished` を `return self.judge_winner() is not None` に変更した
- [x] 01/03/05で「`battle.start()` → `while judge_winner() is None and turn < N: battle.step()`」という
  ほぼ同一の定型ループが繰り返されている（01 L22/L23/L29の根本原因はこれ）。`Battle.play_out(max_turns=100)
  -> Player | None` のような、最後まで進めて勝者を返す便宜メソッドを追加する。`Player.battle_against()`
  内部ループもこれに置き換えられる。01は「手動でstep()する」ことを学ぶ教材のため、ループ自体は残しつつ
  `battle.finished` を使う形に簡素化する（`play_out()` の存在は末尾コメント等で軽く触れる程度に留める）
  → 対応内容 (2026-07-12): `Battle.play_out(max_turns=100) -> Player | None` を新設し、
  `Player.battle_against()` の内部ループを置き換えた。01/03/05は `while battle.judge_winner() is None`
  を `while not battle.finished` に変更（01はループ自体は維持し、末尾に `play_out()` へのコメントを追加）
- [x] 02の「ループ条件で `judge_winner() is None` を見た直後、ループを抜けてから再度 `judge_winner()` を
  呼ぶ」二重呼び出し（L38）は、`battle.finished` / `battle.winner` を使えば1回の呼び出しで済み解消する
  （上記2項目とセットで対応）
  → 対応内容 (2026-07-12): ループ条件を `not battle.finished` に、ループ後の `judge_winner()` 再呼び出しを
  `battle.winner` 参照に変更し、該当TODOコメントを削除した
- [x] `battle.print_logs(turn)` / `get_log_lines(turn)` は指定ターン（省略時は現在ターン）のみを返すため、
  01で「決着までの全ターンのログを見たい」（L37）にはユーザー側でforループが必要になる。
  `turn: int | None | Literal["all"]` を受け付け、`"all"` で1ターン目〜現在ターンを一括出力できるようにする
  （既存の `None`＝現在ターンの意味は変更しない。02のターンごと出力は非破壊）
  → 対応内容 (2026-07-12): `get_log_lines`/`print_logs` の `turn` を `int | None | Literal["all"]` に拡張し、
  `"all"` 指定時は1ターン目から現在ターンまでの全ログを返すようにした。01の `battle.print_logs()` を
  `battle.print_logs("all")` に変更し、該当TODOコメントを削除した
- [x] `Command` から技実体への到達（03 L25、`mon.moves[command.index]`）は、既に公開済みの
  `battle.command_to_move(player, command)` で解決できる。新規実装は不要で、
  `examples/03_custom_player.py` を書き換えるだけでよい（→ 上記「公開APIの使い勝手」節の訂正参照）
  → 対応内容 (2026-07-12): `examples/03_custom_player.py` の `mon.moves[command.index]` を
  `battle.command_to_move(self, command)` に書き換え（未使用になった `mon` 変数も削除）、該当TODOコメントを
  削除した。`Battle.command_to_move` のdocstringに用途（方策実装でコマンドから技を引く）を追記した
- [x] `Battle.calc_lethal`（`battle.py:352`）に **docstring が一切ない**（委譲先の `core/lethal.py:157`
  にはある）。戻り値 `list[LethalResult]` の構造（1要素=1ヒット、`hp_dist`はそのヒット適用後のHP分布、
  最終致死率は `results[-1].lethal_probability`）が呼び出し側から読み取れない（04 L38の指摘）。
  `Battle.calc_lethal` にdocstringを追加して解消する
  → 対応内容 (2026-07-12): `Battle.calc_lethal` に、戻り値の構造（1要素=1ヒット、`hp_dist` はそのヒット
  適用後のHP分布、最終致死率は `results[-1].lethal_probability`）を明記したdocstringを追加した
- [x] `calc_lethal(moves=...)` が `Move` インスタンスを要求し、`Move(move_name)` のラップが必要（04 L27）。
  `moves` の型を `MoveName | Move | tuple[MoveName | Move, int] | list[...]` に広げ、文字列なら内部で
  `Move(name)` に正規化する（既存呼び出しは非破壊）
  → 対応内容 (2026-07-12): `Battle.calc_lethal` / `core.lethal.calc_lethal` の `moves` 型を
  `MoveName | Move | tuple[MoveName | Move, int] | list[...]` に拡張し、文字列は内部で `Move(name)` に
  正規化するようにした（`Move` インスタンス渡しの既存挙動は非破壊）。`examples/04_damage_calculation.py` の
  `moves=Move(move_name)` を `moves=move_name` に変更し、未使用になった `Move` importと該当TODOコメントを
  削除した
- [x] `Battle.__init__(players: tuple[Player, ...], ...)` はタプルで渡す必要があり、`Battle((player1,
  player2), seed=1)` という二重括弧が初見で読みにくい（01 L21）。呼び出し箇所を全リポジトリ検索した結果
  位置引数でのタプル外の渡し方は存在せず、`Player.battle_against(*opponents, ...)` は既に可変長引数化
  されている。`Battle.__init__(self, *players: Player, n_selected=None, ...)` に変更し、
  `Battle(player1, player2, seed=1)` と書けるようにする（内部呼び出し・examples・scripts・testsの
  該当16ファイルを合わせて修正するため、破壊的変更としてCHANGELOGに明記する）
  → 対応内容 (2026-07-12): `Battle.__init__` を `*players: Player` の可変長引数に変更した。
  リポジトリ全体を再検索した結果、当初想定の16ファイルに加えて `Battle(players, ...)` /
  `Battle([p0, p1], ...)` / `Battle(tuple(players), ...)` のようにタプル/リストを事前に組み立てて
  渡す非明示的なパターンが `tests/test_utils.py`・`tests/test_fuzz_regressions.py`・
  `tests/test_replay_fuzz.py`・`src/jpoke/core/replay.py`・`scripts/random_1on1.py`・
  `scripts/fuzz_battle.py`・`scripts/replay_fuzz_battle.py`・`scripts/janken_nash.py` の8ファイルにも
  見つかり、全て `Battle(*players, ...)` 形式に修正した（合計24ファイルを修正）。
  破壊的変更として `CHANGELOG.md` の `### Changed` に明記した
- [x] 05の `KOFocusedPlayer("TreeSearchAI", max_plies=1, max_nodes=50)` は `max_plies` が変更可能な
  パラメータであることが伝わりにくい（L18）。API変更は不要で、行コメント（`max_plies=2にすると相手の
  応手まで読む。分岐は自手数×相手手数で乗算的に増える`、等）と「試してみよう」への追記で解消する
  → 対応内容 (2026-07-12): `KOFocusedPlayer(...)` 行の直前に `max_plies` の意味と増やした場合の
  分岐増加について行コメントを追加し、「試してみよう」に `max_plies` を変えて `nodes_expanded`
  （展開ノード数）の変化を比較する誘導を追記した。あわせて、同趣旨の解消済みTODOコメント
  （「ユーザーからは木探索の深さ設定が見えてこない。」）を削除した
- [x] 02のRandomPlayer化（L10）: 01は1体・1技構成で選択の余地がなくRandomPlayer化しても観測できる差が
  ないため見送り、最小構成のPlayerのまま維持する。02は3体チームで瀕死時の交代コマンドに複数の選択肢が
  あるため、両陣営をRandomPlayerにすると「瀕死→自動交代」のシナリオがより実戦的になる。examples限定の
  軽微な変更として対応する
  → 対応内容 (2026-07-12): `examples/02_team_battle.py` の Team A / Team B を `Player` から
  `jpoke.players.RandomPlayer` に変更し、`from jpoke import Battle, Player` の `Player` importを
  削除して `from jpoke.players import RandomPlayer` を追加した。docstringの
  「既定の `Player.choose_command()` は...」という記述を実態（両陣営とも RandomPlayer を使うため、
  交代コマンドの選択肢が複数あるときはランダムに選ばれる）に合わせて更新し、02側の解消済みTODO
  （「RandomPlayer を使う。」）を削除した。01は本項目の分析どおり変更せず、01側のTODOコメントも
  そのまま残した（見送り確定のため）
- [x] 技名のひらがな入力対応（02 L14、"ぎがどれいん"→"ギガドレイン"）は、`MoveName` Literalの拡張が
  技以外（ポケモン名・特性名・アイテム名）にも波及する広範な変更のため見送り確定。代替として
  `MOVES[name]` のKeyError時にdifflibで近い技名候補を提示するエラーメッセージ改善は費用対効果が
  見合うが優先度は低く、今回は見送り（気になれば別途着手）
- [x] `TreeSearchPlayer` を `MinimaxPlayer` に改名する案（05 L17）は、本クラスがミニマックスだけでなく
  `max_nodes`打ち切り・`fallback`・`opponent_estimator`・`configure_sim`を備えた探索フレームワーク基底
  であるため見送り確定。改名はscripts/tree_search/・tests・docsへの波及が大きく、実態（探索フレームワーク）
  ともTreeSearchの方が合っている
- [x] 01 L26 `# TODO: start()が` は文が途中で切れており意図不明で **ユーザーに確認が必要**としていたが、
  その後ユーザーが記入を完成させ「`# TODO: ユーザー視点だとstart()で何をしているのかわからない`」で
  確定した。`battle.start()` の呼び出し1行だけでは「選出と初期繰り出しを行う」ことが教材コードから
  読み取れない、という指摘。`Battle.start()` 自体のdocstringには既に説明があるため、examples/01側に
  コメントを1行添えるだけで解消できる（API変更は不要）
  → 対応内容 (2026-07-12): `examples/01_quickstart.py` の `battle.start()` 呼び出し行の直前に、
  `Battle.start()` のdocstringを踏まえた説明コメント（`# 選出と初期繰り出しを行い、対戦を開始する`）を
  追加し、該当TODOコメントを削除した

## 4度目のレビュー指摘（2026-07-12、jpoke内部実装を知らない設定のsonnetサブエージェント + Fable本体の検証）

`src/jpoke/` 配下を一切読ませず、poke-env経験者・jpoke初見という設定のsonnetサブエージェントに
`README.md`・`examples/` のみを見せてレビューさせた。指摘の中に「`examples/02_team_battle.py` を
実行すると両陣営が終盤ずっと交代コマンドだけを選び続け、二度と技を出さないまま30ターン打ち切りになる」
という重大な指摘があり、Fable本体が `src/jpoke` 側を調査して原因を特定した。

- [x] **【重大・バグ】`Player.choose_command()` に渡される観測用コピー（`Battle.build_observation()`
  が返す `sim`）の `random` が本体の `battle.random` から独立した deepcopy のスナップショットに
  なっており、`RandomPlayer`（`battle.random.choice(...)` を使う）が `sim.random` を消費しても
  本体側の `battle.random` の状態が一切進まない。デバッグ実行で `battle.random.getstate()` を
  ターンごとに出力したところ、ターン2以降まったく同じ状態のまま固定されることを確認した
  （`src/jpoke/core/battle.py:330` `build_observation()` → `observation_builder.build()`
  → `new = deepcopy(battle)` で `random` も複製される）。技を使わず交代だけが選ばれ続けるターンでは
  `battle.random` がどこからも消費されないため、`build_observation()` は毎ターン全く同じ乱数状態
  から `sim` を作り直すことになり、`sim.random.choice(candidates)` は毎回同じ選択肢を返し続ける。
  結果として「交代を選ぶ→技を使わないので本体のrandomが進まない→次のターンも同じ状態からsimが
  作られ同じ選択が繰り返される」という無限ループに陥る。`examples/02_team_battle.py`
  （`seed=1,2,3,5`）で再現し、`seed=4` のみ他の理由で早期決着していた。
  - `src/jpoke/players/tree_search_player.py` の `TreeSearchPlayer` は探索用に
    `battle.copy()`（`reseed`省略でFalse、独立した`random`のdeepcopy）を明示的に使っており、
    これは意図した設計（探索中の乱数消費が本体を汚染しないようにするため）。しかし
    `TreeSearchPlayer.fallback()`（`_toplevel_commands` で相手コマンドが未公開の場合に呼ばれる）は
    探索の最上位で `build_observation()` が返す最初の `battle`（＝観測用コピー）に対して
    `battle.random.choice(...)` を呼ぶため、こちらも同様に本体の `battle.random` を進められない
    経路になっている
  - 影響箇所は `src/jpoke/core/command_manager.py:178`（`resolve_command` の行動コマンド選択）と
    `src/jpoke/core/turn_controller.py:99`（`_run_selection` の選出）の両方で、
    `battle.build_observation(player)` を経由する全ての `choose_command` / `choose_selection` 呼び出し
  - 修正方針案: `src/jpoke/core/observation_builder.py` の `build()` 内、`new = deepcopy(battle)` の
    直後に `new.random = battle.random`（deepcopyされた複製を捨て、本体と同一のオブジェクト参照に
    差し替える）とすることで、`choose_command`/`choose_selection` 内での乱数消費が本体の
    `battle.random` にも反映されるようにする。`Battle.build_observation()` のもう一方の分岐
    （`self.is_observation()` が真の場合の `return self.copy()`）は探索中の内部シミュレーション
    （`self` が既に本体から切り離された `sim`）向けであり、ここは変更不要（`self.random` を
    そのまま複製すればよい。木探索の各分岐が独立した乱数系列を持つという既存の意図を壊さない）
  - 検証すべき影響範囲: (1) `TreeSearchPlayer` の探索結果が変わらないこと（`sim = battle.copy()` は
    `build_observation()` を経由しないため無関係のはず）、(2) `Battle.replay` 機能（`command_log` に
    記録済みのコマンドを再生する経路）が `random` の消費状況に依存していないか、(3) 修正後に
    `examples/02_team_battle.py` を `seed=1〜10` 程度で実行し、無限交代ループが再現しないこと、
    (4) 既存の乱数依存テスト（`fix_random()` 使用箇所含む）がフルスイートで全件成功すること
  - 再現用の最小デバッグコード（サブエージェントへの指示に転記）:
    ```python
    from jpoke import Battle
    from jpoke.players import RandomPlayer
    player1 = RandomPlayer("Team A")
    player1.add_pokemon("ピカチュウ", move_names=["かみなり"])
    player1.add_pokemon("ヒトカゲ", move_names=["かえんほうしゃ"])
    player1.add_pokemon("フシギダネ", move_names=["ギガドレイン"])
    player2 = RandomPlayer("Team B")
    player2.add_pokemon("ゼニガメ", move_names=["なみのり"])
    player2.add_pokemon("コラッタ", move_names=["すてみタックル"])
    player2.add_pokemon("ピッピ", move_names=["ムーンフォース"])
    battle = Battle(player1, player2, seed=1)
    battle.start()
    for t in range(10):
        print(t + 1, battle.random.getstate()[1][:3])
        battle.step()
    # 修正前: ターン2以降 getstate() が完全に固定されたまま変化しない
    ```
  → 対応内容 (2026-07-12): `src/jpoke/core/observation_builder.py` の `build()` 内、
  `new = deepcopy(battle)` の直後に `new.random = battle.random` を追加し、
  deepcopyされた複製を捨てて本体と同一のオブジェクト参照に差し替えた。
  `self.is_observation()` が真の場合に `self.copy()` を返すもう一方の分岐
  （`TreeSearchPlayer` の探索用 `sim = battle.copy()`）は変更していない。
  `tests/test_poke_env_compat.py` に回帰テストを2件追加した
  （観測用コピーの `random` が本体と同一オブジェクトであることの検証、および
  バグ報告の再現条件（3体チーム・両陣営RandomPlayer、seed=1,2,3,5）で技コマンドが
  実際に選ばれた上で30ターン以内に決着することの検証）。フルテストスイート
  （4831 passed, 1 skipped）で回帰がないことを確認し、`examples/02_team_battle.py` を
  seed=1〜10で実行して無限交代ループが再現しないこと・技コマンドが使われることを
  目視確認した

- [x] **【設計見直し・PR #45への追加修正】上記の `new.random = battle.random` という修正には、
  ユーザー指摘により重大な副作用があると判明した：観測用コピー（`sim`）のゲーム進行用 `random` を
  本体と同一オブジェクトにしたことで、`Player.choose_command(sim)` の中で方策が `sim.random` を
  直接触ると、本来はその後の技実行（ダメージロール・命中判定・急所判定等）で消費されるはずだった
  乱数列を、行動選択の時点で先取り・消費できてしまう。例えば方策が `sim.random.random()` を覗いて
  から行動を決めるような実装をすれば、「これから打つ技が急所に当たるかどうか」を実行前に知った
  上で行動を選べてしまう（観測者が未来の乱数を予知できる、チート的先読みが可能になる）。これは
  無限交代ループより深刻な設計上の欠陥であり、「行動選択に使う乱数」と「ゲーム進行に使う乱数」を
  そもそも同じ `battle.random` に押し込めたことが根本原因
  - 修正方針: `Battle` に行動選択専用の乱数生成器 `decision_random`（`battle.seed` から派生した
    別シードで初期化。`Battle.copy(reseed=True)` が `hash((self.seed, self._reseed_count))` で
    派生シードを作っている方式を参考にする）を新設する。`RandomPlayer.choose_command()` と
    `TreeSearchPlayer.fallback()` は `battle.random.choice(...)` ではなく
    `battle.decision_random.choice(...)` を使うように変更する。`observation_builder.build()` では
    `decision_random` だけを本体と同一参照で共有し（無限ループの再発を防ぐ）、ゲーム進行用の
    `random` は今回のPR #45の変更を巻き戻して元通り独立コピー（deepcopy）に戻す（＝先読み不可能に
    戻す）。`Battle.copy(reseed=True)`（木探索の意図的な系列分離用）でも `decision_random` を
    同様に派生シードで再初期化し、既存の `random` と同じ扱いにする
  - 影響範囲: `RandomPlayer`（`src/jpoke/players/random_player.py`）・`TreeSearchPlayer.fallback`
    （`src/jpoke/players/tree_search_player.py:90`）のdocstring更新（`battle.random` への言及を
    `battle.decision_random` に修正）、`PR #45で追加した回帰テスト2件`
    （`test_observation_randomは本体のbattle_randomと同じ参照を共有する` は
    `decision_random`が共有され`random`は共有されない、という検証に書き換える。
    `test_無限交代ループの再現条件下でもコマンドが技を含んで決着する` は変更なく通るはず）、
    `Battle.__init__` のdocstring・`docs/spec/` 配下に乱数系列の説明があれば更新
  - 検証すべき影響範囲: (1) `examples/02_team_battle.py` をseed=1〜10で再実行し無限交代ループが
    再発しないこと、(2) `sim.random is not battle.random`（先読み不可能）かつ
    `sim.decision_random is battle.decision_random`（無限ループ対策）の両方が成り立つこと、
    (3) `TreeSearchPlayer` の探索結果・決定論性が変わらないこと、(4) フルテストスイート全件成功
  → 対応内容 (2026-07-12): `Battle.__init__`（`src/jpoke/core/battle.py`）に
    `self.decision_random = Random(hash((self.seed, "decision")) & 0xFFFFFFFF)` を新設し、
    `_EXTRA_DEEPCOPY_KEYS` に追加、`Battle.copy(reseed=True)` でも派生シードで再初期化するように
    した。`src/jpoke/players/random_player.py` の `RandomPlayer.choose_command()` と
    `src/jpoke/players/tree_search_player.py` の `TreeSearchPlayer.fallback()` を
    `battle.decision_random.choice(...)` に変更（docstringも修正）。
    `src/jpoke/core/observation_builder.py` の `build()` から `new.random = battle.random` を削除し
    （ゲーム進行用randomは元通り独立deepcopyに戻した）、代わりに
    `new.decision_random = battle.decision_random` を追加した。`tests/test_poke_env_compat.py` の
    回帰テストを `test_observationのdecision_randomは共有されrandomは独立している`
    （`sim.random is not battle.random` かつ `sim.decision_random is battle.decision_random` を検証）
    に書き換え、`test_無限交代ループの再現条件下でもコマンドが技を含んで決着する` は変更なく
    通ることを確認した。`examples/02_team_battle.py` をseed=1〜10で実行し全て30ターン以内に
    技コマンドを使って決着すること・`tests/test_tree_search_framework.py` 11件全件成功・
    フルテストスイート（4831 passed, 1 skipped、既存ベースラインと同数）を確認した

- [x] **教材カバレッジ不足**: 同サブエージェントに、「README『実装状況』の規模（特性310・アイテム247・
  技733・揮発性状態66・場の効果31）に対して、examplesのどのサンプルにも一度も登場しない主要概念」を
  追加調査させたところ、以下が判明した（`src/jpoke` は見せずexamples/READMEのみから調査させたが、
  Fable本体が該当APIの実在をコード側で裏付け済み）：
  - **EV/IVを設定する手段がexamplesに一度も登場しない**。`Pokemon.__init__`/`Player.add_pokemon()`は
    `gender/nature/level/ability_name/item_name/move_names/tera_type`のみで、EV/IVはコンストラクタ引数
    にない。ただし`Pokemon.set_evs(evs, hp_policy=...)`/`Pokemon.set_ivs(ivs, hp_policy=...)`という
    正規のインスタンスメソッドが既に存在する（`src/jpoke/model/pokemon.py:624,650`）。ダメージ計算
    ツール開発ユースケースを掲げる04がまさにEV/IVを振った実数値でこそ効果を発揮する場面なのに、
    一度も使われていない
  - 特性（`ability_name`）がexamples全体で一度も指定されず、ダメージ計算・行動選択への影響が
    一度も見せられていない
  - 天候・地形・状態異常（どく・やけど等の意図的な発生）・交代誘発技（とんぼがえり等）・
    設置技・先制/素早さ操作技・わるあがき（PP切れ）がexamples全体で一度も登場しない
  - テラスタルを能動的に選ぶ方法（`Command.get_terastal_command()`相当）や、交代コマンドを
    明示的に組み立てる方法がexamplesのどこにも示されていない
  - （対応不要・見送り）EV/IV以外の項目は「新規サンプルの追加」が必要な範囲が広く、
    今回のバグ修正（上記random共有）を優先。教材拡充は別タスクとして後日改めて着手する
  → 対応内容 (2026-07-12): EV/IVの実演のみ最小コストで価値が高いため、
    `examples/04_damage_calculation.py` の攻撃側ガブリアスに `mon.set_evs([0, 32, 0, 0, 0, 0])`
    （こうげき努力値をChampions形式で最大まで振る）を追加し、こうげき実数値の表示と
    「無振りより確定数・致死率が高くなる」旨のコメントを添えた（他の未カバー項目は見送り、上記の通り）

### 追加の気づき（Fableサブエージェントの指摘、対応不要）

- `RandomPlayer` は `jpoke.players` 経由でのみ提供され、トップレベル `jpoke` からは未エクスポート。
  ただし `TreeSearchPlayer` 等の既存のPlayer派生クラスも同様の扱いのため、既存の設計方針との整合が
  取れており対応不要と判断

## 実施記録（詳細ログ）

### 2026-07-11 実装（優先度メモ1〜3 + 教材としての質）

- `Battle(seed=None)` のフォールバックを `secrets.randbits(32)`（OSエントロピー）に変更。
  `Player.battle_against(..., seed=...)` は対戦ごとに `seed + 対戦通番` の派生シードを
  自動的に使うよう変更し、examples/06 のワークアラウンド（seedを手動でずらすループ）を
  `battle_against(..., n_battles=N, seed=1)` の素直な呼び出しに戻した
  - 副作用として、`Battle.roll_damage()` の通常ロール抽選が `random.choice()`
    （`getrandbits()` 依存）だったため、テストヘルパー `fix_random()`（`random()` のみ固定）
    では制御できず、seedの高エントロピー化により一部テストが乱数依存で不安定化することが
    判明した。`roll_damage()` の抽選を `random.random()` ベースに変更し、`fix_random()` で
    完全に制御できるようにして解消（`tests/moves_attack/test_move_ma.py` の1件は
    `fix_random()` 追加で対応）
  - さらに `critical_mode="確定のみ"` は「急所を確定させる」設定ではなく「急所レート
    計算を特性等の割り込みなしの基礎値のみにする」設定で、急所に当たるか自体は
    引き続き `random.random()` の実ロールに依存すると判明。`damage_roll="最大"` /
    `critical_mode="確定のみ"` だけに頼り `fix_random()` を使っていなかった
    `test_move_ta.py`（DDラリアット×2）・`test_move_sa.py`（ソーラービーム×2）の
    比較系テストが急所のブレで偶発的に失敗し得たため、`fix_random()` を追加して解消。
    フルテストスイートを10回超連続実行して再発しないことを確認済み
- `Battle(n_selected=None)` を `min(3, 各プレイヤーの手持ち数)` に自動設定するよう変更。
  全examplesから冗長な `n_selected=1`/`n_selected=3` の明示を削除
- `Battle.get_team(player)` を追加し、examples/05 の
  `battle.player_states[battle.opponent(self)].team` を置き換え。examples/04 の
  `battle.actives[0]` も `battle.get_active()` に統一
- 各サンプル末尾に「試してみよう」の1行コメントを追加（01/02/03/04/05/06）
- `Player.team` への追加方法を `.append()` に統一（02, 04 の `= [...]` 代入を書き換え）
- `Pokemon.__init__` のdocstringに暗黙のデフォルト（性格・レベル・特性・技・個体値/努力値）を明記
- ユーザー指摘により、`Player.add_pokemon(name, **kwargs)` を新設。`Pokemon` を直接
  importせずにチームを組めるようにし、examples全体で `from jpoke import ... Pokemon` の
  importと `team.append(Pokemon(...))` を置き換えた（教材としての質・公開APIの使い勝手
  双方の指摘に対応）
- 04の防御側表示も `defender_player.team[0]` から `battle.get_active(defender_player)` に統一

### 2026-07-12 再レビュー対応

PR #38 の差分に対して再度Fableモデルでレビューを受け、上記「再レビュー指摘」の内容を修正した。

### 2026-07-12 残り2項目の実装（`player.team`スナップショット警告 + `RandomPlayer`新設）

- `Player`（`src/jpoke/core/player.py`）の `Attributes:` の `team` 説明に、対戦中は
  更新されないスナップショットであることと、対戦中の実際の状態は
  `battle.get_active(player)` / `battle.get_team(player)` を使うべき旨を追記
- `src/jpoke/players/random_player.py` に `RandomPlayer(Player)` を新設。
  `battle.random.choice(battle.get_available_commands(self))` で選ぶ実装で、
  `examples/05_tree_search_ai.py` に元々ローカル定義されていたものと同等
  （`battle.random` を使うため `Battle(seed=...)` の再現性を壊さない）
- `src/jpoke/players/__init__.py` に `RandomPlayer` を追加してエクスポート
- `Player.choose_command()` のdocstringに、既定実装が決定的（常に先頭のコマンドを
  選ぶ）である旨と、統計比較などで分散が必要な場合は `jpoke.players.RandomPlayer`
  を使うとよい旨を追記
- `examples/05_tree_search_ai.py` のローカル `RandomPlayer` 定義を削除し、
  `from jpoke.players import RandomPlayer` に置き換え（未使用になった `Player` /
  `Command` importも削除）
- `CHANGELOG.md` の `[Unreleased]` / `### Added` に `RandomPlayer` の追加を記載
- `tests/test_poke_env_compat.py` に `RandomPlayer` のテストを2件追加
  （選択コマンドが常に `get_available_commands()` に含まれること、
  `battle.random` 経由で同一seedなら同一コマンド列を再現すること）。
  `scripts/sort_tests.py` / `scripts/generate_test_list.py` を実行し、
  フルテストスイートを3回連続実行して全件成功・非flakyを確認済み
  （worktree分離環境ではeditable installが別チェックアウトの`src`を指すため、
  `tests/test_examples_smoke.py`（サブプロセス起動によるスモークテスト）を
  検証する際は `PYTHONPATH=<worktree>/src` を明示してworktree内の実装を
  優先させる必要があった。mainマージ後は不要な手当て）

### 2026-07-12 3度目のレビュー対応（一部）

「3度目のレビュー指摘」のうち、`Battle.finished`・`play_out()`・ループ簡素化・
`print_logs`/`get_log_lines`の`turn="all"`対応・`command_to_move()`活用・
`calc_lethal`のdocstring・`calc_lethal`の技名文字列対応の7項目に対応した
（`Battle.__init__`可変長引数化、05のmax_pliesコメント、02のRandomPlayer化、
01 L26の意図不明TODOはこのタスクの対象外として触れていない）。

- `Battle.finished` を `self.winner is not None` から `self.judge_winner() is not None`
  に変更。`judge_winner()`未呼び出しのままTODスコアで決着した対戦を見逃さないようにした
- `Battle.play_out(max_turns=100) -> Player | None` を新設し、
  `start()` → `while not battle.finished and battle.turn < N: battle.step()` という
  定型ループを1メソッドに集約。`Player.battle_against()` の内部ループをこれに置き換えた
- `examples/01_quickstart.py`: ループ条件を `not battle.finished` に、
  `winner = battle.judge_winner()` を `winner = battle.winner` に変更。手動`step()`を
  学ぶ教材のためループ自体は維持し、末尾に `play_out()` の存在を一言だけ添えるコメントを追加。
  `battle.print_logs()` を `battle.print_logs("all")` に変更。対応済みTODO
  （step()の戻り値をbool化する案、全ターンログ表示）を削除
- `examples/02_team_battle.py`: ループ条件を `not battle.finished` に変更し、
  ループ後の二重 `judge_winner()` 呼び出しを `battle.winner` 参照に変更。該当TODOコメントを削除
- `examples/05_tree_search_ai.py`: ループ条件を `not battle.finished` に変更
- `Battle.get_log_lines` / `Battle.print_logs` の `turn` を `int | None | Literal["all"]` に拡張。
  `"all"` 指定時は1ターン目から現在ターンまでの全ログをターン番号昇順で返す
  （既存の `None`＝現在ターンの挙動は変更なし）
- `examples/03_custom_player.py`: `mon.moves[command.index]` を
  `battle.command_to_move(self, command)` に書き換え（未使用になった `mon` 変数を削除）。
  該当TODOコメントを削除。`Battle.command_to_move` のdocstringに用途を一言追記
- `Battle.calc_lethal` に、戻り値 `list[LethalResult]` の構造
  （1要素=1ヒット、`hp_dist`はそのヒット適用後のHP分布、最終致死率は
  `results[-1].lethal_probability`）を明記したdocstringを追加
- `Battle.calc_lethal` / `core.lethal.calc_lethal` の `moves` 引数の型を
  `MoveName | Move | tuple[MoveName | Move, int] | list[...]` に拡張し、文字列は内部で
  `Move(name)` に正規化するようにした（既存の `Move` インスタンス渡しは非破壊）。
  `examples/04_damage_calculation.py` の `moves=Move(move_name)` を `moves=move_name` に変更し、
  未使用になった `Move` importと該当TODOコメントを削除
  - 実装中に発見: `core/lethal.py` のトップレベルで `from jpoke.model import Move` すると、
    `jpoke.data.ability` が `jpoke.core.lethal.LethalHandler` を import する経路と衝突して
    循環importになった（`fix/circular-import-fragility` と同種の問題）。`Move` の import を
    実際に文字列を変換する箇所（`_generate_move_list` 内の `to_move`）まで遅延させて解消した
- `CHANGELOG.md` の `[Unreleased]` に Added（`play_out()`）・Changed（`calc_lethal`の技名文字列対応、
  `print_logs`/`get_log_lines`の`turn="all"`対応）・Fixed（`Battle.finished`の不整合修正）を追記
- フルテストスイート（`python -m pytest tests/ -q`）4829 passed, 1 skipped を確認。
  `tests/test_examples_smoke.py` も個別に実行し6件全てPASSEDを確認。examples 01〜05を
  実際に実行し、`print_logs("all")` の全ターン出力・`command_to_move()`・技名文字列指定の
  `calc_lethal` がいずれも意図通り動作することを目視でも確認した

### 2026-07-12 3度目のレビュー対応（残り4項目）

前回の対応で対象外としていた `Battle.__init__` 可変長引数化・05のmax_pliesコメント・
02のRandomPlayer化・01 L26のstart()説明コメントの4項目に対応した。

- `Battle.__init__(self, players: tuple[Player, ...], ...)` を `Battle.__init__(self, *players:
  Player, ...)` に変更（`self.players: tuple[Player, ...] = players` は可変長引数がタプルとして
  受け取れるため変更不要）。呼び出し箇所を全リポジトリ検索した結果、当初想定していた
  `Battle((p1, p2), ...)` という直接的な二重括弧パターン（examples 01〜05・README・
  scripts/lethal_calc.py・scripts/tree_search/tree_search_1〜4.py・
  docs/poke-env/compat_plan.md・docs/plan/poke-env/poke_env_battle_converter.md・
  tests/test_poke_env_compat.py・tests/test_tree_search_framework.py・
  src/jpoke/core/player.py の16ファイル）に加えて、事前に組み立てたタプル/リスト変数を
  そのまま渡す非明示的なパターン（`Battle(players, ...)` / `Battle([p0, p1], ...)` /
  `Battle(tuple(players), ...)`）が `tests/test_utils.py`・`tests/test_fuzz_regressions.py`・
  `tests/test_replay_fuzz.py`・`src/jpoke/core/replay.py`・`scripts/random_1on1.py`・
  `scripts/fuzz_battle.py`・`scripts/replay_fuzz_battle.py`・`scripts/janken_nash.py` の
  8ファイルにも見つかったため、すべて `Battle(*players, ...)` / `Battle(p1, p2, ...)` の
  個別・展開引数渡しに書き換えた（合計24ファイル）。破壊的変更として `CHANGELOG.md` の
  `### Changed` に明記した
- `examples/05_tree_search_ai.py`: `KOFocusedPlayer(...)` の直前に `max_plies` の意味と
  増やした場合の分岐増加について行コメントを追加し、「試してみよう」に `max_plies` を
  変えて `nodes_expanded` を比較する誘導を追記。解消済みだった同趣旨のTODOコメントを削除
- `examples/02_team_battle.py`: Team A / Team B を `Player` から `jpoke.players.RandomPlayer`
  に変更し、docstringの記述も実態に合わせて更新。01は見送り方針どおり変更していない
- `examples/01_quickstart.py`: `battle.start()` 呼び出しの直前に `Battle.start()` の
  docstringを踏まえた説明コメントを追加し、該当TODOコメントを削除
- フルテストスイート（`.venv/Scripts/python.exe -m pytest tests/ -q`）4829 passed, 1 skipped
  を確認。`tests/test_examples_smoke.py` も個別に実行し6件全てPASSEDを確認。
  examples 01〜05および変更した scripts（lethal_calc.py・tree_search_1〜4.py・
  janken_nash.py・random_1on1.py・fuzz_battle.py・replay_fuzz_battle.py）を実際に実行し、
  `Battle` の可変長引数呼び出しがいずれもエラーなく動作することを確認した

### 2026-07-12 4度目のレビュー対応（observation randomの共有バグ修正 + EV/IV教材追加）

「4度目のレビュー指摘」の重大バグ（無限交代ループ）と、追加依頼のあった教材カバレッジ
不足（EV/IV）の2項目に対応した。sonnetサブエージェント（`isolation: "worktree"`）に
委任して実装・検証した。

- `src/jpoke/core/observation_builder.py` の `build()` 内、`new = deepcopy(battle)` の
  直後に `new.random = battle.random` を追加。観測用コピー（`sim`）の乱数生成器を
  deepcopyされた独立インスタンスではなく本体と同一のオブジェクト参照に差し替えることで、
  `RandomPlayer` 等が `sim.random` を消費した際に本体の `battle.random` にも反映される
  ようにした。`Battle.build_observation()` のもう一方の分岐（`is_observation()` が真の
  場合の `self.copy()`、`TreeSearchPlayer` の探索用シミュレーション向け）は意図的に
  変更していない
- `tests/test_poke_env_compat.py` に回帰テストを2件追加:
  `test_observation_randomは本体のbattle_randomと同じ参照を共有する`
  （`sim.random is battle.random` を直接検証）、
  `test_無限交代ループの再現条件下でもコマンドが技を含んで決着する`
  （バグ報告の再現条件そのまま、seed=1,2,3,5で技コマンドの使用と30ターン以内の決着を検証）。
  `scripts/sort_tests.py` / `scripts/generate_test_list.py` を実行
- `examples/04_damage_calculation.py`: 攻撃側ガブリアスに
  `attacker.set_evs([0, 32, 0, 0, 0, 0])`（こうげき努力値をChampions形式で最大まで振る）を
  追加し、こうげき実数値の表示（`攻撃側: ガブリアス（ドラゴンテール, こうげき実数値 182）`）と
  「無振りより確定数・致死率が高くなる」旨のコメントを追加。実行結果は無振り時の確定数3から
  2に短縮されることを確認した
- 影響範囲の確認: `tests/test_tree_search_framework.py`（木探索の決定論性）・
  `tests/test_replay_fuzz.py` / `tests/test_fuzz_regressions.py`（リプレイ再生）・
  `tests/test_observation.py`（情報隠蔽）を個別実行し全件成功を確認。
  `ReplayPlayer.choose_command()` は渡された `battle`（sim）を一切参照せず記録済み
  コマンドをそのまま払い出す実装のため、`sim.random` の共有化とは無関係であることを
  コードで確認した
- フルテストスイート（`.venv/Scripts/python.exe -m pytest tests/ -q`）4831 passed, 1 skipped
  を確認（回帰テスト2件分の純増）。`examples/02_team_battle.py` をseed=1〜10で実行し、
  修正前は無限ループしていた条件が全seedで30ターン以内に決着し、技コマンドが実際に使われる
  ことを確認した。`examples/04_damage_calculation.py` を実行し、EV追加後の出力が意図通り
  変化することを確認した
- `CHANGELOG.md` の `[Unreleased]` / `### Fixed` に本バグ修正を追記

### 2026-07-12 設計見直し（decision_random新設による行動選択用/ゲーム進行用乱数の分離）

上記「observation randomの共有バグ修正」（`new.random = battle.random`）に、ユーザー指摘により
発覚した重大な副作用（方策が `sim.random` を先取り消費し未来の乱数を予知できてしまう設計欠陥）を
解消した。sonnetサブエージェント（`isolation: "worktree"`）に委任して実装・検証した。

- `src/jpoke/core/battle.py`: `Battle.__init__` に行動選択専用の乱数生成器
  `self.decision_random = Random(hash((self.seed, "decision")) & 0xFFFFFFFF)` を新設
  （`self.random` の直後）。`_EXTRA_DEEPCOPY_KEYS` に `decision_random` を追加してdeepcopy対象にし、
  `Battle.copy(reseed=True)` でも `new.decision_random` を派生シードで再初期化するようにした
- `src/jpoke/players/random_player.py`: `RandomPlayer.choose_command()` を
  `battle.decision_random.choice(...)` に変更（docstringの `battle.random` への言及も修正）
- `src/jpoke/players/tree_search_player.py`: `TreeSearchPlayer.fallback()` を
  `battle.decision_random.choice(...)` に変更（docstringも同様に修正）
- `src/jpoke/core/observation_builder.py`: `build()` から `new.random = battle.random` を削除し
  （ゲーム進行用 `random` を元通り独立deepcopyに戻し先読みを不可能にした）、
  代わりに `new.decision_random = battle.decision_random` を追加（無限交代ループ対策は維持）
- `tests/test_poke_env_compat.py`: `test_observation_randomは本体のbattle_randomと同じ参照を共有する`
  を `test_observationのdecision_randomは共有されrandomは独立している` に改名し、
  `sim.random is not battle.random` かつ `sim.decision_random is battle.decision_random` の
  両方を検証するように書き換え。`test_無限交代ループの再現条件下でもコマンドが技を含んで決着する`
  は変更なしでそのまま成功することを確認。あわせて `test_randomplayerは同じseedで対戦すると
  同じコマンド列を再現する` の docstring中の `battle.random` 言及も `battle.decision_random` に
  修正した。`scripts/sort_tests.py` / `scripts/generate_test_list.py` を実行
- 検証: `examples/02_team_battle.py` をseed=1〜10で実行し全seedが30ターン以内に技コマンドを
  使って決着すること（無限交代ループが再発しないこと）を確認。`sim.random is not battle.random`
  かつ `sim.decision_random is battle.decision_random` の両方をテストで担保。
  `tests/test_tree_search_framework.py` 11件全件成功（木探索の決定論性に影響なし）。
  フルテストスイート（`python -m pytest tests/ -q`）4831 passed, 1 skipped
  （バグ修正時点のベースラインと同数、リグレッションなし）を確認
- `CHANGELOG.md` の `[Unreleased]` / `### Fixed` に本追加修正を追記し、PR #45の記述が
  「先読み可能」な問題を残したままの表現になっていた部分を修正後の正しい状態に更新した

### 2026-07-12 4度目のレビュー指摘・残り項目対応（リプレイ・poke-env互換プロパティ・modify_hp系・get_event_logs・優先度低4項目）

「内部実装に精通したsonnetサブエージェントによる追加調査」節の残り5項目（うち1件は4サブ項目の
まとめ）に対応した。damage_roll系・EV/IVは前段の別タスクで対応済みのため対象外。

- 新規 `examples/07_replay.py` を追加。1vs1バトルを最後まで進めて `Battle.build_replay_data()` で
  記録し、`to_dict()`/`from_dict()` でシリアライズ・復元してから `jpoke.core.replay.replay_battle()`
  に渡し、勝者・ターン数が元の対戦と一致することを確認する最小例。`examples/README.md` の対応表に
  1行追加し、`CHANGELOG.md` の `[Unreleased]` / `### Added` にも記載した
- `examples/03_custom_player.py` の `StrongestMovePlayer` に、`battle.available_moves` 等の
  poke-env互換プロパティ（`choose_command` に渡される観測コピーの `battle.observer` が呼び出し元
  プレイヤーに設定されるため、そのまま自分視点の情報として使える）で同じ判断を書いた
  `choose_command_poke_env_style()` を未使用の別メソッドとして併記した。既存の `choose_command()` を
  一時的に差し替えて同一seedで最終ターン数・勝者が一致することを手動検証済み
- `examples/04_damage_calculation.py` に、`modify_hp(r=-0.6)` で防御側のHPを残り40%まで直接
  減らしてから `calc_lethal(max_attack=1)` を呼ぶ例（致死率0.00%→100.00%）と、続けて
  `modify_stats(target, {"def": 1})` でぼうぎょランクを上げると同条件でも致死率が下がる
  （100.00%→56.25%）ことを示す例、`faint()` で対象を即座にひんし化する例を追加した
- `examples/02_team_battle.py` の勝敗表示の直後に、`get_event_logs(turn)` を全ターン分走査して
  `LogCode.CRITICAL_HIT` のログだけを抽出・表示する例を追加した
- 優先度低4項目のうち低コストな2件のみ対応: `Player.n_lost_battles` を
  `examples/06_bulk_simulation.py` の勝率表示に追記し、`Player.add_pokemon()` の戻り値を
  `build_player()` で変数に受けて `mon.set_evs(...)` の追加設定に使う形に書き換えた。
  `Battle.copy(reseed=True)` と `TreeSearchPlayer.configure_sim()`/`opponent_estimator()` は
  意味のある実演に既存サンプルの作り替えが必要になるため見送った（詳細は各チェック項目参照）
- `python -m pytest tests/ -q` 4837 passed, 1 skipped（新規回帰なし、既存テストは無変更）。
  `python -m ruff check src/ tests/ scripts/ examples/` 全件成功。
  変更・追加した `examples/02_team_battle.py`・`03_custom_player.py`・`04_damage_calculation.py`・
  `06_bulk_simulation.py`・`07_replay.py`（新規）を実際に実行し、出力が意図通りであることを
  目視確認した（`tests/test_examples_smoke.py` の7件全PASSEDも確認）

### 2026-07-12 examples/ のユースケース別ディレクトリ構造への再編

フラットな連番（`01_quickstart.py` 〜 `09_janken_nash_cfr.py`）では、独立した作業ブランチが
同じ番号を取り合って衝突する事故（`07` 番号が2つの並行ブランチで衝突）が実際に発生したため、
ユースケース別ディレクトリに分割し、ディレクトリ内で独立して連番を振る構造に変更した。

- `git mv` で以下のように再配置（履歴を保持）:
  `01_quickstart.py`→`01_basics/01_quickstart.py`、
  `02_team_battle.py`→`01_basics/02_team_battle.py`、
  `03_custom_player.py`→`02_ai/01_custom_player.py`、
  `05_tree_search_ai.py`→`02_ai/02_tree_search_ai.py`、
  `04_damage_calculation.py`→`03_damage_calc/01_damage_calculation.py`、
  `06_bulk_simulation.py`→`04_research/01_bulk_simulation.py`、
  `07_replay.py`→`04_research/02_replay.py`、
  `08_janken_nash_fictitious_play.py`→`04_research/03_janken_nash_fictitious_play.py`、
  `09_janken_nash_cfr.py`→`04_research/04_janken_nash_cfr.py`
- `04_research/04_janken_nash_cfr.py` 内の自己参照（「08との違い」「08_janken_nash_fictitious_play.py」）を
  同ディレクトリ内の新ファイル名（「03との違い」「03_janken_nash_fictitious_play.py」）に更新
- `examples/README.md` を全面改訂し、ディレクトリ一覧（ユースケース対応表）とファイル一覧
  （新パス）の2段構成にした。トップレベル `README.md` のクイックスタート例も
  `python examples/01_basics/01_quickstart.py` に更新
- `tests/test_examples_smoke.py` の `EXAMPLES_DIR.glob("*.py")` を `glob("**/*.py")` に変更し、
  サブディレクトリ内のサンプルも再帰的に収集・実行するようにした。パラメータIDが
  `01_basics/01_quickstart.py` のような相対パスになりデバッグしやすくした
- `tests/test_poke_env_compat.py` のdocstring中の `examples/02_team_battle.py` 言及を
  `examples/01_basics/02_team_battle.py` に修正（意味は変更なし、パスの正確性のため）
- `CHANGELOG.md` の `[Unreleased]` / `### Changed` に本再編（破壊的変更）を追記
- 検証: `python -m pytest tests/ -v` 全件成功（`test_examples_smoke.py` は新パスで9件全PASSED）。
  `python -m ruff check src/ tests/ scripts/ examples/` 全件成功。新パスの9ファイルすべてを
  個別実行しエラーなく終了することを確認

### 2026-07-12 examples/ 全体のコメント過密の是正

ユーザーから「poke-envのサンプルスクリプトと比べてコメントが多すぎて読みづらくなっていないか」と
指摘を受けた。9ファイル全てを確認した結果、その後のprint()出力や次の1〜2行のコードをそのまま
日本語で言い換えるだけの説明的コメントが多数残っており、チュートリアル記事のようになっていた。

- 対応方針: 「知らないと事故る／読み取れない」非自明な情報（EV/IVスケールの違い・
  `ability_name`省略時の挙動・`decision_random`の意図・poke-env互換プロパティの存在・
  `expected_hits`の分布など）は残し、コードや直後の出力を単に言い換えているだけの
  コメントを削除した。`03_janken_nash_fictitious_play.py`/`04_janken_nash_cfr.py`の
  モジュールdocstring（Nash均衡・CFR風regret matchingの理論説明）はサンプルの主目的
  そのものであり、削減対象から除外した
- 9ファイル全て（`01_basics/01_quickstart.py`、`01_basics/02_team_battle.py`、
  `02_ai/01_custom_player.py`、`02_ai/02_tree_search_ai.py`、
  `03_damage_calc/01_damage_calculation.py`、`04_research/01_bulk_simulation.py`、
  `04_research/02_replay.py`、`04_research/03_janken_nash_fictitious_play.py`、
  `04_research/04_janken_nash_cfr.py`）から冗長なコメントを削除。挙動・出力は無変更
- 検証: `python -m ruff check examples/` 全件成功、`python -m pytest tests/ -q`
  4842 passed, 1 skipped（既存ベースラインと同数、リグレッションなし）

### 2026-07-12 examples カバレッジチェックリストの残り10項目に対応

「examples カバレッジチェックリスト」に `[ ]` のまま残っていた10項目（天候・地形・状態異常の
実演、アイテム・特性の発動ログ、交代誘発技・設置技、先制技・素早さ操作技、わるあがき、
テラスタルの能動的な選択、交代コマンドの明示的な組み立て、コマンド候補のデバッグ確認）に
まとめて対応した。実装前に `src/jpoke/` を実際に読み、`set_weather()`/`set_terrain()`/
`activate_side_field()`/`activate_global_field()`/`Command.get_switch_command()`/
`get_terastal_command()`/`Move.modify_pp()`/`TreeSearchPlayer.evaluate_commands()` が
いずれも既存の公開APIとして使えることを確認した上で、新規実装は行わずexamplesの追加のみで
全10項目に対応した。

- 新規 `examples/03_damage_calc/02_field_and_status_effects.py`:
  天候（すなあらし）・地形（エレキフィールド）の効果、`set_ailment()`ではなく実際に技
  （どくどく）を当てて状態異常を発生させる例、`battle.step()`を伴う対戦での特性
  （もらいび）・アイテム（きあいのタスキ）の発動ログ確認、の4項目をまとめて実演
- 新規 `examples/01_basics/03_hazards_and_explicit_commands.py`:
  設置技（ステルスロック）と交代誘発技（とんぼがえり）の効果、`Command.get_switch_command()`/
  `get_terastal_command()`による交代・テラスタルコマンドの明示的な組み立て、
  わるあがき（PP切れ）の挙動、`choose_command()`内で`get_available_commands()`を覗く
  コマンド候補のデバッグ確認、の5項目をまとめて実演
- 新規 `examples/02_ai/03_priority_and_command_debug.py`:
  優先度技・素早さ操作技（トリックルーム）が行動順に与える影響、
  `TreeSearchPlayer.evaluate_commands()`によるコマンド候補・評価値のデバッグ確認、の
  2項目をまとめて実演（「コマンド候補・選択理由の確認」は上記ファイルと合わせて2種類の
  確認方法を紹介）
- 実装過程で「とんぼがえり使用後に交代が発生しない」ように見えた挙動を実装コードで調査した
  結果、テスト用チーム構成が非対称（例: 片方1体・もう片方2体）だと`Battle(n_selected=None)`
  の自動調整（`min(3, 各プレイヤーの手持ち数)`）により選出数が1に絞られ、控えが選出漏れに
  なって交代不能になっていただけと判明した（ライブラリ側のバグではない）。両陣営の
  手持ち数を揃えることでこの罠を回避し、examples内のコメントとしては特に触れず自然な
  チーム構成にした
- `examples/README.md` のファイル一覧に新規3ファイルの行を追加
- 公開APIの変更は行っていないため `CHANGELOG.md` の更新は不要と判断した
- 検証: `python -m pytest tests/ -q` 4851 passed, 1 skipped（新規スモークテスト3件分の
  純増、既存分の回帰なし）。`tests/test_examples_smoke.py` は13件全PASSED
  （新規3ファイル分を含む）。`python -m ruff check .` 全件成功。`python -m mypy`
  （`src/jpoke/core`対象）でエラーなし。新規3ファイルをいずれも個別実行し、
  出力が意図通り（すなあらしダメージ・地形補正・もうどく付与・もらいび/きあいのタスキの
  発動ログ・ステルスロックダメージ・とんぼがえり後の自動交代・わるあがきの反動・
  テラスタル状態変化・優先度逆転・トリックルームでの素早さ順反転・評価値表示）で
  あることを目視確認した

## 5度目のラウンド（2026-07-12、フレッシュな視点での再調査 + 実装、`feature/examples-coverage-round5`）

上記4ラウンドで `[ ]` の項目は残っていなかったが、README「実装状況」の規模
（特性310・アイテム247・技733・揮発性状態66・状態異常7・場の効果31）に対し
`examples/` は13ファイルに留まっていたため、フレッシュな視点で
`src/jpoke/core/battle.py`（`Battle` 公開メソッド）・`core/player.py`（`Player` 公開API）・
`model/pokemon.py`（`Pokemon` 公開API）・`docs/api/README.md` を再点検し、examplesに
一度も登場しない概念・APIを洗い出した（ダブルバトルはREADME「対象範囲」
「対象はポケモンチャンピオンズのシングルバトルのみ」により対象外と確認し調査対象から除外）。
新規実装は行わず、既存の公開APIを使ったexamples追加のみで対応した。

### 発見・対応した項目

- [x] **メガシンカ**（`mega_evolution` BattleOption・`Command.get_megaevol_command()`・
  `Pokemon.can_megaevolve()`/`megaevolved`）が一度も実演されていなかった。テラスタルと
  対になる機能で、`docs/api/README.md` のBattleOptionコンストラクタ表には記載があるのに
  examplesには皆無だった
  → 対応: `examples/01_basics/03_hazards_and_explicit_commands.py` に
  `show_explicit_megaevol_command()` を追加。`show_explicit_terastal_command()` と対になる
  構成で、フシギバナ+フシギバナイトを使い `Command.get_megaevol_command(0)` で明示的に
  コマンドを組み立てて `can_megaevolve()`/`megaevolved` の変化を確認する
- [x] **`Battle.set_volatile()`**（揮発性状態66種の直接付与）が一度も実演されていなかった。
  過去ラウンドで `set_ailment()`/`set_weather()`/`set_terrain()` は対応済みだったが、
  `set_volatile()` だけ抜けていた（`docs/api/README.md` のシナリオ構築系の表にも載っていなかった）
  → 対応: `examples/03_damage_calc/02_field_and_status_effects.py` に
  `show_volatile_via_set_volatile()` を追加。やどりぎのタネ（ターン終了時にHPを1/8吸い取り
  相手を回復）を直接付与し `battle.step()` 後のログで確認する。`docs/api/README.md` の
  シナリオ構築系の表にも `set_volatile` の行を追記した
- [x] **`calc_lethal()` の `moves=[...]`（複数技の組み合わせ）・`critical`/`secondary` 引数**が
  一度も実演されていなかった。`moves` はリストで「1発目A、2発目B」という組み合わせを渡せ、
  `secondary=True` は致死率計算に組み込まれた技（例: キラースピンのどく付与）の追加効果を
  自動的に加味する
  → 対応: `examples/03_damage_calc/01_damage_calculation.py` に、でんこうせっか→かみなりの
  コンボダメージ表示（`moves=["でんこうせっか", "かみなり"]`）と、キラースピンの
  `secondary=False/True` 比較（どくの蓄積ダメージで確定数が4発→3発に短縮）を追加した。
  なお `secondary=True` は全ての追加効果技に効くわけではなく、`MoveData.lethal_handlers` に
  該当エントリがある技（例: キラースピン）のみが対象であることを実装コードで確認した
  （かえんほうしゃのやけど付与には `lethal_handlers` が無く、`secondary` 指定は無関係）
- [x] **`effect_chance_threshold`（BattleOption）**が一度も実演されていなかった。
  `accuracy_fix_threshold` と対になる「確率要素を固定してシナリオを決定論的にする」機能で、
  指定値未満の追加効果発動確率を強制的に0%にする
  → 対応: `examples/03_damage_calc/02_field_and_status_effects.py` に
  `show_effect_chance_threshold()` を追加。かえんほうしゃのやけど付与（10%）を
  `effect_chance_threshold=0.11` で確実に抑制できることを、seed 1〜20の20試行で
  比較（既定は1/20発動、指定時は0/20発動）して実証した
- [x] **`Player.choose_selection()` のオーバーライド**が一度も実演されていなかった。
  `choose_command()` は複数ファイルで拡張例があるが、対戦開始前の選出（どの何体を選ぶか・
  誰を先発にするか）をカスタマイズする方法は`docs/api/README.md`に一言触れられているのみで
  実例が無かった
  → 対応: `examples/02_ai/01_custom_player.py` に `FastestLeadPlayer`
  （素早さ実数値が高い順に選出する）を追加。手持ち4体・選出2体の構成で、並び順に関係なく
  最速個体が先発になることを確認する
- [x] **`Battle.play_out()` が実際に呼ばれている箇所が無かった**（3度目のレビュー指摘で
  新設されたが、01のコメントで存在に触れられているだけで、どのexamplesも定型ループを
  手動で書いたままだった）
  → 対応: `examples/04_research/02_replay.py`（手動ループを学ぶ主目的ではなく対戦を最後まで
  進めた上でリプレイに使う主目的のファイル）の定型ループを `battle.play_out(max_turns=100)`
  に置き換えた。01は「手動でstep()する」ことを学ぶ教材のため意図的に変更していない
- [x] **`judge_winner()` の二重呼び出しが再発していた**（02_ai/01_custom_player.py で
  `while battle.judge_winner() is None` のループ後に再度 `battle.judge_winner()` を呼ぶ
  パターン、02_ai/02_tree_search_ai.py で `not battle.finished` ループ後に
  `battle.judge_winner()` を呼ぶパターン）。過去ラウンドで02_team_battleに対して修正済みの
  はずのパターンが別ファイルに残っていた
  → 対応: 前者は `play_out()` への置き換えで解消。後者は `battle.judge_winner()` を
  `battle.winner` に変更した

### 調査したが見送った項目

- `Pokemon.set_level()`/`set_nature()`（構築後のレベル・性格変更）: `set_evs()`/`set_ivs()`と
  同系統のシナリオ構築APIだが、実演するには「同一個体でレベル/性格を変えて比較する」という
  新しい題材を組み立てる必要があり、既存の `modify_hp`/`modify_stats` 系の実演で
  「シナリオ構築系API」という概念自体は既にカバー済みと判断し見送った
- `Battle.won(player)`/`lost(player)`: `battle.winner == player` の薄い糖衣構文で、
  実演しても学習価値が小さいため見送った
- `Battle.set_item()`/`change_ability()`（アイテム・特性の対戦中変更）: シナリオ構築用途は
  あるが、意味のある実演（トリック等で奪われた後の状態を作る、など）には追加の文脈説明が
  必要になり「短い追記」の範囲を超えるため見送った
- `Battle.weather_for(mon)`/`resolve_action_order()`/`can_switch()`/`remove_all_volatiles()`:
  いずれも既存の実演（`weather`/`resolve_speed_order()`等）と概念的に重複するか、実演のために
  新しい題材構築が必要な割に学習価値が小さいため見送った
- `Pokemon.critical_rank`（急所ランクの直接操作）: `critical_mode="always"`
  （BattleOption）で急所を確定させる方法は既に03で実演済みのため、急所"ランク"を直接
  操作する下位APIまで実演する優先度は低いと判断し見送った

### 検証

- `python -m pytest tests/ -q`（フルスイート）はローカル環境で他worktree（`.loop/`系の
  fuzz/review/lethal等の永続バックグラウンドプロセス）とのCPU競合により実行に時間がかかったため、
  本ラウンドが実際に触れたコード領域を狙い撃ちしたサブセットで確認した:
  `tests/test_examples_smoke.py tests/test_lethal.py tests/test_field.py tests/test_ailment.py`
  で312件、`tests/test_examples_smoke.py tests/test_replay.py tests/volatiles/` で247件、
  いずれも全件成功（既存ベースラインと整合）。`src/jpoke` 側のコード変更は本ラウンドでは
  ゼロ（`examples/`・`docs/` のみ）のため、フルスイートへの影響は無いと判断した
- `python -m ruff check .` 3件のエラーはいずれも本ラウンドで変更していないファイル
  （`tests/abilities/test_ability_ka.py`・`tests/items/test_item_ha.py`・別ファイル1件）の
  既存エラーで、origin/main由来（本ラウンドの変更に起因しない）であることを確認した
- 変更・追加した箇所を含む examples 6ファイル
  （`01_basics/03_hazards_and_explicit_commands.py`・`02_ai/01_custom_player.py`・
  `02_ai/02_tree_search_ai.py`・`03_damage_calc/01_damage_calculation.py`・
  `03_damage_calc/02_field_and_status_effects.py`・`04_research/02_replay.py`）を
  実際に実行し、出力が意図通り（メガシンカの`can_megaevolve`/`megaevolved`変化、
  揮発性状態の吸収HPログ、コンボダメージ・secondary比較での確定数短縮、
  effect_chance_thresholdによるやけど抑制、choose_selectionによる最速個体の先発、
  play_out()での決着）であることを目視確認した
- 新規ファイルは追加していないため `tests/test_examples_smoke.py` のパラメータ数は
  13件のまま（既存6ファイルの内容変更のみ）
- 公開APIの追加・変更は行っていないため `CHANGELOG.md` の更新は不要と判断した

## 第5ラウンド（apiループ）

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

## 第6ラウンド（apiループ）

- [x] `jpoke.testing`モジュールがdocs/examples双方から完全に欠落している
  （developer視点、id: r6-1） → 対応内容 (2026-07-12): `src/jpoke/testing.py`は
  `tests/test_utils.py`にあった内部テスト専用ヘルパーが本体パッケージへ昇格したもので、
  モジュール冒頭docstringに「`pip install jpoke`のみでclone不要のシナリオ検証ができる」旨が
  明記された公開モジュールだが、`docs/api/README.md`と`examples/`の両方から言及が欠落しており、
  外部利用者が存在に気づけない状態だった。`docs/api/README.md`に新章
  「テストユーティリティ（jpoke.testing）」を追加し、`__all__`に含まれる全14関数＋
  `CustomPlayer`を一覧表で掲載した（シグネチャ・戻り値は`src/jpoke/testing.py`本体と1行ずつ
  突き合わせて齟齬が無いことを確認済み）。`fix_damage`/`fix_random`がモンキーパッチによる
  デバッグ専用ユーティリティである旨の注記も引き継いだ。`examples/03_damage_calc/`に
  `03_testing_helpers.py`を新規作成し、`start_battle`/`apply_ailment`/`calc_lethal`/`run_move`
  を使って01/02（`Battle(...).start()`+`Player.add_pokemon()`の定型処理）の定型処理を
  1呼び出しにまとめる例を示した。`examples/README.md`のファイル一覧テーブルにも行を追加した。
  新規ファイルを個別実行し、出力（防御側の状態異常`どく`、`calc_lethal`によるどく無し/ありの
  致死率差分、`run_move`実行後の実際のHP変化）が想定通りであることを確認した。
  `tests/test_examples_smoke.py`は`examples/**/*.py`を`glob`で自動収集する構成のため、
  新規ファイルが手動登録なしでパラメータ化対象に追加されることを確認済み（実行環境の
  editable install破損を修正後、14件全てパス）。回帰テストとして`tests/test_code_conventions.py`に
  `test_docs_examplesがjpoke_testingモジュールに言及している`（`docs/api/README.md`に
  `jpoke.testing`という文字列が含まれること、`examples/`配下に`jpoke.testing`をimportする
  ファイルが存在することを静的に検証し、再度の欠落を防止する軽量テスト）を追加した。
  `tests/CLAUDE.md`（clone前提の内部向けドキュメント）との記載重複は、`docs/api/README.md`の
  「関連リンク」節が既に`tests/CLAUDE.md`を「clone前提のテストヘルパーの使い方」として
  参照しており許容範囲と判断した（追記不要、確認済み）。
  `python -m pytest tests/ -v`実行中に、本ラウンドの変更とは無関係な既存のflaky test 2件を
  発見し、その場で修正した（§共通13）。1件目は`tests/test_examples_smoke.py`の全14件が
  `ModuleNotFoundError: No module named 'jpoke'`で失敗する事象で、原因は他worktree
  （`review/slot1`、既に削除済み）を指す壊れたeditable installがマシン全体で共有されていた
  ことだったため、本worktreeで`pip install -e . --no-deps`を再実行し直して復旧した
  （リポジトリ側の変更は無し）。2件目は`tests/moves_attack/test_move_a.py`の
  `うちおとす`系4テスト（`_おんみつマントでも揮発状態が付与される`/
  `_ひこうタイプの浮遊が無効化される`/`_りんぷんでも揮発状態が付与される`/
  `_命中後に揮発状態が付与される`）で、ダメージ乱数・急所判定を固定していなかったため
  低HPの対戦相手（ポッポ、HP115）がまれに1発で瀕死になり、瀕死時は"うちおとす"揮発状態が
  付与されない（`is_floating`も解除されない）実装仕様と衝突して間欠的に失敗することを
  `damage_roll="max"`+`critical_mode="always"`での再現実験で特定した。4件全てに
  `t.fix_damage(battle, 10)`を追加してダメージを固定し撃墜されないようにすることで解消し、
  該当テストを5回連続実行して収束（毎回成功）することを確認した。
  `python -m pytest tests/ -v`は5509 passed, 1 skipped, 0 failedで全件成功
  （連続2回実行して収束を確認済み）。
