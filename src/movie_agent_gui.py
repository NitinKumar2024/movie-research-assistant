import threading
import tkinter as tk
import webbrowser
from tkinter import ttk, scrolledtext

from PIL import Image, ImageTk

from src.movie_agent import MovieAgent


class MovieAgentGUI:
    """GUI interface for the Movie Agent application."""

    def __init__(self, root):
        self.root = root
        self.root.title("Movie Information Assistant")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        self.root.resizable(True, True)

        self.agent = MovieAgent()
        self.trailer_info = None
        self.current_movie = None
        self.last_query_type = None
        self.last_query = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Style configuration
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 11))
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))

        # Search section
        search_frame = ttk.Frame(main_frame, padding="10")
        search_frame.pack(fill=tk.X, pady=10)

        ttk.Label(search_frame, text="Ask about a movie or general question:", style="Header.TLabel").pack(side=tk.LEFT,
                                                                                                           padx=5)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40, font=("Segoe UI", 12))
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", lambda event: self.process_query())

        self.search_button = ttk.Button(search_frame, text="Search", command=self.process_query)
        self.search_button.pack(side=tk.LEFT, padx=5)

        # Split frame for poster and info
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Left frame for poster
        self.poster_frame = ttk.Frame(content_frame, width=200, padding="10")
        self.poster_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Default poster placeholder
        self.poster_label = ttk.Label(self.poster_frame, text="No poster available")
        self.poster_label.pack(pady=10)

        # Movie title label
        self.title_label = ttk.Label(self.poster_frame, text="", style="Title.TLabel", wraplength=180)
        self.title_label.pack(pady=5)

        # Trailer button
        self.trailer_button = ttk.Button(self.poster_frame, text="Watch Trailer", command=self.open_trailer,
                                         state=tk.DISABLED)
        self.trailer_button.pack(pady=10)

        # Right frame for movie information
        info_frame = ttk.Frame(content_frame, padding="10")
        info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Information text area
        self.info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, font=("Segoe UI", 11), padx=10, pady=10)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.info_text.config(state=tk.DISABLED)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def process_query(self):
        """Process user query - either search for a movie or answer a general question."""
        query = self.search_var.get().strip()
        if not query:
            self.show_status("Please enter a question or movie title")
            return

        self.show_status("Processing query...")
        self.search_button.config(state=tk.DISABLED)
        self.clear_info()

        # Use threading to keep UI responsive
        threading.Thread(target=self._handle_query, args=(query,), daemon=True).start()

    def _handle_query(self, query):
        """Handle query processing in background thread."""
        # Determine query type
        query_type, refined_query = self.agent.process_user_query(query)
        self.last_query_type = query_type
        self.last_query = query

        if query_type == "movie":
            self._search_movie(refined_query)
        else:
            self._answer_general_query(query)

    def _search_movie(self, query):
        """Search for movie information."""
        self.show_status(f"Searching for movie: {query}")

        # Search for movie
        movie = self.agent.search_movie(query)
        if not movie:
            self.show_status(f"Movie not found: {query}")
            self._handle_movie_not_found(query)
            return

        self.show_status(f"Found: {movie['title']} - Getting details...")

        # Get detailed information
        movie_details = self.agent.get_movie_details(movie["id"])
        if not movie_details:
            self.show_status(f"Error fetching details for {movie['title']}")
            self.root.after(0, lambda: self.search_button.config(state=tk.NORMAL))
            return

        self.current_movie = movie_details

        # Find trailer
        release_year = movie["release_date"][:4] if movie.get("release_date") else None
        trailer = self.agent.find_trailer(movie["title"], release_year, movie_details)
        self.trailer_info = trailer

        # Load poster
        poster_image = None
        if movie_details.get("poster_path"):
            poster_image = self.agent.get_poster_image(movie_details["poster_path"])

        # Update UI in main thread
        self.root.after(0, lambda: self._update_ui_for_movie(movie_details, trailer, poster_image))

        # Generate response with streaming
        self.show_status(f"Generating information about {movie_details['title']}...")
        self.agent.generate_movie_response(
            movie_details,
            trailer,
            streaming=True,
            callback=lambda text: self.root.after(0, lambda: self._append_text(text))
        )

    def _handle_movie_not_found(self, query):
        """Handle when a movie search returns no results."""
        # Treat it as a general query instead
        self.show_status(f"Treating '{query}' as a general question...")
        self._answer_general_query(query)

    def _answer_general_query(self, query):
        """Handle general questions with Gemini."""
        self.show_status(f"Answering: {query}")

        # Update UI for general query (hide movie-specific elements)
        self.root.after(0, lambda: self._update_ui_for_general_query(query))

        # Generate response with streaming
        self.agent.generate_general_response(
            query,
            streaming=True,
            callback=lambda text: self.root.after(0, lambda: self._append_text(text))
        )

    def _update_ui_for_movie(self, movie_details, trailer, poster_image):
        """Update UI with movie details."""
        # Update title
        title_text = f"{movie_details['title']}"
        if movie_details.get("release_date"):
            title_text += f" ({movie_details['release_date'][:4]})"
        self.title_label.config(text=title_text)

        # Update poster
        if poster_image:
            # Resize poster to fit
            poster_image = poster_image.resize((180, 270), Image.LANCZOS)
            photo = ImageTk.PhotoImage(poster_image)
            self.poster_label.config(image=photo, text="")
            self.poster_label.image = photo  # Keep reference
        else:
            self.poster_label.config(text="No poster available", image="")

        # Update trailer button
        if trailer:
            self.trailer_button.config(state=tk.NORMAL)
        else:
            self.trailer_button.config(state=tk.DISABLED)

        self.search_button.config(state=tk.NORMAL)

    def _update_ui_for_general_query(self, query):
        """Update UI for a general query."""
        # Clear movie-specific UI elements
        self.poster_label.config(text="", image="")
        self.title_label.config(text=f"Query: {query[:30]}..." if len(query) > 30 else f"Query: {query}")
        self.trailer_button.config(state=tk.DISABLED)
        self.search_button.config(state=tk.NORMAL)

    def _append_text(self, text):
        """Append text to the info area."""
        # Update text view
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, text)
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)

        if text:
            self.show_status("Ready")

    def clear_info(self):
        """Clear information display."""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state=tk.DISABLED)
        self.poster_label.config(text="", image="")
        self.title_label.config(text="")
        self.trailer_button.config(state=tk.DISABLED)

    def open_trailer(self):
        """Open trailer in web browser."""
        if self.trailer_info and self.trailer_info.get("url"):
            webbrowser.open(self.trailer_info["url"])
        else:
            self.show_status("No trailer available")

    def show_status(self, message):
        """Update status bar message."""
        self.status_var.set(message)
        # Schedule reset after 5 seconds
        if message != "Ready":
            self.root.after(5000, lambda: self.status_var.set("Ready") if self.status_var.get() == message else None)
