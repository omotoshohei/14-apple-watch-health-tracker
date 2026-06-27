---
name: setup-project
description: 初回セットアップ: 6つの永続ドキュメントを対話的に作成する
---

# プロジェクト初回セットアップスキル

このスキルは、プロジェクトの初期段階で必要となる6つの永続ドキュメントを対話的に作成・整備するためのガイドです。

## 概要

このプロセスでは、以下の6つの永続ドキュメントを順に作成していきます。各ステップで対応する専用スキルを読み込み、連携しながら進めます。

1. `docs/product-requirements.md` ([prd-writing](../prd-writing/SKILL.md) スキル)
2. `docs/functional-design.md` ([functional-design](../functional-design/SKILL.md) スキル)
3. `docs/architecture.md` ([architecture-design](../architecture-design/SKILL.md) スキル)
4. `docs/repository-structure.md` ([repository-structure](../repository-structure/SKILL.md) スキル)
5. `docs/development-guidelines.md` ([development-guidelines](../development-guidelines/SKILL.md) スキル)
6. `docs/glossary.md` ([glossary-creation](../glossary-creation/SKILL.md) スキル)

---

## 実行前の確認

まず、インプットとなるアイデアファイルが `docs/ideas/` ディレクトリに存在するか確認します。

- `docs/ideas/` 配下のファイル（例: `initial-requirements.md` など）が存在する場合：
  - そのファイルの内容をインプットとして読み込み、PRD作成のベースとします。
- `docs/ideas/` 配下にファイルが存在しない場合：
  - ユーザーと対話しながらPRDのベースとなるアイデアを具体化していきます。

---

## セットアップ手順

### ステップ 0: インプットの読み込み
1. `docs/ideas/` ディレクトリ内のすべてのマークダウンファイルを確認し、読み込みます。
2. 内容を深く理解し、以降のプロダクト要求定義（PRD）作成のインプットとします。

### ステップ 1: プロダクト要求定義書 (PRD) の作成
1. [prd-writing](../prd-writing/SKILL.md) スキルの指示とテンプレートを確認します。
2. `docs/ideas/` のインプット、またはユーザーとの対話をもとに、`docs/product-requirements.md` のドラフトを作成します。
3. ユーザーストーリー、受け入れ条件、非機能要件、成功指標（KPI）を具体化します。
4. **重要**: 作成したドラフトを提示し、ユーザーから明示的な承認（Sign-off）を得るまで待機します。

### ステップ 2: 機能設計書の作成
1. [functional-design](../functional-design/SKILL.md) スキルの指示とテンプレートを確認します。
2. 承認された `docs/product-requirements.md` を読み込みます。
3. テンプレートに従って `docs/functional-design.md` を作成します。

### ステップ 3: アーキテクチャ設計書の作成
1. [architecture-design](../architecture-design/SKILL.md) スキルの指示とテンプレートを確認します。
2. これまでに作成されたドキュメントを読み込みます。
3. テンプレートに従って `docs/architecture.md` を作成します。

### ステップ 4: リポジトリ構造定義書の作成
1. [repository-structure](../repository-structure/SKILL.md) スキルの指示とテンプレートを確認します。
2. これまでに作成されたドキュメントを読み込みます。
3. テンプレートに従って `docs/repository-structure.md` を作成します。

### ステップ 5: 開発ガイドラインの作成
1. [development-guidelines](../development-guidelines/SKILL.md) スキルの指示とテンプレートを確認します。
2. これまでに作成されたドキュメントを読み込みます。
3. テンプレートに従って `docs/development-guidelines.md` を作成します。

### ステップ 6: 用語集の作成
1. [glossary-creation](../glossary-creation/SKILL.md) スキルの指示とテンプレートを確認します。
2. これまでに作成されたドキュメントを読み込みます。
3. テンプレートに従って `docs/glossary.md` を作成します。

---

## 完了条件

- 以下の6つの永続ドキュメントがすべて正しく作成され、保存されていること：
  - `docs/product-requirements.md`
  - `docs/functional-design.md`
  - `docs/architecture.md`
  - `docs/repository-structure.md`
  - `docs/development-guidelines.md`
  - `docs/glossary.md`

### 完了時のメッセージ
すべてのドキュメントの作成が完了したら、以下のメッセージ（または同等の内容）をユーザーに提示してください：

> 初回セットアップが完了しました!
>
> 作成したドキュメント:
> - docs/product-requirements.md
> - docs/functional-design.md
> - docs/architecture.md
> - docs/repository-structure.md
> - docs/development-guidelines.md
> - docs/glossary.md
>
> これで開発を開始する準備が整いました。
>
> **今後の使い方**:
> - **ドキュメントの編集**: 普通に会話で依頼してください。
>   - 例: 「PRDに新機能を追加して」「architecture.mdを見直して」
> - **機能の追加**: 新しい機能を開発する際は、ロードマップや設計に従って順次対話で進めます。
