import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).parent
NOTEBOOK = ROOT / "notebooks"


def load_recommender():
    data = pd.read_pickle(NOTEBOOK / "data.pkl").reset_index(drop=True)
    with (NOTEBOOK / "indices.pkl").open("rb") as file:
        indices = pickle.load(file)
    with (NOTEBOOK / "tfidf_metrix.pkl").open("rb") as file:
        tfidf_matrix = pickle.load(file)

    # Keep the first row for repeated titles, matching the notebook's index.
    title_to_row = {}
    for title, row in indices.items():
        title_to_row.setdefault(str(title).strip().casefold(), int(row))

    return data, title_to_row, tfidf_matrix


def recommend(movie_title, data, title_to_row, tfidf_matrix, count=5):
    row = title_to_row.get(movie_title.strip().casefold())
    if row is None:
        return None

    similarity = cosine_similarity(tfidf_matrix[row], tfidf_matrix).ravel()
    ranked_rows = np.argsort(similarity)[::-1]

    suggestions = []
    seen_titles = {str(data.iloc[row]["title"]).casefold()}
    for candidate_row in ranked_rows:
        title = str(data.iloc[candidate_row]["title"])
        normalized_title = title.casefold()
        if normalized_title in seen_titles:
            continue
        suggestions.append(title)
        seen_titles.add(normalized_title)
        if len(suggestions) == count:
            break

    return suggestions


def main():
    data, title_to_row, tfidf_matrix = load_recommender()
    print("Movie Recommendation Engine")
    print("Type 'q' to quit.\n")

    while True:
        movie_title = input("Enter a movie name: ").strip()
        if movie_title.casefold() in {"q", "quit", "exit"}:
            break
        if not movie_title:
            continue

        suggestions = recommend(movie_title, data, title_to_row, tfidf_matrix)
        if suggestions is None:
            print(f"Movie not found: {movie_title}\n")
            continue

        print(f"Movies similar to {movie_title}:")
        for number, suggestion in enumerate(suggestions, start=1):
            print(f"{number}. {suggestion}")
        print()


if __name__ == "__main__":
    main()
