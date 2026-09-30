import streamlit as st
import pickle
import requests
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CineMatch | Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

TMDB_API_KEY = "70afddcfd2a0ae3eb5ad8cf6e847132e"
PLACEHOLDER_POSTER = "https://placehold.co/500x750?text=No+Poster"

# --- CUSTOM CSS ---
st.markdown(
    """
    <style>
    /* Main container background */
    .stApp {
        background: radial-gradient(circle at 50% -20%, #1a1e29 0%, #0d1117 70%);
        color: #E2E8F0;
    }
    
    /* Header styling */
    .hero-container {
        text-align: center;
        padding: 1.5rem 0 1.2rem 0;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF4B4B 0%, #FF8A00 50%, #E50914 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
        margin-bottom: 0.3rem;
    }
    .hero-sub {
        font-size: 1.1rem;
        color: #94A3B8;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    /* Badges */
    .badge-row {
        display: flex;
        gap: 6px;
        align-items: center;
        margin: 6px 0;
        flex-wrap: wrap;
    }
    .badge-star {
        background: rgba(251, 191, 36, 0.12);
        color: #FBBF24;
        border: 1px solid rgba(251, 191, 36, 0.3);
        font-size: 0.78rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 6px;
    }
    .badge-year {
        background: rgba(148, 163, 184, 0.12);
        color: #CBD5E1;
        border: 1px solid rgba(148, 163, 184, 0.25);
        font-size: 0.78rem;
        font-weight: 600;
        padding: 2px 7px;
        border-radius: 6px;
    }
    .badge-genre {
        background: rgba(229, 9, 20, 0.15);
        color: #FFA5A5;
        border: 1px solid rgba(229, 9, 20, 0.35);
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
    }

    /* Card styling */
    .card-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Poster rounded corners & hover lift */
    [data-testid="stImage"] img {
        border-radius: 12px;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.45);
    }
    [data-testid="stImage"] img:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 22px rgba(229, 9, 20, 0.3);
    }

    /* Primary button */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #E50914 0%, #B81D24 100%);
        color: #FFFFFF;
        font-weight: 700;
        font-size: 1.05rem;
        border: none;
        border-radius: 8px;
        padding: 0.65rem 1.6rem;
        box-shadow: 0 4px 18px rgba(229, 9, 20, 0.4);
        transition: all 0.2s ease;
        height: 48px;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #FF1E27 0%, #E50914 100%);
        box-shadow: 0 6px 25px rgba(229, 9, 20, 0.6);
        transform: translateY(-1px);
    }

    /* Selected spotlight card */
    .spotlight-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 75, 75, 0.3);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 25px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #64748B;
        font-size: 0.85rem;
        padding: 2.5rem 0 1rem 0;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        margin-top: 3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- DATA LOADING (CACHED) ---
@st.cache_resource
def load_data():
    with open("movies.pkl", "rb") as file:
        movies_data = pickle.load(file)
    with open("similarity.pkl", "rb") as file:
        similarity_data = pickle.load(file)
    return movies_data, similarity_data


movies, similarity = load_data()


# --- TMDB DETAILS FETCHER ---
@st.cache_data(show_spinner=False)
def _get_tmdb_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    for _ in range(4):
        try:
            response = requests.get(
                url,
                params={"api_key": TMDB_API_KEY, "language": "en-US"},
                headers=headers,
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                poster_path = data.get("poster_path")
                poster = (
                    f"https://image.tmdb.org/t/p/w500{poster_path}"
                    if poster_path
                    else PLACEHOLDER_POSTER
                )
                vote_avg = data.get("vote_average", 0)
                rating = round(vote_avg, 1) if vote_avg else "N/A"
                release_date = data.get("release_date", "")
                year = release_date.split("-")[0] if release_date else "N/A"
                genres = [g["name"] for g in data.get("genres", [])[:2]]
                overview = data.get("overview") or "No overview available."
                return {
                    "poster": poster,
                    "rating": rating,
                    "year": year,
                    "genres": genres,
                    "overview": overview,
                }
        except requests.RequestException:
            time.sleep(0.3)

    raise RuntimeError("TMDB request failed")


def fetch_movie_details(movie_id):
    if not TMDB_API_KEY or TMDB_API_KEY == "YOUR_TMDB_API_KEY":
        return {
            "poster": PLACEHOLDER_POSTER,
            "rating": "N/A",
            "year": "N/A",
            "genres": [],
            "overview": "Please configure your TMDB API key to see details.",
        }

    try:
        return _get_tmdb_details(movie_id)
    except Exception:
        return {
            "poster": PLACEHOLDER_POSTER,
            "rating": "N/A",
            "year": "N/A",
            "genres": [],
            "overview": "Overview currently unavailable.",
        }


# --- RECOMMENDATION LOGIC ---
def recommend(movie_title, top_n=5):
    matches = movies.index[movies["title"] == movie_title]
    if len(matches) == 0:
        return []

    movie_index = matches[0]
    distances = similarity[movie_index]

    movie_list = sorted(
        enumerate(distances),
        reverse=True,
        key=lambda item: item[1],
    )[1 : top_n + 1]

    recommendations = []
    for index, score in movie_list:
        row = movies.iloc[index]
        details = fetch_movie_details(row["id"])
        recommendations.append(
            {
                "id": row["id"],
                "title": row["title"],
                "similarity": round(score * 100, 1),
                **details,
            }
        )

    return recommendations


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎬 CineMatch Hub")
    st.caption("AI-powered content similarity recommendation engine.")
    st.markdown("---")

    num_recommendations = st.slider(
        "Number of Recommendations",
        min_value=3,
        max_value=10,
        value=5,
        step=1,
        help="Choose how many similar movies you want to discover.",
    )

    st.markdown("---")
    st.markdown("#### 💡 How it works")
    st.caption(
        "• Features extracted from movie genres, keywords, cast, and crew\n"
        "• High-dimensional vectorization & Cosine Similarity ranking\n"
        "• Real-time TMDB metadata, posters, and ratings"
    )

    st.markdown("---")
    if st.button("🧹 Clear Poster Cache"):
        st.cache_data.clear()
        st.success("Cache cleared!")


# --- HERO HEADER ---
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">🎬 CineMatch</div>
        <div class="hero-sub">Discover films tailored to your cinematic taste</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --- SEARCH & ACTION ---
col_search, col_btn = st.columns([3.5, 1], vertical_alignment="bottom")

with col_search:
    selected_movie_name = st.selectbox(
        "Select or search for a movie you enjoyed:",
        movies["title"].dropna().values,
        index=0,
        help="Type or scroll to select any movie from the 5,000 TMDB dataset",
    )

with col_btn:
    show_recommendations = st.button("🚀 Recommend", use_container_width=True)


# --- PERSISTENT STATE ---
if "last_recommended" not in st.session_state:
    st.session_state.last_recommended = None

if show_recommendations:
    st.session_state.last_recommended = selected_movie_name
    st.session_state.num_recs = num_recommendations


# --- DISPLAY RECOMMENDATIONS ---
if st.session_state.last_recommended:
    current_movie = st.session_state.last_recommended
    n_recs = st.session_state.get("num_recs", num_recommendations)

    # Selected movie spotlight
    selected_row = movies[movies["title"] == current_movie]
    if not selected_row.empty:
        selected_id = selected_row.iloc[0]["id"]
        selected_details = fetch_movie_details(selected_id)

        with st.container():
            st.markdown(
                f"""
                <div class="spotlight-box">
                    <span style="color: #FF4B4B; font-weight: 700; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px;">Selected Film</span>
                    <h3 style="margin: 4px 0 8px 0; color: #FFFFFF;">{current_movie} <span style="color: #94A3B8; font-weight: 400; font-size: 1.1rem;">({selected_details.get('year', 'N/A')})</span></h3>
                    <div class="badge-row">
                        <span class="badge-star">⭐ {selected_details.get('rating', 'N/A')}</span>
                        {''.join([f'<span class="badge-genre">{g}</span>' for g in selected_details.get('genres', [])])}
                    </div>
                    <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 8px; line-height: 1.4;">{selected_details.get('overview', '')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### 🍿 Recommended For You")

    with st.spinner("Finding matches..."):
        recs = recommend(current_movie, top_n=n_recs)

    if not recs:
        st.warning("No recommendations found for this title.")
    else:
        # Display in rows of 5 columns maximum
        cards_per_row = min(len(recs), 5)
        for row_start in range(0, len(recs), cards_per_row):
            batch = recs[row_start : row_start + cards_per_row]
            cols = st.columns(len(batch))

            for col, item in zip(cols, batch):
                with col:
                    st.image(item["poster"], use_container_width=True)
                    st.markdown(
                        f"<div class='card-title' title='{item['title']}'>{item['title']}</div>",
                        unsafe_allow_html=True,
                    )

                    # Badges for Rating, Year, and Genres
                    genre_badges = "".join(
                        [
                            f"<span class='badge-genre'>{g}</span>"
                            for g in item.get("genres", [])
                        ]
                    )
                    st.markdown(
                        f"""
                        <div class="badge-row">
                            <span class="badge-star">⭐ {item['rating']}</span>
                            <span class="badge-year">{item['year']}</span>
                            {genre_badges}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Expandable synopsis
                    with st.expander("📖 Synopsis"):
                        st.caption(item["overview"])
                        st.caption(f"Match Score: **{item['similarity']}%**")

# --- FOOTER ---
st.markdown(
    """
    <div class="footer">
        Powered by <b>Machine Learning (Cosine Similarity)</b> & <b>The Movie Database (TMDB) API</b><br>
        Crafted for smooth cinema discovery
    </div>
    """,
    unsafe_allow_html=True,
)