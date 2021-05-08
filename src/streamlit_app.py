import streamlit as st
import pandas as pd
import numpy as np
import json

from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import RendererAgg
import logging
import sys

logging.basicConfig(level=logging.DEBUG)
_lock = RendererAgg.lock

sys.path.append('../src/')
sys.path.append('..')
sys.path.append('.')

import src.data_retrieval as dr

# st.beta_set_page_config(
#     page_title="Analysis of Glioblastoma papers from PubMed",
#     layout="wide",
#     initial_sidebar_state="expanded")

st.title('Analysis of Glioblastoma papers from PubMed')

get_data = dr.GetPubmedData(create_db=False)
logging.info("Make DB connection")
cnx = get_data.db_con

st.subheader("Newest papers")
n_articles = st.number_input(label="Newest N papers",
                             value=5,
                             min_value=1,
                             max_value=50)
if st.button('Refresh latest data (WARNING: this is slow)'):
    st.text('Fetching latest day of data, please wait a moment...')
    get_data.get_recent_data()
    st.write("Done")

st.text('Creating summary table')

sub_df = pd.read_sql_query(f"""SELECT * FROM abstracts 
                              ORDER BY retrieval_date DESC
                              LIMIT {n_articles}""", cnx)


#@st.cache(allow_output_mutation=True, max_entries=10, ttl=1600)
def get_abstract_table(sub_df, n_articles):
    logging.info("Get top entities")
    sub_df['top_entities'] = [pd.Series(json.loads(x)).value_counts()[:10].
                                  index.tolist() for x in sub_df['entities']]
    logging.info("Iterate over year")
    sub_df["year"] = sub_df.date.apply(lambda x: int(x[:4]))
    logging.info("Return subbed df")
    sub_df = sub_df[["date",
                     "title",
                     "full_journal_name",
                     "last_author",
                     "doi",
                     "top_entities",
                     "genes",
                     "retrieval_date"]].tail(n_articles)[::-1]

    return sub_df


sub_df_new = get_abstract_table(sub_df, n_articles)
st.table(sub_df_new)

logging.info("Run query over full table")
df = pd.read_sql_query("SELECT * FROM abstracts", cnx)
logging.info("Load entities from json")
df.entities = df.entities.apply(lambda x: json.loads(x))
logging.info("Apply substrining to years")
df["year"] = df.date.apply(lambda x: int(x[:4]))
logging.info("Sort values by date")
df.sort_values(by="retrieval_date",
               ascending=True,
               inplace=True)

year_since = st.slider("Display data since",
                       min_value=int(df.year.min()),
                       max_value=int(df.year.max()),
                       value=2020,
                       step=1)
logging.info("Get year index")
year_index = df.year >= year_since
logging.info("Subset df by year")
sub_year1 = df.genes[year_index]
st.write(f"Computed on {len(sub_year1)} abstracts")
logging.info("Get gene value counts")
value_counts = get_data.preprocessor.get_gene_value_counts(sub_year1)
# logging(f"df: {sub_year1}")
# logging(f"Value counts: {value_counts}")

TOP = 20
st.subheader(f'Plot top {TOP} Gene counts accross all abstracts')
logging.info("Plot word freqs")
with _lock:
    fig, ax = plt.subplots()
    ax.bar(value_counts.index[:TOP],
           value_counts.values[:TOP])
    plt.xticks(rotation=45)
    plt.tick_params(axis='x', which='major', labelsize=5)
    plt.tight_layout()

    st.pyplot(fig)

st.subheader('Plot heatmap of TOP N co-occurences of terms in abstracts')

# year_since2 = st.slider("Display data since year",
#                         min_value=int(df.year.min()),
#                         max_value=int(df.year.max()),
#                         value=2020,
#                         step=1)

max_features = st.number_input(label="Number of top co-occurences",
                               value=20,
                               min_value=2,
                               max_value=50)

max_sample_size = st.number_input(label="Number of abstracts to sample",
                                  value=500,
                                  min_value=2,
                                  max_value=10000)

# year_index2 = df.year >= year_since2
#
# sub_year2 = df.genes[year_index2]

#@st.cache(allow_output_mutation=True, max_entries=10, ttl=1600)
def plot_heatmap(year_df, max_features, sample_size=500):

    logging.info("Sample dataframe")
    sample_df = year_df.sample(np.min([sample_size, len(year_df)]))
    st.write(f"Computed on {len(sample_df)} abstracts")
    logging.info("Run heatmap function")
    fig_map = get_data.preprocessor.plot_entity_heatmap(sample_df,
                                                        font_scale=.9,
                                                        max_entities=max_features)

    return fig_map

with _lock:
    heatmp_plot = plot_heatmap(sub_year1,
                                max_features,
                                sample_size=max_sample_size)
    logging.info("Set axis")
    plt.setp(heatmp_plot.ax_heatmap.get_xticklabels(), rotation=45)
    logging.info("Plot heatmap")
    st.pyplot(heatmp_plot)
# logging.info("Close DB connection")
# cnx.close()
