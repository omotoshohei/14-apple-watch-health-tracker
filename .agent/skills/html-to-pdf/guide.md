# HTML to PDF Export 詳細ガイド

## 現在の実装概要

`src/cli/html_to_pdf.py` は、生成済みHTMLをPlaywright Chromiumで開き、印刷用CSSを注入してPDF化します。

主要な設計:

- `DEFAULT_INPUT_DIR = Path("output")`
- `DEFAULT_OUTPUT_DIR = Path("output/pdf")`
- デフォルトでは `output/*.html` をファイル名順に変換
- `--input` は単一HTMLファイルのみ変換
- `--input-dir` は指定ディレクトリ直下の `.html` のみ変換
- `--output-dir` は出力先ディレクトリを変更
- `--skip-existing` は既存PDFを上書きせずスキップ

## 印刷用CSSの要点

PDF出力では `PRINT_CSS` を注入します。

維持すべき要点:

```css
@page {
  size: 20in 11.25in;
  margin: 0;
}
```

- `20in x 11.25in` は 16:9 のページサイズです。
- Chromium のCSS px換算で 1920x1080px 相当として扱えます。
- `.slide-wrapper` は `1920px x 1080px` に固定します。
- `.slide-wrapper` に `page-break-after: always` と `break-after: page` を指定します。
- `.slide-wrapper:last-child` は `page-break-after: auto` と `break-after: auto` にします。
- `.slide` は `transform: none !important` で画面表示用スケールを打ち消します。
- `border-radius` と `box-shadow` はPDFでは無効化します。

## エラー処理

想定する終了コード:

- `0`: 正常終了
- `1`: 入力ファイルなし、HTML未検出、Playwright/Chromiumエラー、予期しない実行時エラー
- `2`: CLI引数の使い方の問題、特に `--input` と `--input-dir` の同時指定

代表的なエラーと対応:

- `HTML input file not found`: `--input` のパスを確認する
- `No HTML files found in input directory`: `output/` または `--input-dir` に `.html` があるか確認する
- `Cannot specify both --input and --input-dir`: どちらか一方だけ指定する
- `Playwright is not installed`: 依存関係をインストールする
- `If Chromium is not installed`: `uv run playwright install chromium` を実行する

## 検証手順

### 1. CLI単体テスト

```bash
uv run python -m pytest tests/test_html_to_pdf.py
```

テスト対象:

- デフォルト入力解決
- 単一HTML指定
- 入力ディレクトリ指定
- `--input` と `--input-dir` の同時指定エラー
- 出力PDFパス決定
- `--skip-existing` のスキップ判定

### 2. 実HTMLスモーク検証

```bash
uv run python src/cli/html_to_pdf.py --input output/apple_watch_health_weekly_report.html
```

期待される出力:

```text
PDF conversion complete: 1 converted, 0 skipped (...)
```

出力PDF:

```text
output/pdf/apple_watch_health_weekly_report.pdf
```

### 3. ページ数とページサイズの確認

Poppler がある場合:

```bash
pdfinfo output/pdf/apple_watch_health_weekly_report.pdf
```

Poppler がない場合は、PythonでPDF内部を簡易確認します。

```bash
uv run python - <<'PY'
from pathlib import Path

pdf = Path("output/pdf/apple_watch_health_weekly_report.pdf").read_bytes()
print("page markers:", pdf.count(b"/Type /Page") - pdf.count(b"/Type /Pages"))
print("has 16:9 mediabox:", b"/MediaBox [0 0 1440 810]" in pdf or b"/MediaBox[0 0 1440 810]" in pdf)
PY
```

HTML側のスライド数は次で確認できます。

```bash
uv run python - <<'PY'
from pathlib import Path

html = Path("output/apple_watch_health_weekly_report.html").read_text(encoding="utf-8")
print(html.count('class="slide-wrapper"'))
PY
```

### 4. 視覚確認

Poppler がある場合:

```bash
pdftoppm -png output/pdf/apple_watch_health_weekly_report.pdf /tmp/apple_watch_health_weekly_report
```

Poppler がない場合は、PlaywrightでHTMLに同じ印刷CSSを注入し、先頭スライドをPNG化して目視確認します。必要な場合のみ一時スクリプトで実行し、リポジトリに不要な検証用ファイルを残さないでください。

確認観点:

- 先頭ページの左上から右下までスライドが収まっている
- 大きな白余白がない
- SVGグラフや表が欠けていない
- テキストが画面表示時の縮小状態になっていない

## 変更時の注意点

### CLI仕様を変える場合

以下を同時に更新します。

- `src/cli/html_to_pdf.py`
- `tests/test_html_to_pdf.py`
- `README.md`
- 必要に応じて `.agent/skills/html-to-pdf/`

### ページサイズを変える場合

`PRINT_CSS` の `@page size`、`.slide-wrapper`、`.slide` のサイズ指定を一貫して変更します。

ページ比率を変える場合は、以下も再検証します。

- PDFの `/MediaBox`
- `.slide-wrapper` 数とPDFページ数
- 余白ページの有無
- グラフ、テーブル、文字の欠け

### HTML構造が変わった場合

現在の前提は `.slide-wrapper > .slide` です。HTMLテンプレート側でクラス名や階層が変わった場合は、`PRINT_CSS` と検証観点を更新します。

## よくある修正方針

### 余分な空白ページが出る

- `.slide-wrapper:last-child` の `break-after: auto` が効いているか確認する
- `body` や親要素の余白、padding、height指定を確認する
- 画面表示用の余分なコンテナが印刷時に高さを持っていないか確認する

### スライドが縮小・拡大される

- `.slide` の `transform: none !important` を確認する
- `.slide-wrapper` と `.slide` の width/height が 1920x1080 で揃っているか確認する
- Playwright の `viewport={"width": 1920, "height": 1080}` を維持する

### 背景やSVGが消える

- `page.pdf(..., print_background=True, prefer_css_page_size=True)` を維持する
- `page.emulate_media(media="print")` 後にCSSを注入しているか確認する
- HTML側で印刷メディア時に非表示になるCSSがないか確認する
