import spacy
from collections import Counter, defaultdict
import pandas as pd
import sys
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from src.keywords import CATEGORY_KEYWORDS  # defense, economy, nuclear, immigration

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


def is_political(phrase):
    """Return True if the phrase contains any political keyword."""
    return any(keyword in phrase for keyword in ALL_POLITICAL_KEYWORDS)


def matched_categories(phrase):
    """Return the list of keyword categories a phrase matches."""
    return [cat for cat, kws in CATEGORY_KEYWORDS.items() if any(kw in phrase for kw in kws)]


def build_top_political_phrases_df(speeches_df, year_start=YEAR_START, year_end=YEAR_END, min_doc_freq=MIN_DOC_FREQ, top_n=100):

    speeches_range = speeches_df[
        (speeches_df.index.year >= year_start) & (speeches_df.index.year <= year_end)
    ]

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
        if len(phrase_doc_ids[phrase]) >= min_doc_freq
    ]

    return (
        pd.DataFrame(rows)
        .sort_values("total_count", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
