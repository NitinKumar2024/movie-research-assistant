import re
from io import BytesIO
from typing import Dict, List, Optional, Any, Tuple

import google.generativeai as genai
import requests
from PIL import Image
from bs4 import BeautifulSoup
from src.config import TMDB_API_KEY


class MovieAgent:
    """Agent for searching movie information, finding trailers, and synthesizing responses."""

    def __init__(self):
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')

    def process_user_query(self, query: str) -> Tuple[str, str]:
        """
        Process user query to determine if it's a movie search or a general question.

        Returns:
        Tuple of (query_type, refined_query) where query_type is either 'movie' or 'general'
        """
        # Ask Gemini to classify the query
        classification_prompt = f"""
        Determine if the following query is asking about a specific movie or is a general question.

        Query: "{query}"

        If it's about a specific movie, respond with:
        movie: [extracted movie title]

        If it's a general question or request, respond with:
        general: [original query]

        Be very concise and only return one of the above formats.
        """

        try:
            response = self.gemini_model.generate_content(classification_prompt)
            result = response.text.strip().lower()

            if result.startswith("movie:"):
                return "movie", result.replace("movie:", "").strip()
            else:
                return "general", query

        except Exception as e:
            print(f"Error classifying query: {e}")
            # Default to treating it as a movie search if classification fails
            return "movie", query

    def search_movie(self, query: str) -> Optional[Dict[str, Any]]:
        """Search for a movie using TMDB API."""
        url = f"{self.tmdb_base_url}/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": query,
            "language": "en-US",
            "include_adult": "false"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data["results"] and len(data["results"]) > 0:
                return data["results"][0]
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error searching for movie: {e}")
            return None

    def get_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a movie from TMDB."""
        url = f"{self.tmdb_base_url}/movie/{movie_id}"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "append_to_response": "credits,reviews,similar,videos"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting movie details: {e}")
            return None

    def find_trailer(self, movie_title: str, year: Optional[str] = None, movie_data: Optional[Dict] = None) -> Optional[
        Dict[str, str]]:
        # First try TMDB videos if available
        if movie_data and "videos" in movie_data and movie_data["videos"]["results"]:
            for video in movie_data["videos"]["results"]:
                if video["site"] == "YouTube" and video["type"] == "Trailer":
                    return {
                        "title": f"{movie_title} Official Trailer",
                        "url": f"https://www.youtube.com/watch?v={video['key']}",
                        "video_id": video['key']
                    }

        # Web scraping approach as fallback
        search_query = f"{movie_title} official trailer"
        if year:
            search_query += f" {year}"

        try:
            # Use a search engine to find the trailer
            search_url = f"https://www.google.com/search?q={search_query}+site:youtube.com"
            response = requests.get(search_url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract YouTube links
            youtube_links = []
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if 'youtube.com/watch' in href:
                    match = re.search(r'youtube\.com/watch\?v=([^&]+)', href)
                    if match:
                        video_id = match.group(1)
                        youtube_links.append({
                            "title": f"{movie_title} Trailer",
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "video_id": video_id
                        })

            if youtube_links:
                return youtube_links[0]

            return None
        except Exception as e:
            print(f"Error finding trailer: {e}")
            return None

    def get_poster_image(self, poster_path: str) -> Optional[Image.Image]:
        """Fetch movie poster image from TMDB."""
        if not poster_path:
            return None

        try:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            response = requests.get(poster_url)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            print(f"Error fetching poster: {e}")
            return None

    def generate_movie_response(self, movie_data: Dict[str, Any], trailer_info: Optional[Dict[str, str]],
                                streaming: bool = False, callback=None) -> str:
        """Generate a comprehensive response about a movie using Gemini API with streaming support."""
        # Create structured context for Gemini
        context = {
            "title": movie_data.get("title", "Unknown"),
            "release_date": movie_data.get("release_date", "Unknown"),
            "overview": movie_data.get("overview", "No overview available"),
            "vote_average": movie_data.get("vote_average", "N/A"),
            "genres": [genre["name"] for genre in movie_data.get("genres", [])],
            "runtime": movie_data.get("runtime", "Unknown"),
            "budget": movie_data.get("budget", 0),
            "revenue": movie_data.get("revenue", 0),
            "director": self._get_director(movie_data),
            "cast": self._get_cast(movie_data),
            "trailer": trailer_info["url"] if trailer_info else "Trailer not available"
        }

        prompt = f"""
        Based on the following movie information, create a comprehensive and engaging summary:

        Title: {context['title']}
        Release Date: {context['release_date']}
        Runtime: {context['runtime']} minutes
        Genres: {', '.join(context['genres'])}
        Rating: {context['vote_average']}/10
        Director: {context['director']}
        Main Cast: {', '.join(context['cast'][:5])}

        Overview: {context['overview']}

        Budget: ${context['budget']:,}
        Revenue: ${context['revenue']:,}

        Trailer: {context['trailer']}

        Provide insights about the movie's reception, significance, and interesting facts if applicable.
        Format the response in a clear, professional way for someone interested in learning about this movie.
        DO NOT use markdown formatting. Use plain text formatting with clear section divisions.
        """

        try:
            if streaming and callback:
                # For streaming response
                response_text = ""
                for chunk in self.gemini_model.generate_content(prompt, stream=True):
                    piece = chunk.text
                    response_text += piece
                    callback(piece)  # Send chunk to callback
                return response_text
            else:
                # For non-streaming response
                response = self.gemini_model.generate_content(prompt)
                return response.text
        except Exception as e:
            print(f"Error generating response with Gemini: {e}")
            # Fall back to formatted response if Gemini fails
            fallback = self._create_fallback_response(context)
            if callback:
                callback(fallback)
            return fallback

    def generate_general_response(self, query: str, streaming: bool = False, callback=None) -> str:
        """Generate a response for general queries using Gemini API."""
        prompt = f"""
        The user has asked: "{query}"

        Please provide a helpful, informative response. If this is a question about movies in general
        (not about a specific film), provide relevant information about the topic.

        If you're not sure what the user is asking for, try to interpret their query in the context
        of movies, cinema, or entertainment.

        Format your response in plain text with clear section divisions. DO NOT use markdown formatting.
        """

        try:
            if streaming and callback:
                # For streaming response
                response_text = ""
                for chunk in self.gemini_model.generate_content(prompt, stream=True):
                    piece = chunk.text
                    response_text += piece
                    callback(piece)  # Send chunk to callback
                return response_text
            else:
                # For non-streaming response
                response = self.gemini_model.generate_content(prompt)
                return response.text
        except Exception as e:
            print(f"Error generating general response with Gemini: {e}")
            fallback = f"I'm sorry, I couldn't process your query: '{query}'. Please try asking in a different way."
            if callback:
                callback(fallback)
            return fallback

    def _get_director(self, movie_data: Dict[str, Any]) -> str:
        """Extract director name from movie data."""
        crew = movie_data.get("credits", {}).get("crew", [])
        directors = [member["name"] for member in crew if member["job"] == "Director"]
        return directors[0] if directors else "Unknown"

    def _get_cast(self, movie_data: Dict[str, Any]) -> List[str]:
        """Extract cast names from movie data."""
        cast = movie_data.get("credits", {}).get("cast", [])
        return [member["name"] for member in cast]

    def _create_fallback_response(self, context: Dict[str, Any]) -> str:
        """Create a formatted response if Gemini API fails."""
        return f"""
        {context['title']} ({context['release_date'][:4]})

        Rating: {context['vote_average']}/10  
        Runtime: {context['runtime']} minutes  
        Genres: {', '.join(context['genres'])}

        Overview:
        {context['overview']}

        Cast & Crew:
        Director: {context['director']}  
        Starring: {', '.join(context['cast'][:5])}

        Watch Trailer:
        {context['trailer']}

        Budget: ${context['budget']:,}  
        Box Office: ${context['revenue']:,}
        """