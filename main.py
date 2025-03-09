import tkinter as tk
import google.generativeai as genai

from src.config import GEMINI_API_KEY
from src.movie_agent_gui import MovieAgentGUI


# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


def main():
    root = tk.Tk()
    app = MovieAgentGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()