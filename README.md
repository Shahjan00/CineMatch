# CineMatch

CineMatch is a lightweight movie recommendation system built with Python, scikit-learn, and FastAPI. It uses a TF-IDF vectorizer over movie tags (title, genres, overview, tagline) and cosine similarity to recommend movies similar to a selected title. The project includes a web frontend, a FastAPI backend, and a notebook-based training pipeline.

## Features

- Content-based movie recommendations using TF-IDF + cosine similarity
- FastAPI backend with JSON endpoints for movies and recommendations
- Search and browse interface in the frontend
- Poster retrieval and local caching for movie thumbnails
- Precomputed model artifacts for quick inference
- Easy local setup with a single requirements file

## Tech Stack

- Python 3.x
- pandas
- scikit-learn
- FastAPI
- Uvicorn
- NumPy
- pyarrow
- HTML/CSS/JavaScript frontend

## Project Structure

```text
Movie-Recommendation-System/
├── main.py                         # FastAPI application and recommendation API
├── recomending-engine.py          # CLI recommender for simple local testing
├── requirements.txt               # Python dependencies
├── README.md                      # Project documentation
├── frontend/
│   ├── index.html                 # Web UI
│   ├── css/
│   └── js/
├── notebooks/
│   ├── movies.ipynb               # Training notebook
│   ├── data.pkl                   # Processed movie dataframe
│   ├── indices.pkl                # Title-to-index lookup
│   ├── tfidf.pkl                  # TF-IDF vectorizer
│   └── tfidf_metrix.pkl           # Sparse TF-IDF matrix
├── data/
│   ├── raw/
│   │   └── movies_metadata.csv    # Source metadata
│   └── poster_cache/              # Cached poster images (generated locally)
└── .gitignore
```

## How It Works

The recommendation pipeline follows this flow:

1. Load the movie metadata from the raw dataset.
2. Clean and normalize movie text fields such as genres, overview, and tagline.
3. Combine them into a single text column called `tags`.
4. Convert the tags into TF-IDF vectors using unigrams and bigrams.
5. Compute cosine similarity between each movie vector and every other movie.
6. For a given movie title, rank the most similar titles and return the top recommendations.

This is a classic content-based recommendation approach, and it works well when the user is looking for semantically similar titles based on textual metadata.

## Setup

### 1) Clone the repository

```bash
git clone https://github.com/<your-username>/Movie-Recommendation-System.git
cd Movie-Recommendation-System
```

### 2) Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

## Run the Web App

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/
```

The frontend uses the backend API to show movies, browse titles, and display recommendations.

## API Endpoints

### Get all movies

```bash
curl "http://127.0.0.1:8000/api/movies?limit=10"
```

### Get a single movie

```bash
curl "http://127.0.0.1:8000/api/movies/42"
```

### Get recommendations for a movie

```bash
curl "http://127.0.0.1:8000/api/recommendations/42"
```

This returns the top similar movies using the precomputed TF-IDF matrix and cosine similarity ranking.

## Run the CLI Recommender

If you want to try the recommendation logic directly from the terminal:

```bash
python recomending-engine.py
```

Example interaction:

```text
Enter a movie name: Toy Story
Movies similar to Toy Story:
1. Monsters, Inc.
2. Finding Nemo
3. The Incredibles
4. Toy Story 2
5. Cars
```

## Dataset and Model Details

The dataset contains movie metadata with nearly 45,000 entries.

### Current model statistics

```text
=======================================================
           CINEMATCH METRICS REPORT
=======================================================

[ DATASET ]
Movies processed       : 45,447
Dataset shape          : 45,447 × 7

[ TF-IDF ]
Matrix shape           : 45,447 × 50,000
TF-IDF features        : 50,000
Non-zero entries       : 1,715,627
Matrix density         : 0.0755%
Matrix sparsity        : 99.9245%

[ VOCABULARY ]
Vocabulary size        : 50,000

[ CONFIGURATION ]
n-gram range           : (1, 2)
Max features           : 50000

=======================================================
                    SUMMARY
=======================================================
Movies                 : 45,447
TF-IDF features        : 50,000
Non-zero entries       : 1,715,627
Sparsity               : 99.92%
=======================================================
```

### Performance interpretation

- The model uses a sparse TF-IDF matrix with 45,447 rows and 50,000 features.
- The matrix is highly sparse, with only 1,715,627 non-zero entries out of 2,272,350,000 possible entries.
- That leads to a density of only 0.0755% and a sparsity of 99.9245%.
- This is expected for text-based recommendation systems using bag-of-words-style features.
- The approach is efficient for recommendation lookup because the matrix is sparse and similarity is computed using optimized linear algebra.

## Recommendation Quality and Evaluation

This project is a strong baseline for content-based recommendation, but it is important to understand its limits:

- It recommends by text similarity alone, so it is strongest when metadata and descriptions are relevant.
- It does not use collaborative filtering or user rating history.
- Recommendation quality can be evaluated with metrics such as Precision@K, Recall@K, NDCG@K, and coverage, but those require labeled relevance information.

For a real production system, you might combine this with user behavior data, implicit feedback, or a hybrid recommender.

## Notes on Posters and Caching

Poster images are fetched from TMDB and fall back to Wikipedia thumbnails when needed. Fetched images are saved in `data/poster_cache/` and served locally on future requests, which reduces repeated network calls and improves perceived response time.

## Dependencies

```bash
fastapi
uvicorn[standard]
pandas
pyarrow
scikit-learn
```

## Future Improvements

- Add collaborative filtering for stronger personalization
- Include user ratings and implicit feedback
- Improve search ranking and result diversity
- Add a production database and model versioning
- Build a Docker setup for easier deployment
- Add unit tests for the recommender and API endpoints

## License

This project is intended for educational and personal use. Add your preferred license if you plan to share it publicly.

## Contributing

Contributions are welcome. If you improve the recommender, add evaluation metrics, or improve the frontend, open a pull request and share your changes.

## Author

Built as a movie recommendation system prototype using content-based filtering and modern web tooling.
