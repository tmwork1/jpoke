# flakyテスト根本原因修正レポート

## 前提: mainブランチとの重複調査

作業開始時に `loop/review/flaky-fix` ブランチ（`review/integration` から分岐、main との
マージベースは古い時点）と `main` の乖離を確認したところ、`main` 側では
「flakyの即時main反映ルール」に基づき、対象リストの大半のテストが既に個別コミットで
修正済みであることが判明した（`ae243ffa`, `34a3bee9`, `50df14e1`, `9c101de2`, `8f665d17`,
`b2873d78`, `6a2f709c`, `4a40424f`, `19b24b9f` 等）。本ワークツリーは分岐が古いためこれらの
修正を含んでおらず、`ごりむちゅう_特殊技には効果がない` のみ main に存在しない
（レビューループでのみ追加された未マージのテスト）ため独自調査が必要だった。

方針として、main で既に検証済みの修正内容をこのワークツリーの該当テスト・実装に移植し、
`ごりむちゅう` のみ新規に原因調査・修正を行った。

## 修正したテスト一覧と原因

- `test_field.py::test_オーロラベール_ひかりのかべとは重複しない`: 原因: fix_random漏れ（急所
  （1/24）で壁の軽減が無視されダメージ比較が崩れる）→ `t.fix_random(battle, 0.99)` を追加
- `test_field.py::test_オーロラベール_リフレクターとは重複しない`: 同上 → `t.fix_random(battle, 0.99)` を追加
- `test_field.py::test_リフレクター_ワンダールーム中でも物理技を軽減する`: 原因: fix_random漏れ
  （急所で壁の軽減が無視される）→ `t.fix_random(battle, 0.999)` を追加
- `test_field.py::test_サイドフィールド_ダメージ軽減`（パラメトライズ全ケース）: 同上 →
  `t.fix_random(battle, 0.999)` を追加
- `test_move_ma.py::test_むしくい_ねんちゃく持ちをひんしにさせた場合は奪える`: 原因:
  `fix_random`では制御できないまひの行動不能判定（`getrandbits`系）が未固定で、稀に攻撃側が
  まひで行動不能になりテストの前提が崩れる → `battle.test_option.trigger_ailment = False` を
  追加してまひによる行動不能そのものを発生させないようにした
- `test_move_ma.py::test_ミラーコート_まねっこでコピーできる`: 原因: fix_random漏れ（10まんボルト
  の追加効果确率とダメージロールが未固定で、追加効果（まひ）が発生すると後続の行動順・状態が
  崩れる）→ `t.fix_random(battle, 0.5)` を追加（命中は通過しつつ追加効果は発生しない値）
- `test_ability_ka.py::test_ごりむちゅう_特殊技には効果がない`: 原因: 命中率固定漏れ。
  だいもんじの命中率は85%で `accuracy=100` の指定がなかったため、稀に技が外れると
  `damage_calculator.atk_modifier` がダメージ計算未実行のため `None` のままとなりアサーション
  に失敗する。近隣の物理技版テスト（`test_ごりむちゅう_物理技の攻撃1_5倍`）はじしん（命中100%）
  を使っていたため気づかれていなかった → `accuracy=100` を追加
- `test_item_ta.py::test_だっしゅつパック_わるいてぐせに奪われた場合は発動しない`: 原因:
  fix_random漏れ（急所だと1発で瀕死になり、わるいてぐせの発動条件「被弾側が生存」を満たせない）
  → `battle.random.random = lambda: 0.9` を追加
- `test_item_ta.py::test_だっしゅつボタン_ちからずくの効果が発動した技を受けたときは発動しない`:
  同様の原因（急所で瀕死→強制交代によりactive_indexが変わる）→
  `battle.random.random = lambda: 0.9` を追加
- `test_move_ka.py::test_くらいつく_ちからずくでも威力上昇せず効果は発動する`: 原因:
  fix_random漏れ（急所で相手がひんしになると使用者側ににげられない状態が付与されない）→
  `t.fix_random(battle, 0.999)` を追加
- `test_move_ka.py::test_くらいつく_相手がりんぷんでも効果は発動する`: 同上 →
  `t.fix_random(battle, 0.999)` を追加
- `test_move_ka.py::test_くらいつく_相手と自分の両方をにげられない状態にする`: 同上 →
  `t.fix_random(battle, 0.999)` を追加
- `test_move_ta.py::test_DDラリアット_相手のぼうぎょランクを無視する` /
  `test_DDラリアット_相手のぼうぎょランク低下も無視する`: 原因はテスト側ではなくプロダクション
  コード側。`Battle.roll_damage()` の通常ロール抽選が `self.random.choice(damages)`
  （内部で `getrandbits()` を使用）のままだったため、`battle.random.random = lambda: 0.9` で
  固定しても2つの独立した `Battle`（各々シードが異なる）間でダメージロールの選択インデックスが
  揃わず、ダメージ比較が偶発的に食い違っていた。テスト側は既に乱数固定コードを持っていたため、
  根本原因はプロダクションコード側と判断 → `Battle.roll_damage()` を
  `index = min(int(self.random.random() * len(damages)), len(damages) - 1)` による
  `random()` ベースの選択に書き換え（`self.random.choice(damages)` を廃止）。この変更は
  main側で既に検証済みのパターン（2026-07-11 の roll_damage 修正、および境界クランプを追加した
  Fableレビュー対応）をそのまま移植したもの。`damage_roll` が "最大"/"最小"/"平均" のテストは
  この分岐を通らないため影響なし。修正後、フルスイート実行（4回連続、うち3回は本タスクの
  検証手順、1回は追加確認）で全件成功を確認済み。

## 修正しなかった項目（あれば）

なし。指示書に列挙された全対象テストについて原因を特定し修正した。

## 検証

- 上記の各テストを単独実行し全てパスすることを確認
- `python -m pytest tests/ -q` をフルスイートで計4回連続実行し、いずれも
  `5109 passed, 0 failed, 1 skipped` で安定することを確認（既存の1件のskipは本タスクと無関係）
- `scripts/sort_tests.py` で修正対象ファイルを五十音順に再整列、
  `scripts/generate_test_list.py` で `.internal/tests/` を再生成し、再度フルスイートを3回連続実行して
  全件成功を再確認
