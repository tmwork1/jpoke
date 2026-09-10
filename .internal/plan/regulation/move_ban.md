# 種族専用の技使用禁止（レギュレーションM-C）

## 背景

Pokemon Showdown champions modのフォーマット制限として、特定の種族と技の組み合わせに使用禁止が導入された。
この制限はps-champ-jaのデータスキーマの対象外であり、そのデータファイルには表れないため、jpoke独自の仕組みを追加した。
種族自体や技自体の使用可否は変わらない。

## 設計

既存の`get_pokemon_by_regulation` / `get_items_by_regulation`と同じパターンで、
公開クエリAPI `get_banned_moves(species, regulation)`を追加した。
`regulation/move_ban.csv`は`species`、`move`とレギュレーションごとの列を持ち、`1`を禁止として扱う。
現在は`M-C`列のみとし、将来の制限は列を追加して管理する。`implemented`列は不要とする。

読み込み時に同じ種族・レギュレーションの技を集約し、`PokemonData.banned_moves`に
`dict[Regulation, frozenset[MoveName]]`として保持する。該当する禁止がなければAPIは空の`frozenset`を返す。
種族名は`POKEDEX`、技名は`typing.get_args(MoveName)`で検証し、循環インポートを避けるため`data.move`は直接importしない。

既存の`regulations`と同様、外部のチーム構築・bot側が参照する公開クエリAPIとしてのみ提供する。
`Pokemon.learnset`や`Battle`の内部ロジック、技選択判定には一切組み込まない。

## 対象

| レギュレーション | 種族 | 使用禁止技 |
|---|---|---|
| M-C | ブリジュラス | ミラーコート・メタルバースト |
| M-C | ニョロトノ | はたく |
