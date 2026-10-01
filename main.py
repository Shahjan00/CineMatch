import ast
import csv
import json
import pickle
import threading
from time import perf_counter
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).parent
NOTEBOOK = ROOT / "notebooks"
POSTER_BASE = "https://image.tmdb.org/t/p/w500"
POSTER_CACHE = ROOT / "data" / "poster_cache"
POSTER_CACHE.mkdir(parents=True, exist_ok=True)
pending_posters = set()
failed_posters = set()
poster_lock = threading.Lock()
poster_slots = threading.Semaphore(4)

data = pd.read_pickle(NOTEBOOK / "data.pkl").reset_index(drop=True)
with (NOTEBOOK / "indices.pkl").open("rb") as file:
    indices = pickle.load(file)
with (NOTEBOOK / "tfidf_metrix.pkl").open("rb") as file:
    tfidf_matrix = pickle.load(file)

posters = {}
genres_by_title = {}
years_by_title = {}
with (ROOT / "data" / "raw" / "movies_metadata.csv").open(encoding="utf-8", errors="replace", newline="") as file:
    for row in csv.DictReader(file):
        movie_title = row.get("title")
        if movie_title:
            if row.get("poster_path"):
                posters.setdefault(movie_title, row["poster_path"])
            if row.get("release_date"):
                years_by_title.setdefault(movie_title, row["release_date"][:4])
            try:
                genres_by_title.setdefault(movie_title, [genre["name"] for genre in ast.literal_eval(row.get("genres") or "[]")])
            except (ValueError, SyntaxError, TypeError, KeyError):
                pass

popularity = pd.to_numeric(data["popularity"], errors="coerce").fillna(0)
popular_rows = popularity.sort_values(ascending=False).index.tolist()
app = FastAPI(title="CineMatch")


@app.middleware("http")
async def measure_request_time(request, call_next):
    start = perf_counter()
    response = await call_next(request)
    elapsed_ms = (perf_counter() - start) * 1000
    response.headers["Server-Timing"] = f"app;dur={elapsed_ms:.2f}"
    return response


def movie_at(row_number):
    row = data.iloc[int(row_number)]
    movie_title = str(row["title"])
    rating = pd.to_numeric(row.get("vote_average", 0), errors="coerce")
    return {
        "id": int(row_number),
        "title": movie_title,
        "overview": "" if pd.isna(row.get("overview")) else str(row.get("overview", "")),
        "tagline": "" if pd.isna(row.get("tagline")) else str(row.get("tagline", "")),
        "genres": genres_by_title.get(movie_title, str(row.get("genres", "")).split()),
        "rating": float(rating) if pd.notna(rating) else 0,
        "year": years_by_title.get(movie_title, ""),
        "poster": posters.get(str(row["title"]), ""),
    }


@app.get("/")
def home():
    return FileResponse(ROOT / "frontend" / "index.html")


@app.get("/api/movies")
def get_movies(search: str = "", limit: int = 30):
    search = search.lower().strip()
    result = []
    for row_number in popular_rows:
        row = data.iloc[row_number]
        searchable = f"{row['title']} {row.get('genres', '')} {row.get('overview', '')}".lower()
        if not search or search in searchable:
            result.append(movie_at(row_number))
            if len(result) >= min(max(limit, 1), 100):
                break
    return result


@app.get("/api/movies/{movie_id}")
def get_movie(movie_id: int):
    if movie_id < 0 or movie_id >= len(data):
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie_at(movie_id)


@app.get("/api/recommendations/{movie_id}")
def recommendations(movie_id: int):
    if movie_id < 0 or movie_id >= len(data):
        raise HTTPException(status_code=404, detail="Movie not found")

    # Resolve the selected title with the notebook's title-to-row index, then
    # run the same cosine similarity calculation used in the notebook.
    title = str(data.iloc[movie_id]["title"])
    model_row = indices.get(title, movie_id)
    # A title can occur more than once in the notebook Series. In that case
    # .get() returns a Series; keep the selected row so it matches the matrix.
    if isinstance(model_row, pd.Series):
        model_row = movie_id
    model_row = int(model_row)
    similarities = cosine_similarity(tfidf_matrix[model_row], tfidf_matrix).flatten()
    similar_rows = similarities.argsort()[::-1]
    return [movie_at(row) for row in similar_rows if row != model_row][:5]


@app.get("/api/posters/{movie_id}")
def get_poster(movie_id: int, background_tasks: BackgroundTasks):
    if movie_id < 0 or movie_id >= len(data):
        raise HTTPException(status_code=404, detail="Movie not found")
    cached = next(POSTER_CACHE.glob(f"{movie_id}.*"), None)
    if cached:
        return FileResponse(cached)
    with poster_lock:
        if movie_id in failed_posters:
            return Response(status_code=204)
        if movie_id not in pending_posters:
            pending_posters.add(movie_id)
            background_tasks.add_task(download_poster, movie_id)
    # The browser retries this URL while the background download runs.
    return Response(status_code=202)


def fetch_image(url):
    request = Request(url, headers={"User-Agent": "CineMatch/1.0 (movie recommendation project)"})
    with urlopen(request, timeout=8) as response:
        return response.read(), response.headers.get_content_type()


def download_poster(movie_id):
    with poster_slots:
        try:
            movie = movie_at(movie_id)
            poster = posters.get(movie["title"])
            image = None
            if poster:
                try:
                    image = fetch_image(POSTER_BASE + poster)
                except (URLError, TimeoutError, OSError):
                    pass

            # TMDB paths are missing for some catalogue entries. Try the
            # Wikipedia page thumbnail as a fallback for those movies.
            if not image:
                query = urlencode({
                    "action": "query", "format": "json", "prop": "pageimages",
                    "piprop": "thumbnail", "pithumbsize": 500, "titles": movie["title"],
                })
                try:
                    with urlopen(Request(f"https://en.wikipedia.org/w/api.php?{query}", headers={"User-Agent": "CineMatch/1.0 (movie recommendation project)"}), timeout=8) as response:
                        pages = json.loads(response.read()).get("query", {}).get("pages", {})
                    thumbnail = next((page.get("thumbnail", {}).get("source") for page in pages.values() if page.get("thumbnail", {}).get("source")), None)
                    if thumbnail:
                        image = fetch_image(thumbnail)
                except (URLError, TimeoutError, OSError, ValueError):
                    pass

            if image:
                content, media_type = image
                suffix = {"image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}.get(media_type, ".jpg")
                (POSTER_CACHE / f"{movie_id}{suffix}").write_bytes(content)
            else:
                with poster_lock:
                    failed_posters.add(movie_id)
        finally:
            with poster_lock:
                pending_posters.discard(movie_id)


app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")
