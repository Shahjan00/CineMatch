const app = document.querySelector('#app');
const searchInput = document.querySelector('#search');

function escapeHtml(value) {
  return String(value || '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
}

function retryPoster(image) {
  const retries = Number(image.dataset.retries || 0);
  if (retries >= 8) {
    image.style.display = 'none';
    return;
  }
  image.dataset.retries = retries + 1;
  setTimeout(() => {
    image.src = `/api/posters/${image.dataset.movieId}?retry=${retries + 1}`;
  }, 1500);
}

function movieCard(movie) {
  return `<article class="movie-card" onclick="showMovie('${encodeURIComponent(movie.id)}')">
    <div class="movie-poster"><img loading="lazy" data-movie-id="${encodeURIComponent(movie.id)}" src="/api/posters/${encodeURIComponent(movie.id)}" alt="${escapeHtml(movie.title)} poster" onerror="retryPoster(this)"><span class="movie-rating">★ ${Number(movie.rating || 0).toFixed(1)}</span></div>
    <div class="movie-meta"><h3>${escapeHtml(movie.title)}</h3><p>${escapeHtml(movie.year || 'Year unavailable')} · ${escapeHtml((movie.genres || []).slice(0, 2).join(', '))}</p></div>
  </article>`;
}

async function showMovies(query = '') {
  const response = await fetch(`/api/movies?search=${encodeURIComponent(query)}&limit=30`);
  const movies = await response.json();
  app.innerHTML = `<section class="content-section" id="popular"><div class="section-heading"><div><p class="eyebrow">${query ? 'SEARCH RESULTS' : 'A GOOD PLACE TO START'}</p><h2>${query ? `Results for “${escapeHtml(query)}”` : 'Popular right now'}</h2></div></div><div class="movie-grid">${movies.map(movieCard).join('') || '<p>No movies found.</p>'}</div></section>`;
}

async function showMovie(id) {
  const [movieResponse, recResponse] = await Promise.all([
    fetch(`/api/movies/${id}`),
    fetch(`/api/recommendations/${id}`)
  ]);
  const movie = await movieResponse.json();
  const recommendations = await recResponse.json();
  app.innerHTML = `<section class="detail-view">
    <button class="back-button" onclick="showMovies(searchInput.value)"><span>←</span> Back to discover</button>
    <div class="detail-main"><img class="detail-poster" data-movie-id="${encodeURIComponent(movie.id)}" src="/api/posters/${encodeURIComponent(movie.id)}" alt="${escapeHtml(movie.title)} poster" onerror="retryPoster(this)">
      <div class="detail-copy"><p class="eyebrow">MOVIE DETAILS</p><h1>${escapeHtml(movie.title)}</h1>
        <div class="detail-facts"><span>${escapeHtml(movie.year || 'Year unavailable')}</span><span>★ ${Number(movie.rating || 0).toFixed(1)} / 10</span></div>
        <div class="genre-list">${(movie.genres || []).map(genre => `<span>${escapeHtml(genre)}</span>`).join('')}</div>
        <h3>${escapeHtml(movie.tagline || 'About the film')}</h3><p class="overview">${escapeHtml(movie.overview || 'No synopsis available.')}</p>
      </div>
    </div>
    <section class="detail-recommendations"><div class="section-heading"><div><p class="eyebrow">BASED ON GENRE AND STORY</p><h2>You might also like</h2></div></div><div class="movie-grid">${recommendations.map(movieCard).join('')}</div></section>
  </section>`;
  window.scrollTo(0, 0);
}

document.querySelector('#search-form').addEventListener('submit', event => {
  event.preventDefault();
  showMovies(searchInput.value.trim());
});

showMovies();
