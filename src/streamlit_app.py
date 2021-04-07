import streamlit as st
import pandas as pd

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

get_data = dr.GetPubmedData()
st.text('Fetching latest day of data, please wait a moment...')
get_data.get_recent_data()
st.text('Done!')
st.text('Creating summary table')
cnx = get_data.db_con

prep = preprocess()

st.subheader("Newest papers")
n_articles = st.number_input(label="Newest N papers",
                             value=5)
sub_df = pd.read_sql_query(f"""SELECT * FROM abstracts 
                              ORDER BY retrieval_date DESC
                              LIMIT {n_articles}""", cnx)

sub_cleaned_entities = prep.get_cleaned_entities(sub_df["abstract"])
sub_df['entities'] = [pd.Series(x).value_counts()[:10].
                      index.tolist() for x in sub_cleaned_entities]
sub_df["year"] = sub_df.date.apply(lambda x: int(x[:4]))

st.table(sub_df[["date",
                 "title",
                 "full_journal_name",
                 "last_author",
                 "doi",
                 "entities",
                 "retrieval_date"]].tail(n_articles)[::-1])


df = pd.read_sql_query("SELECT * FROM abstracts", cnx)

#df["entities"] = df.abstract.apply(lambda x: prep.get_entities(x))

cleaned_entities = prep.get_cleaned_entities(df["abstract"])
df['entities'] = [pd.Series(x).value_counts()[:10].
                      index.tolist() for x in cleaned_entities]
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
value_counts = prep.get_gene_value_counts(cleaned_entities[year_index])

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

year_since2 = st.slider("Display data since year",
                        min_value=int(df.year.min()),
                        max_value=int(df.year.max()),
                        value=2020,
                        step=1)

max_features = st.number_input(label="Number of top co-occurences",
                               value=30)

year_index2 = df.year >= year_since2


fig_map = prep.plot_entity_heatmap(cleaned_entities[year_index2],
                                   font_scale=.9,
                                   max_entities=max_features)
st.pyplot(fig_map)

cnx.close()