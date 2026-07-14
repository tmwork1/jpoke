# 第6ラウンド（apiループ）

[← 目次に戻る](../README.md)

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

- [x] `battle.query`（`PokemonQuery`）が公開属性なのに大半のメソッドが未文書化・未委譲
  （developer視点、id: r6-2） → 対応内容 (2026-07-13): `battle.query`は`Battle`の公開属性
  （`self.query = PokemonQuery(self)`）だが、`can_switch()`以外の判定メソッド
  （`has_available_bench`/`is_floating`/`is_trapped`/`is_nervous`/`is_hazard_immune`/
  `can_use_last_resort`/`get_forced_move_name`/`is_first_actor`/`is_second_actor`等）は
  `Battle`直下にラッパーが無く、`docs/api/README.md`にも未掲載で、外部利用者が
  `battle.query.<method>()`という非公開想定の内部経路を直接呼ぶしかない状態だった。
  `Pokemon`/`Player`単体の引数で完結する上記9メソッドを`Battle`直下に薄い委譲として追加し、
  `docs/api/README.md`「状態取得系」節に一覧表とコード例を追記、`CHANGELOG.md`の
  `[Unreleased]`/`[Added]`にも追記した（`src/jpoke/core/query.py`の各メソッド docstring と
  1つずつ突き合わせ、追加した`Battle`側 docstring の記述に齟齬が無いことを確認済み）。
  `AttackContext`/`EventContext`を要求する内部専用メソッド（`is_contact`/`is_contact_reaction`/
  `is_super_effective`/`is_not_very_effective`/`resolve_move_category`/`deals_physical_damage`/
  `get_volatile_duration`）は対象外のまま維持した。`is_first_actor`/`is_second_actor`は
  行動順未確定時に`bool | None`で`None`を返す仕様、`has_available_bench`は`can_switch`と異なり
  とらわれ状態（にげられない・バインド等）を無視して控えの生存のみで判定する仕様であることを
  `src/jpoke/core/query.py`の実装（`self.battle.turn_controller.action_order`の空判定、
  `state.bench`の`fainted`判定のみで`is_trapped`を経由しない実装）で確認し、いずれも
  ドキュメント・docstringの記述と一致していることを検証した。回帰テストとして
  `tests/test_query.py`を新規作成し、追加した9メソッドそれぞれについて委譲が正しく機能する
  ことを確認する軽量テスト14件（`has_available_bench`/`is_trapped`は`can_switch`との違いや
  ゴーストタイプ免除等のエッジケースも含め各2件、他は正常系中心に1〜2件）を追加した。
  `python -m pytest tests/ -v`は5570 passed, 1 skipped, 0 failedで全件成功
  （本ラウンドの変更に起因する失敗なし）。

- [x] シナリオ構築系メソッドの動詞が`set_*`/`activate_*`で不統一（developer視点、id: r6-3）
  → 対応内容 (2026-07-13): `set_ailment`/`set_volatile`/`set_weather`/`set_terrain`と
  `activate_global_field`/`activate_side_field`の動詞の違いを調査した結果、実装上の裏付けの
  ある意図的な設計であることを確認した。`set_*`は排他的な単一状態の直接セット
  （`ExclusiveFieldManager.apply()`/対象ポケモンに紐づく個別状態への委譲）、`activate_*`は
  複数効果が同時にスタックしうるフィールド効果の発動（`StackableFieldManager.activate()`への
  委譲）という区別があり、リネームは不要と判断した。`count`のデフォルト値差についても、
  天候・地形は通常の発動元（技・特性）が例外なく5ターンで発動する一方、グローバル/サイド
  フィールド効果は技によって持続ターンの意味がバラバラ（フェアリーロックのみ1ターン、壁技は
  5ターン、設置技は1層ずつ、みらいよち等の遅延効果は発動までのターン数）なため、単一の
  デフォルト値を設けると誤ったシナリオを組む恐れがあり、デフォルト値の新設は見送った。
  `src/jpoke/core/battle.py`の該当6メソッドのdocstringに動詞使い分けの説明を追記し、
  `docs/api/README.md`のシナリオ構築系表に`activate_global_field`/`activate_side_field`の
  行を追加（副次的な記載漏れ発見）、「`set_*`と`activate_*`の使い分け」節を新設した。
  レビュー時に、天候の`count=5`根拠説明が不正確だったことを発見し修正した：当初の記述は
  「天候を発動する全ての技・特性ハンドラが例外なく5ターンで発動している」としていたが、
  実際には強天候（おおひでり・おおあめ・らんきりゅう）を発動する特性（`おわりのだいち`等）は
  `count=1`で発動しており（`handlers/ability.py`）文言と矛盾していた。調査の結果、強天候の
  `FieldData`（`data/field/weather.py`）には`ON_TURN_END`のターンカウントダウンハンドラが
  そもそも登録されておらず、`count`の値に関係なく特性保持者が場を離れるまで持続する仕様
  であることを確認し、「通常天候は全ハンドラが例外なく5ターン。強天候の`count=1`は
  ターン経過による自然消滅の仕組みを持たないため実質無視される値であり、既定値5の判断には
  影響しない」という正確な記述に修正した（`battle.py`の`set_weather`docstringと
  `docs/api/README.md`の両方）。公開APIのシグネチャ変更はないため`CHANGELOG.md`更新は
  不要と判断した。docstringのみの変更でロジック変更はないため新規テストは追加せず、
  `python -m pytest tests/ -v`で5571 passed, 1 skipped, 0 failedの全件成功を確認した
  （既存テストと無関係のflaky事象は発生せず）。

- [x] `judge_winner() is None`パターンがexamples/05_benchmarkと04_researchの計3ファイルに
  再発している（developer視点、id: r6-4） → 対応内容 (2026-07-13): `battle.judge_winner()`は
  呼ぶたびにTOD判定込みで再計算する重い遅延判定APIであり、決着したかどうかの単純なチェックには
  軽量な`battle.finished`（`self.winner`のキャッシュを経由）と、勝者取得には`battle.winner`を
  使うべきという規約になっているが、`examples/05_benchmark/01_step_time_benchmark.py`の
  ループ継続条件と、`examples/04_research/03_janken_nash_fictitious_play.py`・
  `04_janken_nash_cfr.py`のループ継続条件・勝者取得の計3ファイルで
  `battle.judge_winner() is None`パターンが残っていた。3ファイルとも
  `while battle.judge_winner() is None and ...` を `while not battle.finished and ...` に、
  `winner = battle.judge_winner()` を `winner = battle.winner` に置き換えた。
  `battle.winner`はwhileループの条件判定で毎周`battle.finished`（内部で`judge_winner()`を
  呼びキャッシュを更新する）を経由してから参照される構造になっており、ループが1周も
  回らない場合でも条件判定自体は必ず1回評価されるため、`battle.winner`参照前に必ず
  `judge_winner()`が呼ばれてキャッシュが更新されていることを`core/battle.py`の
  `finished`/`winner`プロパティ実装で確認した。3ファイルを個別実行し、従来通り動作する
  （`01_step_time_benchmark.py`はベンチマーク結果を出力、`03_janken_nash_fictitious_play.py`は
  Nash近似の反復ログを出力、`04_janken_nash_cfr.py`は600エピソードのCFR自己対戦を完走し
  状態別戦略表を出力）ことを確認した。回帰テストとして`tests/test_code_conventions.py`に
  `test_examplesがjudge_winnerのis_None比較を使っていない`（`examples/`配下を静的走査し、
  `judge_winner()`の`is None`/`is not None`直接比較が無いことを検証する軽量テスト。
  `judge_winner()`自体はAPIとして今後も使われてよいため、None比較のみを禁止対象とした）を
  追加した。`python -m pytest tests/ -v`は5574 passed, 1 skipped, 0 failedで全件成功
  （本ラウンドの変更に起因する失敗なし）。

- [x] `GIGAMAX_*`/`ZMOVE_*`コマンドがAPIリファレンスに載っているが実装上は無効でわるあがきに
  化ける（beginner視点、id: r6-5） → 対応内容 (2026-07-13): `docs/api/README.md`の`Command`章
  （定数表・クラスメソッド表・プロパティ表）は`GIGAMAX_*`/`ZMOVE_*`を他の技コマンドと並列に
  掲載しており、初見の利用者がダイマックス・Zワザに対応していると誤解する構成だった。実際には
  `src/jpoke/core/command_manager.py`の`get_available_action_commands()`はこれらを候補として
  一切生成せず（通常技・メガシンカ・テラスタル・交代・わるあがきのみ）、`resolve_move_from_command()`
  も`command.is_gigamax`/`command.is_zmove`のいずれかが真なら無条件で`Move("わるあがき")`を返す
  実装（143〜147行目）であることをコードで確認した。本プロジェクトの対象範囲
  （ポケモンチャンピオンズのシングルバトル、README.md「対象範囲」節）にダイマックス・Zワザは
  存在しないため未実装であること自体は仕様通りだが、ドキュメント上でその旨が説明されておらず、
  利用者が`Command.GIGAMAX_0`等を選んでも黙ってわるあがきになる罠になっていた。`docs/api/README.md`
  の該当3表（定数・クラスメソッド・プロパティ）の`GIGAMAX_*`/`ZMOVE_*`行に
  「（**未実装**、下記/上記注記参照）」を追記し、定数表の直後に注記ブロックを新設して
  未実装の理由・`get_available_commands()`が候補に含めないこと・明示的に渡した場合は常に
  わるあがき扱いになることを説明した。注記内の相対リンク`../../README.md#対象範囲`
  （`docs/api/README.md`→ルート`README.md`）がルート`README.md`12行目の`## 対象範囲`見出しに
  正しく解決することを確認した。回帰テストとして`tests/test_command.py`を新規作成し、
  `get_available_commands()`が`GIGAMAX_*`/`ZMOVE_*`を候補に含めないこと、`battle.command_to_move()`
  （`command_manager.resolve_move_from_command()`への公開委譲）に`GIGAMAX_0`/`ZMOVE_0`を明示的に
  渡すと`Move("わるあがき")`が返ることを検証する軽量テスト計4件を追加した。
  `python -m pytest tests/ -v`は5578 passed, 1 skipped, 0 failedで全件成功
  （本ラウンドの変更に起因する失敗・既存テストのflaky事象なし）。

- [x] `n_selected`省略時の自動設定が両者に同じ値が適用されることを`docs/api/README.md`が
  明記していない（beginner視点、id: r6-6） → 対応内容 (2026-07-13): `docs/api/README.md`の
  `n_selected`説明は「省略時は`min(3, 各プレイヤーの手持ち数)`が自動設定される」とだけ書かれており、
  この`min`が「プレイヤーごとに個別計算される」のか「両プレイヤーの手持ち数をまとめて1つの値に
  丸める」のかが読み手には曖昧だった。`src/jpoke/core/battle.py`の実装
  （`self.n_selected = n_selected if n_selected is not None else min(3, min(len(ply.team) for ply in
  players))`）を確認し、全プレイヤーの手持ち数を`min()`で1つに集約してから3と比較する、
  すなわち片方の手持ちが少ないと両者とも選出数が絞られる仕様であることを確認した。
  `docs/api/README.md`の`n_selected`説明に「手持ち数がプレイヤー間で異なる場合も両者に同じ値が
  適用されるため、片方の手持ちが少ないと両者とも選出数が絞られる点に注意」を追記した。
  `src/jpoke/core/battle.py`の`__init__`docstringには既に同趣旨の注記
  （146〜148行目）が存在しており、両者の記述に齟齬が無いことを確認した（コード変更なし、
  ドキュメントのみの修正）。回帰テストは追加していない（ドキュメント文言のみの修正であり、
  検証すべき静的な文字列パターンや振る舞いの変化が無いため）。`python -m pytest tests/ -v`は
  5627 passed, 1 skipped, 0 failedで全件成功（本ラウンドの変更に起因する失敗・既存テストの
  flaky事象なし）。

- [x] `decision_random`の種が`PYTHONHASHSEED`に依存し、同一seedでもプロセスを跨ぐと再現しない
  （ai_developer視点、id: r6-7） → 対応内容 (2026-07-13): `Battle.decision_random`（行動選択専用の
  乱数生成器）の種の派生式が`hash((self.seed, "decision")) & 0xFFFFFFFF`だったが、`str`を含む
  `tuple`の`hash()`は`str`のハッシュが`PYTHONHASHSEED`によりプロセスごとにランダム化される
  影響を受けるため、同じ`seed`を指定しても`decision_random`が生成する乱数列がプロセスを
  跨ぐと再現しない不具合があった（`RandomPlayer.choose_command()`/`TreeSearchPlayer.fallback()`
  はこの乱数列を消費するため、これらを経由するコマンド選択の再現実験・CI比較が壊れうる
  問題だった）。`Battle.__init__`と`Battle.copy(reseed=True)`の2箇所を、整数の算術演算のみで
  `PYTHONHASHSEED`に依存しない`(self.seed + 0x9E3779B9) & 0xFFFFFFFF`（ハッシュ撹拌でよく
  使われる黄金比由来の定数、Boost `hash_combine`等で使われる`0x9E3779B9`）に変更した。
  加算する定数が0でないため`mod 2**32`上で不動点を持たず（`x ≡ x+C (mod 2**32)`は
  `C ≡ 0 (mod 2**32)`のときのみ成立するため、`C = 0x9E3779B9 ≠ 0`である限りあらゆる`seed`で
  成立しない）、`self.random`（種は`seed`そのもの、`seed`が32bit範囲内である前提）と
  衝突しないことを数学的に確認した。レビュー時に、impl側が採用した定数`0x9E3779B1`が
  実際の黄金比由来の定数（`2^32 / φ ≈ 2654435769.5 = 0x9E3779B9`）から8ずれていることを
  発見し、コード・コメント・`CHANGELOG.md`を`0x9E3779B9`に修正した（機能上はどちらの値でも
  非ゼロなら衝突しないため正しく動作するが、コメントが「黄金比由来の値」と明記している以上
  実際の定数と一致させるべきと判断した）。`Battle.copy(reseed=True)`側の`new.seed = hash((self.seed,
  self._reseed_count)) & 0xFFFFFFFF`は要素がすべて`int`のタプルであり、`PYTHONHASHSEED`は
  `str`/`bytes`/`datetime`のハッシュのみをランダム化する（`int`のハッシュ・タプルの結合
  アルゴリズム自体はランダム化されない）ため対象外であることを確認した。`CHANGELOG.md`に
  破壊的変更として明記済み（同じ`seed`でも`decision_random`が生成する具体的な乱数列は
  旧バージョンから変わる。ゲーム進行用の`Battle.random`の乱数列には影響しない）。
  回帰テストとして`tests/test_poke_env_compat.py`に
  `test_battle_decision_randomの種はpythonhashseedに依存しない`を追加した。異なる
  `PYTHONHASHSEED`環境変数（`"0"`/`"12345"`）を設定した2つのサブプロセスで同一の
  `Battle(seed=12345)`を作り、`decision_random.getstate()`が完全に一致することを確認する
  （修正前の式に戻すと`PYTHONHASHSEED`ごとに異なる状態になることを手動検証済み）。
  `python -m pytest tests/ -v`実行中に、本ラウンドの変更とは無関係な既存のflaky testを1件
  発見し、その場で修正した（§共通13）。`tests/items/test_item_sa.py`の
  `test_じゃくてんほけん_マジシャンより先に発動して奪われない`が、`critical_mode`未指定
  （デフォルト"normal"）のため`battle.random`の急所判定がまれに成立し、フシギダネが
  かえんほうしゃの効果抜群クリティカルヒットで1発瀕死になることがあった。既存の
  `test_じゃくてんほけん_瀕死になったときは発動しない`の仕様通り、瀕死になった場合は
  じゃくてんほけんが発動しないため被弾側が生存する前提のこのテストの検証が崩れ、
  代わりにマジシャンがアイテムを奪う（=`not foe.has_item()`は成立するがブースト量が
  `0`になり`assert foe.boosts["atk"] == 2`が失敗する）間欠的な失敗だった。他の既存テスト
  （`test_だっしゅつパック_わるいてぐせに奪われた場合は発動しない`等）と同じ`t.fix_random(battle,
  0.99)`（急所を回避する乱数固定）パターンを追加して解消し、該当テストを20回連続実行して
  収束（毎回成功）することを確認した。`python -m pytest tests/ -v`は5630 passed, 1 skipped,
  0 failedで全件成功（2回連続実行して収束を確認済み）。

- [x] `TreeSearchPlayer.evaluate()`の既定実装が公開APIの`get_team()`を使わず内部構造に
  直接アクセスしている（ai_developer視点、id: r6-8） → 対応内容 (2026-07-13):
  `src/jpoke/players/tree_search_player.py`の`evaluate()`既定実装（残りHP割合差）が
  `battle.player_states[target].team`という内部管理用属性（`player_states`は
  `Battle`の実装詳細でCLAUDE.mdの規約上も外部APIは`battle.<manager>.<method>()`ではなく
  公開メソッドを入口にすべき対象）に直接アクセスしていた。`battle.get_team(target)`
  （`docs/api/README.md`にも掲載済みの公開メソッド）へ1行置き換えた。
  `battle.get_team()`の実装（`src/jpoke/core/battle.py`）を確認したところ
  `return self.player_states[player].team`そのものであり、置き換え後も返す
  リストの中身・順序は完全に同一（副作用は「対象プレイヤーが`player_states`に
  存在しない場合の例外が`KeyError`から`ValueError`に変わる」点のみだが、
  `evaluate()`は`Battle`が構築した既知のプレイヤーしか渡さないため実害なし）で
  あることを確認した。公開APIのシグネチャ変更はなくドキュメント記載も既存のまま
  で問題ないため`CHANGELOG.md`更新は不要と判断した。回帰テストとして
  `tests/test_tree_search_framework.py`に
  `test_evaluateの既定実装がget_team経由で対戦中の実データを反映する`を追加した。
  対戦開始後にアクティブのHPを`battle.modify_hp()`で変化させ、ベンチの1体を
  `battle.modify_hp(..., r=-1.0)`で瀕死にした上で`player1.evaluate(battle)`を呼び、
  `battle.get_team()`から手計算した期待値（瀕死個体を除外した残りHP割合の差）と
  一致することを確認する内容で、コンストラクタ時点の`player.team`スナップショット
  ではなく対戦中の実データが使われていることを間接的に検証する。
  `python -m pytest tests/ -v`は5631 passed, 1 skipped, 0 failedで全件成功
  （本ラウンドの変更に起因する失敗・既存テストのflaky事象なし）。

- [x] `TreeSearchPlayer.evaluate_commands()`が`max_nodes`を無条件に無効化することが
  docstringで警告されていない（ai_developer視点、id: r6-9） → 対応内容 (2026-07-13):
  `evaluate_commands()`の実装（`src/jpoke/players/tree_search_player.py`）は呼び出し中
  `self.max_nodes`を`None`（無制限）に一時的に上書きし、`finally`節で呼び出し前の値へ
  復元する仕様だが、この挙動がdocstringに明記されておらず、`max_nodes`でコストを抑えている
  つもりの利用者が`choose_command()`の呼び出しごとにこのメソッドも呼ぶデバッグ表示等に
  組み込むと、意図せず全合法手×全合法手の打ち切りなし評価が毎ターン走りコストが
  想定外に膨らむ恐れがあった。`evaluate_commands()`のdocstringに「呼び出し中は`max_nodes`を
  一時的に無効化し、`max_plies`の深さまで打ち切りなく評価するため実行コストが
  `max_plies`が大きいほど大きくなりうる」旨の注意書きを追記した。また
  `examples/02_ai/03_priority_and_command_debug.py`の`DebugPlayer`（`choose_command()`の
  たびに`evaluate_commands()`を呼び出すデバッグ用サブクラス、`max_nodes=50`で構築される
  実例）のdocstringにも同様の注意書きを追記し、このサンプル構成をそのまま学習ループの
  可視化等へ転用する場合の注意を促した。いずれもコメント・docstringのみの変更で
  ロジック変更はない。回帰テストとして`tests/test_tree_search_framework.py`に
  `test_evaluate_commandsがmax_nodesを無視して全合法手を評価する`を追加した。
  `max_nodes=1`という極端に小さい値を設定した状態で`evaluate_commands()`を呼び出し、
  `_best_command()`のようにノード数上限で打ち切られていれば未評価コマンドの評価値が
  `float("inf")`のまま残るところ、実際は全コマンドが有限値で返ることを確認し、
  さらに呼び出し後に`max_nodes`・`nodes_expanded`とも呼び出し前の値へ復元されていることも
  合わせて確認する内容。`python -m pytest tests/ -v`は5664 passed, 1 skipped, 0 failedで
  全件成功（本ラウンドの変更に起因する失敗・既存テストのflaky事象なし）。

- [x] `observation_builder.py`のモジュールグローバル辞書がスレッド安全でない
  （ai_developer視点、id: r6-10） → 対応内容 (2026-07-13):
  `src/jpoke/core/observation_builder.py`の`OBSERVED_MOVE_INDEXES`はモジュールグローバルな
  `dict[Pokemon, dict[int, int]]`で、`_mask()`が呼び出しのたびに`OBSERVED_MOVE_INDEXES = {}`で
  丸ごと再代入し（63〜64行目）、`_mask_move()`がポケモンごとに書き込み（181〜189行目）、
  `_mask_command()`が同じ呼び出し内で読み出す（213行目）という、1回の`build()`呼び出し内で
  完結する前提の実装だった。複数スレッドから同時に`build()`（内部実装）／
  `Battle.build_observation()`（公開API）を呼び出すと、あるスレッドの`_mask()`が
  `OBSERVED_MOVE_INDEXES = {}`で辞書を丸ごと差し替えるタイミングで、別スレッドが
  書き込み途中・読み出し途中の内容を失ったり存在しないキーを参照したりして壊れる
  （`KeyError`または誤ったコマンドインデックス対応）可能性がある。この注記が
  `build()`にも`build_observation()`にも存在せず、`ThreadPoolExecutor`で自己対戦データ収集を
  並列化しようとする`ai_developer`が気づかずに踏む罠だった。`observation_builder.build()`と
  `Battle.build_observation()`の両docstringに`Warning`節を追加し、モジュールグローバル辞書を
  再代入・書き込み・読み出しする実装でスレッドセーフではないこと、並列化する場合は
  `ProcessPoolExecutor`等のプロセス並列を使うべきことを明記した。実装コード
  （`_mask()`/`_mask_move()`/`_mask_command()`の`OBSERVED_MOVE_INDEXES`の使われ方）を
  1行ずつ確認し、注記内容と実態に齟齬が無いことを確認済み。動作変更はなくドキュメントのみの
  修正のため回帰テストは追加していない。`python -m pytest tests/ -v`は5664 passed, 1 skipped,
  0 failedで全件成功（本ラウンドの変更に起因する失敗・既存テストのflaky事象なし）。

- [x] `Battle.activate_side_field()`がひかりのねんどによる持続ターン延長を反映しない
  （developer視点、id: r6-11） → 対応内容 (2026-07-14): 「調査中に判明した別課題」節で
  記録していた挙動差（`activate_side_field()`は`SideFieldManager`が継承する
  `StackableFieldManager.activate()`〔`field_manager.py:250`〕を使い、まきびし・どくびし等の
  重ね掛け（既にアクティブでも`max_count`未満なら`count`を+1する挙動）に対応する一方、
  `Event.ON_MODIFY_DURATION`を発火しないため「ひかりのねんど」による壁技の持続ターン延長を
  反映しない）を調査した。対応候補として挙がっていた「`activate_side_field`内で壁技かどうかを
  判定して`.apply()`に振り分ける」案は、`SideFieldManager.apply()`（`field_manager.py:355`）が
  既にアクティブな場合は無条件で`False`を返し重ね掛けに対応しないため、`.apply()`へ完全に
  置き換えると`まきびし`/`どくびし`等の重ね掛けシナリオ構築が壊れ「既存の挙動を一切変えない」
  という前提を満たせないと判断し、コード変更（`.apply()`への置き換え）は行わなかった。代わりに
  `Battle.activate_side_field()`のdocstringに既知の制約として、内部で`.activate()`を使う理由
  （重ね掛け対応）、`.apply()`との違い（`ON_MODIFY_DURATION`発火の有無、既にアクティブな場合の
  失敗挙動）、「ひかりのねんど」延長後の状態を再現したい場合の代替手段（延長後のターン数を
  呼び出し側で計算して`count`に渡すか、`run_move()`で実際に技を使わせる）を明記した。
  `SideFieldManager.apply()`/`StackableFieldManager.activate()`の実装（`field_manager.py`）と
  docstringの記述を1行ずつ突き合わせて齟齬が無いことを確認済み。既存の`tests/`配下を検索した
  結果`activate_side_field()`を直接呼ぶテスト（`src/jpoke/testing.py`の`start_battle()`が
  内部で使う`side0`/`side1`引数経由の呼び出しを含む）で「ひかりのねんど」延長を期待するものは
  無く、既存のひかりのねんどテスト（`tests/items/test_item_ha.py`）はいずれも`run_move()`
  （`.apply()`経由）で壁技を使わせる構成のため、本ドキュメント修正の影響を受けないことを
  確認した。回帰テストとして`tests/test_field.py`に
  `test_activate_side_field_ひかりのねんどによる延長は反映されない`を追加した。
  「ひかりのねんど」持ちのポケモンがいる状態で`activate_side_field(player, "リフレクター", 5)`
  を呼び出し、`run_move()`で実際に張った場合は8ターンに延長されるところ、指定した5ターンの
  ままであることを確認する内容（将来`.apply()`への置き換え等で挙動が変わった場合に検知できる）。
  `python -m pytest tests/ -v`は5665 passed, 1 skipped, 0 failedで全件成功
  （本ラウンドの変更に起因する失敗・既存テストのflaky事象なし）。

### 調査中に判明した別課題（次ラウンド候補）

- （スコープ外・未対応・**ハングを引き起こす重大バグ、次ラウンドでの調査を強く推奨**）
  `src/jpoke/core/switch_manager.py`の`_process_events_after_switch()`内
  `while self.battle.has_interrupt(): ...`ループが、特定のシード・チーム構成の組み合わせで
  無限ループしてプロセスがハングする潜在バグが存在する。だっしゅつボタン/だっしゅつパックの
  連鎖的な交代割り込み処理まわりが原因と推測されるが、根本原因は未調査。r6-7の対応時、
  `decision_random`の種派生式の対応案として当初検討していた`(seed*2+1) & 0xFFFFFFFF`を
  一時的に採用した状態で`examples/05_benchmark/01_step_time_benchmark.py`（`seed=0`,
  `n_battles=300`）を実行したところ、79戦目（`battle_seed=2115938757`）でこのバグを踏んで
  ハングすることが判明した。**このバグ自体は`decision_random`の変更が原因ではなく元から
  存在するバグであり**、`decision_random`の派生式を最終的に`(seed + 0x9E3779B9) & 0xFFFFFFFF`
  に変更したことで今回このシードは回避したが、**別のseedでは今後も再発しうる**。
  再現条件: `Random(0)`から79戦目に生成される`battle_seed=2115938757`（`decision_random`の
  種を`(seed*2+1) & 0xFFFFFFFF`にした場合に再現）。チーム構成:
  T1=モンメン（だっしゅつボタン）/コオリッポ/アメタマ、T2=シロデスナ/ププリン/グランブル。
  ハング（無限ループ）を引き起こす重大なバグのため、次のimplループやfuzzループでの
  調査を強く推奨する。

- （**対応済み・r6-11参照**）`Battle.activate_side_field()`は内部で`SideFieldManager`が継承する
  基底クラス`StackableFieldManager.activate()`（`field_manager.py:250`）をそのまま呼んでいるが、
  実戦の壁技ハンドラ（リフレクター等、`handlers/move_status.py`）は`SideFieldManager`が
  オーバーライドする`.apply()`（`field_manager.py:355`）を使っている。`.apply()`は
  `ON_MODIFY_DURATION`を発火して「ひかりのねんど」による持続ターン延長を反映するが、
  `.activate()`にはこのイベント発火が無い（層数スタック専用のロジックのみ）。そのため
  `battle.activate_side_field(player, "リフレクター", 5)`でシナリオ構築すると、実戦で
  「ひかりのねんど」持ちが壁を張った場合と異なり持続ターン延長が反映されない、という
  挙動差が存在する（`ステルスロック`/`まきびし`等の設置技は元々`.activate()`を使うため
  この差は影響しない）。`.apply()`は既にアクティブな場合は無条件で失敗し重ね掛けに対応しない
  ため`.apply()`へ完全に置き換えることはできないと判断し、第6ラウンド（id: r6-11）で
  `Battle.activate_side_field()`のdocstringに既知の制約として明記した。詳細は上記r6-11の
  対応内容を参照。

