---
name: monthly-report-cli
description: input/*.xml の Apple Health export から CLI で Apple Watch 月次HTMLレポートを生成する
---

# Apple Watch 月次レポート生成スキル CLI版 (Antigravity版)

このスキルは、`input/` 配下の Apple Health export XML を使って、Apple Watch の月次HTMLレポートを `output/` に生成するためのガイドです。

## 使用タイミング

ユーザーが Apple Watch / Apple Health の月次レポート生成を依頼したときに使用します。

## 前提

- Apple Health export XML は `input/` 配下に配置されていること。
- レポート生成には `GEMINI_API_KEY` または `GOOGLE_API_KEY` が必要です。
- 生成コマンドはプロジェクトルートから実行します。
- 出力先ディレクトリは既定で `output/` を使用します。

## 実行手順

### ステップ 1: 入力XMLの確認

1. `input/*.xml` を確認します。
   ```bash
   find input -maxdepth 1 -type f -name '*.xml' -print
   ```
2. XML ファイルが存在しない場合は、Apple Health export XML を `input/` 配下に配置するようユーザーに依頼し、処理を停止します。
3. XML ファイルが1件だけの場合は、そのファイルを使用します。
4. XML ファイルが複数ある場合は、ユーザーに使用するXMLファイルを選択してもらいます。

### ステップ 2: 対象年月の確認

1. ユーザーに対象年 `year` を確認します。
   - 例: `2026`
2. ユーザーに対象月 `month` を確認します。
   - 例: `6`
   - 有効範囲は `1` から `12` です。
3. 対象月はコマンドではゼロ埋めせず、`1` から `12` の整数として渡します。

### ステップ 3: APIキーの確認

1. `GEMINI_API_KEY` または `GOOGLE_API_KEY` が環境変数として利用可能か確認します。
   ```bash
   test -n "$GEMINI_API_KEY" || test -n "$GOOGLE_API_KEY"
   ```
2. どちらも未設定の場合は、ユーザーに以下のいずれかを設定するよう案内し、処理を停止します。
   ```bash
   export GEMINI_API_KEY="..."
   ```
   または:
   ```bash
   export GOOGLE_API_KEY="..."
   ```

### ステップ 4: レポート生成

選択したXMLファイル、対象年、対象月を使って、以下の形式でCLIを実行します。

```bash
uv run python src/cli/health_monthly_report.py --year YYYY --month M --xml input/SELECTED.xml --output-dir output
```

例:

```bash
uv run python src/cli/health_monthly_report.py --year 2026 --month 6 --xml input/export.xml --output-dir output
```

### ステップ 5: 出力確認

1. 生成されるHTMLの想定パスを確認します。
   ```text
   output/apple_watch_health_monthly_report_YYYY_MM.html
   ```
   `MM` はゼロ埋め2桁です。
2. ファイルの存在を確認します。
   ```bash
   test -f output/apple_watch_health_monthly_report_YYYY_MM.html
   ```
3. 出力ファイルが存在する場合のみ、生成成功として報告します。
4. CLI が成功したように見えても想定HTMLが存在しない場合は、検証失敗として扱い、成功とは報告しません。

## 失敗時の対応

### XMLが見つからない場合

- `input/` 配下に `*.xml` がないことを伝えます。
- Apple Health export XML を `input/` に配置してから再実行するよう依頼します。

### APIキーが未設定の場合

- `GEMINI_API_KEY` または `GOOGLE_API_KEY` が必要であることを伝えます。
- `.env` またはシェル環境にキーを設定してから再実行するよう案内します。

### CLIが失敗した場合

- エラー出力を保持し、原因を診断します。
- XMLパス、対象年月、APIキー、依存関係、CLI引数を順に確認します。
- 失敗時に成功したとは報告しません。

### 出力HTMLが見つからない場合

- `output/apple_watch_health_monthly_report_YYYY_MM.html` が存在しないことを明示します。
- CLIの標準出力に表示されたパスと期待パスが一致しているか確認します。
- 必要に応じて `output/` の内容を確認します。

## 検証

必要に応じて、関連するテストを実行します。

```bash
uv run pytest tests/test_cli.py tests/test_html.py
```

テストが失敗した場合は、失敗内容を確認し、レポート生成結果の成功とは切り分けて報告します。

## 完了条件

- 使用したXMLファイル、対象年、対象月が明確であること。
- CLIがエラーなく終了していること。
- `output/apple_watch_health_monthly_report_YYYY_MM.html` が存在すること。
- 生成されたHTMLパスをユーザーに報告していること。
