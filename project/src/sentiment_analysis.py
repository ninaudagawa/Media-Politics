"""
Article sentiment scoring against a local Ollama model or the Gemini API.

Usage:
    analyzer = ArticleSentimentAnalyzer(backend="ollama")
    score = analyzer.score_article(article_text, topic="immigration")
"""

from __future__ import annotations

import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


KEYWORDS = [
    "china",
    "nuclear",
    "immigration",
    "constitution",
    "deflation",
    "North Korea",
]


class ArticleSentimentAnalyzer:
    """Scores article sentiment toward a topic using a configurable LLM backend."""

    OLLAMA_URL = "http://localhost:11434/api/generate"
    OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
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

    # -- LLM backends ---------------------------------------------------

    def _call_ollama(self, prompt: str) -> str:
        """Query Ollama's /api/generate endpoint with a single prompt string."""
        response = requests.post(
            self.OLLAMA_URL,
            json={
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["response"]

    def _call_ollama_chat(self, prompt: str) -> str:
        """Query Ollama's /api/chat endpoint (chat-style messages), if you need it instead."""
        response = requests.post(
            self.OLLAMA_CHAT_URL,
            json={
                "model": self.ollama_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def _call_gemini(self, prompt: str) -> str:
        """Query the Gemini API with a single prompt string."""
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
        """Dispatch a prompt to whichever backend this instance was configured with."""
        if self.backend == "ollama":
            return self._call_ollama(prompt)
        return self._call_gemini(prompt)

    # -- Scoring ----------------------------------------------------------

    def score_article(self, article_text: str, topic: str) -> Optional[int]:
        """
        Score sentiment toward `topic` in `article_text` on a -2..2 scale.

        Returns None if the model's response can't be parsed as an integer.
        """
        prompt = f"""You are a political text analysis assistant.

Evaluate the sentiment expressed toward {topic}.

Return ONLY ONE NUMBER:

-2 = strongly negative
-1 = somewhat negative
0 = neutral
1 = somewhat positive
2 = strongly positive

Article:

{article_text[:3000]}
"""
        result = self.query_llm(prompt)
        try:
            return int(result.strip())
        except ValueError:
            return None


if __name__ == "__main__":
    analyzer = ArticleSentimentAnalyzer(backend="ollama")
    sample_text = "Sample article text goes here..."
    for keyword in KEYWORDS:
        score = analyzer.score_article(sample_text, keyword)
        print(f"{keyword}: {score}")
"""
Topic-based sentiment analysis over the Japan English-language news dataset.

Loads the news CSV, finds articles matching a set of topic keyword lists,
samples articles per topic, sends each to an LLM for structured analysis
(score / frame / key sentence), and produces per-topic summaries plus a
sentiment comparison chart.

Depends on ArticleSentimentAnalyzer from sentiment_analyzer.py for LLM calls.
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd

from sentiment_analyzer import ArticleSentimentAnalyzer


# Keyword lists per topic, used to filter articles via a case-insensitive
# substring match against the article text.
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


class JapanNewsTopicAnalyzer:
    """Runs topic-filtered, LLM-scored sentiment analysis over a news CSV."""

    def __init__(
        self,
        csv_path: str,
        analyzer: Optional[ArticleSentimentAnalyzer] = None,
        sample_size: int = 20,
        random_state: int = 42,
    ):
        self.csv_path = csv_path
        self.analyzer = analyzer or ArticleSentimentAnalyzer(backend="ollama")
        self.sample_size = sample_size
        self.random_state = random_state

        self.df = self._load_data()
        self.topic_dfs: Dict[str, pd.DataFrame] = {}

    # -- Data loading -----------------------------------------------------

    def _load_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path, sep="\t")
        df["date"] = pd.to_datetime(df["date"])
        return df

    # -- Topic filtering ----------------------------------------------------

    def _topic_mask(self, keywords: List[str]) -> pd.Series:
        pattern = "|".join(keywords)
        return self.df["text"].str.contains(pattern, case=False, na=False, regex=True)

    def count_topic_mentions(self) -> Dict[str, int]:
        """Count how many articles mention each topic's keywords."""
        return {
            topic: int(self._topic_mask(keywords).sum())
            for topic, keywords in TOPIC_KEYWORDS.items()
        }

    def get_topic_articles(self, topic: str) -> pd.DataFrame:
        return self.df[self._topic_mask(TOPIC_KEYWORDS[topic])]

    def sample_topic_articles(self, topic: str) -> pd.DataFrame:
        articles = self.get_topic_articles(topic)
        n = min(self.sample_size, len(articles))
        return articles.sample(n=n, random_state=self.random_state)

    # -- LLM analysis -------------------------------------------------------

    def analyze_article(self, article_text: str, topic: str) -> dict:
        """
        Send one article to the LLM and return a parsed dict with
        score (-2..2), frame, key_sentence, and the raw response text.
        """
        prompt = f"""You are a political text analysis assistant.

Evaluate how {topic} is portrayed in the article below and respond with
ONLY a JSON object (no markdown, no commentary) in this exact shape:

{{
  "score": <integer from -2 (strongly negative) to 2 (strongly positive)>,
  "frame": "<one short phrase describing the dominant framing>",
  "key_sentence": "<the single most representative sentence from the article>"
}}

Article:

{article_text[:3000]}
"""
        raw = self.analyzer.query_llm(prompt)
        return self._parse_analysis(raw)

    @staticmethod
    def _parse_analysis(raw: str) -> dict:
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

    def analyze_topic(self, topic: str) -> pd.DataFrame:
        """Sample articles for a topic, analyze each, and store the result."""
        sample = self.sample_topic_articles(topic)

        records = []
        for _, row in sample.iterrows():
            analysis = self.analyze_article(row["text"], topic)
            records.append({"date": row["date"], "title": row["title"], **analysis})

        df = pd.DataFrame(records)
        self.topic_dfs[topic] = df

        if not df.empty:
            print(f"Average {topic} sentiment: {df['score'].mean()}")

        return df

    def analyze_all_topics(self, topics: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        topics = topics or list(TOPIC_KEYWORDS.keys())
        for topic in topics:
            print(f"Analyzing {topic}...")
            self.analyze_topic(topic)
        return self.topic_dfs

    # -- Summaries and plotting ----------------------------------------------

    def summary_table(self) -> pd.DataFrame:
        """Average sentiment score per analyzed topic, sorted ascending."""
        rows = [
            {"Topic": topic, "Average Sentiment": df["score"].mean()}
            for topic, df in self.topic_dfs.items()
        ]
        return pd.DataFrame(rows).sort_values("Average Sentiment")

    def plot_summary(self, save_path: Optional[str] = None) -> None:
        summary = self.summary_table()

        plt.figure(figsize=(8, 5))
        plt.barh(summary["Topic"], summary["Average Sentiment"])
        plt.axvline(x=0, linestyle="--")
        plt.xlabel("Average Sentiment")
        plt.title("Average Sentiment by Topic based on News Articles")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)
        plt.show()

    def summarize_topic_with_llm(self, topic: str) -> str:
        df = self.topic_dfs[topic]
        text = "\n\n".join(df["raw"].dropna().tolist())

        prompt = f"""Summarize the findings for {topic}.

Include:
- overall sentiment
- dominant frames
- recurring themes

Keep to 4-5 sentences.

{text[:12000]}
"""
        return self.analyzer.query_llm(prompt)

    def summarize_all_topics_with_llm(self) -> Dict[str, str]:
        summaries = {}
        for topic in self.topic_dfs:
            summary = self.summarize_topic_with_llm(topic)
            summaries[topic] = summary
            print("=" * 80)
            print(topic)
            print(summary)
        return summaries


if __name__ == "__main__":
    pipeline = JapanNewsTopicAnalyzer(
        csv_path="../../project/data/raw/japan_english_news_kaggle.csv",
    )

    print(pipeline.count_topic_mentions())

    pipeline.analyze_all_topics()
    pipeline.plot_summary()
    pipeline.summarize_all_topics_with_llm()        
"""
Topic-based government-stance analysis over Japanese PM speech transcripts.

Loads the speech CSV, finds speeches matching topic keyword lists, samples
speeches per topic, sends each to an LLM to classify the government's stance
(score / frame / key sentence / reasoning), and produces per-topic summaries
plus a stance comparison chart.

Depends on ArticleSentimentAnalyzer from sentiment_analyzer.py for LLM calls,
and reuses the topic keyword definitions from japan_news_topic_analyzer.py so
the news and speech pipelines stay aligned on what each topic means.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd

from sentiment_analyzer import ArticleSentimentAnalyzer
from japan_news_topic_analyzer import TOPIC_KEYWORDS

# Matches "LABEL: value" blocks up to the next known label or end of string.
_LABEL_PATTERN = re.compile(
    r"(SCORE|FRAME|KEY SENTENCE|REASONING):\s*(.*?)"
    r"(?=\n(?:SCORE|FRAME|KEY SENTENCE|REASONING):|\Z)",
    re.DOTALL | re.IGNORECASE,
)


class PMSpeechTopicAnalyzer:
    """Runs topic-filtered, LLM-scored government-stance analysis over PM speeches."""

    def __init__(
        self,
        csv_path: str,
        analyzer: Optional[ArticleSentimentAnalyzer] = None,
        sample_size: int = 20,
        random_state: int = 42,
        topics: Optional[Dict[str, List[str]]] = None,
    ):
        self.csv_path = csv_path
        self.analyzer = analyzer or ArticleSentimentAnalyzer(backend="ollama")
        self.sample_size = sample_size
        self.random_state = random_state
        self.topics = topics or TOPIC_KEYWORDS

        self.df = self._load_data()
        self.topic_dfs: Dict[str, pd.DataFrame] = {}

    # -- Data loading -----------------------------------------------------

    def _load_data(self) -> pd.DataFrame:
        return pd.read_csv(self.csv_path, index_col="date", parse_dates=True)

    # -- Topic filtering ------------------------------------------------------

    def _topic_mask(self, keywords: List[str]) -> pd.Series:
        pattern = "|".join(keywords)
        return self.df["text"].str.contains(pattern, case=False, na=False, regex=True)

    def count_topic_mentions(self) -> Dict[str, int]:
        """Count how many speeches mention each topic's keywords."""
        return {
            topic: int(self._topic_mask(keywords).sum())
            for topic, keywords in self.topics.items()
        }

    def get_topic_speeches(self, topic: str) -> pd.DataFrame:
        return self.df[self._topic_mask(self.topics[topic])]

    def sample_topic_speeches(self, topic: str) -> pd.DataFrame:
        speeches = self.get_topic_speeches(topic)
        n = min(self.sample_size, len(speeches))
        return speeches.sample(n=n, random_state=self.random_state)

    # -- LLM analysis -------------------------------------------------------

    def analyze_speech(self, speech_text: str, topic: str) -> dict:
        """
        Send one speech to the LLM and return a parsed dict with score
        (-2..2), frame, key_sentence, reasoning, and the raw response text.
        """
        prompt = f"""You are a political scientist analyzing Japanese Prime Minister speeches.

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
{speech_text[:2500]}

Return EXACTLY:

SCORE:
FRAME:
KEY SENTENCE:
REASONING:
"""
        raw = self.analyzer.query_llm(prompt)
        return self._parse_analysis(raw)

    @staticmethod
    def _parse_analysis(raw: str) -> dict:
        fields = {
            label.upper(): value.strip()
            for label, value in _LABEL_PATTERN.findall(raw)
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

    def analyze_topic(self, topic: str) -> pd.DataFrame:
        """Sample speeches for a topic, analyze each, and store the result."""
        sample = self.sample_topic_speeches(topic)

        records = []
        for date, row in sample.iterrows():
            analysis = self.analyze_speech(row["text"], topic)
            records.append({"date": date, "title": row["title"], **analysis})

        df = pd.DataFrame(records)
        self.topic_dfs[topic] = df

        if not df.empty:
            print(f"Average {topic} sentiment: {df['score'].mean()}")

        return df

    def analyze_all_topics(self, topics: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        topics = topics or list(self.topics.keys())
        for topic in topics:
            print(f"Analyzing {topic}...")
            self.analyze_topic(topic)
        return self.topic_dfs

    # -- Summaries and plotting ----------------------------------------------

    def summary_table(self) -> pd.DataFrame:
        """Average government-stance score per analyzed topic, sorted ascending."""
        rows = [
            {"Topic": topic, "Average Government Stance": df["score"].mean()}
            for topic, df in self.topic_dfs.items()
        ]
        return pd.DataFrame(rows).sort_values("Average Government Stance")

    def plot_summary(self, save_path: Optional[str] = None) -> None:
        summary = self.summary_table()

        plt.figure(figsize=(8, 5))
        plt.barh(summary["Topic"], summary["Average Government Stance"])
        plt.axvline(x=0, linestyle="--")
        plt.xlim(-2, 2)
        plt.xlabel("Average Government Stance")
        plt.title("Average Government Stance by Topic in Prime Minister Speeches")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)
        plt.show()

    def summarize_topic_with_llm(self, topic: str) -> str:
        df = self.topic_dfs[topic]
        text = "\n\n".join(df["raw"].dropna().tolist())

        prompt = f"""Summarize the findings for {topic}.

Include:
- overall sentiment
- dominant frames
- recurring themes

Keep to 4-5 sentences.

{text[:12000]}
"""
        return self.analyzer.query_llm(prompt)

    def summarize_all_topics_with_llm(self) -> Dict[str, str]:
        summaries = {}
        for topic in self.topic_dfs:
            summary = self.summarize_topic_with_llm(topic)
            summaries[topic] = summary
            print("=" * 80)
            print(topic)
            print(summary)
        return summaries


if __name__ == "__main__":
    pipeline = PMSpeechTopicAnalyzer(
        csv_path="../data/clean/pm_speeches_en.csv",
    )

    print(pipeline.count_topic_mentions())

    pipeline.analyze_all_topics()
    pipeline.plot_summary()
    pipeline.summarize_all_topics_with_llm()
"""
Compares per-topic sentiment between news coverage and PM speeches.

Takes an already-analyzed JapanNewsTopicAnalyzer and PMSpeechTopicAnalyzer
(i.e. analyze_all_topics() has been run on both) and builds a side-by-side
comparison table and grouped bar chart, pulling live numbers from each
pipeline's topic_dfs rather than hardcoded values.
"""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from japan_news_topic_analyzer import JapanNewsTopicAnalyzer
from pm_speech_topic_analyzer import PMSpeechTopicAnalyzer


class NewsSpeechComparison:
    """Builds a side-by-side comparison of news sentiment vs. PM speech stance per topic."""

    def __init__(
        self,
        news_pipeline: JapanNewsTopicAnalyzer,
        speech_pipeline: PMSpeechTopicAnalyzer,
    ):
        self.news_pipeline = news_pipeline
        self.speech_pipeline = speech_pipeline

    def comparison_table(self) -> pd.DataFrame:
        """
        Average score per topic for both news and speeches.

        Only topics analyzed in BOTH pipelines are included, so this stays
        correct however many topics you've actually run analyze_all_topics() on.
        """
        topics = sorted(
            set(self.news_pipeline.topic_dfs) & set(self.speech_pipeline.topic_dfs)
        )
        if not topics:
            raise ValueError(
                "No shared analyzed topics found between the two pipelines. "
                "Run analyze_all_topics() on both before comparing."
            )

        rows = [
            {
                "Topic": topic,
                "News": self.news_pipeline.topic_dfs[topic]["score"].mean(),
                "Speeches": self.speech_pipeline.topic_dfs[topic]["score"].mean(),
            }
            for topic in topics
        ]
        return pd.DataFrame(rows)

    def print_summary(self) -> None:
        table = self.comparison_table()

        print("News")
        for _, row in table.iterrows():
            print(f"{row['Topic']}: {row['News']}")

        print("\nSpeeches")
        for _, row in table.iterrows():
            print(f"{row['Topic']}: {row['Speeches']}")

    def plot_comparison(
        self,
        news_label: str = "Japan Times",
        speech_label: str = "PM Speeches",
        save_path: Optional[str] = None,
    ) -> None:
        comparison = self.comparison_table()

        x = np.arange(len(comparison))
        width = 0.35

        plt.figure(figsize=(9, 6))
        plt.bar(x - width / 2, comparison["News"], width, label=news_label)
        plt.bar(x + width / 2, comparison["Speeches"], width, label=speech_label)
        plt.axhline(0, color="black", linestyle="--")
        plt.xticks(x, comparison["Topic"], rotation=20)
        plt.ylabel("Average LLM Sentiment Score")
        plt.title("Average LLM Sentiment Score by Topic: News vs. Prime Minister Speeches")
        plt.legend()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)
        plt.show()


if __name__ == "__main__":
    news_pipeline = JapanNewsTopicAnalyzer(
        csv_path="../../project/data/raw/japan_english_news_kaggle.csv",
    )
    news_pipeline.analyze_all_topics()

    speech_pipeline = PMSpeechTopicAnalyzer(
        csv_path="../data/clean/pm_speeches_en.csv",
    )
    speech_pipeline.analyze_all_topics()

    comparison = NewsSpeechComparison(news_pipeline, speech_pipeline)
    comparison.print_summary()
    comparison.plot_comparison()