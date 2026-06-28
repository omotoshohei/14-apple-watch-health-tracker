---
name: preprocess
description: Apple Health XML エクスポートデータから必要な健康指標データを抽出し、日別の CSV ファイルに変換する
---

# Apple Health XML前処理スキル CSVエクスポート版 (Antigravity版)

このスキルは、`input/`（または指定フォルダ）配下の Apple Health export XML (`export.xml` 等) から、指定年月の健康指標データを日別に集計し、中間データとしての CSV ファイルを生成するためのガイドです。現在の前処理対象は CLI / コアレポート用CSVであり、アーカイブ済みの Streamlit UI と Google Cloud Run inline function は対象外です。

## 使用タイミング

ユーザーが Apple Health XML から CSV 形式でデータを抽出したいとき、または HTML レポート生成の前にデータの前処理段階のみを実行したいときに使用します。

## 前提

- Apple Health export XML は `input/` 等のパスに配置されていること。
- 前処理専用モードの実行には外部 API キーは不要です。
- 生成コマンドはプロジェクトルートから実行します。

## 実行手順

### ステップ 1: 入力XMLの確認

1. 入力 XML ファイルのパスを確認します。
   - 例: `data/input/export.xml` または `data/input/export-20260627.xml`
2. `sleep_onset`（寝る時間）を確認する場合は、Apple Watch由来の睡眠ステージ (`HKCategoryValueSleepAnalysisAsleepCore` / `AsleepDeep` / `AsleepREM` など) が入った実エクスポートXMLを使います。
   - `data/input/export.xml` のようなサンプルXMLは、睡眠開始が23:00固定で作られている場合があり、実際の就寝時刻の妥当性確認には使いません。
   - 深夜1時台・2時台に寝た場合、CSV上の `sleep_onset` は前日の値として `25.x` / `26.x` のように出力されます。
3. XML ファイルが存在しない場合は、ユーザーに配置を依頼し、処理を停止します。

### ステップ 2: 対象年月と出力先の確認

1. 対象年 `year`（例: `2026`）と対象月 `month`（例: `6`）を確認します。
2. 出力先の CSV パスを決めます。
   - `--csv-output` を明示しない場合の CLI デフォルト: `data/preprocess/health_metrics_YYYY_MM.csv`

### ステップ 3: 前処理コマンドの実行

前処理専用モードを示す `--preprocess-only` を付与し、以下の形式で CLI を実行します。

```bash
uv run python src/cli/health_monthly_report.py --year YYYY --month M --xml INPUT_XML_PATH --preprocess-only --csv-output OUTPUT_CSV_PATH
```

例:

```bash
uv run python src/cli/health_monthly_report.py --year 2026 --month 6 --xml data/input/export-20260627.xml --preprocess-only --csv-output data/preprocess/health_metrics_2026_06.csv
```

### ステップ 4: 出力CSVの確認

1. 指定した出力先パスに CSV が生成されていることを確認します。
2. CSV のカラムおよび行構造を確認します。

## 出力CSVの仕様

エクスポートされる CSV ファイルは以下の仕様を満たします。

### カラム構成 (ヘッダー)
```text
date,sleep_duration,steps,active_energy,exercise_time,stand_hours,sleep_onset,wake_time,awake_count,awake_duration,longest_awake_duration,first_morning_awake_time
```

- **date**: 日付 (`YYYY-MM-DD` 形式)
- **sleep_duration**: 睡眠時間 (単位: hours / 時間)
- **steps**: 歩数 (単位: steps / 歩)
- **active_energy**: 消費アクティブエネルギー (単位: kcal)
- **exercise_time**: エクササイズ時間 (単位: minutes / 分)
- **stand_hours**: スタンド時間 (単位: hours / 時間)
- **sleep_onset**: 就寝時間 (単位: hours / 時刻を小数で表現。例: 23:30 は `23.5`、翌日 01:30 は `25.5`。※秒数は切り捨てられ、時と分のみで算出されます)
- **wake_time**: 起床時刻 (単位: hours / 時刻を小数で表現。例: 翌日08:15 は `32.25`)
- **awake_count**: 途中覚醒回数 (単位: times / 回)
- **awake_duration**: 途中覚醒時間 (単位: minutes / 分)
- **longest_awake_duration**: 最長途中覚醒時間 (単位: minutes / 分)
- **first_morning_awake_time**: 朝の最初の途中覚醒開始時刻 (単位: hours / 時刻を小数で表現。例: 翌日06:30 は `30.5`)

### 行構成
- 対象月（例: 2026年6月であれば 6/1 〜 6/30）の全日付が日付順に必ず 1 行ずつ含まれます。
- データがパースされず欠損している日は、その列の値が `NA` として出力されます。
- `sleep_onset` は、日付 D の18:00以上から翌日 D+1 の18:00未満に開始された最初の `Asleep*` 睡眠セッションを、日付 D の寝る時間として保存します。（秒数は切り捨てて、時と分から小数の時刻値にします）
- `wake_time` は、日付 D の睡眠セッションの最後の `Asleep*` 終了時刻を起床時刻として保存します。
- `awake_count`, `awake_duration`, `longest_awake_duration` は、睡眠セッション範囲（最初の `Asleep*.start` から 最後の `Asleep*.end` まで）と重複する `HKCategoryValueSleepAnalysisAwake` レコードから算出されます。重複部分のみを集計し、セッション範囲外の `Awake` レコードは除外されます。
- `first_morning_awake_time` は、翌日 05:00 以上 12:00 未満に開始され、睡眠セッション範囲と重複する `Awake` の最初の開始時刻を採用します。
- `HKCategoryValueSleepAnalysisInBed` は主に iPhone 由来の「ベッドにいた」期間であり、寝付いた時刻や起床・覚醒の集計には使いません。

## 失敗時の対応

### XMLが見つからない場合

- XML ファイルが存在しないことを伝えます。正しいパスを確認しユーザーに配置を依頼します。

### CSV出力ディレクトリが作成できない場合

- パーミッションやパスの有効性を確認します。`--csv-output` の親ディレクトリはプログラム内で自動生成されますが、書き込み権限がない場合はエラーになります。

### データが空、または不正な場合

- 指定した対象年月のデータが XML に全く含まれていない場合、CSV の日付行は作成されますが、すべての指標値が `NA` になります。

## 完了条件

- XML ファイルから、指定した年月のデータが抽出されていること。
- `data/preprocess/health_metrics_YYYY_MM.csv` などの指定パスに CSV ファイルが出力されていること。
- CSV の列順と行数が対象月の仕様を満たしていること。
- 実エクスポートXMLを使う場合、深夜1時台・2時台の就寝開始が `sleep_onset` に `25.x` / `26.x` として出力されることを確認すること。
