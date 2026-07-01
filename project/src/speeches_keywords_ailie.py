"""
Function library version of notebooks/speeches_keywords_AILIE.ipynb.

Import these into any notebook and call them with a speeches_df instead of
copy-pasting the analysis code:

    from src.speeches_keywords_ailie import (
        plot_category_trend_charts,
        plot_combined_category_trend_chart,
        count_category_matches,
        build_top_political_phrases_df,
        plot_wordcloud,
        plot_top_bar_chart,
    )
"""

import re
from collections import Counter, defaultdict

import pandas as pd
import spacy
import matplotlib.pyplot as plt
from wordcloud import WordCloud

from src.keywords import CATEGORY_KEYWORDS  # defense, economy, nuclear, immigration

YEAR_START, YEAR_END = 2004, 2021
COLORS = ["blue", "red", "green", "orange"]

TARGET_POS = {"NOUN", "PROPN", "ADJ"}
GLUE_WORDS = {"of", "the", "this", "these", "those", "our", "their", "his", "her"}
GENERIC_NOUNS = {
    "number", "amount", "kind", "type", "part", "lot", "rest", "use",
    "case", "way", "fact", "thing", "point", "matter", "issue", "term",
}
MIN_DOC_FREQ = 2

nlp = spacy.load("en_core_web_sm")


def _category_patterns(category_keywords):
    return {
        category: r"\b(" + "|".join(re.escape(kw) for kw in keywords) + r")\b"
        for category, keywords in category_keywords.items()
    }


def _category_speech_counts(pattern, df, year_start, year_end):
    matches = df[df["text"].str.contains(pattern, case=False, na=False, regex=True)]
    counts = matches.resample("YE").size()
    return counts.reindex(
        pd.date_range(f"{year_start}-01-01", f"{year_end}-12-31", freq="YE"), fill_value=0
    )


def get_category_year_counts(speeches_df, category_keywords=CATEGORY_KEYWORDS, year_start=YEAR_START, year_end=YEAR_END):
    """Yearly speech counts per category, restricted to [year_start, year_end]."""
    speeches_range = speeches_df[
        (speeches_df.index.year >= year_start) & (speeches_df.index.year <= year_end)
    ]
    patterns = _category_patterns(category_keywords)
    return {
        category: _category_speech_counts(pattern, speeches_range, year_start, year_end)
        for category, pattern in patterns.items()
    }


def plot_category_trend_charts(speeches_df, category_keywords=CATEGORY_KEYWORDS, year_start=YEAR_START, year_end=YEAR_END):
    """One line chart per category showing speech counts per year."""
    category_year_counts = get_category_year_counts(speeches_df, category_keywords, year_start, year_end)
    for category, counts in category_year_counts.items():
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(counts.index.year, counts.values, marker="o")
        ax.set_xlabel("Year")
        ax.set_ylabel("Number of speeches")
        ax.set_title(f"Speeches Mentioning {category.capitalize()} Keywords ({year_start}-{year_end})")
        ax.set_xticks(range(year_start, year_end + 1))
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True)
        plt.tight_layout()
        plt.show()


def plot_combined_category_trend_chart(speeches_df, category_keywords=CATEGORY_KEYWORDS, year_start=YEAR_START, year_end=YEAR_END, colors=COLORS):
    """Single chart with all categories' yearly speech counts overlaid."""
    category_year_counts = get_category_year_counts(speeches_df, category_keywords, year_start, year_end)
    fig, ax = plt.subplots(figsize=(12, 6))
    for (category, counts), color in zip(category_year_counts.items(), colors):
        ax.plot(counts.index.year, counts.values, label=category.capitalize(), color=color, marker="o", linewidth=2)

    ax.set_xlabel("Year")
    ax.set_ylabel("Number of speeches")
    ax.set_title(f"PM Speeches by Keyword Category Over Time ({year_start}-{year_end})")
    ax.set_xticks(range(year_start, year_end + 1))
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper left")
    ax.grid(True)
    plt.tight_layout()
    plt.show()


def count_category_matches(speeches_df, category_keywords=CATEGORY_KEYWORDS, verbose=True):
    """Return {category: matching speeches df}, optionally printing counts."""
    patterns = _category_patterns(category_keywords)
    category_matches = {}
    for category, pattern in patterns.items():
        matches = speeches_df[speeches_df["text"].str.contains(pattern, case=False, na=False, regex=True)]
        category_matches[category] = matches
        if verbose:
            print(f"{category}: {len(matches)} speeches mention this category's keywords")
    return category_matches


def extract_phrases(text):
    """Extract candidate noun/adjective phrases from a piece of text."""
    doc = nlp(str(text))
    tokens = [t for t in doc if not t.is_space and not t.is_punct]
    phrases = []
    i = 0
    while i < len(tokens):
        phrase_tokens = []
        j = i
        while j < len(tokens) and (
            tokens[j].pos_ in TARGET_POS
            or (tokens[j].text.lower() in GLUE_WORDS and phrase_tokens)
        ):
            phrase_tokens.append(tokens[j].text)
            j += 1

        # drop trailing glue words so phrases don't end mid-thought (e.g. "use of")
        while phrase_tokens and phrase_tokens[-1].lower() in GLUE_WORDS:
            phrase_tokens.pop()
            j -= 1

        if (
            len(phrase_tokens) >= 2
            and phrase_tokens[0].lower() not in GENERIC_NOUNS
            and phrase_tokens[-1].lower() not in GENERIC_NOUNS
        ):
            phrases.append(" ".join(phrase_tokens).lower())

        i = j if j > i else i + 1
    return phrases


def is_political(phrase, all_keywords):
    return any(keyword in phrase for keyword in all_keywords)


def matched_categories(phrase, category_keywords=CATEGORY_KEYWORDS):
    return [cat for cat, kws in category_keywords.items() if any(kw in phrase for kw in kws)]




import spacy
from collections import Counter, defaultdict
import pandas as pd

import sys
sys.path.append("notebooks")
from keywords import CATEGORY_KEYWORDS  # defense, economy, nuclear, immigration

YEAR_START, YEAR_END = 2004, 2021
TARGET_POS = {"NOUN", "PROPN", "ADJ"}
GLUE_WORDS = {"of", "the", "this", "these", "those", "our", "their", "his", "her"}
GENERIC_NOUNS = {
    "number", "amount", "kind", "type", "part", "lot", "rest", "use",
    "case", "way", "fact", "thing", "point", "matter", "issue", "term",
}
MIN_DOC_FREQ = 2

nlp = spacy.load("en_core_web_sm")
ALL_POLITICAL_KEYWORDS = set().union(*CATEGORY_KEYWORDS.values())

speeches_range = speeches_df[
    (speeches_df.index.year >= YEAR_START) & (speeches_df.index.year <= YEAR_END)
]

def extract_phrases(text):
    doc = nlp(str(text))
    tokens = [t for t in doc if not t.is_space and not t.is_punct]
    phrases = []
    i = 0
    while i < len(tokens):
        phrase_tokens = []
        j = i
        while j < len(tokens) and (
            tokens[j].pos_ in TARGET_POS
            or (tokens[j].text.lower() in GLUE_WORDS and phrase_tokens)
        ):
            phrase_tokens.append(tokens[j].text)
            j += 1

        # drop trailing glue words so phrases don't end mid-thought (e.g. "use of")
        while phrase_tokens and phrase_tokens[-1].lower() in GLUE_WORDS:
            phrase_tokens.pop()
            j -= 1

        if (
            len(phrase_tokens) >= 2
            and phrase_tokens[0].lower() not in GENERIC_NOUNS
            and phrase_tokens[-1].lower() not in GENERIC_NOUNS
        ):
            phrases.append(" ".join(phrase_tokens).lower())

        i = j if j > i else i + 1
    return phrases

def is_political(phrase):
    return any(keyword in phrase for keyword in ALL_POLITICAL_KEYWORDS)

def matched_categories(phrase):
    return [cat for cat, kws in CATEGORY_KEYWORDS.items() if any(kw in phrase for kw in kws)]

phrase_counts = Counter()
phrase_doc_ids = defaultdict(set)

for date, row in speeches_range.iterrows():
    for phrase in extract_phrases(row["text"]):
        if not is_political(phrase):
            continue
        phrase_counts[phrase] += 1
        phrase_doc_ids[phrase].add(date)

rows = [
    {
        "phrase": phrase,
        "categories": ", ".join(matched_categories(phrase)),
        "total_count": count,
        "doc_freq": len(phrase_doc_ids[phrase]),
    }
    for phrase, count in phrase_counts.items()
    if len(phrase_doc_ids[phrase]) >= MIN_DOC_FREQ
]

top_political_phrases_df = pd.DataFrame(rows).sort_values("total_count", ascending=False).head(100).reset_index(drop=True)
print(top_political_phrases_df)

# word cloud, bar chart, and graph of frequency of top 10 keywords

from wordcloud import WordCloud
import matplotlib.pyplot as plt

phrase_frequencies = dict(zip(top_political_phrases_df["phrase"], top_political_phrases_df["total_count"]))

political_wordcloud = WordCloud(
    width=1000, height=600, background_color="white"
).generate_from_frequencies(phrase_frequencies)

plt.figure(figsize=(12, 7))
plt.imshow(political_wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title(f"Political Keywords in PM Speeches ({YEAR_START}-{YEAR_END})")
plt.show()


import matplotlib.pyplot as plt

top_10_phrases_df = top_political_phrases_df.head(10)

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(top_10_phrases_df["phrase"], top_10_phrases_df["total_count"])

ax.set_xlabel("Keyword")
ax.set_ylabel("Total count")
ax.set_title(f"Top 10 Political Keywords ({YEAR_START}-{YEAR_END})")
ax.tick_params(axis="x", rotation=45, labelsize=9)
for label in ax.get_xticklabels():
    label.set_horizontalalignment("right")
ax.grid(True, axis="y")
plt.tight_layout()
plt.show()














def build_top_political_phrases_df(speeches_df, category_keywords=CATEGORY_KEYWORDS, year_start=YEAR_START, year_end=YEAR_END, min_doc_freq=MIN_DOC_FREQ, top_n=100):
    """Top political noun/adjective phrases in speeches, ranked by total count."""
    all_keywords = set().union(*category_keywords.values())
    speeches_range = speeches_df[
        (speeches_df.index.year >= year_start) & (speeches_df.index.year <= year_end)
    ]

    phrase_counts = Counter()
    phrase_doc_ids = defaultdict(set)

    for date, row in speeches_range.iterrows():
        for phrase in extract_phrases(row["text"]):
            if not is_political(phrase, all_keywords):
                continue
            phrase_counts[phrase] += 1
            phrase_doc_ids[phrase].add(date)

    rows = [
        {
            "phrase": phrase,
            "categories": ", ".join(matched_categories(phrase, category_keywords)),
            "total_count": count,
            "doc_freq": len(phrase_doc_ids[phrase]),
        }
        for phrase, count in phrase_counts.items()
        if len(phrase_doc_ids[phrase]) >= min_doc_freq
    ]

    return (
        pd.DataFrame(rows)
        .sort_values("total_count", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


def plot_wordcloud(phrases_df, phrase_col="phrase", count_col="total_count", title="Political Keywords in PM Speeches"):
    """Render a word cloud sized by phrase frequency."""
    frequencies = dict(zip(phrases_df[phrase_col], phrases_df[count_col]))
    wordcloud = WordCloud(width=1000, height=600, background_color="white").generate_from_frequencies(frequencies)

    plt.figure(figsize=(12, 7))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title(title)
    plt.show()


#def plot_top_bar_chart(phrases_df, phrase_col="phrase", count_col="total_count", top_n=10, title="Top 10 Political Keywords"):
    #"""Bar chart of the top N phrases by count."""
    #top_df = phrases_df.head(top_n)
    #fig, ax = plt.subplots(figsize=(10, 6))
    #ax.bar(top_df[phrase_col], top_df[count_col])
    #ax.set_xlabel("Keyword")
    #ax.set_ylabel("Total count")
    #ax.set_title(title)
    #ax.tick_params(axis="x", rotation=45, labelsize=9)
    #for label in ax.get_xticklabels():
        #label.set_horizontalalignment("right")
    #ax.grid(True, axis="y")
    #plt.tight_layout()
    #plt.show()

#this is the one I'm trying to make look like speeches_analysis.py where it gives me the distinct key words 
def plot_top_bar_chart(top_political_phrases_df):
    top_10_phrases_df = top_political_phrases_df.head(10)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(top_10_phrases_df["phrase"], top_10_phrases_df["total_count"])

    ax.set_xlabel("Keyword")
    ax.set_ylabel("Total count")
    ax.set_title(f"Top 10 Political Keywords ({YEAR_START}-{YEAR_END})")
    ax.tick_params(axis="x", rotation=45, labelsize=9)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    ax.grid(True, axis="y")
    plt.tight_layout()
    plt.show()
