# CineMatch

A small movie recommendation frontend backed by the recommender in `notebooks/movies.ipynb`. FastAPI loads `data.pkl`, `indices.pkl`, and `tfidf_metrix.pkl`; recommendations use the notebook's TF-IDF matrix and cosine similarity. Poster paths come from the original metadata CSV and FastAPI fetches the poster images.

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000>. The pickle files were created with pandas' PyArrow string type, so `pyarrow` is included in the requirements. Poster requests return immediately while FastAPI downloads and caches images in the background. It tries TMDB first, then a Wikipedia thumbnail; cached posters are served locally on later requests. The cache is stored in `data/poster_cache/` and ignored by Git.

## Project layout

```text
main.py                 FastAPI endpoints and poster fetching
requirements.txt        Python dependencies
frontend/               Simple CineMatch page and styles
notebooks/              Notebook and saved recommender artifacts
data/raw/               Movie metadata and source CSV
```

## Evaluating the recommender

**Response time:** each API response includes a `Server-Timing` header with FastAPI processing time in milliseconds. In browser DevTools, open Network, select `/api/recommendations/<movie_id>`, and check Timing or the `Server-Timing` response header. For a simple repeatable check, request that endpoint 30–50 times and report the median and 95th percentile; measure with `uvicorn` running without `--reload` for a cleaner result. Also record the machine and whether the first request is included, since the first request can include startup or cache effects.

**Recommendation quality:** standard metrics need known relevant movies for each user's query (for example, movies they watched or rated). The current metadata has movie ratings but no user-to-movie rating history, so it cannot support valid user-based Precision@K or Recall@K by itself. With relevance labels, use Precision@5, Recall@5, and NDCG@5. Until then, manually review recommendations for a sample of movies and report that as a qualitative check. You can also report catalogue coverage and genre diversity, but those describe variety rather than whether a recommendation is relevant.
