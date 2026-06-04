# 優先度 M 特性 実装計画 インデックス

作成日: 2026-06-04

## 実装推奨順

| # | 特性 | 計画書 | 複雑度 |
|---|------|-------|--------|
| 1 | ドラゴンスキン | [ability_ドラゴンスキン.md](ability_ドラゴンスキン.md) | 低（フェアリースキン転用） |
| 2 | おみとおし | [ability_おみとおし.md](ability_おみとおし.md) | 低（switch-in 系） |
| 3 | ふしぎなまもり | [ability_ふしぎなまもり.md](ability_ふしぎなまもり.md) | 低（ON_TRY_MOVE_1 ガード） |
| 4 | とびだすハバネロ | [ability_とびだすハバネロ.md](ability_とびだすハバネロ.md) | 低（ON_DAMAGE_HIT やけど付与） |
| 5 | へんしょく | [ability_へんしょく.md](ability_へんしょく.md) | 中（ON_DAMAGE タイプ変化） |
| 6 | ふうりょくでんき | [ability_ふうりょくでんき.md](ability_ふうりょくでんき.md) | 中（ON_DAMAGE + ON_FIELD_ACTIVATE） |
| 7 | さまようたましい | [ability_さまようたましい.md](ability_さまようたましい.md) | 中（ON_DAMAGE_HIT 特性交換） |
| 8 | とびだすなかみ | [ability_とびだすなかみ.md](ability_とびだすなかみ.md) | 高（ON_DAMAGE_HIT + ON_MOVE_KO、HP事前保存） |
| 9 | おもかげやどし | [ability_おもかげやどし.md](ability_おもかげやどし.md) | 中（フォルム依存・発動回数管理） |

## 共通メモ

- `ON_DAMAGE_HIT` 発火時は damage > 0 が担保されているため `ctx.move_damage > 0` ガード不要
- 風技の識別は `move.has_label("wind")`（ラベルリストの手書き不要）
- わるあがきは `move.type == ""` → `not move_type` で除外
- とびだすなかみは `ON_MOVE_KO` を使う（ON_DAMAGE は存在しない）
