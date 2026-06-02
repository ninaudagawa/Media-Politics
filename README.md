# Project Title

## 👥 Team Members

- Erin (@erinlpat) 
- Martin (@Menendezhmartin) 
- Mariiam (@togomariiam) 
- Ailie (@akbalke)
- Cyrus (@cyrusncw05)
- Nina (@ninaudagawa)

### 📃 Team Google Doc
This is a link to our shared team [google doc](https://docs.google.com/document/d/1Du4dsbBI-boIYcwgLPmUy349A3xhu8lIs0hSR87-xnA/edit?usp=sharing) where we are currently drafting our ideas and saving potential resources.


## ❓ Research Question & 🎯 Hypothesis

NEW (still working): 
1. What topical trends can we draw between media coverage by the Japan Times and party manifestos between 2001-2021?
2. Which core policy issues championed in party manifestos (e.g., constitutional reform, nuclear energy) are consistently under-represented or over-represented in mainstream Japanese news articles?
3. How did the semantic context of politically charged terms like "Stability" {安定} and "Reform" {改革} evolve in Japanese news media compared to how the LDP and DPJ/CDPJ framed them between 2001 and 2021?
4. How did media coverage and party manifestos' priorities of coverage shift as a result of significant events such as the 2008 financial crash, the 2011 triple disaster, the 2020 pandemic and Ddd the text data eventually revert to pre-crisis baselines, and if so, how fast?
5. Does the sentiment of news media toward specific political parties become more polarized during years marked by major crises compared to the compared to the parties' self-representation in manifestos
6. Does a spike in topic salience within party manifestos precede a corresponding increase in news coverage, or does media attention drive changes in the subsequent election's manifestos?

   

    \[maybe] Does issue salience relate to political discourse (political speeches, etc.)? Which one precedes the other?

**Hypotheses**
- **Hypothesis 1**: drafting...
- **Hypothesis 2**: drafting...

## 📁 Data Sources

| Source | Description | URL |
|--------|-------------|-----|
| Kaggle| News articles from Japanese newspapers, collected from newspapers websites and the Old Newspapers dataset. In Japanese and English. | (https://www.kaggle.com/datasets/vyhuholl/japanese-newspapers-20052021) |
| Manifesto Project| Japanese party manifestos between 2001-2023 from various political parties| ([https://www.kaggle.com/datasets/vyhuholl/japanese-newspapers-20052021](https://manifestoproject.wzb.eu/)) |


### Possible CAP Topics and variables 
| Topic | Example Subtopics |
|--------|-------------|
| Macroeconomics|Interest rates, unemployment, national budget, tariffs|
| Civil Rights |Voting rights, gender discrimination, privacy|
| Public Health |Healthcare reform, prescription drugs, mental health|
|Environment |Climate change, pollution|

## 📂 Folder Structure

### Folder Structure Notes
- All projects MUST follow this standardized folder structure
- `data/raw/` - **NEVER** edit manually; store original data here
- `data/clean/` - Cleaned datasets ready for analysis
- `data/temp/` - Temporary files (can be deleted)
- `notebooks/` - Jupyter notebooks for analysis
- `src/` - Python code
- `reports/` - Final outputs: plots, summaries, model files
- `docs/` - Project documentation, README, presentations

### Folder Structure Tree

```tree
project/
├── data/
│   ├── raw/                   # Original, immutable data
│   │   ├── world_bank_raw.csv
│   │   └── imf_financials_raw.csv
│   ├── clean/                 # Cleaned, transformed data
│   │   ├── world_bank_clean.csv
│   │   └── imf_merged_clean.csv
│   └── temp/                  # Temporary working files
├── notebooks/                 # Jupyter notebooks for exploration
│   ├── 01_eda_worldbank.ipynb
│   ├── 02_regression_analysis.ipynb
│   └── 03_policy_simulations.ipynb
├── src/                       # Production-ready scripts
│   ├── download_worldbank.py  # API/Scraping script
│   ├── clean_data.py          # Merging and cleaning logic
│   └── visualize_worldbank.py # Chart generation functions
├── reports/                   # Final outputs
│   ├── figures/               # Saved .png plots for the memo
│   │   ├── gdp_trend_line.png
│   │   └── debt_distribution.png
│   ├── policy_memo_final.pdf
│   └── regression_results.txt
└── docs/                      # Documentation
    ├── data_details.md        # Data dictionary & column definitions
    ├── data_architecture.md   # Pipeline logic and join keys
    ├── policy_context.md      # Political background & stakeholders
```

## 📅 Timeline

| Milestone | Deadline | Deliverable |
|-----------|----------|-------------|
| M1        | May 20     | Research Question, Datasets, Use python to show descriptive statistics      |
| M2        | June 6     | 5 Visualizations with descriptions, Migrate to .py files (Stretch)     |
| M3        | July 1     | Presentation video      |
| Final        | July 8 or 15     | Video and Peer Review      |

## 🤝 Contributions

| Member | Tasks |
|--------|-------|
| Erin   | Cleaning datasets, News Article Keyword Analysis, Manifesto API Data Extraction |
| Ailie   | Description of contributions |
| Nina   | Description of contributions |
| Martin   | Description of contributions |
| Cyrus   | Description of contributions |
| Mariiam   | Description of contributions |

## 🔗 References
- Link to methodology references

