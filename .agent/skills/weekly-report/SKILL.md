---
name: weekly-report
description: health_metrics_all.csv から週次集計CSVを作成し、Apple Watch健康指標の週次トレンドHTMLレポートを生成・確認する
---

# Apple Watch 週次レポート生成スキル (Antigravity版)

このスキルは、`data/preprocess/health_metrics_all.csv` を元データとして、月曜始まりの完全週だけを週次集計し、複数週の短期トレンドを確認するための中間CSVおよびHTMLレポートを生成するためのガイドです。

## 使用タイミング

ユーザーが Apple Watch / Apple Health の健康指標を週単位で確認したいとき、または日次統合CSVから週次集計データと週次HTMLレポートを作成したいときに使用します。

## 前提

- コマンドはプロジェクトルートから実行します。
- 外部APIキーは不要です。統計計算とグラフ生成はローカルで実行します。
- `data/preprocess/health_metrics_all.csv` が存在していること。
- `health_metrics_all.csv` が未作成または古い場合は、先に `merge-metrics` スキルで `data/preprocess/health_metrics_YYYY_MM.csv` を統合します。
- 週次集計は月曜始まりの完全週だけを対象にし、データ範囲の先頭・末尾にある7日未満の端数週は除外します。

## 入力データ

### 日次統合CSV

デフォルト入力:

```text
data/preprocess/health_metrics_all.csv
```

必須カラム:

```text
date,sleep_duration,steps,active_energy,exercise_time,stand_hours,sleep_onset,wake_time,awake_count,awake_duration,longest_awake_duration,first_morning_awake_time
```

欠損値は `NA` として扱います。欠損日は `0` に変換せず、平均・最大・最小・達成率の母数から除外します。

## 実行手順

### ステップ 1: 日次統合CSVの存在確認

```bash
test -f data/preprocess/health_metrics_all.csv
```

存在しない場合は、以下を実行して月別日次CSVを統合します。

```bash
uv run python src/cli/merge_metrics.py
```

### ステップ 2: 週次集計CSVの生成

日次統合CSVから、週別・指標別の統計値を集計します。

```bash
uv run python src/cli/aggregate_weekly_metrics.py
```

デフォルト出力:

```text
data/preprocess/health_metrics_weekly.csv
```

入力・出力パスを明示する場合:

```bash
uv run python src/cli/aggregate_weekly_metrics.py --input data/preprocess/health_metrics_all.csv --output data/preprocess/health_metrics_weekly.csv
```

### ステップ 3: 週次集計CSVの確認

生成後、以下を確認します。

```bash
test -f data/preprocess/health_metrics_weekly.csv
head -5 data/preprocess/health_metrics_weekly.csv
```

出力CSVは `week x metric` のロング形式です。

必須カラム:

```text
week,week_start,week_end,metric,metric_name,unit,target_value,lower_is_better,average,maximum,minimum,achieved_days,valid_days,missing_days,achievement_rate
```

主な意味:

- `week`: ISO week-year を使った週ラベル (`YYYY-Www`)
- `week_start`: 対象週の月曜日 (`YYYY-MM-DD`)
- `week_end`: 対象週の日曜日 (`YYYY-MM-DD`)
- `metric`: 指標キー (`steps`, `sleep_duration` など)
- `average`: 欠損値を除外した週平均
- `maximum`: 週内最大値
- `minimum`: 週内最小値
- `achieved_days`: 目標達成日数
- `valid_days`: 欠損ではない日数
- `missing_days`: 対象週内の欠損日数
- `achievement_rate`: 目標達成率 (%)

### ステップ 4: 週次HTMLトレンドレポートの生成

週次集計CSVを入力としてHTMLを生成します。

```bash
uv run python src/cli/health_weekly_report.py --csv data/preprocess/health_metrics_weekly.csv --output-dir output
```

想定出力:

```text
output/apple_watch_health_weekly_report.html
```

### ステップ 5: HTML出力の確認

```bash
test -f output/apple_watch_health_weekly_report.html
```

出力ファイルが存在する場合のみ、生成成功として報告します。

## 出力CSVの仕様

週次集計CSVは以下の仕様を満たします。

- 1行は1週・1指標を表します。
- 週は月曜始まり、日曜終わりです。
- `week` は ISO week-year の `YYYY-Www` 形式です。
- データ範囲の先頭・末尾にある7日未満の端数週は除外します。
- 採用対象週は Monday-Sunday の7日に再索引し、日付行が存在しない日や指標値が欠けた日は `missing_days` として数えます。
- 指標は `src/health_report/report.py` の `METRIC_DEFINITIONS` の順序に従います。
- `NA` は平均・最大・最小・目標達成率の母数から除外します。
- `sleep_onset`, `wake_time`, `first_morning_awake_time` は小数時間のまま集計します。
  - 例: `25.5` は翌日 01:30 を意味します。
  - 表示時は `format_to_time_str` と同じ考え方で `HH:MM` に変換します。
- `lower_is_better=True` の指標は、値が目標値以下の日を達成日として扱います。
- `lower_is_better=False` の指標は、値が目標値以上の日を達成日として扱います。

## HTMLレポートの仕様

- `output/apple_watch_health_weekly_report.html` に出力します。
- 既存11指標について、指標ごとに1スライドを生成します。
- 各スライドには週次平均の折れ線グラフ、目標ライン、週別テーブルを表示します。
- 週次CSVに一部指標が存在しない場合でも、該当指標は空状態のスライドとして表示し、他の指標の生成を継続します。

## 失敗時の対応

### `health_metrics_all.csv` が見つからない場合

- `data/preprocess/health_metrics_YYYY_MM.csv` が存在するか確認します。
- 存在する場合は `uv run python src/cli/merge_metrics.py` を実行します。
- 月別日次CSVも存在しない場合は、先に `preprocess` スキルで Apple Health XML から日次CSVを作成します。

### 必須カラムが不足している場合

- エラーに表示された不足カラムを確認します。
- 元の日次CSVが古い形式の場合は、`preprocess` スキルで再生成し、`merge-metrics` スキルで統合し直します。

### 完全週が存在しない場合

- 入力CSVの日付範囲が月曜始まりの7日間を含んでいるか確認します。
- データ範囲が短すぎる場合は、追加月の日次CSVを生成して `merge-metrics` スキルで統合し直します。

### HTML生成に失敗する場合

- `data/preprocess/health_metrics_weekly.csv` が存在するか確認します。
- 週次CSVの必須カラムが揃っているか確認します。
- 必要に応じて `uv run python src/cli/aggregate_weekly_metrics.py` を再実行します。

## 検証

週次集計・週次HTML生成ロジックの検証:

```bash
uv run pytest tests/test_weekly.py
```

CLIを含む関連テスト:

```bash
uv run pytest tests/test_weekly.py tests/test_cli.py
```

全体テスト:

```bash
uv run pytest tests/
```

静的解析:

```bash
uv run ruff check src tests
```

フォーマット確認:

```bash
uv run ruff format --check src tests
```

## 完了条件

- `data/preprocess/health_metrics_all.csv` が確認済みであること。
- `uv run python src/cli/aggregate_weekly_metrics.py` がエラーなく終了していること。
- `data/preprocess/health_metrics_weekly.csv` が生成されていること。
- 生成CSVに `week`, `week_start`, `week_end`, `metric`, `average`, `valid_days`, `missing_days`, `achievement_rate` が含まれていること。
- `uv run python src/cli/health_weekly_report.py` がエラーなく終了していること。
- `output/apple_watch_health_weekly_report.html` が存在すること。
