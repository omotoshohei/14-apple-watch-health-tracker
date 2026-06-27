# 2026-06-27: `uv run` で CLI レポート生成が失敗する

## 概要

README と CLI スキルでは、月次レポート生成コマンドとして `uv run python src/cli/health_monthly_report.py ...` を案内している。

しかし現在の `pyproject.toml` には `[project]` テーブルがないため、`uv run` がプロジェクトとして解釈できず失敗する。

## 再現手順

プロジェクトルートで以下を実行する。

```bash
uv run python src/cli/health_monthly_report.py --year 2026 --month 5 --xml input/export-20260627.xml --output-dir output
```

## 実際の結果

```text
error: No `project` table found in: `/Users/sho/code/01-project/14-apple-watch-health-tracker/pyproject.toml`
```

## 期待結果

README に記載された `uv run` コマンドで、月次HTMLレポートが生成される。

例:

```text
Report generated: output/apple_watch_health_monthly_report_2026_05.html
```

## 暫定回避策

既存の仮想環境を直接使うと生成できる。

```bash
.venv/bin/python src/cli/health_monthly_report.py --year 2026 --month 5 --xml input/export-20260627.xml --output-dir output
```

## 修正案

### 第一候補

`pyproject.toml` に最小限の `[project]` 定義と依存関係を追加し、`uv run` が標準手順として動くようにする。

確認事項:

- Python バージョン要件を README と合わせる。
- `requirements.txt` と依存関係が二重管理になるため、どちらを正とするか決める。
- 可能なら CLI entry point も定義する。

### 代替案

README とスキルの実行手順を `.venv/bin/python ...` に変更する。

ただし、プロジェクトでは `uv` 使用を推奨しているため、長期的には `[project]` を追加して `uv run` を復旧するほうが自然。

## 受け入れ条件

- `uv run python src/cli/health_monthly_report.py --year 2026 --month 5 --xml input/export-20260627.xml --output-dir output` が成功する。
- `output/apple_watch_health_monthly_report_2026_05.html` が生成される。
- README の CLI 手順と実際に動くコマンドが一致している。
- 関連する CLI テストが成功する。
