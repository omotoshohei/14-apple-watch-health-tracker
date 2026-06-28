---
name: merge-metrics
description: 各月の健康指標データCSVをマージし、全期間のデータを含むhealth_metrics_all.csvを生成・更新する
---

# 健康指標データ全期間マージスキル (Antigravity版)

このスキルは、`data/preprocess/` 配下にある複数の月次健康指標データ CSV（`health_metrics_YYYY_MM.csv`）をマージし、全期間のデータを含む `health_metrics_all.csv` を作成・更新するためのガイドです。

## 使用タイミング

新しく月次の健康データ CSV が追加・更新された際、または全期間のデータをまとめた最新の CSV を生成したい場合に使用します。

## 前提

- `data/preprocess/` ディレクトリに、1つ以上の月次健康データ CSV（`health_metrics_YYYY_MM.csv`）が存在すること。
- プロジェクトに必要な依存パッケージ（`pandas` 等）が仮想環境にインストールされていること。

## 実行手順

### ステップ 1: マージコマンドの実行

プロジェクトルートから、以下のコマンドを実行します。

```bash
uv run python src/cli/merge_metrics.py
```

※デフォルトの入力ディレクトリは `data/preprocess`、出力ファイルは `data/preprocess/health_metrics_all.csv` です。
必要に応じて、以下のオプションを指定できます。

```bash
uv run python src/cli/merge_metrics.py --input-dir INPUT_DIR_PATH --output OUTPUT_CSV_PATH
```

### ステップ 2: 出力CSVの確認

1. `data/preprocess/health_metrics_all.csv`（または指定した出力先）が生成・更新されていることを確認します。
2. CSV のヘッダーおよびデータ行が日付順（昇順）に正しくソートされ、重複なく結合されていることを確認します。

## 出力CSVの仕様

エクスポートされる `health_metrics_all.csv` は以下の仕様を満たします。

### カラム構成 (ヘッダー)
```text
date,sleep_duration,steps,active_energy,exercise_time,stand_hours
```

- **date**: 日付 (`YYYY-MM-DD` 形式)
- **sleep_duration**: 睡眠時間 (単位: hours / 時間)
- **steps**: 歩数 (単位: steps / 歩)
- **active_energy**: 消費アクティブエネルギー (単位: kcal)
- **exercise_time**: エクササイズ時間 (単位: minutes / 分)
- **stand_hours**: スタンド時間 (単位: hours / 時間)

### 行構成
- 各月次CSVに含まれる全日付のデータが日付順に結合され、重複行が排除されます。
- 欠損値は `NA` として出力されます。

## 完了条件

- 指定した入力先から月次データが正しくマージされ、`data/preprocess/health_metrics_all.csv`（または指定パス）に出力されていること。
