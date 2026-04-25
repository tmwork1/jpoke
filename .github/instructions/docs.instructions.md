---
applyTo: "docs/**/*.md,README.md,.github/**/*.md"
description: "このリポジトリの計画書、調査メモ、README、Copilot 指示書を更新する時に使う。"
---

# 文書更新指示

## 文書を現在形に保つ
- リポジトリ内に実在するファイルとモジュールだけを参照する。
- 古い計画を積み増すより、古い内容を置き換えることを優先する。
- `.github/` の案内は簡潔に保つ。ほぼ同じことを言うファイルが複数あるなら統合する。

## ディレクトリの役割
- `spec/`: 調査結果と挙動仕様の参照（トップレベル）。
- `plan/`: 現在の実行計画と優先順位（トップレベル）。
- `progress/`: カテゴリ別の実装追跡（トップレベル）。
- `README.md`: プロジェクト全体像と最新の集計サマリ。

## 計画書の書き方
- コアなバトル基盤は概ね揃っており、残る量の中心が特性、アイテム、技である現状を反映する。
- 現在のコードで本当に未解決な補助機構だけを書く。`ability_manager`・`item_manager`・`command_manager`・`status_manager` はすでに存在する。
- 実装数を書くときは `dashboard.json` と整合させる。

## 指示書ファイルの扱い
- リポジトリ全体の既定ルールは `copilot-instructions.md` に置く。
- ファイル単位のルールは `.instructions.md` に置く。
- `.github/instructions/` に、実装判断へ直接効かない migration log や changelog は置かない。