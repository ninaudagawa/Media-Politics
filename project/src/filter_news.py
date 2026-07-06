import pandas as pd
import json
import re
from tqdm import tqdm

BATCH_SIZE = 10          # articles per model call
CHECKPOINT_EVERY = 50    # batches between saves to disk
CHECKPOINT_PATH = "political_filter_checkpoint.csv"

def first_n_sentences(text, n=3):
    if pd.isna(text) or not text.strip():
        return ""
    # simple sentence splitter -- good enough for this purpose, doesn't need to be perfect
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:n])

def classify_batch(texts, model="llama3.1"):
    snippets = [first_n_sentences(t, n=3) for t in texts]
    numbered = "\n\n".join(
        f"[{i}] {s}" for i, s in enumerate(snippets)
    )

    prompt = f"""You are classifying news articles by genre.

For each numbered article below, decide if it is primarily about politics, 
government, diplomacy, or international relations (as opposed to e.g. entertainment, 
sports, movies, celebrity news, etc).

Articles:
{numbered}

Respond with ONLY a JSON array of {len(texts)} values, each "yes" or "no", 
in order matching the article numbers. Example format: ["yes", "no", "yes"]
No explanation, no other text."""

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0},
    )
    content = response["message"]["content"].strip()

    # model sometimes wraps JSON in ```json fences despite instructions -- strip if present
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())

    try:
        results = json.loads(content)
        if len(results) != len(texts):
            raise ValueError(f"expected {len(texts)} results, got {len(results)}")
        return [str(r).strip().lower().startswith("yes") for r in results]
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  WARNING: batch parse failed ({e}), falling back to per-row classification")
        return [classify_single(t, model=model) for t in texts]


def classify_single(text, model="llama3.1"):
    if pd.isna(text) or not text.strip():
        return False
    snippet = first_n_sentences(text, n=3)
    prompt = f"""Article text:
\"\"\"{snippet}\"\"\"

Is this article primarily about politics, the economy, government, diplomacy, or international relations?
Answer with ONLY one word: "yes" or "no"."""

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0},
    )
    return response["message"]["content"].strip().lower().startswith("yes")


def classify_dataframe(df, text_col="text", model="llama3.1", resume=True):
    df = df.copy().reset_index(drop=True)
    df["is_political"] = pd.NA

    start_idx = 0
    if resume:
        try:
            checkpoint = pd.read_csv(CHECKPOINT_PATH)
            df.loc[checkpoint.index, "is_political"] = checkpoint["is_political"].values
            start_idx = checkpoint["is_political"].notna().sum()
            print(f"Resuming from checkpoint: {start_idx} rows already classified")
        except FileNotFoundError:
            pass

    rows_to_process = df.index[start_idx:]
    batches = [rows_to_process[i:i + BATCH_SIZE] for i in range(0, len(rows_to_process), BATCH_SIZE)]

    for batch_num, batch_idx in enumerate(tqdm(batches, desc="Classifying")):
        texts = df.loc[batch_idx, text_col].fillna("").tolist()
        results = classify_batch(texts, model=model)
        df.loc[batch_idx, "is_political"] = results

        if (batch_num + 1) % CHECKPOINT_EVERY == 0:
            df[["is_political"]].to_csv(CHECKPOINT_PATH)

    df[["is_political"]].to_csv(CHECKPOINT_PATH)  # final save
    return df