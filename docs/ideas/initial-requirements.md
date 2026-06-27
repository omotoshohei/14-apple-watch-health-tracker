# Apple Watch Health Monthly Report 要件定義

## 1. 概要

AppleヘルスケアAppからエクスポートしたApple Watchのヘルスデータをもとに、指定した月の健康指標を可視化するHTMLレポートをPythonで自動生成する。

レポートは、1920×1080px / 16:9 のHTMLスライド形式で出力する。
各スライドでは、1つの健康指標について日別グラフと月次統計サマリーを表示する。

---

## 2. レポート名

**Apple Watch Health Monthly Report**

---

## 3. 入力データ

### 3.1 データソース

AppleヘルスケアAppからエクスポートしたXMLファイルを使用する。

```python
export_path = "export.xml"
```

### 3.2 対象月の指定方法

Pythonコード内で対象年月を指定する。

```python
target_year = 2026
target_month = 2
```

---

## 4. 出力形式

### 4.1 ファイル形式

HTML形式で出力する。

```text
output/apple_watch_health_monthly_report_2026_02.html
```

### 4.2 スライドサイズ

各スライドは以下のサイズで作成する。

```text
1920 × 1080px
16:9
```

### 4.3 スライド表示形式

1つのHTMLファイル内に、複数のスライドを縦に並べる形式とする。

---

## 5. 対象指標

以下の5指標を対象とする。

| No. | 指標                   | 単位      |
| --: | -------------------- | ------- |
|   1 | Sleep Duration       | hours   |
|   2 | Steps                | steps   |
|   3 | Active Energy Burned | kcal    |
|   4 | Exercise Time        | minutes |
|   5 | Stand Hours          | hours   |

---

## 6. 目標値

各指標の目標値は以下の通り固定する。

| 指標                   |                 目標値 |
| -------------------- | ------------------: |
| Sleep Duration       |     7 hours or more |
| Steps                | 8,000 steps or more |
| Active Energy Burned |    500 kcal or more |
| Exercise Time        |  30 minutes or more |
| Stand Hours          |    12 hours or more |

---

## 7. スライド構成

各指標につき1枚のスライドを作成する。

| Slide | 内容                   |
| ----: | -------------------- |
|     1 | Sleep Duration       |
|     2 | Steps                |
|     3 | Active Energy Burned |
|     4 | Exercise Time        |
|     5 | Stand Hours          |

Cover slideや総合サマリースライドは作成しない。

---

## 8. 各スライドの表示内容

各スライドには以下のみを表示する。

1. Metric title
2. Target month
3. Daily bar chart
4. Target line
5. Average / Maximum / Minimum / Goal Achieved Rate

---

## 9. グラフ仕様

### 9.1 グラフ形式

各指標は日別の棒グラフで表示する。

### 9.2 X軸

対象月の日付を表示する。

例：

```text
02/01, 02/02, 02/03 ...
```

### 9.3 Y軸

各指標の値を表示する。

| 指標                   | Y軸      |
| -------------------- | ------- |
| Sleep Duration       | Hours   |
| Steps                | Steps   |
| Active Energy Burned | kcal    |
| Exercise Time        | Minutes |
| Stand Hours          | Hours   |

### 9.4 目標ライン

各グラフには目標値を示す水平ラインを表示する。

---

## 10. 月次統計サマリー生成

### 10.1 表示内容

各指標ごとに、欠損日を除外して以下の4項目を表示する。

* Average
* Maximum
* Minimum
* Goal Achieved Rate

### 10.2 計算方法

Average、Maximum、Minimumは有効日のみで計算する。
Goal Achieved Rateは「目標値以上の有効日数 / 有効日数 * 100」で計算する。

### 10.3 出力言語

統計ラベルは英語とする。有効日がない場合は `N/A` と表示する。

---

## 11. 欠損データの扱い

Apple Watchを着けていない日や、データが取得できない日は欠損として扱う。

### 11.1 グラフ表示

欠損日は0として表示しない。
欠損データとして扱い、必要に応じてグラフ上で空白または欠損表示にする。

### 11.2 集計・統計サマリー生成

Average、Maximum、Minimum、Goal Achieved Rateでは、欠損日は除外する。

---

## 12. 言語

レポート内の見出し、グラフタイトル、ラベル、統計サマリーは英語とする。

---

## 13. 実行環境

ユーザー自身のMacで実行する。

想定実行環境：

```text
macOS
Python 3.x
```

---

## 14. 想定ディレクトリ構成

```text
health_report/
  export.xml
  health_monthly_report.py
  output/
    apple_watch_health_monthly_report_2026_02.html
    assets/
      sleep_duration.png
      steps.png
      active_energy.png
      exercise_time.png
      stand_hours.png
```

---

## 15. 実装フロー

Pythonスクリプトは以下の流れで処理する。

1. Apple Healthの `export.xml` を読み込む
2. 必要なRecordデータを抽出する
3. 指定された年月のデータにフィルタする
4. 指標ごとに日別データを集計する
5. 欠損日を欠損として保持する
6. 各指標の日別グラフを生成する
7. 各指標の月次統計サマリーを生成する
8. 統計サマリーをHTMLテンプレートへ渡す
9. 1920×1080pxのHTMLスライドを生成する
10. HTMLファイルとして出力する

---

## 16. 今回は実装しないもの

以下は今回のスコープ外とする。

* PDF出力
* Cover slide
* Monthly summary table
* Goal achievement count
* Sleep stage analysis
* Sleep × activity correlation
* Next Actions
* 総合インサイト
* カフェイン分析
* 安静時心拍数分析
* 登った階数分析

---

## 17. 最終成果物

Pythonスクリプトを実行すると、指定した月のApple Watchヘルスデータをもとに、以下のHTMLレポートが生成される。

```text
Apple Watch Health Monthly Report
対象月: 指定した年月
形式: HTML
サイズ: 1920×1080px / 16:9
スライド数: 5枚
```
