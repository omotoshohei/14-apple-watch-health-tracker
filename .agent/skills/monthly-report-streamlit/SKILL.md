---
name: monthly-report-streamlit
description: Streamlit Web UIでApple Health XMLをアップロードし、Apple Watch月次HTMLレポートを生成する
---

# Apple Watch 月次レポート生成スキル Streamlit版 (Antigravity版)

このスキルは、Streamlit Web UI (`src/streamlit_app/app.py`) を起動し、ブラウザから Apple Health export XML をアップロードして、Apple Watch の月次HTMLレポートを生成・プレビュー・ダウンロードするためのガイドです。

## 使用タイミング

ユーザーが Apple Watch / Apple Health の月次レポートを Web UI または Streamlit 版で生成したいと依頼したときに使用します。

## 前提

- Streamlit アプリのエントリポイントは `src/streamlit_app/app.py` です。
- アップロードする Apple Health export XML は、ユーザーがブラウザ上のファイルアップローダーで選択します。
- **本機能は完全にローカルで処理を行うため、`GEMINI_API_KEY` などの外部 API キーは不要です。**
- Streamlit のアップロード上限は `.streamlit/config.toml` の `server.maxUploadSize = 1024` により 1024MB です。
- Streamlit 版は生成物を一時ディレクトリで作成し、画像を埋め込んだ自己完結HTMLをダウンロードボタンで提供します。

## 実行手順

### ステップ 1: Streamlitアプリの起動

プロジェクトルートから以下を実行します。

```bash
.venv/bin/streamlit run src/streamlit_app/app.py
```

`.venv/bin/streamlit` が存在しない場合は、依存関係のセットアップ状況を確認してから、利用可能な Streamlit 実行方法で起動します。

```bash
python -m streamlit run src/streamlit_app/app.py
```

起動後、ターミナルに表示されるローカルURLをユーザーに伝えます。通常は以下の形式です。

```text
http://localhost:8501
```

### ステップ 2: Web UIで対象年月を選択

1. サイドバーの `Report Period` で対象年を選択します。
2. サイドバーの `Month` で対象月を選択します。
3. 月は `1` から `12` の整数として扱われ、ダウンロードファイル名ではゼロ埋め2桁になります。

### ステップ 3: XMLファイルをアップロード

1. メイン画面の `Upload export.xml from Apple Health` に Apple Health export XML をアップロードします。
2. XML をアップロードするまで `Generate Monthly Report` ボタンは無効です。
3. XML が 1024MB を超える場合は、`.streamlit/config.toml` の `server.maxUploadSize` を調整する必要があります。

### ステップ 4: レポート生成

1. `Generate Monthly Report` を押します。
2. 進行中は以下の処理がバックグラウンドで行われます。
   - アップロードされた XML を一時フォルダ内の `uploaded_export.xml` に保存。
   - `preprocess_xml_to_csv()` を実行し、一時フォルダ内に中間 CSV ファイルを生成。
   - 生成された CSV を入力として `generate_report(csv_path=...)` を実行し、HTML レポートとグラフを生成。
   - 生成HTML内の画像を Data URI に変換。
   - 自己完結HTMLとしてダウンロード可能にする。
3. 成功時は画面上にプレビューが表示され、ダウンロードボタンが有効になります。

### ステップ 5: 出力確認

1. `Download Self-Contained Report HTML` ボタンが表示されていることを確認します。
2. ダウンロードファイル名は以下の形式です。
   ```text
   apple_watch_health_monthly_report_YYYY_MM.html
   ```
3. Streamlit 版では `output/` への永続保存ではなく、ブラウザからのダウンロードを生成結果として扱います。
4. プレビューが表示され、ダウンロード可能なHTMLが生成された場合のみ、成功として報告します。

## 失敗時の対応

### Streamlitが起動しない場合

- `.venv/bin/streamlit` が存在するか確認します。
- `requirements.txt` に `streamlit>=1.35.0` が含まれていることを確認します。
- 依存関係が未インストールの場合は、プロジェクトのセットアップ手順に従ってインストールします。
- ポート `8501` が使用中の場合は、Streamlit が提示する別ポート、または `--server.port` を指定して起動します。

### XMLアップロードに失敗する場合

- ファイル拡張子が `.xml` であることを確認します。
- ファイルサイズが `.streamlit/config.toml` の上限を超えていないか確認します。
- Apple Health export の ZIP を解凍し、`export.xml` を選択しているか確認します。

### レポート生成が失敗する場合

- 画面に表示された `Failed to generate report: ...` のエラー文を保持します。
- 対象年月、XML内容、依存関係を順に確認します。
- 失敗時に成功したとは報告しません。

## 検証

必要に応じて、Streamlit UIの動作検証を行います。アプリ起動後にブラウザで以下を確認します。

- ページが表示されること。
- 年月を選択できること。
- XMLをアップロードできること。
- `Generate Monthly Report` を押せること。
- プレビューと `Download Self-Contained Report HTML` が表示されること。

## 完了条件

- Streamlit アプリのローカルURLをユーザーに共有していること。
- 使用した対象年、対象月、XMLファイルが明確であること。
- プレビューが表示されていること。
- `apple_watch_health_monthly_report_YYYY_MM.html` をダウンロードできること。
