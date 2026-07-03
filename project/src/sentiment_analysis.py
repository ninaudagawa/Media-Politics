"""
sentiment_analysis.py

LLM-based topic sentiment analysis for Japan news articles and PM speeches.

Mirrors the calling convention of graph_articles.py:

    from src.sentiment_analysis import run_topic_sentiment, plot_sentiment_comparison

    news_results = run_topic_sentiment(JPnews_df, source="news")
    speech_results = run_topic_sentiment(JPspeeches_df, source="speech")

    plot_sentiment_comparison(news_results, speech_results, labels=["News", "Speeches"])
"""

from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Topic definitions
# ---------------------------------------------------------------------------

TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "Immigration": ["immigration", "immigrant", "migrant"],
    "China": ["china", "chinese", "beijing"],
    "Nuclear": ["nuclear", "nuclear power", "nuclear reactor", "fukushima"],
    "Constitution": ["constitution", "constitutional", "article 9"],
    "Deflation": ["deflation", "deflationary", "falling prices"],
    "North Korea": [
        "north korea",
        "kim jong un",
        "nuclear weapons",
        "democratic people's republic of korea",
        "dprk",
    ],
}


# ---------------------------------------------------------------------------
# LLM client (Ollama or Gemini)
# ---------------------------------------------------------------------------

class ArticleSentimentAnalyzer:
    """Thin client for sending prompts to a local Ollama model or the Gemini API."""

    OLLAMA_URL = "http://localhost:11434/api/generate"
    GEMINI_URL_TEMPLATE = (
        "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    )

    def __init__(
        self,
        backend: str = "ollama",
        ollama_model: str = "llama3.2",
        gemini_model: str = "gemini-3.5-flash",
        gemini_api_key: Optional[str] = None,
        timeout: int = 120,
    ):
        if backend not in ("ollama", "gemini"):
            raise ValueError(f"Unsupported backend: {backend!r}. Use 'ollama' or 'gemini'.")

        self.backend = backend
        self.ollama_model = ollama_model
        self.gemini_model = gemini_model
        self.timeout = timeout

        if backend == "gemini":
            self.gemini_api_key = gemini_api_key or os.getenv("GEMINIE")
            if not self.gemini_api_key:
                raise ValueError("Add GEMINIE to your .env file before using the gemini backend.")

    def _call_ollama(self, prompt: str) -> str:
        response = requests.post(
            self.OLLAMA_URL,
            json={"model": self.ollama_model, "prompt": prompt, "stream": False},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["response"]

    def _call_gemini(self, prompt: str) -> str:
        url = self.GEMINI_URL_TEMPLATE.format(model=self.gemini_model)
        response = requests.post(
            url,
            params={"key": self.gemini_api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def query_llm(self, prompt: str) -> str:
        if self.backend == "ollama":
            return self._call_ollama(prompt)
        return self._call_gemini(prompt)


# ---------------------------------------------------------------------------
# Prompt builders + parsers — news uses a JSON response, speeches use a
# labeled-text response, so each source gets its own pair.
# ---------------------------------------------------------------------------

def _build_news_prompt(text: str, topic: str) -> str:
    return f"""You are a political text analysis assistant.

Evaluate how {topic} is portrayed in the article below and respond with
ONLY a JSON object (no markdown, no commentary) in this exact shape:

{{
  "score": <integer from -2 (strongly negative) to 2 (strongly positive)>,
  "frame": "<one short phrase describing the dominant framing>",
  "key_sentence": "<the single most representative sentence from the article>"
}}

Article:

{text[:3000]}
"""


def _parse_news_analysis(raw: str) -> dict:
    try:
        cleaned = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(cleaned)
        return {
            "score": data.get("score"),
            "frame": data.get("frame"),
            "key_sentence": data.get("key_sentence"),
            "raw": raw,
        }
    except (json.JSONDecodeError, AttributeError, TypeError):
        return {"score": None, "frame": None, "key_sentence": None, "raw": raw}


def _build_speech_prompt(text: str, topic: str) -> str:
    return f"""You are a political scientist analyzing Japanese Prime Minister speeches.

Your task is to evaluate the government's stance toward {topic}.

Do NOT evaluate the emotional tone or writing style.
Instead, determine whether the Prime Minister presents {topic} as something the government supports, opposes, or discusses neutrally.

SCORE:
-2 Strongly opposed
-1 Somewhat opposed
0 Neutral, descriptive, or no clear position
1 Somewhat supportive
2 Strongly supportive

If {topic} is only briefly mentioned or lacks a clear policy position, assign a score of 0.

FRAME:
Identify the primary policy frame used to discuss {topic}. Choose the single best frame, such as:
- Economic
- Security
- Diplomatic
- Humanitarian
- Demographic
- Labor Market
- Administrative
- Environmental
- Other

KEY SENTENCE:
Quote the single sentence that best supports your evaluation.

REASONING:
Briefly explain why you assigned the score and frame.

Speech:
{text[:2500]}

Return EXACTLY:

SCORE:
FRAME:
KEY SENTENCE:
REASONING:
"""


_SPEECH_LABEL_PATTERN = re.compile(
    r"(SCORE|FRAME|KEY SENTENCE|REASONING):\s*(.*?)"
    r"(?=\n(?:SCORE|FRAME|KEY SENTENCE|REASONING):|\Z)",
    re.DOTALL | re.IGNORECASE,
)


def _parse_speech_analysis(raw: str) -> dict:
    fields = {
        label.upper(): value.strip()
        for label, value in _SPEECH_LABEL_PATTERN.findall(raw)
    }

    score = None
    score_match = re.search(r"-?\d+", fields.get("SCORE", ""))
    if score_match:
        score = int(score_match.group())

    return {
        "score": score,
        "frame": fields.get("FRAME"),
        "key_sentence": fields.get("KEY SENTENCE"),
        "reasoning": fields.get("REASONING"),
        "raw": raw,
    }


_SOURCE_CONFIG = {
    "news": {"build_prompt": _build_news_prompt, "parse": _parse_news_analysis},
    "speech": {"build_prompt": _build_speech_prompt, "parse": _parse_speech_analysis},
}


# ---------------------------------------------------------------------------
# Core analysis pipeline
# ---------------------------------------------------------------------------

class TopicSentimentAnalyzer:
    """
    Filters a dataframe of articles or speeches by topic keywords, samples
    rows per topic, and scores each sample with an LLM.

    `source` controls both the prompt style and how the response is parsed:
    "news" -> JSON response; "speech" -> labeled-text response.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        source: str = "news",
        topics: Optional[Dict[str, List[str]]] = None,
        text_column: str = "text",
        title_column: str = "title",
        date_column: str = "date",
        analyzer: Optional[ArticleSentimentAnalyzer] = None,
        sample_size: int = 20,
        random_state: int = 42,
    ):
        if source not in _SOURCE_CONFIG:
            raise ValueError(f"Unsupported source: {source!r}. Use 'news' or 'speech'.")

        self.df = df
        self.source = source
        self.topics = topics or TOPIC_KEYWORDS
        self.text_column = text_column
        self.title_column = title_column
        self.date_column = date_column
        self.analyzer = analyzer or ArticleSentimentAnalyzer(backend="ollama")
        self.sample_size = sample_size
        self.random_state = random_state

        self.topic_dfs: Dict[str, pd.DataFrame] = {}

    def _topic_mask(self, keywords: List[str]) -> pd.Series:
        pattern = "|".join(keywords)
        return self.df[self.text_column].str.contains(pattern, case=False, na=False, regex=True)

    def count_topic_mentions(self) -> Dict[str, int]:
        return {topic: int(self._topic_mask(kw).sum()) for topic, kw in self.topics.items()}

    def get_topic_rows(self, topic: str) -> pd.DataFrame:
        return self.df[self._topic_mask(self.topics[topic])]

    def sample_topic_rows(self, topic: str) -> pd.DataFrame:
        rows = self.get_topic_rows(topic)
        n = min(self.sample_size, len(rows))
        return rows.sample(n=n, random_state=self.random_state)

    def analyze_text(self, text: str, topic: str) -> dict:
        config = _SOURCE_CONFIG[self.source]
        prompt = config["build_prompt"](text, topic)
        raw = self.analyzer.query_llm(prompt)
        return config["parse"](raw)

    def analyze_topic(self, topic: str) -> pd.DataFrame:
        sample = self.sample_topic_rows(topic)

        records = []
        for _, row in sample.iterrows():
            analysis = self.analyze_text(row[self.text_column], topic)
            date_value = row[self.date_column] if self.date_column in row.index else row.name
            title_value = row[self.title_column] if self.title_column in row.index else None
            records.append({"date": date_value, "title": title_value, **analysis})

        df_result = pd.DataFrame(records)
        self.topic_dfs[topic] = df_result

        if not df_result.empty:
            print(f"Average {topic} sentiment ({self.source}): {df_result['score'].mean()}")

        return df_result

    def analyze_all_topics(self, topics: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        topics = topics or list(self.topics.keys())
        for topic in topics:
            print(f"Analyzing {topic} ({self.source})...")
            self.analyze_topic(topic)
        return self.topic_dfs


# ---------------------------------------------------------------------------
# Public functional API — mirrors graph_articles.py's
# keyword_yearly_counts(df) / plot_category(...) calling convention
# ---------------------------------------------------------------------------

def run_topic_sentiment(
    df: pd.DataFrame,
    source: str = "news",
    topics: Optional[Dict[str, List[str]]] = None,
    analyzer: Optional[ArticleSentimentAnalyzer] = None,
    sample_size: int = 20,
    random_state: int = 42,
    **kwargs,
) -> Dict[str, pd.DataFrame]:
    """
    Run LLM topic-sentiment analysis over a dataframe of articles or speeches.

    Equivalent to keyword_yearly_counts(df) from graph_articles.py: pass in
    a cleaned dataframe, get back a dict of topic -> results DataFrame.
    """
    pipeline = TopicSentimentAnalyzer(
        df,
        source=source,
        topics=topics,
        analyzer=analyzer,
        sample_size=sample_size,
        random_state=random_state,
        **kwargs,
    )
    return pipeline.analyze_all_topics()


def plot_sentiment_comparison(
    news_results: Dict[str, pd.DataFrame],
    speech_results: Dict[str, pd.DataFrame],
    labels: Tuple[str, str] = ("News", "Speeches"),
    save_path: Optional[str] = None,
) -> None:
    """
    Grouped bar chart comparing average sentiment/stance per topic between
    two result sets (e.g. news vs. speeches), pulled live from the score
    columns rather than hardcoded numbers.
    """
    topics = sorted(set(news_results) & set(speech_results))
    if not topics:
        raise ValueError("No shared topics found between news_results and speech_results.")

    news_scores = [news_results[topic]["score"].mean() for topic in topics]
    speech_scores = [speech_results[topic]["score"].mean() for topic in topics]

    x = np.arange(len(topics))
    width = 0.35

    plt.figure(figsize=(9, 6))
    plt.bar(x - width / 2, news_scores, width, label=labels[0])
    plt.bar(x + width / 2, speech_scores, width, label=labels[1])
    plt.axhline(0, color="black", linestyle="--")
    plt.xticks(x, topics, rotation=20)
    plt.ylabel("Average LLM Sentiment Score")
    plt.title(f"Average LLM Sentiment Score by Topic: {labels[0]} vs. {labels[1]}")
    plt.legend()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
    plt.show()