---
name: daily-report
description: CLIで健康データCSV（またはApple Health XML）からApple Watch日次HTMLレポートを生成する
---

# Apple Watch 日次レポート生成スキル CLI版 (Antigravity版)

このスキルは、前処理済みの健康指標 CSV データ（または Apple Health export XML）を使用して、Apple Watch の日次HTMLレポートを `output/` に生成するためのガイドです。

## 使用タイミング

ユーザーが Apple Watch / Apple Health の日次レポート生成を CLI から実行したいと依頼したときに使用します。

## 前提

- 本機能は、完全にローカルで統計計算とグラフ（SVG）の生成を行うため、**`GEMINI_API_KEY` などの外部 API キーは不要**です。
- 生成コマンドはプロジェクトルートから実行します。
- 出力先ディレクトリは既定で `output/` を使用します。

## 実行手順

### パターン A: 抽出済みの健康データ CSV から生成する場合 (推奨・高速)

すでに XML から前処理によって抽出された CSV ファイル（例: `data/preprocess/health_metrics_YYYY_MM.csv`）が存在する場合、XML の巨大なパース処理をスキップして高速にレポートを再生成できます。

1. CSV ファイルが存在することを確認します。
   - 例: `data/preprocess/health_metrics_2026_06.csv`
2. 対象年 `year` と対象月 `month` を指定し、`--csv` オプションに CSV パスを指定して実行します。
   ```bash
   uv run python src/cli/health_monthly_report.py --year 2026 --month 6 --csv data/preprocess/health_metrics_2026_06.csv --output-dir output
   ```

### パターン B: XML から一括で生成する場合 (前処理 + レポート生成)

Apple Health から書き出した `export.xml` を直接入力として、中間 CSV の生成と HTML レポートの作成を一括で実行します。

1. `input/*.xml` を確認します。
   - XML ファイルが存在しない場合は、Apple Health export XML を `input/` 配下に配置するようユーザーに依頼し、処理を停止します。
2. 対象年 `year` と対象月 `month` を指定し、`--xml` オプションに XML パスを指定して実行します。
   ```bash
   uv run python src/cli/health_monthly_report.py --year 2026 --month 6 --xml input/export.xml --output-dir output
   ```
   - ※ `--xml` を省略した場合は、自動的にプロジェクトルートの `export.xml` がデフォルト入力として使用されます。
3. 実行完了後、中間 CSV (`data/preprocess/health_metrics_YYYY_MM.csv`) が `data/preprocess/` に、HTML レポート (`output/apple_watch_health_daily_report_YYYY_MM.html`) が `output/` に出力されます。

## 出力確認

1. 生成される HTML の想定パスを確認します。
   ```text
   output/apple_watch_health_daily_report_YYYY_MM.html
   ```
   `MM` はゼロ埋め2桁です。
2. ファイルの存在を確認します。
   ```bash
   test -f output/apple_watch_health_daily_report_YYYY_MM.html
   ```
3. 出力ファイルが存在する場合のみ、生成成功として報告します。

## 失敗時の対応

### CSV/XMLが見つからない場合

- 指定された CSV/XML ファイルがパス上に存在しないことを伝えます。パスを確認するか、先に前処理を行って CSV を生成してください。

### CSVのデータ・日付が不足している場合

- CSV 内に必須カラム（`date`, `sleep_duration`, `steps`, `active_energy`, `exercise_time`, `stand_hours`, `sleep_onset`）が不足している場合、または対象月以外の日付が含まれていたり対象月の日付が不足している場合は `ValueError` が発生します。前処理スクリプト（`preprocess` スキルを参照）を用いて CSV を再生成してください。

## 検証

必要に応じて、関連するテストを実行します。

```bash
uv run pytest tests/test_cli.py tests/test_report_csv.py
```

## 完了条件

- 使用した CSV/XML ファイル、対象年、対象月が明確であること。
- CLI がエラーなく終了していること。
- `output/apple_watch_health_daily_report_YYYY_MM.html` が存在すること。
