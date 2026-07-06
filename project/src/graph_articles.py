import re
import pandas as pd
import matplotlib.pyplot as plt
from src.keywords import CATEGORY_KEYWORDS


def build_pattern(keywords):
    sorted_kws = sorted(keywords, key=len, reverse=True)
    return '|'.join(re.escape(kw) for kw in sorted_kws)


def keyword_yearly_counts(df, date_col='date'):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    yearly_totals = (
        df.resample('YE', on=date_col)
        .size()
        .rename('total_articles')
    )

    rows = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        pattern = build_pattern(keywords)
        yearly_counts = (
            df.assign(count=(
                df['text'].str.contains(pattern, case=False, na=False) |
                df['title'].str.contains(pattern, case=False, na=False)
            ).astype(int))
            .resample('YE', on=date_col)['count']
            .sum()
            .reset_index()
        )
        yearly_counts.columns = ['date', 'article_count']
        yearly_counts['category'] = category

        yearly_counts = yearly_counts.join(yearly_totals, on='date')
        yearly_counts['normalized'] = yearly_counts['article_count'] / yearly_counts['total_articles']
        yearly_counts['normalized'] = yearly_counts['normalized'].fillna(0)
        yearly_counts['article_count'] = yearly_counts['article_count'].fillna(0)

        rows.append(yearly_counts)

    results = pd.concat(rows, ignore_index=True)
    results['date'] = results['date'].dt.to_period('Y').astype(str)
    return results


def plot_category(category, *result_dfs, labels=None, title=None, min_docs=5):
    if labels is None:
        labels = [f'Dataset {i+1}' for i in range(len(result_dfs))]

    fig, ax = plt.subplots(figsize=(14, 4))

    for i, (df, label) in enumerate(zip(result_dfs, labels)):
        cat_df = df[df['category'] == category].copy()
        color = f'C{i}'
        
        # plot full line (clipped) to keep scale tight
        cat_df['clipped'] = cat_df['normalized'].clip(upper=cat_df[cat_df['total_articles'] >= min_docs]['normalized'].max() * 1.2)
        ax.plot(cat_df['date'], cat_df['clipped'],
                linestyle='dotted', color=color, alpha=0.3)
        
        # overlay solid line for reliable years only
        reliable = cat_df[cat_df['total_articles'] >= min_docs]
        ax.plot(reliable['date'], reliable['normalized'],
                linestyle='solid', color=color, label=label)

    ax.set_title(title or f'{category.capitalize()} keyword frequency over time')
    ax.set_xlabel('Year')
    ax.set_ylabel('Proportion of documents')
    ax.legend()
    plt.tight_layout()
    # plt.savefig(f'{category}_newsvspeech_comparison.png')
    plt.show()