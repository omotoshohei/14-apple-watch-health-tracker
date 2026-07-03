# Data Analysis Report

## Overview
This report summarizes the analysis of the correlation between daily activity data (steps, active energy burned) obtained from wearable devices such as the Apple Watch and nighttime sleep data (sleep duration, awake count, awake duration). The goal is to understand how daytime activity affects sleep quality and to obtain actionable insights for personal health management. The analysis reveals that, within this dataset, there is no statistically significant or strong correlation between daytime activity metrics and nighttime sleep quality metrics.

## Analysis Objectives and Hypotheses
### Objectives
To analyze the correlation between daytime activity (steps, active energy) and nighttime sleep quality (sleep duration, awake count, awake duration) to derive insights for personal health management.

### Hypotheses
Based on general health and wellness principles, we established the following hypotheses:
- **Hypothesis 1**: Increased daytime activity (`steps`, `active_energy`) improves sleep quality. Specifically, `sleep_duration` will tend to increase, while `awake_count` and `awake_duration` will decrease.
- **Hypothesis 2**: While moderate activity contributes to quality sleep, excessive activity may conversely disrupt sleep. However, this analysis focuses primarily on evaluating simple linear correlations.

## Dataset Description

### Data Source and Collection Period
The data used in this analysis consists of individual health metrics stored in `2-data/20260629-apple-watch/health_metrics_all.csv`. This dataset records daily activity and sleep-related metrics for the period from February 1, 2026, to July 3, 2026.

### Data Structure
The dataset comprises 150 observations and 12 columns.
The details of each column are outlined below:

| Column Name                 | Data Type   | Description                                      |
|:-------------------------|:-----------|:------------------------------------------|
| `date`                   | `str`      | Date when the data was recorded                     |
| `sleep_duration`         | `float64`  | Sleep duration (hours)                           |
| `steps`                  | `float64`  | Step count                                      |
| `active_energy`          | `float64`  | Active energy burned (kcal)         |
| `exercise_time`          | `float64`  | Exercise time (minutes)                     |
| `stand_hours`            | `float64`  | Stand hours (hours)                       |
| `sleep_onset`            | `float64`  | Sleep onset time (hours from midnight, e.g., 25.0 is 1:00 AM) |
| `wake_time`              | `float64`  | Wake time (hours from midnight, e.g., 32.0 is 8:00 AM) |
| `awake_count`            | `float64`  | Number of awakenings (times)                         |
| `awake_duration`         | `float64`  | Awake duration (minutes)                         |
| `longest_awake_duration` | `float64`  | Longest awake duration (minutes)                   |
| `first_morning_awake_time` | `float64` | Time of first morning awakening (hours from midnight)|

### Missing Values and Handling
The dataset contains missing values (NaN) across several columns, specifically in `sleep_duration`, `steps`, `active_energy`, `exercise_time`, `stand_hours`, `sleep_onset`, `wake_time`, `awake_count`, `awake_duration`, `longest_awake_duration`, and `first_morning_awake_time`.

To calculate the correlation coefficients and generate visualizations, missing values were excluded using listwise deletion for each pair of target variables. This approach ensures that correlation coefficients are computed using only complete and valid data pairs.

### Sample Data
Below is a random sample of 5 rows from the dataset:

|     | date       |   sleep_duration |   steps |   active_energy |   exercise_time |   stand_hours |   sleep_onset |   wake_time |   awake_count |   awake_duration |   longest_awake_duration |   first_morning_awake_time |
|----:|:-----------|-----------------:|--------:|----------------:|----------------:|--------------:|--------------:|------------:|--------------:|-----------------:|-------------------------:|---------------------------:|
|  76 | 2026-04-18 |          6.89    |   23136 |         490.496 |              43 |            13 |       26.35   |     33.0303 |             6 |          9.51667 |                  4.01667 |                    29.0083 |
|  11 | 2026-02-12 |          6.28778 |   16444 |         386.992 |              16 |            13 |       25.6    |     31.5961 |             2 |         25.0833  |                 23.0833  |                    31.1528 |
| 147 | 2026-06-28 |        nan       |     nan |         nan     |             nan |           nan |      nan      |    nan      |           nan |        nan       |                nan       |                   nan      |
|  52 | 2026-03-25 |          6.09583 |   12719 |         387     |              32 |            14 |       25.7167 |     32.455  |             4 |         11.5333  |                  4.51667 |                    30.0383 |
| 112 | 2026-05-24 |          6.6975  |   25189 |         504.603 |              51 |            15 |       25.9667 |     32.625  |             2 |         11.55    |                 11.0333  |                    30.9444 |

## Detailed Analysis Results

### 1. Correlation Coefficients and Valid Sample Sizes

- **Overview**:
    We calculated the Pearson correlation coefficient (r) and the corresponding valid sample size (n) between daytime activity metrics (`steps`: step count, `active_energy`: active energy burned) and nighttime sleep quality metrics (`sleep_duration`: sleep duration, `awake_count`: number of awakenings, `awake_duration`: awake duration). This analysis quantifies the strength and direction of the linear relationship between daytime activity and sleep quality.

- **Analysis Results**:
    The table below presents the correlation coefficient (r) and the valid sample size (n) for each analyzed pair:

## Correlation Analysis Results: Activity vs. Sleep Quality
| Activity Metric   | Sleep Metric   |   Correlation Coefficient (r) |   Sample Size (n) |
|:------------------|:---------------|------------------------------:|------------------:|
| steps             | sleep_duration |                        -0.051 |               143 |
| steps             | awake_count    |                         0.069 |               143 |
| steps             | awake_duration |                         0.079 |               143 |
| active_energy     | sleep_duration |                        -0.116 |               143 |
| active_energy     | awake_count    |                         0.003 |               143 |
| active_energy     | awake_duration |                         0.021 |               143 |

- **Insights**:
    As indicated in the table, the absolute value of the correlation coefficient is below 0.2 for all metric pairs, demonstrating a **negligible or very weak linear correlation** between daytime activity and nighttime sleep quality.

    - `steps` vs. `sleep_duration` (-0.051) and `active_energy` vs. `sleep_duration` (-0.116) both show a slight negative correlation. This suggests that sleep duration decreases very marginally as activity increases, but the relationship is statistically weak.
    - `steps` vs. `awake_count` (0.069) and `steps` vs. `awake_duration` (0.079) show a very slight positive correlation, indicating that higher step counts correspond to a marginal increase in awakenings and awake duration.
    - `active_energy` and `awake_count` (0.003) exhibit almost zero correlation, while `active_energy` vs. `awake_duration` (0.021) shows an extremely weak positive correlation.

    In summary, the primary hypothesis—that increased daytime activity improves sleep quality (by extending sleep duration and reducing nighttime awakenings)—is not supported by this dataset. Instead, some metrics show a very weak trend in the opposite direction.

### 2. Visualization of Correlations

- **Overview**:
    To visually evaluate the relationships between daytime activity and nighttime sleep quality, scatter plots were generated for the six analyzed pairs. A linear regression line (trend line) was fitted to each plot, with the correlation coefficient (r) and valid sample size (n) clearly annotated.

- **Analysis Results**:
    The scatter plots below illustrate each activity and sleep quality pair. The distribution of the data points and the flat slopes of the trend lines visually confirm the weak correlation coefficients discussed above.

![活動量と睡眠の相関](activity_sleep_correlations.png)

- **Insights**:
    The scatter plots reinforce the finding of a weak correlation. The data points are highly dispersed across all charts, showing no distinct patterns or trends. The flat slopes of the regression lines indicate that changes in daytime activity have a minimal predictable impact on sleep quality.

    For example, in the "Steps vs Sleep Duration" plot, sleep duration remains highly variable regardless of the step count, resulting in an almost horizontal trend line. This indicates that higher step counts or active energy expenditure do not directly translate to improved or degraded sleep quality in this dataset. The relationship between daily activity and sleep quality likely involves more complex, non-linear dynamics.

## Summary and Discussion

This analysis evaluated the correlation between daytime activity (steps, active energy) and nighttime sleep quality (sleep duration, awake count, awake duration). The Pearson correlation coefficients for all analyzed pairs were extremely low (absolute values between 0.0 and 0.2), leading to the conclusion that **there is no statistically significant linear correlation** between these variables.

Consequently, the initial hypothesis that "appropriate physical activity leads to higher-quality sleep" is not supported by the current dataset. This does not rule out a relationship between activity and sleep; rather, it suggests several alternative possibilities:

1.  **Non-linear Relationships**: The relationship may be non-linear (e.g., moderate activity optimizes sleep, while extremely low or high activity disrupts it).
2.  **Confounding Factors**: Unmeasured variables—such as diet, stress levels, caffeine/alcohol consumption, physical health, room temperature, and bedroom environment—may significantly influence sleep quality, confounding or obscuring the impact of daytime activity.
3.  **Individual Variations**: The physiological response to exercise and its impact on sleep vary significantly by individual. Aggregating the data may obscure unique individual patterns.
4.  **Measurement Granularity**: The high-level metrics analyzed may be too broad to capture subtle relationships (e.g., the specific timing/intensity of exercise or deep vs. light sleep stages).
5.  **Absence of Direct Causality**: The negligible correlation suggests that daytime activity and sleep quality are not directly or strongly linked in a simple, linear causal chain.

Crucially, **correlation does not imply causation**. The findings demonstrate that, within this dataset, daytime activity and sleep quality do not exhibit a strong, direct linear relationship.

## Next Actions

To better understand the factors influencing sleep quality and its relationship with physical activity, we recommend the following next steps:

-   **Perform Multivariate Analysis**: Collect additional data on potential confounding factors (e.g., exercise intensity, nutrition, caffeine intake, stress, evening light exposure, bedroom temperature) and apply multiple regression or machine learning models to identify complex interactions.
-   **Analyze Time-of-Day Activity**: Segment activity data by time of day (e.g., morning vs. late evening exercise) to evaluate how the timing of physical exertion impacts sleep.
-   **Explore Non-linear Models**: Apply non-linear modeling techniques, such as spline regression, to test for quadratic or threshold-based relationships.
-   **Conduct Individual-Level Analysis**: Analyze time-series data on an individual basis to identify personalized sleep-activity patterns, rather than relying solely on aggregate cohort trends.
-   **Enhance Data Quality and Granularity**: Capture more detailed sleep metrics (e.g., sleep stage distributions, sleep latency) and activity types (e.g., cardio vs. strength training).
-   **Design Controlled Intervention Studies**: To establish causal relationships, consider structured intervention testing (such as A/B testing) with specific activity regimens.
