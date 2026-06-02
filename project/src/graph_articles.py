import pandas as pd
import matplotlib.pyplot as plt

def article_graph(keyword, x_title, y_title, main_title):
    japan_english_filepath = "../../project/data/clean/Japan_cleaned_news.csv"
    JPnews_pd = pd.read_csv(japan_english_filepath, index_col='date', parse_dates=True)

    JPnews_pd_keyword = JPnews_pd[JPnews_pd['text'].str.contains(keyword, case=False)]

    df_plot = JPnews_pd_keyword.resample('YE').size()

    fig, ax = plt.subplots()
    ax.plot(df_plot.index, df_plot.values)
    ax.set_xlabel(x_title)
    ax.set_ylabel(y_title)
    ax.set_title(main_title)
    ax.grid(True)
    
    return fig