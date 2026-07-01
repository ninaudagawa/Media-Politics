#Below is: Most common political keywords, Most common keywords within 4 distinct
# categories, the count of the same keywords as the news analysis notebook, then
# visualizations of the most common political keywords at the end

import os
print(os.getcwd())

import os
import pandas as pd

os.chdir('/Users/ailiebalke/Documents/GitHub/Media-Politics/project')

speeches_df = pd.read_csv('data/clean/pm_speeches_en.csv', index_col="date", parse_dates=True)
print(speeches_df.tail())

import re
import matplotlib.pyplot as plt
import pandas as pd

CATEGORY_KEYWORDS = {
    "defense": {
        "defense", "defence", "military", "self-defense", "self-defence",
        "security", "troops", "army", "navy", "armed forces", "war", "SDF",
        "missile", "military base", "alliance", "deterrence", "article 9", "threat", "north korea", "china", "russia", "security council"
    },
    "economy": {
        "economy", "economic", "trade", "tax", "budget", "growth",
        "inflation", "employment", "wage", "industry", "investment",
        "market", "finance", "financial", "gdp", "deficit", "export",
        "import", "business", "company", "stimulus", "interest rate", "exchange rate",
        "Bank of Japan", "economic growth", "financial contributions"
    },
    "nuclear": {
        "nuclear", "atomic", "reactor", "radiation", "fukushima",
        "non-proliferation", "weapons", "plutonium", "uranium",
        "power plant", "nuclear weapons", "world free of nuclear weapons", "atomic bomb survivors", "nuclear disarmament"
    },
    "immigration": {
        "immigration", "immigrant", "refugee", "migrant", "migration",
        "asylum", "border", "foreign worker", "visa", "naturalization",
        "nationalisation", "nationalization", "permanent resident",
        "foreigner"
    },
}

YEAR_START, YEAR_END = 2004, 2021
COLORS = ["blue", "red", "green", "orange"]

speeches_2004_2021 = speeches_df[
    (speeches_df.index.year >= YEAR_START) & (speeches_df.index.year <= YEAR_END)
]

category_patterns = {
    category: r"\b(" + "|".join(re.escape(kw) for kw in keywords) + r")\b"
    for category, keywords in CATEGORY_KEYWORDS.items()
}

def category_speech_counts(pattern, df):
    matches = df[df["text"].str.contains(pattern, case=False, na=False, regex=True)]
    counts = matches.resample("YE").size()
    return counts.reindex(
        pd.date_range(f"{YEAR_START}-01-01", f"{YEAR_END}-12-31", freq="YE"), fill_value=0
    )

category_year_counts = {
    category: category_speech_counts(pattern, speeches_2004_2021)
    for category, pattern in category_patterns.items()
}

# Individual trend chart per category
for category, counts in category_year_counts.items():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(counts.index.year, counts.values, marker="o")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of speeches")
    ax.set_title(f"Speeches Mentioning {category.capitalize()} Keywords ({YEAR_START}-{YEAR_END})")
    ax.set_xticks(range(YEAR_START, YEAR_END + 1))
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True)
    plt.tight_layout()
    plt.show()

# Combined trend chart, all categories together
fig, ax = plt.subplots(figsize=(12, 6))
for (category, counts), color in zip(category_year_counts.items(), COLORS):
    ax.plot(counts.index.year, counts.values, label=category.capitalize(), color=color, marker="o", linewidth=2)

ax.set_xlabel("Year")
ax.set_ylabel("Number of speeches")
ax.set_title(f"PM Speeches by Keyword Category Over Time ({YEAR_START}-{YEAR_END})")
ax.set_xticks(range(YEAR_START, YEAR_END + 1))
ax.tick_params(axis="x", rotation=45)
ax.legend(loc="upper left")
ax.grid(True)
plt.tight_layout()
plt.show()

import sys
import re
import pandas as pd

sys.path.append("notebooks")
from keywords import CATEGORY_KEYWORDS

category_patterns = {
    category: r"\b(" + "|".join(re.escape(kw) for kw in keywords) + r")\b"
    for category, keywords in CATEGORY_KEYWORDS.items()
}

category_matches = {}
for category, pattern in category_patterns.items():
    matches = speeches_df[speeches_df["text"].str.contains(pattern, case=False, na=False, regex=True)]
    category_matches[category] = matches
    print(f"{category}: {len(matches)} speeches mention this category's keywords")

# Example: look at the speeches matched for one category
print(category_matches["defense"][["title", "place"]].head())

# Just top keywords for speeches:

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
