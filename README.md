# Project Title

## 👥 Team Members

- Erin (@erinlpat) 
- Martin (@Menendezhmartin) 
- Mariiam (@togomariiam) 
- Ailie (@akbalke)
- Cyrus (@cyrusncw05)
- Nina (@ninaudagawa)

Note: For our main document, please refer to our media_politics_guide notebook which summarizes all of our steps and project introduction, methodology, results, and conclusion. (https://github.com/ninaudagawa/Media-Politics/blob/main/project/notebooks/media_politics_guide.ipynb)

## ❓ Research Question & 🎯 Hypothesis

1. How did the policy agenda emphasized in Prime Minister speeches compare with that of the Japan Times between 2001 and 2021?
2. Which policy issues received consistently greater attention in Prime Minister speeches versus the Japan Times?
3. How did sentiment toward shared policy issues differ between Prime Minister speeches and the Japan Times? Can AI-based sentiment analysis effectively capture differences in the tone of government and media discourse, and what methodological challenges arise when applying it to political texts?
4. Can this analytical framework be generalized to compare political and media discourse in other democratic countries?
   

    \[maybe] Does issue salience relate to political discourse (political speeches, etc.)? Which one precedes the other?

**Hypotheses**
- **Hypothesis 1**: Prime Minister speeches and The Japan Times will exhibit significant differences in the policy issues they prioritize between 2001 and 2021, reflecting the distinct objectives of government leaders and the news media.
Rationale: Government speeches are intended to promote and justify policy agendas, while news media select issues based on newsworthiness, public interest, and editorial priorities. 
- **Hypothesis 2**: AI-based text tokenization and sentiment analysis will identify measurable differences in the tone of policy discussions between Prime Minister speeches and The Japan Times*, but its performance will be constrained by the complexity and nuance of political language.
Rationale: Political speeches often employ diplomatic, strategic, or deliberately neutral language that may not be fully captured by automated sentiment analysis. 

## 📁 Data Sources

| Source | Description | URL |
|--------|-------------|-----|
| Kaggle| News articles from Japanese newspapers, collected from newspapers websites and the Old Newspapers dataset. In Japanese and English. | (https://www.kaggle.com/datasets/vyhuholl/japanese-newspapers-20052021) |
| "The World and Japan" Database by Institute for Advanced Studies on Asia (IASA), The University of Tokyo| Database of Japanese Politics and International Relations Speeches of Prime Ministers| (https://worldjpn.net/documents/indices/exdpm/index-ENG.html)) |
| New York Times Index by Comparative Agnedas Project| This dataset is a systematic random sample of the New York Times Index. The sample includes the first entry on every odd-numbered page of the Index. Each entry is coded by CAP and U.S. Policy Agendas major topics and includes other variables such as the length, date and location of the story and whether it addressed government actions.| (https://www.comparativeagendas.net/datasets_codebooks) |
| State of the Union Speeches by Comparative Agnedas Project| This dataset contains information on each quasi-statement in the Presidential State of the Union Speeches. Each quasi-statement is coded according to our system of policy content categories and other variables. | ([https://worldjpn.net/documents/indices/exdpm/index-ENG.html)](https://www.comparativeagendas.net/datasets_codebooks)) |


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
| Ailie   | Manifesto analysis attempts (failed), Keywords under categories for analysis, PM speech analysis: Against keywords,indiv. analysis |
| Nina   | Finding datasets, timeline, sentiment analysis, guide markdowns, video |
| Martin   | Literature review, timeline, NYT news analysis and regression, video |
| Cyrus   | Description of contributions |
| Mariiam   | Description of contributions |

## 🔗 References
- Link to methodology references

