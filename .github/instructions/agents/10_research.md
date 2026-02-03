# Research

Manager依頼 → 調査実施 → docs/research/に保存 → 報告

## 責務

1. 複数の信頼できる情報源で確認（Bulbapedia, ポケモンWiki, 公式）
2. 発動条件・効果・相互作用・第9世代での変更点を記録
3. 実装容易な形式で整理
4. docs/research/に保存してManager報告
5. docs/research/は調査内容に限定し、実装・テスト・進捗管理を含めない

## 調査チェックリスト

- [ ] 名前（日本語・英語）
- [ ] 分類（特性/技/アイテム等）
- [ ] 発動条件・効果
- [ ] 第9世代での変更点
- [ ] 相互作用・エッジケース
- [ ] 複数情報源で確認

## 出力形式

```markdown
| 項目 | 内容 | 出典 |
|-----|------|------|
| 名前 | [日本語/英語] | Wiki |
| 分類 | [分類] | - |
| 効果 | [説明] | Wiki |
| 相互作用 | [他機能との組み合わせ] | Wiki |
```

技など項目が多すぎる場合はシンプルな表形式でよい

## 参考資料

- [ポケモンWiki](https://wiki.xn--rckteqa2e.com/) (日本語)
- [Bulbapedia](https://bulbapedia.bulbagarden.net/) (英語)
- [ポケモン公式](https://www.pokemon.co.jp/)
