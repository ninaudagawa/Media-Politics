"""
Compare normalised category frequency between speeches and articles.

For each category in CATEGORY_KEYWORDS:
  1. Scatter plot: normalised article share vs normalised speech share (by year)
  2. Same scatter plot with an OLS regression line, plus R^2 and p-value
"""

import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

from src.keywords import CATEGORY_KEYWORDS
from src.news_analysis_keyword import build_category_normalised_df


def load_merged_data(speeches_path, articles_path):
    """Load normalised speech data (from CSV) and article data (built from raw
    articles CSV), then merge them on category/year."""
    speeches_normalised = pd.read_csv(speeches_path)

    articles_df = pd.read_csv(articles_path)
    category_normalised = build_category_normalised_df(
        CATEGORY_KEYWORDS, articles_df, date_col="date", text_col="text"
    )

    merged_df = pd.merge(
        speeches_normalised,
        category_normalised,
        on=["category", "year"],
        suffixes=("_speeches", "_articles"),
    )
    return merged_df


def plot_scatter(merged_df, category):
    """Plot normalised article share vs speech share for a single category."""
    df_plot = merged_df[merged_df["category"] == category]

    plt.figure(figsize=(10, 6))
    plt.scatter(
        x=df_plot["normalised_share_articles"],
        y=df_plot["normalised_share_speeches"],
        color="purple",
        alpha=0.7,
    )
    plt.title(f"Normalised Article vs Speech Frequency: {category.capitalize()}")
    plt.xlabel("Normalised Share (Articles)")
    plt.ylabel("Normalised Share (Speeches)")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.show()


def plot_regression(merged_df, category):
    """Plot scatter + OLS regression line for a category, and return the fitted model."""
    df_plot = merged_df[merged_df["category"] == category].dropna()

    X = sm.add_constant(df_plot["normalised_share_articles"])
    y = df_plot["normalised_share_speeches"]
    model = sm.OLS(y, X).fit()

    intercept, slope = model.params.iloc[0], model.params.iloc[1]

    plt.figure(figsize=(10, 6))
    plt.scatter(
        df_plot["normalised_share_articles"],
        df_plot["normalised_share_speeches"],
        color="purple",
        alpha=0.7,
        label="Years",
    )
    plt.plot(
        df_plot["normalised_share_articles"],
        intercept + slope * df_plot["normalised_share_articles"],
        color="red",
        label="OLS Best Fit Regression Line",
    )
    plt.title(f"Normalised Article vs Speech Frequency: {category.capitalize()}")
    plt.xlabel("Normalised Share (Articles)")
    plt.ylabel("Normalised Share (Speeches)")
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.show()

    print(
        f"{category.capitalize()}: "
        f"R²={model.rsquared:.3f}, p-value={model.pvalues.iloc[1]:.3f}"
    )
    return model


def main():
    merged_df = load_merged_data(
        speeches_path="../data/clean/speeches_normalised.csv",
        articles_path="../data/clean/japan_news_cleaned.csv",
    )

    for category in CATEGORY_KEYWORDS.keys():
        plot_regression(merged_df, category)


if __name__ == "__main__":
    main()