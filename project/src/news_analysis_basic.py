# src/analysis.py
import pandas as pd
import matplotlib.pyplot as plt
import os

def monthly_article_counts(df, date_col='date'):
    """
    Returns a Series of article counts grouped by month.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    return df[date_col].groupby(df[date_col].dt.to_period('M')).size()


def plot_monthly_counts(monthly_count, title='Number of articles per month over time',
                         save_path=None):
    """
    Plots a monthly count Series as a line chart, and optionally saves it.
    """
    monthly_count.plot(kind='line', figsize=(12, 5))
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Number of articles')
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    plt.show()


import spacy
from collections import Counter, defaultdict

NOUN_POS = {"NOUN", "PROPN", "ADJ"}
GLUE_WORDS = {"of", "the"}

GENERIC_PHRASES = {
    "list of", "number of", "end of", "part of", "result of",
    "kind of", "type of", "set of", "sort of", "lot of",
    "series of", "range of", "lack of", "use of", "case of",
    "matter of", "way of", "form of", "level of", "amount of",
    "pair of", "group of", "head of", "period of", "point of",
    "total of", "full of", "percent of", "age of", "front of",
    "suspicion of"
    # ← ADD more as you spot them in results
}
GENERIC_WORDS = {
    "last", "first", "next", "previous", "recent", "new", "old",
    "list", "number", "end", "part", "result", "kind", "type",
    "month", "year", "week", "day"
    # ← ADD more as you spot them
}
STOPWORDS = {"the", "and", "in", "to", "a", "for", "on", "at", "by"}


def extract_noun_phrases(df, text_col="text", nlp=None, batch_size=500):
    """
    Extracts multi-word noun phrases from a text column using spaCy.
    Returns (phrase_counts, phrase_doc_ids).
    """
    if nlp is None:
        nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "parser", "senter"])

    phrase_counts = Counter()
    phrase_doc_ids = defaultdict(set)

    texts = df[text_col].fillna("").tolist()
    ids = df.index.tolist()

    for doc_id, doc in zip(ids, nlp.pipe(texts, batch_size=batch_size)):
        tokens = [t for t in doc if not t.is_space and not t.is_punct]

        i = 0
        while i < len(tokens):
            phrase_tokens = []
            j = i
            while j < len(tokens) and (
                tokens[j].pos_ in NOUN_POS
                or (tokens[j].text.lower() in GLUE_WORDS and phrase_tokens)
            ):
                phrase_tokens.append(tokens[j].text)
                j += 1

            if len(phrase_tokens) >= 2:
                phrase = " ".join(phrase_tokens).lower()
                phrase_counts[phrase] += 1
                phrase_doc_ids[phrase].add(doc_id)

            i = j if j > i else i + 1

    return phrase_counts, phrase_doc_ids


def is_valid_phrase(phrase):
    words = phrase.split()
    if words[0] in STOPWORDS or words[-1] in STOPWORDS:
        return False
    if all(w in STOPWORDS for w in words):
        return False
    if phrase in GENERIC_PHRASES:
        return False
    if any(w in GENERIC_WORDS for w in words):
        return False
    return True


def build_top_phrases_df(phrase_counts, phrase_doc_ids, min_doc_freq=2, top_n=None):
    """
    Builds a filtered, sorted DataFrame of top phrases.
    """
    rows = [
        {"phrase": phrase, "total_count": count, "doc_freq": len(phrase_doc_ids[phrase])}
        for phrase, count in phrase_counts.items()
        if len(phrase_doc_ids[phrase]) >= min_doc_freq and is_valid_phrase(phrase)
    ]
    df = pd.DataFrame(rows).sort_values("total_count", ascending=False).reset_index(drop=True)
    return df.head(top_n) if top_n else df

from wordcloud import WordCloud

def plot_top_phrases_barh(df, phrase_col="phrase", count_col="total_count", top_n=10, save_path=None):
    df.head(top_n).set_index(phrase_col)[count_col].sort_values().plot(kind="barh")
    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_wordcloud(df, phrase_col="phrase", count_col="total_count", save_path=None):
    word_freq = dict(zip(df[phrase_col], df[count_col]))
    wordcloud = WordCloud(width=800, height=400, background_color='white')
    wordcloud.generate_from_frequencies(word_freq)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    plt.show()