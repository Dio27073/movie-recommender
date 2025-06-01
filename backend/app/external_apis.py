# backend/app/external_apis.py
import asyncio
import time
import requests
import os
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# API Base URLs
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
OMDB_BASE_URL = "http://www.omdbapi.com"

async def fetch_imdb_data(title: str, year: int, retry_count: int = 0) -> dict:
    """
    Fetch IMDb data by first searching TMDb to get a reliable IMDb ID, then using OMDb.
    Falls back to a direct OMDb title search if needed.
    
    Args:
        title (str): Movie title.
        year (int): Release year.
        retry_count (int): Current retry count for exponential backoff.
    
    Returns:
        dict: Processed IMDb data including id, rating, votes, etc., or None if not found.
    """
    max_retries = 3
    base_delay = 1.0

    # A helper to perform HTTP requests with exponential backoff.
    async def fetch_with_backoff(url: str, params: dict, current_retry: int) -> dict:
        if current_retry > 0:
            await asyncio.sleep(base_delay * (2 ** (current_retry - 1)))
        response = requests.get(url, params=params)
        return response.json()

    # --- Step 1: Use TMDb search to get the IMDb ID ---
    tmdb_search_url = f"{TMDB_BASE_URL}/search/movie"
    tmdb_search_params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "year": year,
        "language": "en-US"
    }
    tmdb_search_result = await fetch_with_backoff(tmdb_search_url, tmdb_search_params, retry_count)
    
    imdb_id = None
    if tmdb_search_result.get("results"):
        # Prefer a result whose release_date matches exactly the given year.
        best_match = None
        for result in tmdb_search_result["results"]:
            release_date = result.get("release_date", "")
            if release_date:
                try:
                    result_year = int(release_date[:4])
                    if result_year == year:
                        best_match = result
                        break
                except Exception:
                    continue
        if not best_match:
            best_match = tmdb_search_result["results"][0]
        
        # Fetch movie details from TMDb to retrieve the IMDb ID.
        tmdb_movie_id = best_match["id"]
        tmdb_details_url = f"{TMDB_BASE_URL}/movie/{tmdb_movie_id}"
        tmdb_details_params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US"
        }
        tmdb_details = await fetch_with_backoff(tmdb_details_url, tmdb_details_params, retry_count)
        imdb_id = tmdb_details.get("imdb_id")
    
    # --- Step 2: Use the IMDb ID to fetch data from OMDb if available ---
    if imdb_id:
        omdb_params = {
            "apikey": OMDB_API_KEY,
            "i": imdb_id,
            "type": "movie"
        }
        omdb_data = await fetch_with_backoff(OMDB_BASE_URL, omdb_params, retry_count)
        if omdb_data.get("Response") == "True":
            return process_imdb_data(omdb_data)
    
    # --- Fallback: Direct title search via OMDb ---
    search_params = {
        "apikey": OMDB_API_KEY,
        "t": title,
        "y": year,
        "type": "movie"
    }
    omdb_data = await fetch_with_backoff(OMDB_BASE_URL, search_params, retry_count)
    if omdb_data.get("Response") == "True":
        return process_imdb_data(omdb_data)
    
    # Optionally, try a looser search using 's' if needed.
    search_params = {
        "apikey": OMDB_API_KEY,
        "s": title,
        "y": year,
        "type": "movie"
    }
    search_result = await fetch_with_backoff(OMDB_BASE_URL, search_params, retry_count)
    if search_result.get("Response") == "True" and search_result.get("Search"):
        best_movie = search_result["Search"][0]
        detail_params = {
            "apikey": OMDB_API_KEY,
            "i": best_movie["imdbID"],
            "type": "movie"
        }
        detail_result = await fetch_with_backoff(OMDB_BASE_URL, detail_params, retry_count)
        if detail_result.get("Response") == "True":
            return process_imdb_data(detail_result)
    
    # Retry if we haven't hit the maximum attempts.
    if retry_count < max_retries:
        return await fetch_imdb_data(title, year, retry_count + 1)
    
    return None

def process_imdb_data(data: dict) -> dict:
    """Process and validate IMDB API response data"""
    try:
        imdb_rating = data.get("imdbRating", "N/A")
        imdb_votes = data.get("imdbVotes", "N/A")
        
        rating = float(imdb_rating) if imdb_rating != "N/A" else None
        votes = int(imdb_votes.replace(",", "")) if imdb_votes != "N/A" else None
        
        return {
            "imdb_id": data.get("imdbID"),
            "imdb_rating": rating,
            "imdb_votes": votes,
            "title": data.get("Title"),
            "year": data.get("Year"),
            "match_confidence": "exact" if data.get("Response") == "True" else "partial"
        }
    except (ValueError, AttributeError) as e:
        print(f"Error processing IMDB data: {str(e)}")
        return None

async def fetch_movie_trailer(tmdb_id: int) -> Optional[str]:
    """Fetch movie trailer URL from TMDB"""
    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/videos",
            params={
                "api_key": TMDB_API_KEY,
                "language": "en-US"
            }
        )
        if response.status_code == 200:
            videos = response.json().get("results", [])
            # Look for official trailers
            trailer = next(
                (
                    video for video in videos 
                    if video["type"].lower() == "trailer" 
                    and video["site"].lower() == "youtube"
                    and video["official"]
                ),
                None
            )
            if trailer:
                return f"https://www.youtube.com/watch?v={trailer['key']}"
    except Exception as e:
        print(f"Error fetching trailer: {str(e)}")
    return None

async def fetch_movie_cast_crew(tmdb_id: int) -> dict:
    """Fetch cast and crew data for a movie using TMDB API."""
    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits",
            params={"api_key": TMDB_API_KEY, "language": "en-US"}
        )
        if response.status_code == 200:
            credits = response.json()
            cast = [actor["name"] for actor in credits.get("cast", [])[:5]]  # Top 5 cast members
            crew = [member["name"] for member in credits.get("crew", []) if member["job"] == "Director"]  # Directors
            return {"cast": cast, "crew": crew}
    except Exception as e:
        print(f"Error fetching cast/crew for movie {tmdb_id}: {str(e)}")
    return {"cast": [], "crew": []}

async def fetch_streaming_platforms(tmdb_id: int, region: str = "US") -> List[str]:
    """Fetch accurate streaming platform data from TMDB."""
    try:
        # Add rate limiting
        time.sleep(0.25)  # 250ms delay between requests
        
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/watch/providers",
            params={"api_key": TMDB_API_KEY}
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", {})
            region_data = results.get(region, {})
            
            # Get flatrate (subscription) streaming services
            streaming_platforms = []
            if "flatrate" in region_data:
                for provider in region_data["flatrate"]:
                    provider_name = provider.get("provider_name")
                    # Map TMDB provider names to your platform names
                    platform_mapping = {
                        "Netflix": "Netflix",
                        "Amazon Prime Video": "Prime Video",
                        "Disney Plus": "Disney+",
                        "Hulu": "Hulu",
                        "HBO Max": "HBO Max",
                        "Max": "HBO Max",  # Add this line
                        "Apple TV Plus": "Apple TV+",
                        "Peacock": "Peacock"
                    }
                    if provider_name in platform_mapping:
                        streaming_platforms.append(platform_mapping[provider_name])
            
            return list(set(streaming_platforms))  # Remove duplicates
            
    except Exception as e:
        print(f"Error fetching streaming platforms for movie {tmdb_id}: {str(e)}")
        return []

def get_trending_movies_from_tmdb(time_window: str, page: int) -> Dict:
    """Fetch trending movies from TMDB API"""
    try:
        tmdb_response = requests.get(
            f"{TMDB_BASE_URL}/trending/movie/{time_window}",
            params={
                "api_key": TMDB_API_KEY,
                "page": page
            }
        )
        tmdb_response.raise_for_status()
        return tmdb_response.json()
    except Exception as e:
        print(f"Error fetching trending movies: {str(e)}")
        return {"results": [], "total_pages": 1}

def get_popular_movies_from_tmdb(page: int) -> Dict:
    """Fetch popular movies from TMDB API"""
    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/popular",
            params={
                "api_key": TMDB_API_KEY,
                "language": "en-US",
                "page": page
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return {"results": []}
    except Exception as e:
        print(f"Error fetching popular movies from page {page}: {str(e)}")
        return {"results": []}

def get_movie_details_from_tmdb(tmdb_id: int) -> Optional[Dict]:
    """Fetch detailed movie information from TMDB"""
    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}",
            params={"api_key": TMDB_API_KEY, "language": "en-US"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching movie details for {tmdb_id}: {str(e)}")
        return None