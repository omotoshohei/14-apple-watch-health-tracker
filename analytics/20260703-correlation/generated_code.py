import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def analyze_activity_sleep_correlation():
    """
    日中の活動量と夜間の睡眠の質の相関関係を分析し、結果を可視化・出力する。
    """

    # 出力ディレクトリの定義と作成
    output_dir = Path("5-output/20260629-apple-watch")
    output_dir.mkdir(parents=True, exist_ok=True)

    # データの読み込み
    file_path = "2-data/20260629-apple-watch/health_metrics_all.csv"
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: Data file not found at {file_path}")
        return

    # 分析対象の活動量指標と睡眠の質指標を定義
    activity_metrics = ['steps', 'active_energy']
    sleep_metrics = ['sleep_duration', 'awake_count', 'awake_duration']

    # 相関分析結果を格納するリスト
    correlation_results = []

    # 相関係数と有効サンプル数の算出
    for activity_col in activity_metrics:
        for sleep_col in sleep_metrics:
            # 各ペアで欠損値を除外したデータフレームを作成
            temp_df = df[[activity_col, sleep_col]].dropna()

            # 有効サンプル数
            n = len(temp_df)

            # 相関係数 (ピアソン相関係数) を算出
            # pandas.corr() はデフォルトでピアソン相関係数を算出し、欠損値を自動でスキップする
            if n > 1: # 相関係数計算には最低2つのデータポイントが必要
                r = temp_df[activity_col].corr(temp_df[sleep_col])
                correlation_results.append({
                    'Activity Metric': activity_col,
                    'Sleep Metric': sleep_col,
                    'Correlation Coefficient (r)': r,
                    'Sample Size (n)': n
                })
            else:
                correlation_results.append({
                    'Activity Metric': activity_col,
                    'Sleep Metric': sleep_col,
                    'Correlation Coefficient (r)': float('nan'),
                    'Sample Size (n)': n
                })

    # 相関分析結果をDataFrameに変換
    results_df = pd.DataFrame(correlation_results)

    # Markdownテーブル形式で結果を出力
    print("## Correlation Analysis Results: Activity vs. Sleep Quality")
    print(results_df.to_markdown(index=False, floatfmt=".3f"))
    print("\n")

    # 相関関係の可視化
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten() # 2x3の配列を1次元にする

    # グラフの日本語対応は不要（英語ラベルとタイトルを使用するため）

    for i, result in enumerate(correlation_results):
        ax = axes[i]
        activity_col = result['Activity Metric']
        sleep_col = result['Sleep Metric']
        r = result['Correlation Coefficient (r)']
        n = result['Sample Size (n)']

        # 各ペアで欠損値を除外したデータフレーム
        temp_df = df[[activity_col, sleep_col]].dropna()

        # Seabornのregplotで散布図と回帰直線を描画
        if not temp_df.empty:
            sns.regplot(x=activity_col, y=sleep_col, data=temp_df, ax=ax,
                        scatter_kws={'alpha':0.6}, line_kws={'color':'red'})
        else:
            # データがない場合は散布図を描画しない
            ax.text(0.5, 0.5, 'No data available for this pair', horizontalalignment='center',
                    verticalalignment='center', transform=ax.transAxes, color='gray')

        # グラフのタイトルに相関係数とサンプル数を表示
        title_str = f"{activity_col} vs {sleep_col}\nr = {r:.2f}, n = {n}" if not pd.isna(r) else f"{activity_col} vs {sleep_col}\nNo correlation (n = {n})"
        ax.set_title(title_str, fontsize=14)
        ax.set_xlabel(activity_col.replace('_', ' ').title(), fontsize=12) # X軸ラベル
        ax.set_ylabel(sleep_col.replace('_', ' ').title(), fontsize=12) # Y軸ラベル
        ax.tick_params(axis='x', labelsize=10)
        ax.tick_params(axis='y', labelsize=10)

    # レイアウトの調整
    plt.tight_layout(rect=[0, 0.03, 1, 0.98]) # タイトルが被らないように調整

    # 全体のタイトル
    fig.suptitle('Correlation between Activity and Sleep Quality Metrics', fontsize=16, y=1.0)

    # グラフの保存
    plot_filename = "activity_sleep_correlations.png"
    plot_filepath = output_dir / plot_filename
    plt.savefig(plot_filepath, bbox_inches='tight')
    print(f"Correlation plot saved to: {plot_filepath}")

    plt.close(fig) # メモリ解放

# スクリプト実行
if __name__ == "__main__":
    analyze_activity_sleep_correlation()