import requests
from bs4 import BeautifulSoup as Soup
from tqdm import tqdm
import re
import datetime
import sqlite3
import configparser
import sys
import json

from src.process_data import DataProcessor as preprocess

import logging
logging.basicConfig(level=logging.DEBUG)

sys.path.append('../src/')
sys.path.append('src/')
sys.path.append('..')
sys.path.append('.')

class GetPubmedData():
    
    def __init__(self,
                 create_db=True,
                 connect_to_db=True):

        self.config = configparser.ConfigParser()
        self.config.read('src/tmp_config.ini')
        self.preprocessor = preprocess()
        print(self.config.sections())
        api_key = self.config['API_KEY']['api_key']
        self.api_string = ""
        if api_key == None:
            """if there is no API key present run with default which returns
                just twenty records per request"""
            self.api_string = f"&api_key={self.config['API_KEY']['api_key']}"
        print(self.api_string)

        if connect_to_db:
            logging.info("connecting to DB")
            self.local_database_name = "src/database/"+self.config['DATABASE']['db_name']
            self.db_con = sqlite3.connect(self.local_database_name)
        
        if create_db:
            logging.info("Creating DB")
            self.db_con.execute("""CREATE TABLE IF NOT EXISTS abstracts 
                                                    (id INTEGER PRIMARY KEY,
                                                    date text,
                                                    retrieval_date text,
                                                    source text,
                                                    last_author text,
                                                    title text,
                                                    language text,
                                                    doi text,
                                                    full_journal_name text,
                                                    abstract text,
                                                    entities text,
                                                    genes text)""")
            
    def _try_get_field(self, field):
        
        return_field = ""
        
        if field is not None:
            
            if len(field) == 1:
                return_field = field[0].getText()
            elif len(field) > 1:
                try:
                    return_field = field.getText()
                except Exception as e:
                    print(f"Failed to extract field {field} "
                          f"with exception {e}")
            
        return return_field
            
    def get_abstract(self, id):

        base_url = "https://pubmed.ncbi.nlm.nih.gov/"
        abstract_page = requests.get(base_url+id)

        soup_abstract = Soup(abstract_page.content)
        
        abstract = soup_abstract.find("div", {"id": "enc-abstract"})
        clean_abstract = re.sub(r"[\n\t]*", "", str(abstract))

        return clean_abstract

    def get_entities_from_abstract(self, text):

        abstract = self.preprocessor.striphtml(data=text)
        sub_cleaned_entities = self.preprocessor.get_entities(abstract)

        gene_list = self.preprocessor.get_genes_from_entities(sub_cleaned_entities)

        json_entities = json.dumps(sub_cleaned_entities)
        json_genes = json.dumps(gene_list)

        return json_entities, json_genes

    def get_meta_data(self, id):

        response = requests.get(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={id}{self.api_string}')

        summary = Soup(response.content,'html.parser')

        pub_date = self._try_get_field(summary.find_all("item",  {"name": "PubDate"}))
        source = self._try_get_field(summary.find_all("item",  {"name": "Source"}))
        last_author = self._try_get_field(summary.find_all("item",  {"name": "LastAuthor"}))
        title = self._try_get_field(summary.find_all("item",  {"name": "Title"}))
        language = self._try_get_field(summary.find_all("item",  {"name": "Lang"}))
        doi = self._try_get_field(summary.find_all("item",  {"name": "DOI"}))
        full_journal_name = self._try_get_field(summary.find_all("item",  {"name": "FullJournalName"}))
        retrieval_date = str(datetime.datetime.today())

        return pub_date, retrieval_date, source, last_author, title, language, doi, full_journal_name

    def write_data_to_db(self, id, db=None):

        if db is None:
            db = self.db_con
    
        (pub_date, retrieval_date, source,
         last_author, title, language,
         doi, full_journal_name) = self.get_meta_data(id)
        abstract = self.get_abstract(str(id))
        entities, genes = self.get_entities_from_abstract(abstract)

        try:
            db.execute("""INSERT OR IGNORE INTO abstracts 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (id,
                        pub_date,
                        retrieval_date,
                        source,
                        last_author,
                        title,
                        language,
                        doi,
                        full_journal_name,
                        abstract,
                        entities,
                        genes))
            db.commit()
        except Exception as e:
            logging.error('Encountered error: ' + str(e))


    def query_definition(self, pub_med_database, year):

        string = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db={pub_med_database}&usehistory=y{self.api_string}&retmax=100000&term=glioblastoma+AND+{year}[pdat]"

        return string

    def recent_query(self,
                     pub_med_database,
                     last_n_days):

        string = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db={pub_med_database}&usehistory=y{self.api_string}&retmax=100000&term=glioblastoma&reldate={last_n_days}"

        return string

    def query_to_db(self, query):

        page = requests.get(query)

        soup = Soup(page.content, 'html.parser')
        idlist = [x.get_text() for x in soup.idlist.find_all('id')]
        n_ids = len(idlist)
        print(f"{n_ids} IDs retrieved")
        logging.info("Writing items to DB")
        i = 0
        for id in tqdm(idlist):
            self.write_data_to_db(id)
            if (i % 100) == 0:
                print(f"{i}/{n_ids} abstracts processed")
            i += 1

        print("Idlist saved to database")

    def get_data_from_years(self,
                            start_year=None,
                            database="pubmed"):

        present_year = datetime.datetime.today().year

        if start_year is None:
            start_year = present_year

        year_list = list(range(start_year, present_year))
        logging.info(f"Fetching data from {start_year} to {present_year}")

        if len(year_list) == 0:
            year_list = [start_year]

        for year in tqdm(year_list):
            year_query = self.query_definition(database, year)
            print(f"Processing year {year}")
            self.query_to_db(year_query)

        print("Finished processing years")

    def get_recent_data(self,
                        database="pubmed",
                        n_days=1):
        logging.info(f"Fetching data from past {n_days}")
        query = self.recent_query(database,
                                  n_days)

        self.query_to_db(query)
        print(f"Finished retrieving last {n_days} days of data")


if __name__ == '__main__':

    gpd = GetPubmedData()
    print("WARNING: this could take a while")
    #gpd.get_data_from_years(2021)
    gpd.get_recent_data()
    print("Finished querying historical data")