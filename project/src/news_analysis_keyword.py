import pandas as pd
import matplotlib.pyplot as plt
import os

def category_article_count(keywords, df, text_col='text'):
    """
    Counts articles containing ANY keyword in the given list (category-level count).
    """
    pattern = "|".join(keywords)
    return df[text_col].str.contains(pattern, case=False, na=False).sum()


def category_totals_df(category_keywords, df, text_col='text'):
    """
    Builds a DataFrame of total article counts per category.
    """
    rows = []
    for category, keywords in category_keywords.items():
        count = category_article_count(keywords, df, text_col=text_col)
        rows.append({"category": category, "unique_articles": count})

    return pd.DataFrame(rows).sort_values("unique_articles", ascending=False).reset_index(drop=True)


def category_article_count_by_year(keywords, df, text_col='text', year_col='year'):
    """
    Counts articles matching a category's keywords, grouped by year.
    """
    pattern = "|".join(keywords)
    mask = df[text_col].str.contains(pattern, case=False, na=False)
    return df[mask].groupby(year_col).size()


def build_category_normalised_df(category_keywords, df, date_col='date', text_col='text'):
    """
    Builds a long-format DataFrame of normalised category shares per year.
    Adds a 'year' column to df internally (does not mutate the original).
    """
    df = df.copy()
    df = df.set_index(date_col)
    df['year'] = df.index.year

    total_per_year = df.groupby('year').size()

    rows = []
    for category, keywords in category_keywords.items():
        counts_by_year = category_article_count_by_year(keywords, df, text_col=text_col)
        normalised = (counts_by_year / total_per_year).fillna(0)

        for year, norm_value in normalised.items():
            rows.append({
                "category": category,
                "year": year,
                "article_count": counts_by_year.get(year, 0),
                "total_articles": total_per_year[year],
                "normalised_share": norm_value
            })

    return pd.DataFrame(rows).sort_values(["category", "year"]).reset_index(drop=True)


def plot_category_share(category_name, category_normalised, x_title="Time",
                         y_title="Normalised share (%)", main_title=None, save_path=None):
    """
    Plots normalised share over time for a single category.
    """
    df_plot = category_normalised[category_normalised['category'] == category_name]
    title = main_title or f"Articles with Keyword Category: {category_name.capitalize()}"

    fig, ax = plt.subplots()
    ax.plot(df_plot['year'].astype(int), df_plot['normalised_share'])
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.set_xlabel(x_title)
    ax.set_ylabel(y_title)
    ax.set_title(title)
    ax.grid(True)

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, bbox_inches='tight', dpi=300)

    return fig


def plot_combined_category_shares(category_keywords, category_normalised, colors=None,
                                   title="Articles by Keyword Category Over Time", save_path=None):
    """
    Plots normalised share over time for all categories on one chart.
    """
    colors = colors or ['blue', 'red', 'green', 'orange']

    fig, ax = plt.subplots(figsize=(12, 6))
    for category, color in zip(category_keywords.keys(), colors):
        df_plot = category_normalised[category_normalised['category'] == category]
        ax.plot(df_plot['year'].astype(int), df_plot['normalised_share'],
                label=category.capitalize(), color=color, linewidth=2)

    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.set_xlabel("Years")
    ax.set_ylabel("Normalised Share (%)")
    ax.set_title(title)
    ax.legend(loc='upper left')
    ax.grid(True)

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, bbox_inches='tight', dpi=300)

    return fig