# 第9ラウンド（apiループ、手動起票分）

[← 目次に戻る](../README.md)

- [x] `examples/`配下の全27ファイルの冒頭docstringが「jpoke で学べること: 」という
  書き出しで統一されており、内容と重複する不要な前置きになっていた。また、
  Windows環境で標準出力の既定エンコーディングにより日本語ログが文字化けし得る点の
  実行案内が`examples/README.md`に無かった（id: r9-1） → 対応内容 (2026-07-15):
  `examples/`配下全27ファイルの冒頭docstringから「jpoke で学べること: 」という書き出しを削除し、
  各ファイルの内容に即した自然な文（「〜を扱う」「〜を示す」「〜を確認する」等）に書き換えた。
  レビューの過程で`03_damage_calc/01_basic_lethal_calculation.py`の
  「確定数・乱数ダメージを計算する基本を扱う」（動詞の重複でやや不自然）を
  「確定数・乱数ダメージの基本的な計算方法を扱う」に、`05_benchmark/01_step_time_benchmark.py`の
  「所要時間を計測する計算速度ベンチマークを実行する」（「計測する」と「実行する」の二重表現）を
  「所要時間（計算速度）を計測する」に、それぞれ修正した。`examples/README.md`には
  `PYTHONUTF8=1`を指定して実行する案内（PowerShell/bash双方のコマンド例）を追記した。
  公開APIのシグネチャ変更は無いため`docs/api/README.md`の更新は不要と判断した。
  docstring・README文言の修正でありロジック変更を伴わないため新規の回帰テストは不要と判断し、
  代わりに`examples/01_basics/01_battle_against_intro.py`・
  `examples/03_damage_calc/01_basic_lethal_calculation.py`・
  `examples/01_basics/05_hazards_and_explicit_commands.py`を実行し、docstringの説明内容と
  実際の出力が一致することを確認した。`python -m pytest tests/ -v`で5848件全件パス・
  1件skip（既存件数のまま、flaky testの新規発生なし）を確認した。
- [x] `examples/01_basics/01_battle_against_intro.py`に残っていた
  「TODO: battle.print_logs("all") でログを表示する」「TODO: print文を短くまとめる」の2件（id: r9-2）
  → 対応内容 (2026-07-15): `battle_against()`に
  `on_battle_end=lambda battle: battle.print_logs("all")`を渡して対戦後ログを表示する例に変更し、
  print文を`player1.win_rate`を使った1行（`勝率{:.0%}（{n_finished_battles}戦）`）に整理した。
  レビューの過程で、本ファイルが最初の入門サンプルであり、過去のフィードバックで
  「関数の中に関数」「lambda」がPython初心者には難しいと指摘されていた点を踏まえ、
  defによる関数定義への置き換え（別途トップレベル関数を増やすことになり概念負担が増える）ではなく、
  `lambda battle: ...`が「その場で書ける名前のない小さな関数」であることを簡潔に説明する
  コメントを追加する対応にとどめた。`PYTHONUTF8=1 python
  examples/01_basics/01_battle_against_intro.py`を実行し、対戦ログの表示と
  勝率表示（`player1: 勝率100%（1戦）`）が正しく出力されることを確認した。
  ロジック変更を伴う公開APIの追加・変更は無いため`docs/api/README.md`の更新は不要と判断した。
  `python -m pytest tests/ -v`で5848件全件パス・1件skip（既存件数のまま、flaky testの新規発生なし）
  を確認した。
- [x] `examples/01_basics/03_team_battle.py`に残っていた
  「TODO: battle.finished(max_turn=30)のように、ターン上限を指定してfinished判定できるようにする」
  （id: r9-3） → 対応内容 (2026-07-15): 調査の結果、TODOが要求していたAPI相当は
  `Battle.play_out(max_turns=)`として既に実装・文書化済みと判明したため、新規API追加は不要と判断した。
  `03_team_battle.py`のTODOコメントは、`battle.play_out(max_turns=30)`も使えるが本ファイルの目的が
  ターンごとの`battle.print_logs()`による経過観察であるため手動`while`ループを維持している旨の説明
  コメントに置き換えた（ループ自体は変更なし）。一方、`04_log_and_pokedex_lookup.py`と
  `02_ai/03_tree_search_ai.py`はループ内で`print_logs()`等の観察を行っておらず
  `battle.play_out(max_turns=...)`と完全に等価な`while not battle.finished and battle.turn < N:
  battle.step()`を素朴に書いていただけだったため、`play_out()`呼び出しに置き換えて重複例を整理した。
  `play_out()`の実装（`src/jpoke/core/battle.py`）と突き合わせ、境界条件（`<`）・返り値
  （`self.winner`）が置き換え前後で完全一致することを確認した上で、置き換え前後のコードを
  それぞれ実行し標準出力が完全一致すること（diffなし）を確認した。ロジック変更を伴う公開APIの
  追加・変更は無いため`docs/api/README.md`の更新は不要と判断した。
  `python -m pytest tests/ -v`で5848件全件パス・1件skip（既存件数のまま、flaky testの新規発生なし）
  を確認した。
- [x] `01_basics/04_log_and_pokedex_lookup.py`が「LogCodeの使い方」と「POKEDEXの使い方」という
  異なる2つの調べ物を1ファイルに同居させており、`show_critical_hit_logs()`内の3重forを含む
  リスト内包表記が初心者には追いづらかった（id: r9-4） → 対応内容 (2026-07-15):
  `04_log_and_pokedex_lookup.py`を削除し、`04_pokedex_ability_lookup.py`
  （POKEDEX特性確認専用、バトル実行なしでPOKEDEXの静的データだけを扱う最も手軽な例として整理）と
  `06_structured_log_extraction.py`（構造化ログ抽出専用）の2ファイルに分割した
  （`05`は既存の`05_hazards_and_explicit_commands.py`と衝突するため`06`を採番）。
  `show_critical_hit_logs()`のリスト内包表記は、何が繰り返されているか分かりやすいよう
  ターン→プレイヤー→ログの3段のネストしたfor文+if文に書き換え、各段にコメントを追加した
  （置き換え前後で同じ`(t, username, pokemon)`のタプル列を同じ順序で生成することを確認済み）。
  `show_logcode_variety()`ではLogCodeの代表5種類（`CRITICAL_HIT`/`ABILITY_TRIGGERED`/
  `AILMENT_APPLIED`/`HP_CHANGED`/`MOVE_MISSED`）を個別に案内し、全種類（37種類）を確認したい場合は
  `list(LogCode)`で列挙する方法を示すにとどめ、全列挙はしない方針にした。実装の過程で
  `POKEDEX[name].abilities`が固定長でなく、隠れ特性を持たないポケモン等では2要素になる
  可変長リストである点を実行時に発見したため、`show_pokedex_abilities()`の説明文を
  「通常特性1・2・隠れ特性の順のリスト。持てる特性が1つや2つしかないポケモンでは、
  存在しない枠は含まれず短いリストになる」に修正し、`フシギバナ`（隠れ特性なし、2要素）を
  例に加えて動作を確認できるようにした。`examples/README.md`のファイル一覧・目次を
  04（POKEDEX特性確認）/05（設置技・交代コマンド）/06（構造化ログ抽出）の3ファイル構成に
  更新した。`tests/`配下にこれらのexamplesファイルを直接参照するテストが無いことを確認した。
  分割後の2ファイル（`04_pokedex_ability_lookup.py`・`06_structured_log_extraction.py`）を
  それぞれ実行し、POKEDEXの特性一覧（可変長を含む）とLogCodeの抽出結果
  （急所ログ2件・LogCode37種類）が意図通り出力されることを確認した。ロジック変更を伴う
  公開APIの追加・変更は無いため`docs/api/README.md`の更新は不要と判断した。
  docstring・サンプル構成の整理でありコアロジック変更を伴わないため新規の回帰テストは
  不要と判断し、`python -m pytest tests/ -v`で5849件全件パス・1件skip
  （既存件数のまま、flaky testの新規発生なし）を確認した。
- [x] `01_basics/05_hazards_and_explicit_commands.py`冒頭の
  「TODO: このサンプルは削除すべき」というTODOコメントについて、削除の是非を判断する必要が
  あった（id: r9-5） → 対応内容 (2026-07-15): ファイル自体の削除ではなく、
  `show_struggle_when_out_of_pp()`内で`Player`を継承していた`ShowCommandsPlayer`インナークラス
  定義（`choose_command()`をオーバーライドして`battle.get_available_commands()`を表示するだけの
  デバッグ用実装）を除去し、`mon.last_move.name`とHP変化の確認のみで完結する簡潔な実装に
  書き換えた。コマンド候補が「わるあがきのみ」であることを事前に確認したい場合は
  `battle.is_struggle_only(player)`を`choose_command()`内などphase解決中のコンテキストで
  呼べる旨、および`02_ai/01_custom_player.py`への参照コメントを関数内に追加した。
  冒頭のTODOコメントは対応済みのため削除した。`examples/README.md`の該当行
  （45行目、設置技・交代誘発技・交代コマンド組み立て・わるあがきの挙動を扱う旨の説明）は
  クラス継承の有無に言及しておらず書き換え後も実態と一致しているため、更新不要と判断した。
  `01_basics/`配下の01〜06全ファイルを`PYTHONUTF8=1`で実行し、各docstringの説明内容と
  実際の出力が一致することを確認した（わるあがき使用後の技名`わるあがき`・HP変化
  `110 → 83`等）。ロジック変更を伴う公開APIの追加・変更は無いため`docs/api/README.md`の
  更新は不要と判断した。クラス継承除去は表示方法の整理でありコアロジック変更を伴わないため
  新規の回帰テストは不要と判断し、`python -m pytest tests/ -v`で5849件全件パス・1件skip
  （既存件数のまま、flaky testの新規発生なし）を確認した。
- [x] `02_ai/01_custom_player.py`に「`is_move()`のような名前のほうがわかりやすいのでは」
  「戻り値もpoke-envのように`create_order()`で作ったオブジェクトにすべき」の2件のTODOが
  残っており、`02_ai/02_selection_customization.py`の`sorted(key=lambda ...)`・
  `01_custom_player.py`の`max(commands, key=move_power)`・
  `03_tree_search_ai.py`の`super().evaluate(battle)`など、Python初心者には
  読み方が難しい`key=`/`lambda`/`super()`の使い方に補足コメントが無かった（id: r9-6） →
  対応内容 (2026-07-15): `01_custom_player.py`の`is_move()`改名TODOは、`is_type()`が
  `"move"`/`"switch"`/`"any"`のどの種別かも判定できる汎用メソッドで
  `Command.switch_commands()`等の内部実装からも使われている（`r8-2`で`is_switch()`を
  プロパティ化した際に確認済みの用途）ため改名しない方針とし、その理由をコメントとして
  明記した。`choose_command_poke_env_style()`のTODOは、poke-envの`Player.choose_move()`が
  `create_order(move)`で作る`BattleOrder`を返す仕様である一方、jpokeの`Command`は
  技・交代等の選択肢を表す単純なEnum値でコマンド生成専用クラスが存在しないため、
  本メソッドが比較用の未使用コードである旨の補足コメントに置き換えた（戻り値の型を
  合わせる対応はしない）。同ファイルの`move_power()`内の`key=move_power`、
  `choose_command_poke_env_style()`内の`key=lambda i: ...`、`02_selection_customization.py`の
  `sorted(..., key=..., reverse=True)`、`03_tree_search_ai.py`の`super().evaluate(battle)`
  各行に、それぞれ何をしているか（`key=`は各要素を関数に通した結果を比較キーにする、
  `lambda`はその場限りの名前のない関数、`super()`は親クラスの既定実装をそのまま呼ぶ）を
  説明するコメントを追加した。`01_custom_player.py`の`print_logs("all")`直後に
  `print("-" * 50)`を追加し、TODOが指摘していた出力の見づらさを解消した
  （`02_ai/05〜07`は`print_logs()`が出力の最後尾で後続に別の`print()`が無いため、
  同種の問題が無いことをレビューで確認した）。`03_tree_search_ai.py`の
  「相手を瀕死にできる技とそうでない技を混ぜて、AIがどの技を選ぶか観察できるようにする」
  というTODOについては、実装時の構成（`カビゴン`に`じしん`/`たいあたり`、相手を
  `ピカチュウ`＋HP努力値32）をレビューで`evaluate_commands()`を使い内部評価値まで
  確認したところ、対戦相手の技が未公開な1ターン目は`fallback()`（ランダム）に委譲されて
  評価自体が行われず、2ターン目に実際の探索が働く時点では1ターン目の`たいあたり`chip
  ダメージで相手が瀕死間際まで減っており、`たいあたり`の急所込み最大ダメージ
  （`STAB×急所`で通常時の`じしん`最小ダメージを上回る）でも確実に瀕死にできてしまうため、
  `evaluate_commands()`が両技とも`inf`（同点）を返し、「確実に瀕死にできる技を優先する」
  という判断が実際には検証できていないことが判明した。技を`たいあたり`から
  `みずでっぽう`（みずタイプ、威力40、カビゴンはみずタイプでないためSTABも乗らない）に
  差し替え、相手ピカチュウのHP努力値の底上げ（`evs={"hp": 32}`）を撤去してデフォルトHPに
  戻すことで、`じしん`の最小ダメージ（急所なし）が相手の最大HPを常に上回って確実に
  瀕死にでき、`みずでっぽう`は急所が入っても瀕死にできない、という関係をHP調整に依存せず
  成立させた。この修正後に`evaluate_commands()`で確認すると、2ターン目の評価値は
  `じしん=inf`・`みずでっぽう`は有限値（残りHP割合差相当）とはっきり分かれ、
  `KOFocusedPlayer`が`じしん`を選ぶ判断が実際の探索結果として観察できることを確認した。
  `04_priority_and_command_debug.py`の「合法手の評価値を確認するだけなのに
  コードの量が多すぎる」というTODOは、`DebugPlayer`の冗長なdocstring（`evaluate_commands()`
  自身のdocstringと重複していた注意書き）を圧縮する対応にとどめた。本ファイルは
  `examples/README.md`に優先度・素早さ操作（トリックルーム）の話題と
  `evaluate_commands()`のデバッグ確認という2つの話題を扱うと明記されており、
  `show_priority_and_speed_control()`は前者に必須のため削除できず、`DebugPlayer`＋
  2ターンの`battle.step()`という後者の実装も`choose_command()`内で`evaluate_commands()`を
  呼んで結果を表示するだけの最小構成に既になっていたため、これ以上の構造簡略化は
  行わずTODOコメント自体を削除した。`docs/api_feedback/loop_rounds/round8.md`の
  `r8-2`（`is_switch()`→`is_switch`プロパティ化）は命名からプロパティ化への変更であり、
  今回の`is_type()`温存判断（プロパティ化ではなく汎用メソッドとしての用途を理由に改名見送り）
  と矛盾しないことを確認した。ロジック変更を伴う公開APIの追加・変更は無いため
  `docs/api/README.md`の更新は不要と判断した。`02_ai/`配下全7ファイルを`PYTHONUTF8=1`で
  実行し、いずれも正常終了・出力内容が説明コメントと一致することを確認した
  （`03_tree_search_ai.py`は2ターンで`TreeSearchAI`勝利、`じしん`で確定KOする決着を確認）。
  `python -m pytest tests/ -v`で5849件全件パス・1件skip（既存件数のまま、flaky testの
  新規発生なし）を確認した。
- [x] `03_damage_calc/01_basic_lethal_calculation.py`の`add_pokemon()`の第1引数を
  `_name`サフィックス付きに改名すべきかというTODO、`Pokemon.show()`（`render_info()`）の
  未所持アイテム・テラスタル未設定時の表示が`"No item"`/`"No terastal"`という英語の
  ハードコードのままだった件、`03_damage_calc/`配下のファイル構成（生ダメージロールと
  状態操作の単体確認が分離されておらず、りゅうせいぐんの自傷効果が`secondary`の対象外である
  理由の実装根拠が未確認だった点）の3件（id: r9-7） → 対応内容 (2026-07-15):
  `add_pokemon()`の第1引数は`Pokemon.__init__`と同じく単に`name`であり`_name`等の
  サフィックスは付いていない（事実誤認だったTODO）と判明したため、改名は行わず
  その事実を明記したコメントに置き換えた。`render_info()`内の`'No item'`/`'No terastal'`を
  それぞれ`'アイテムなし'`/`'テラスタルなし'`に変更し（区切り文字・並び順は変更なし）、
  `CHANGELOG.md`の`[Unreleased] Changed`に出力文字列変更である旨と、この文字列を直接
  パースしているコードがあれば影響を受ける旨を記載した。`tests/test_render_info.py`を
  新規追加し、アイテム未所持時に`"アイテムなし"`を含み`"No item"`を含まないこと、
  アイテム所持時はアイテム名がそのまま表示されること、`show()`が`render_info()`の
  結果をそのままprintするだけであることを検証した。あわせて`Pokemon.__init__`
  （`self.tera_type: Type = tera_type or self.base_types[0]`）を確認したところ、
  `tera_type`は常に非空値（省略時は第1タイプ由来）になるため、`render_info()`の
  `else`節（`"テラスタルなし"`）は現状の設計では到達不能なdead codeであると判明した。
  設計変更は本タスクの範囲外と判断し、`render_info()`内に到達不能である理由を
  説明するコメントを追加するにとどめた（`tests/test_render_info.py`にも、常に
  基本タイプ由来のテラスタイプ表記になることを確認するテストを追加し、この設計を
  回帰的に固定した）。`03_damage_calc/`は生ダメージロール（01）→状態操作の単体確認
  （新設`02_direct_state_manipulation.py`、`set_ailment()`/`modify_hp()`/`modify_stats()`/
  `faint()`を技を介さず単体で確認）→calc_lethal基本（03、旧01）→シナリオ比較
  （04、旧02、02と03を組み合わせる位置づけを明記）→…という順に組み直し、10→11ファイルに
  renumberし、docstring相互参照・`examples/README.md`のファイル一覧を追従させた。
  りゅうせいぐんの自傷効果については`src/jpoke/handlers/lethal.py`の
  `りゅうせいぐん_lower_spa`が（`りんごさん`/`ルミナコリジョン`/`れんごく`の各ハンドラとは
  異なり）`ctx.move_secondary`を一切参照せず常に適用されること、対応する
  `src/jpoke/handlers/move_attack.py`の`りゅうせいぐん_sharply_lower_attacker_spa`も
  `Event.ON_HIT`（追加効果ではなく命中時に必ず発生する効果）に登録されていることを
  実装で確認し、既存の`06_secondary_effects.py`（キラースピンのどく付与デモ）は維持した上で
  `show_self_stat_drop_is_always_applied()`を新規追加し、`secondary=True`/`False`いずれでも
  りゅうせいぐん使用後のとくこうランクが同じ値になることを実行結果で示した。
  `03_damage_calc/`配下の全11ファイルを`PYTHONUTF8=1`で実行し、いずれも正常終了することを
  確認した。ロジック変更を伴う公開APIのシグネチャ変更は無いため`docs/api/README.md`の
  更新は不要と判断した。`python -m pytest tests/ -v`で5854件全件パス・1件skip
  （既存件数から新規追加した`test_render_info.py`の4件分増加、flaky testの新規発生なし）を
  確認した。
- [x] `04_research/03_janken_nash_cfr.py`冒頭に残っていた
  「TODO: 難易度勾配を考慮して、04のfictitious playを03に繰り上げたほうがよいか検討する」、
  `02_replay.py`の「TODO: リプレイを再生する箇所にも説明を追加する」
  「TODO: 勝者だけを確認するのではなく、print_logs()の出力が元の対戦と同じになることを
  確認できるようにする」の計3件（id: r9-8） → 対応内容 (2026-07-15):
  `git mv`で`03_janken_nash_cfr.py`↔`04_janken_nash_fictitious_play.py`の番号を入れ替え、
  概念的に単純なfictitious playを03（Nash均衡の基礎、固定の混合戦略）、状態に応じて
  戦略を変えるCFR風の発展形を04にする順序に戻した。この順序（03=fictitious_play,
  04=cfr）は`tests/test_code_conventions.py`の複数テスト（`test_examplesがjudge_winnerの
  is_None比較を使っていない`のid:r6-4コメント等）が2026-07-12〜13時点で既に前提としていた
  ものであり、2026-07-14の`3329db02`（`examples: origin/mainのTODOコメントを反映し
  1ファイル=1事例に再構成`）で「04_researchのjanken_nash 2ファイルの番号を入れ替えた」
  際にテストのdocstring更新が漏れ、実ファイルと記述が食い違っていたことを`git log`で
  確認した上で復元した。両ファイル冒頭に「ゲーム理論の用語ミニ解説」節を追加し、
  03では混合戦略・Nash均衡・fictitious play・exploitabilityを、04ではinformation set・
  regret・regret matching・CFRを対戦経験（読み合いの確率配分、相手の使用率統計への
  回答の積み重ね、反省会での「あの技の方が勝ちやすかった」という振り返り等）に
  紐づけて解説し、04冒頭では03で解説済みの用語への参照を挟んで重複を避けた。
  `02_replay.py`の2件のTODOは、`replay_battle()`呼び出し前に処理内容（ReplayDataから
  Battleを再構築しReplayPlayerでコマンドを払い出す仕組み）の説明コメントを追加し、
  再生後に`battle.get_log_lines(turn="all")`（`print_logs()`が内部で出力する行そのもの）
  を元の対戦・再生した対戦の両方から取得して完全一致をassertで検証するコードに
  置き換えることで解消した。`examples/README.md`のファイル一覧・実行時間注記
  （元の「数十秒・十数秒」を実測に基づき「十数秒・数十秒」に入れ替え）と、03→04の順で
  読むと理解しやすい旨の案内を追記した。`PYTHONUTF8=1 python examples/04_research/
  02_replay.py`を実行し、ログ完全一致のassertが例外なく通ること（元・再生とも20行、
  勝者・ターン数一致）を確認した。`03_janken_nash_fictitious_play.py`
  （実測約8秒）・`04_janken_nash_cfr.py`（実測約26秒）・`01_bulk_simulation.py`を含む
  `04_research/`配下の全4ファイルを実行し、いずれも正常終了・出力内容が更新後の
  docstringと整合することを確認した。ロジック変更を伴う公開APIの追加・変更は無いため
  `docs/api/README.md`の更新は不要と判断した。ファイル名変更後も
  `tests/test_code_conventions.py`が問題なく通ることを含め、`python -m pytest tests/ -v`で
  5854件全件パス・1件skip（既存件数のまま、flaky testの新規発生なし）を確認した。
- [x] `05_benchmark/01_step_time_benchmark.py`冒頭に残っていた
  「TODO: import文をまとめられないか。」（id: r9-9） → 対応内容 (2026-07-15):
  `from typing import Callable, get_args`を標準ライブラリ群（`argparse`/`statistics`/`time`/
  `random.Random`）の直後に移動し、標準ライブラリ→自プロジェクト（`jpoke`）の順に整理した
  （`import X`形式・`from X import Y`形式それぞれの中でアルファベット順を維持）。
  `jpoke.data.ability`/`jpoke.data.item`/`jpoke.data.move`/`jpoke.data.pokedex`の個別importは
  参照先モジュールが異なり1行にまとめると意味が変わる（各モジュールが公開する定数名
  `ABILITIES`/`ITEMS`/`MOVES`/`POKEDEX`をそれぞれ別名前空間から取っている）ため統合せず
  現状維持とし、TODOコメントは対応済みとして削除した。`PYTHONUTF8=1 python
  examples/05_benchmark/01_step_time_benchmark.py --n-battles 5 --max-turns 20
  --progress-every 0`を実行し、import順整理のみでロジック変更が無いことを出力
  （stepサンプル数・所要時間・battles/sec等が正常に出力され例外が発生しないこと）で確認した。
  import順序の整理のみでロジック変更を伴わないため新規の回帰テストは不要と判断し、
  `python -m pytest tests/ -v`で5855件全件パス・1件skip（既存件数のまま、flaky testの
  新規発生なし）を確認した。
