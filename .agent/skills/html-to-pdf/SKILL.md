---
name: html-to-pdf
description: 生成済み Apple Watch Health HTML レポートを、16:9 のスライド単位PDFへ変換・検証・保守する
---

# HTML to PDF Export スキル (Antigravity版)

このスキルは、`output/` 配下に生成済みの Apple Watch Health HTML レポートを、横長 16:9 のPDFへ変換するためのガイドです。

既存の実装は `src/cli/html_to_pdf.py` にあり、Playwright Chromium のPDF出力を使って、HTML内の `.slide-wrapper > .slide` 構造を1スライド1ページとして出力します。

## 使用タイミング

以下の依頼ではこのスキルを使用してください。

- HTMLレポートをPDFへ変換したい
- `output/*.html` から `output/pdf/*.pdf` を生成したい
- PDFのページサイズ、ページ数、ページ区切りを検証したい
- `src/cli/html_to_pdf.py` の不具合修正や仕様変更を行いたい
- Playwright / Chromium 関連のPDF変換エラーを調査したい

## 関連ファイル

- 実装: `src/cli/html_to_pdf.py`
- テスト: `tests/test_html_to_pdf.py`
- README: `README.md`
- 元の作業記録: `.steering/20260703-html-to-pdf-export/`
- 詳細ガイド: [guide.md](./guide.md)

## 基本コマンド

### デフォルト変換

`output/` 直下の `.html` ファイルをすべてPDFへ変換し、`output/pdf/` に出力します。

```bash
uv run python src/cli/html_to_pdf.py
```

### 単一HTMLファイルの変換

```bash
uv run python src/cli/html_to_pdf.py --input output/apple_watch_health_weekly_report.html
```

### 入力・出力ディレクトリを明示

```bash
uv run python src/cli/html_to_pdf.py --input-dir output --output-dir output/pdf
```

### 既存PDFを上書きしない

```bash
uv run python src/cli/html_to_pdf.py --skip-existing
```

### Chromium の初回セットアップ

Playwright はインストール済みでも、Chromium が未導入の場合があります。その場合は次を実行します。

```bash
uv run playwright install chromium
```

## 実行手順

### 1. 目的を確認する

ユーザーの依頼が「PDFを生成するだけ」か、「PDF変換機能を修正する」かを切り分けます。

- 生成のみ: 基本コマンドを実行し、出力PDFを確認する
- 修正あり: `src/cli/html_to_pdf.py`、`tests/test_html_to_pdf.py`、`README.md` を確認してから変更する

### 2. 入力HTMLを確認する

デフォルト対象は `output/*.html` です。サブディレクトリは再帰探索しません。

確認観点:

- `output/` が存在するか
- 対象 `.html` が存在するか
- 単一指定時は拡張子が `.html` か
- HTML内に `.slide-wrapper` と `.slide` があるか

### 3. PDF変換を実行する

目的に応じて基本コマンドを実行します。

変換結果は標準出力に以下の形式で表示されます。

```text
PDF conversion complete: N converted, M skipped (took X.XX seconds)
```

### 4. 生成結果を検証する

最低限、以下を確認します。

- PDFが `output/pdf/` または指定した出力先に作成されている
- ページが横長 16:9 になっている
- HTMLの `.slide-wrapper` 数とPDFページ数が一致している
- 背景、SVGグラフ、テーブル、文字が欠けていない
- 余分な空白ページがない

検証方法の詳細は [guide.md](./guide.md) を参照してください。

### 5. 修正した場合は品質チェックを実行する

PDF変換実装やテストを変更した場合は、少なくとも次を実行します。

```bash
uv run python -m pytest
uv run python -m ruff check src/ tests/
uv run python -m ruff format --check src/ tests/
```

## 実装方針

PDF変換機能を変更する場合は、以下を維持してください。

- 既存HTMLレポート生成処理には手を入れず、生成済みHTMLを入力にする
- CLIは `argparse` を使い、`uv run python src/cli/html_to_pdf.py` で実行できる形を保つ
- `--input` と `--input-dir` は同時指定不可にする
- デフォルト入力は `output/`、デフォルト出力は `output/pdf/` にする
- ページサイズは 16:9 横長を維持する
- `.slide-wrapper:last-child` の後には余分な改ページを入れない
- Playwright / Chromium 未導入時は、`uv run playwright install chromium` を案内する

## 完了条件

このスキルを使った作業は、以下を満たしたら完了です。

- 目的のHTMLがPDFへ変換されている
- 生成PDFのページ数とページサイズが妥当である
- 修正を行った場合、テスト・リント・フォーマットチェックが成功している
- READMEや手順に影響する仕様変更をした場合、関連ドキュメントが更新されている
