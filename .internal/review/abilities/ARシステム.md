# ARシステム レビュー結果

## 仕様書
- 変更なし。`.internal/spec/abilities/ARシステム.md` は一次情報（ポケモンWiki）と照合し、内容は正確だった。

## 実装計画書
- `.internal/plan/abilities/ARシステム.md` を実際の実装内容に合わせて全面的に更新した。
  - 対応表が `src/jpoke/data/signature_items.py` の `MEMORY_TO_TYPE` に集約されていること、
    `Pokemon.ability_override_type` / `Pokemon.types` によるタイプ解決方式であることを明記。
  - 道具保護（自分の道具・相手の道具どちらも対象）の実装方式（`EventContext.is_exchange`）を明記。
  - 変更候補ファイルを実際に触ったファイル一覧に更新（旧計画書は存在しない `tests/test_ability.py` 等
    古いパスを参照していた）。
  - マルチアタック・へんしんが実装対象外／保留である旨、マルチタイプ側にも同種の抜けがある
    可能性がある旨を「保留・論点」に追記。

## 実装（handlers/ / data/）
- **道具交換ブロックの欠落を修正**: `ARシステム_prevent_item_change` は自分の持つメモリの
  奪取・交換のみをブロックしており、「相手がメモリを持っている場合も交換自体が失敗する」
  （仕様書のトリック/すりかえ/ギフトパスの節）が未実装だった。
  - `src/jpoke/core/context.py` の `EventContext` に `is_exchange: bool = False` を追加。
  - `src/jpoke/core/item_manager.py` の `can_change_item()` に `is_exchange` 引数を追加し、
    `swap_items()`（トリック/すりかえ/どろぼう等が内部的に使用する道具交換処理）から
    `is_exchange=True` を渡すようにした（はたきおとす等の一方的な除去では渡さないため
    影響しない）。
  - `handlers/ability.py` の `ARシステム_prevent_item_change` を、`is_exchange=True` の場合に
    相手（`battle.foe(mon)`）の道具もメモリかどうか判定するよう修正。
  - 修正前は `Pokemon('シルヴァディ', item_name='')` に対して
    `battle.item_manager.swap_items()` を呼ぶと、相手がメモリを持っていてもシルヴァディに
    メモリが渡ってしまう不具合があった（再現・修正確認済み）。
- **メモリアイテムの登録漏れを修正**: `src/jpoke/data/item.py` の `ITEMS` 辞書に
  `フェアリーメモリ` しか登録されておらず、残り16種（ファイトメモリ・フライングメモリ・
  ポイズンメモリ・グラウンドメモリ・ロックメモリ・バグメモリ・ゴーストメモリ・
  スチールメモリ・ファイアーメモリ・ウォーターメモリ・グラスメモリ・エレクトロメモリ・
  サイキックメモリ・アイスメモリ・ドラゴンメモリ・ダークメモリ）が `ItemName` 型にも
  `ITEMS` 辞書にも存在しなかった。そのため `Pokemon(..., item_name="ファイトメモリ")` は
  `KeyError` になり、ARシステムの効果を17種のうち1種でしか検証できていなかった。
  - `フェアリーメモリ` と同じ形式（`fling_power=50`、ハンドラなし）で16種を追加登録。
  - `python scripts/generate_literals/generate_item_literal.py` を実行して `ItemName` 型を再生成。
  - 五十音順ソート（`sort_items.py`）はマージ後に一括整形するため今回は未実行。
- 上記以外の既存実装（`ARシステム_apply_type`、`_apply_multitype` 共通ロジック、
  `flags={"uncopyable", "protected", "gas_proof"}`）は仕様と一致しており変更なし。

## リーサル計算
- 対象外（`.internal/progress/ability.md` のリーサル実装列が `n/a`）。ARシステムはタイプ変更のみで
  ダメージ計算に直接関与しないため、リーサルハンドラの対象にならない。

## テスト
- `tests/abilities/test_ability_a.py`
  - 既存のパラメタライズテスト `test_ARシステム_メモリで対応タイプになる` は
    `ITEMS` 辞書に存在するメモリのみでパラメタライズしていたため、アイテム登録漏れの修正により
    自動的に1ケースから17ケースへ拡大した（テストコード自体の変更は不要）。
  - 新規追加:
    - `test_ARシステム_自分のメモリの奪取交換を防ぐ`
    - `test_ARシステム_メモリなしなら自分の道具変更は防がれない`
    - `test_ARシステム_相手がメモリを持つ場合トリックすりかえ相当の交換が失敗する`
      （`is_exchange` 修正の回帰テスト。修正前はこのテストが失敗することを確認済み）
    - `test_ARシステム_相手がメモリを持たなければ通常の道具変更を防がない`
    - `test_ARシステム_はたきおとすは相手の道具に影響されない`
      （`is_exchange=False` の一方的な除去では相手の道具に影響されないことを確認）
  - `python scripts/sort_tests.py tests/abilities/test_ability_a.py` と
    `python scripts/generate_test_list.py` を実行済み。
  - `python -m pytest tests/ -v` で 4683 passed, 1 skipped（全件成功）。
    ログ: `.loop/test_logs/ARシステム.log`
