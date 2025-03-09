# Movie Research Assistant

A powerful desktop application that helps users find information about movies, watch trailers, and get answers to movie-related questions using AI.

![Movie Research Assistant](https://github.com/nitinkumar2024/movie-research-assistant/static/img/screenshots/app_screenshot.png)

## Features

- **Movie Information Lookup**: Search for any movie and get detailed information including plot, cast, director, release date, and ratings.
- **Trailer Search**: Automatically finds and provides links to movie trailers.
- **AI-Powered Responses**: Uses Google's Gemini AI to provide intelligent answers to movie-related questions.
- **User-Friendly Interface**: Clean and intuitive GUI built with Tkinter.
- **Real-Time Processing**: Asynchronous processing for a smooth user experience.

## Installation

### Prerequisites

- Python 3.8 or higher
- Pip package manager

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/nitinkumar2024/movie-research-assistant.git
   cd movie-research-assistant
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure API keys:
   - The application uses TMDB API and Google Gemini API
   - You need to configured API keys in `src/config.py`
   - You can replace them with your own keys

## Usage

1. Run the application:
   ```
   python main.py
   ```

2. The application window will open with a search bar at the top.

3. You can:
   - Search for a specific movie (e.g., "Tell me about Inception")
   - Ask general movie-related questions (e.g., "Who directed The Godfather?")
   - Get recommendations (e.g., "Recommend me some sci-fi movies")

4. The results will be displayed in the main window, including:
   - Movie details (for specific movie searches)
   - Movie poster (when available)
   - Trailer link (when available)
   - AI-generated responses to your questions

## Project Structure

- `main.py`: Entry point of the application
- `src/`
  - `movie_agent.py`: Core functionality for movie searches and AI responses
  - `movie_agent_gui.py`: GUI implementation using Tkinter
  - `config.py`: Configuration file with API keys
- `requirements.txt`: List of Python dependencies

## Technologies Used

- **Python**: Core programming language
- **Tkinter**: GUI framework
- **Google Gemini AI**: For natural language processing and generating responses
- **TMDB API**: For fetching movie information
- **BeautifulSoup**: For web scraping additional movie data
- **Pillow**: For image processing


## Acknowledgments

- [The Movie Database (TMDB)](https://www.themoviedb.org/) for providing the movie data API
- [Google Gemini](https://ai.google.dev/) for the AI capabilities

---

