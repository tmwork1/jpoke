# 5度目のラウンド（2026-07-12、フレッシュな視点での再調査 + 実装）

[← 目次に戻る](../README.md)

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

