import streamlit as st
import pandas as pd
import numpy as np
import json

from matplotlib import pyplot as plt

import sys

sys.path.append('../src/')
sys.path.append('..')
sys.path.append('.')

from src.process_data import DataProcessor as preprocess
import src.data_retrieval as dr

# st.beta_set_page_config(
#     page_title="Analysis of Glioblastoma papers from PubMed",
#     layout="wide",
#     initial_sidebar_state="expanded")

st.title('Analysis of Glioblastoma papers from PubMed')

get_data = dr.GetPubmedData(create_db=False)

cnx = get_data.db_con

prep = preprocess()

st.subheader("Newest papers")
n_articles = st.number_input(label="Newest N papers",
                             value=5)
if st.button('Refresh latest data (WARNING: this is slow)'):
    st.text('Fetching latest day of data, please wait a moment...')
    get_data.get_recent_data()
    st.write("Done")

st.text('Creating summary table')

sub_df = pd.read_sql_query(f"""SELECT * FROM abstracts 
                              ORDER BY retrieval_date DESC
                              LIMIT {n_articles}""", cnx)


@st.cache(allow_output_mutation=True, max_entries=10, ttl=3600)
def get_abstract_table(sub_df, n_articles):
    sub_df['top_entities'] = [pd.Series(json.loads(x)).value_counts()[:10].
                                  index.tolist() for x in sub_df['entities']]
    sub_df["year"] = sub_df.date.apply(lambda x: int(x[:4]))

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

df = pd.read_sql_query("SELECT * FROM abstracts", cnx)
df.entities = df.entities.apply(lambda x: json.loads(x))

df["year"] = df.date.apply(lambda x: int(x[:4]))
df.sort_values(by="retrieval_date",
               ascending=True,
               inplace=True)

year_since = st.slider("Display data since",
                       min_value=int(df.year.min()),
                       max_value=int(df.year.max()),
                       value=2020,
                       step=1)

year_index = df.year >= year_since
sub_year1 = df.genes[year_index]
st.write(f"Computed on {len(sub_year1)} abstracts")
value_counts = prep.get_gene_value_counts(sub_year1)

TOP = 20
st.subheader(f'Plot top {TOP} Gene counts accross all abstracts')
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
                               value=20)

max_sample_size = st.number_input(label="Number of abstracts to sample",
                                  value=500,
                                  min_value=2,
                                  max_value=2000)

# year_index2 = df.year >= year_since2
#
# sub_year2 = df.genes[year_index2]

@st.cache(allow_output_mutation=True, max_entries=10, ttl=3600)
def plot_heatmap(year_df, max_features, sample_size=500):

    sample_df = year_df.sample(np.min([sample_size, len(year_df)]))
    st.write(f"Computed on {len(sample_df)} abstracts")

    fig_map = prep.plot_entity_heatmap(sample_df,
                                       font_scale=.9,
                                       max_entities=max_features)
    st.pyplot(fig_map)


plot_heatmap(sub_year1,
             max_features,
             sample_size=max_sample_size)

cnx.close()
