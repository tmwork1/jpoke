# 初回カバレッジレビュー（2026-07-11/12）

[← 目次に戻る](../README.md)

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


### 実施記録

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

