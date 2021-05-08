import re
import pandas as pd
import numpy as np

import spacy
import seaborn as sns # plotting
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import CountVectorizer

class DataProcessor():

    def __init__(self):
        self.nlp = spacy.load("en_core_sci_lg")
        self.genes = pd.read_csv("data/genes.csv", sep='\t')
        self.list_of_genes = self.genes["Approved symbol"].\
            apply(lambda x: str(x).lower())

    def striphtml(self, data):
        p = re.compile(r'<.*?>')
        return p.sub('', data)

    def get_entities(self, abstract):

        ent_list = []

        doc = self.nlp(abstract)

        for ent in doc.ents:
            ent_list.append(ent.text)

        return ent_list

    def get_genes_from_entities(self, entity_list):
        # print(entity_list)
        entity_series = pd.Series(entity_list).apply(lambda x: x.lower())
        # print(entity_series)
        gene_entities = entity_series[entity_series.isin(self.list_of_genes)]

        out_string = " ".join(gene_entities.unique().tolist())

        return out_string

    def get_cleaned_entities(self, abstracts_list):

        abstracts = abstracts_list.apply(lambda x: self.striphtml(x))
        cleaned_entities = abstracts.apply(lambda x: self.get_entities(x))

        return cleaned_entities

    def plot_entity_heatmap(self,
                            cleaned_genes,
                            font_scale=.6,
                            max_entities=50):


        term_list = np.unique(
            [element.lower() for list_ in
             cleaned_genes for element in list_])

        cv = CountVectorizer(ngram_range=(1, 1),
                             max_features=max_entities)
        # matrix of token counts
        X = cv.fit_transform(cleaned_genes)
        Xc = (X.T * X)  # matrix manipulation
        Xc.setdiag(
            0)  # set the diagonals to be zeroes as it's pointless to be 1

        labels = dict(
            cv.vocabulary_.items(), key=lambda item: item[1]).keys()

        X_dense = Xc.todense()
        print(f"x mat shape: {X_dense.shape}")
        sns.set(font_scale=font_scale)
        fig = sns.clustermap(X_dense,
                             xticklabels=labels,
                             yticklabels=labels)

        return fig

    def get_gene_value_counts(self, cleaned_entities):

        # get list of all entities to calculate terms
        all_terms = [element.lower() for list_ in cleaned_entities for element in
                     list_]

        all_terms_series = pd.Series(all_terms)
        # count occurrence of each term
        val_counts = all_terms_series.value_counts()

        return val_counts