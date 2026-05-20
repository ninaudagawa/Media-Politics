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

   

> State your central research question clearly and concisely
- **Research Question 1** (not question but just idea):  Use the Multisource Financial News corpus to track how political issues are framed (economic opportunity vs. security threat vs. humanitarian crisis) over time. Cross-reference with CAP legislation counts to test whether negative media framing predicts legislative restrictiveness on specific issues. Supplement with V-Dem media freedom scores to analyze whether framing differs across regime types
- **Research Question 2**: How does one political topic “_____” displayed in the media (specifically news) change over 2 national election cycles (within 3 years pre-election, during election, post election) within one country 
- **Research Question 3**: What is the pattern of specific political topics that appear in the news during 1 national election cycle? 
- **Research Question 4**: Issue salience in the media and electoral cycles: starting with frequency of appearance and adding more sophistication to the analysis (framing, sentiment, etc.)
    12 months before election -> 3/6 months after election
    Control year without elections
    Pre-announcement of elections vs. post-announcement of elections
    Questions to be answered: 
    Issue emergence and persistence: are issues perennial or cyclical? Which are more permanent? When does an issue become salient? 
    Does media coverage change across different media outlets (according to ideology, etc.)? 
    Do topics interact with each other? Do they compete?
    Does the campaign narrow to fewer topics as the election comes closer?
    Does framing of topics change according to electoral cycles?
    Do topics relate to actual events? Or are they fully manufactured by media discourse?
    \[maybe] Does issue salience relate to political discourse (political speeches, etc.)? Which one precedes the other?

**Hypotheses**
- **Hypothesis 1**: specific political topics that are highly controversial "Tariffs, unemployment, taxes, cost of living, inflation, pensions), migration (asylum, refugees, migrants, immigrants, border, etc.), gender and identity (abortion, LGTB, trans, etc.), etc." appear more in the news during national election cycles. 
- **Hypothesis 2**: Political issues are framed more using strong language that elicits emotional responses during national election cycles in countries with polarizing politics? 
- **Hypothesis 3**: Issue salience increases as election day approaches, especially for high-stakes or conflictual topics
- **Hypothesis 4**: A small number of issues dominate coverage in the final weeks of the campaign.
- **Hypothesis 5**: Some issues show a short peak and quick disappearance, while others remain stable across the full cycle.
- **Hypothesis 6**: Issues linked to scandals or crises rise sharply but have shorter life spans than structural issues like the economy or immigration.
- **Hypothesis 7**: Migration has become the most salient topic in election cycles
- **Hypothesis 8**: Ideologically distinct outlets differ in the timing and intensity of issue attention.
- **Hypothesis 9**: Right-leaning and left-leaning outlets may not just mention different issues, but also frame the same issue differently.
- **Hypothesis 10**: Issue salience is competitive: an increase in one topic crowds out others.
- **Hypothesis 11**: Some issues co-occur systematically, such as immigration and crime, or economy and inflation.
- **Hypothesis 12**: Topic co-occurrence becomes stronger during campaign periods than in non-election periods.
- **Hypothesis 13**: Political actors lead issue attention before the media does, especially after formal campaign announcement.
- **Hypothesis 14**: Media coverage amplifies or distorts the issue agenda set by candidates rather than reproducing it exactly.

### Potential Countries to analyze 
- From literature review: "Among these are countries that are known to have very polarized politics, such as the **United States**, **Brazil**, and **Malaysia**, and others that do not, such as **Canada**, **New Zealand**, and **Japan**. By testing these potential moderators, this study addresses several gaps in the literature.”
- Recommendations: France, Germany, Italy, Denmark, Brazil, Australia
  

## 📁 Data Sources

| Source | Description | URL |
|--------|-------------|-----|
| Kaggle| News articles from Japanese newspapers, collected from newspapers websites and the Old Newspapers dataset. In Japanese and English. | (https://www.kaggle.com/datasets/vyhuholl/japanese-newspapers-20052021) |
| World Bank | Development Statistics | [World Bank Open Data API](https://data360.worldbank.org/en/api) |
| IMF | Economic Information | [IMF Data APIs](https://data.imf.org/en/Resource-Pages/IMF-API) |
| Comparative Agendas Project (CAP)| Includes dedicated datasets mapping media agendas and political topics.| [CAP Datasets](https://www.comparativeagendas.net/datasets_codebooks) |
| Multisource Financial News| Large-scale news archive|
|Geopolitical Risk Index (GPR) | Daily/Monthly news-based text mining of geopolitical risk factors globally| 
|V-Dem (Varieties of Democracy) | Has specialized modules evaluating media freedom, censorship, and political pluralism| [V-Dem Datasets](https://www.v-dem.net/data/)|
|RSS Scraper Live Feed|  Real-time global news headlines and/or articles to use for webscraping and NLP|
|Apify Web Scrapers|Some social media websites like twitter no longer have a functioning up-to-date API for us to source posts from. Apify has user-built models to help us scrape posts for content or sentiment analysis.|[Apify Website](https://apify.com/)|
|Hugging Face | Sentiment analysis models that "specialize" in different things. We might plan to use this to analyze whatever media type we chose to focus on (News articles, social media posts, etc.). We will probably use some BERT model. | [Various Sentiment Analysis Models](https://huggingface.co/models?other=sentiment-analysis) |
| Legislative Information APIs | Some countries make legislative voting data public using APIs like the USA and UK. Could be a useful way to track different governments' attention to policies. | [USA](https://www.congress.gov/), [UK](https://api.electoralcommission.org.uk/docs/) |
| IPU Parline | Global Data on National Parliaments. | [Parline API](https://data.ipu.org/data-tools/api/) | 

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
| M2        | June 6     | 5 Visualizations with descriptions, Migrate to .py files      |
| M3        | July 1     | Presentation video      |
| Final        | July 8 or 15     | Video and Peer Review      |

## 🤝 Contributions

| Member | Tasks |
|--------|-------|
| Erin   | Description of contributions |
| Ailie   | Description of contributions |
| Nina   | Description of contributions |
| Martin   | Description of contributions |
| Cyrus   | Description of contributions |
| Mariiam   | Description of contributions |

## 🔗 References
- Link to methodology references

