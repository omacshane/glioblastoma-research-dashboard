# glioblastoma-research-dashboard

The demo version of the app is now live [here](https://share.streamlit.io/omacshane/glioblastoma-research-dashboard/main/src/streamlit_app.py), thanks to [Streamlit sharing](https://streamlit.io/sharing)!

# Streamlit app

<img src="/figures/clustermap.png" width="250" height="250">

## Summary

The Streamlit app retrives recent GBM-related abstracts using the [PubMed Entrez API](https://www.ncbi.nlm.nih.gov/home/develop/api/) app displays summaries and relations between papers.

## API keys

The default settings access the API without an API key and return only 30 records per query.
The use the full search capability, get an API key from https://www.ncbi.nlm.nih.gov/account/ and replace the value for `api_key` in `src/tmp_config.ini`:

```yaml
[API_KEY]
api_key = <your API key goes here>
```
## Funtionality
#### Recent abstract retrieval
#### Word frequencies
#### Named Entity Recognition (NER)
[scispaCy](https://allenai.github.io/scispacy/) is used to extract entities from the biomedical domain. These are then linked with know biomarker lists and correlated across abstracts

## Example outputs:

![Papers](/figures/new_papers.png)

![Barplot](/figures/barplot.png)

![Papers2](/figures/streamlit11.png)

![Heatmap](/figures/clustermap.png)

Gene data via https://www.ensembl.org/Homo_sapiens/Info/Index

Utilises SciSpacy - SpaCy models for biomedical text processing for entity recognition https://allenai.github.io/scispacy/

All feedback is welcome on usability and functionality requests.