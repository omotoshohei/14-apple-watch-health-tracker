---
name: monthly-report
description: health_metrics_all.csv から月次集計CSVを作成し、Apple Watch健康指標の月次レポートを生成・確認する
---

# Apple Watch 月次レポート生成スキル (Antigravity版)

このスキルは、`data/preprocess/health_metrics_all.csv` を元データとして、全期間の健康指標を月次集計し、月ごとの推移を確認するための中間CSVおよびHTML月次レポートを生成するためのガイドです。

## 使用タイミング

ユーザーが Apple Watch / Apple Health の複数月にわたる健康指標トレンドを確認したいとき、または日次統合CSVから月次集計データを作成したいときに使用します。

## 前提

- コマンドはプロジェクトルートから実行します。
- 外部APIキーは不要です。統計計算とグラフ生成はローカルで実行します。
- `data/preprocess/health_metrics_all.csv` が存在していること。
- `health_metrics_all.csv` が未作成または古い場合は、先に `merge-metrics` スキルで `data/preprocess/health_metrics_YYYY_MM.csv` を統合します。

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

欠損値は `NA` として扱います。

## 実行手順

### ステップ 1: 日次統合CSVの存在確認

```bash
test -f data/preprocess/health_metrics_all.csv
```

存在しない場合は、以下を実行して月別日次CSVを統合します。

```bash
uv run python src/cli/merge_metrics.py
```

### ステップ 2: 月次集計CSVの生成

日次統合CSVから、月別・指標別の統計値を集計します。

```bash
uv run python src/cli/aggregate_monthly_metrics.py
```

デフォルト出力:

```text
data/preprocess/health_metrics_monthly.csv
```

入力・出力パスを明示する場合:

```bash
uv run python src/cli/aggregate_monthly_metrics.py --input data/preprocess/health_metrics_all.csv --output data/preprocess/health_metrics_monthly.csv
```

### ステップ 3: 月次集計CSVの確認

生成後、以下を確認します。

```bash
test -f data/preprocess/health_metrics_monthly.csv
head -5 data/preprocess/health_metrics_monthly.csv
```

出力CSVは `month x metric` のロング形式です。

必須カラム:

```text
month,metric,metric_name,unit,target_value,lower_is_better,average,maximum,minimum,achieved_days,valid_days,missing_days,achievement_rate
```

主な意味:

- `month`: 対象月 (`YYYY-MM`)
- `metric`: 指標キー (`steps`, `sleep_duration` など)
- `average`: 欠損値を除外した月平均
- `maximum`: 月内最大値
- `minimum`: 月内最小値
- `achieved_days`: 目標達成日数
- `valid_days`: 欠損ではない日数
- `missing_days`: 対象月内の欠損日数
- `achievement_rate`: 目標達成率 (%)

### ステップ 4: HTMLトレンドレポートの生成

トレンドレポート生成CLIが実装済みの場合は、月次集計CSVを入力としてHTMLを生成します。

```bash
uv run python src/cli/health_trend_report.py --csv data/preprocess/health_metrics_monthly.csv --output-dir output
```

想定出力:

```text
output/apple_watch_health_monthly_report.html
```

`src/cli/health_trend_report.py` が未実装の場合は、`.steering/20260628-monthly-trend-report/` の要件・設計・タスクリストに従い、まずトレンドレポート生成機能を実装します。

## 出力CSVの仕様

月次集計CSVは以下の仕様を満たします。

- 1行は1か月・1指標を表します。
- 月は `YYYY-MM` 形式で昇順に並びます。
- 指標は `src/health_report/report.py` の `METRIC_DEFINITIONS` の順序に従います。
- `NA` は平均・最大・最小・目標達成率の母数から除外します。
- `sleep_onset`, `wake_time`, `first_morning_awake_time` は小数時間のまま集計します。
  - 例: `25.5` は翌日 01:30 を意味します。
  - 表示時は `format_to_time_str` と同じ考え方で `HH:MM` に変換します。
- `lower_is_better=True` の指標は、値が目標値以下の日を達成日として扱います。
- `lower_is_better=False` の指標は、値が目標値以上の日を達成日として扱います。

## 失敗時の対応

### `health_metrics_all.csv` が見つからない場合

- `data/preprocess/health_metrics_YYYY_MM.csv` が存在するか確認します。
- 存在する場合は `uv run python src/cli/merge_metrics.py` を実行します。
- 月別日次CSVも存在しない場合は、先に `preprocess` スキルで Apple Health XML から日次CSVを作成します。

### 必須カラムが不足している場合

- エラーに表示された不足カラムを確認します。
- 元の日次CSVが古い形式の場合は、`preprocess` スキルで再生成し、`merge-metrics` スキルで統合し直します。

### HTML生成CLIが存在しない場合

- 月次集計CSV生成までを完了状態として報告します。
- `.steering/20260628-monthly-trend-report/tasklist.md` の未完了タスクに従い、`src/health_report/trend.py` と `src/cli/health_trend_report.py` を実装します。

## 検証

月次集計ロジックの検証:

```bash
uv run pytest tests/test_preprocess.py
```

全体テスト:

```bash
uv run pytest tests/
```

静的解析:

```bash
uv run ruff check src/ tests/
```

## 完了条件

- `data/preprocess/health_metrics_all.csv` が確認済みであること。
- `uv run python src/cli/aggregate_monthly_metrics.py` がエラーなく終了していること。
- `data/preprocess/health_metrics_monthly.csv` が生成されていること。
- 生成CSVに `month`, `metric`, `average`, `valid_days`, `missing_days`, `achievement_rate` が含まれていること。
- HTML生成まで実行する場合は、`output/apple_watch_health_monthly_report.html` が存在すること。
