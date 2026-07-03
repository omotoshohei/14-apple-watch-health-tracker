---
name: github-upload-check
description: GitHub公開・アップロード前に、個人データ混入、未追跡ファイル、ドキュメント整合性、テストと品質チェックを一通り確認する
---

# GitHubアップロード前チェックスキル (Antigravity版)

このスキルは、Apple Watch Health Tracker リポジトリを GitHub にアップロードまたは公開する前に、公開してよい状態かを確認するためのチェックリストです。

個人情報を含む Apple Health データの混入防止、Git管理対象の確認、README/docs の整合性、テスト・lint・format の検証をまとめて実行します。

## 使用タイミング

- GitHubへ初回アップロードする前。
- READMEやdocsを更新した後。
- 新しいCLI、レポート、スキル、デモ出力を追加した後。
- `git add` / commit / push の直前に、公開してよいファイルだけが含まれているか確認したいとき。

## 前提

- コマンドはプロジェクトルートから実行します。
- 個人の Apple Health XML、生データ、通常の出力HTMLは Git 管理対象にしません。
- `output-demo/` はダミーデータ由来のショーケースとして Git 管理対象にできます。
- 外部APIキーは不要です。

## チェック対象

### 公開してよいファイル

- `README.md`
- `docs/`
- `src/`
- `tests/`
- `.agent/skills/`
- `data/preprocess/` のデモ・サンプル用CSV
- `output-demo/` のダミーデータ由来PDF
- `pyproject.toml`, `requirements.txt`, `uv.lock`

### 公開してはいけないファイル

- `input/`
- `output/`
- `export.xml`
- `.env`, `.env.*`
- 個人名、住所、メール、APIキー、アクセストークンなどを含むファイル
- ローカル環境固有のキャッシュやIDE設定

## 実行手順

### ステップ 1: Git差分と未追跡ファイルの確認

現在の変更内容を確認します。

```bash
git status --short
git diff --stat
```

確認観点:

- 意図しないファイルが変更されていないか。
- 新機能に必要な新規ファイルが未追跡のまま残っていないか。
- `input/`, `output/`, `.env`, `export.xml` が表示されていないか。
- `.steering/` やローカル作業用ファイルを公開対象に含めていないか。

### ステップ 2: 個人データ・秘密情報のGit管理チェック

Git管理対象に、個人データや秘密情報が含まれていないか確認します。

```bash
git ls-files | rg '(^|/)(input|output)(/|$)|export\.xml$|\.env'
```

期待結果:

- 何も出力されないこと。

出力がある場合:

- Git管理から除外する必要があります。
- ローカルファイルを残す場合は `git rm --cached` を使用します。
- 削除・追跡解除の前に、ユーザーへ確認します。

### ステップ 3: `.gitignore` の効き方を確認

個人データ系が `.gitignore` で無視され、`output-demo/` が無視されていないことを確認します。

```bash
git check-ignore -v input/export.xml output/test.html export.xml .env
git check-ignore -v output-demo/apple_watch_health_daily_report_2026_05.pdf
```

期待結果:

- `input/export.xml`, `output/test.html`, `export.xml`, `.env` は `.gitignore` によって無視されること。
- `output-demo/...pdf` は無視されないこと。

注意:

- `git check-ignore` は、無視されないファイルに対して終了コード `1` を返します。`output-demo/` の確認では、終了コード `1` は期待どおりです。

### ステップ 4: READMEとdocsの整合性確認

現行実装とドキュメントのズレを検索します。

```bash
rg -n "8000|8,000|Sleep Duration: 7|7\.0時間|単一のPython|src/health_monthly_report.py|5指標|output/assets|png形式|6指標|src/streamlit_app" docs README.md .agent/skills -g '*.md'
```

確認観点:

- 現在の目標値と異なる古い値が残っていないか。
- 旧構成の `src/health_monthly_report.py` 前提が残っていないか。
- 現在は11指標なのに、5指標・6指標と書かれていないか。
- 現在はSVG埋め込みHTMLなのに、PNG assets前提が残っていないか。
- Streamlit UI がアーカイブ済みなのに、旧パス `src/streamlit_app/app.py` が残っていないか。

例外:

- `docs/ideas/initial-requirements.md` は初期メモなので、古い要件が残っていても意図的な履歴として扱えます。

### ステップ 5: テスト実行

プロジェクトの `.venv` 側の Python を使うため、`python -m` 経由で実行します。

```bash
uv run python -m pytest
```

期待結果:

- 全テストが pass すること。
- 失敗した場合は、失敗テスト名、原因、修正方針を確認してから再実行します。

### ステップ 6: Ruffによる品質チェック

```bash
uv run python -m ruff check src/ tests/
uv run python -m ruff format --check src/ tests/
```

期待結果:

- `All checks passed!`
- `files already formatted`

フォーマット違反がある場合:

```bash
uv run python -m ruff format src/ tests/
```

その後、再度 `ruff format --check` を実行します。

### ステップ 7: Git差分の空白チェック

```bash
git diff --check
```

期待結果:

- 何も出力されないこと。

出力がある場合:

- trailing whitespace や conflict marker などを修正します。

### ステップ 8: デモ出力の確認

GitHub上で見せるためのデモPDFが存在するか確認します。

```bash
find output-demo -maxdepth 1 -type f -name '*.pdf' -print
```

確認観点:

- 実データではなく、ダミーデータから生成したPDFであること。
- READMEに記載したデモPDFのパスが実在すること。
- `output-demo/` が `.gitignore` で無視されていないこと。

### ステップ 9: 最終Gitステータス確認

```bash
git status --short
```

確認観点:

- commit に含めるべき変更がすべて見えていること。
- 個人データや一時出力が見えていないこと。
- 新機能の実装ファイル、テスト、ドキュメント、必要なスキル定義が未追跡のまま残っていないこと。

## 完了条件

- `git ls-files` の個人データ検索で何も出力されないこと。
- `input/`, `output/`, `export.xml`, `.env` が `.gitignore` で無視されること。
- `output-demo/` が Git 管理可能であること。
- README と docs が現在の実装に合っていること。
- `uv run python -m pytest` が pass すること。
- `uv run python -m ruff check src/ tests/` が pass すること。
- `uv run python -m ruff format --check src/ tests/` が pass すること。
- `git diff --check` が無出力であること。
- 最終的な `git status --short` に、公開対象として意図したファイルだけが表示されていること。

## 報告フォーマット

チェック完了後は、以下の形式でユーザーに報告します。

```markdown
## GitHubアップロード前チェック結果

- Git管理対象の個人データ: なし / あり
- `.gitignore` 確認: OK / 要修正
- README/docs整合性: OK / 要修正
- テスト: pass / fail
- Ruff check: pass / fail
- Ruff format: pass / fail
- `git diff --check`: OK / 要修正
- デモ出力: OK / 要確認

### 残タスク
- [必要な場合のみ記載]
```

## 注意事項

- `git rm --cached` やファイル削除が必要な場合は、対象ファイルを明示してから実行します。
- ユーザーが作業中の変更を勝手に戻さないでください。
- `.steering/` は作業管理用なので、公開対象に含めない運用を基本とします。
- GitHubへ push する前には、最後に必ず `git status --short` を再確認します。
