""" 
Main module for running the application.
"""

# Standard library
import tkinter as tk

# Third party libraries
import ttkbootstrap

# Local
from authorisation import AuthorisationCanvas
from playlist_info import MainCanvas
from file_handler import CustomCacheFileHandler


CACHE_FILE_HANDLER = CustomCacheFileHandler()


class App:
    """ Class for running the whole application. """

    def __init__(self, root) -> None:
        """ Create a window and run the authorisation code. """
        self.root = root
        self.root.iconbitmap("../img/music.ico")
        self.style = ttkbootstrap.Style(theme='vapor')
        
        tokens = CACHE_FILE_HANDLER.get_cached_token()
        if not tokens:
            self.run_authorisation()
        else:
            self.run_main()

    def on_authorisation_success(self) -> None:
        """ Run the main application. """
        # Hide the current (authorisation) canvas
        self.authorisation_canvas.pack_forget()  
        # Show the main application canvas
        self.run_main()

    def run_authorisation(self) -> None:
        """ Show the tk.Canvas for user authentication. """
        self.root.title("Authorisation")
        self.authorisation_canvas = AuthorisationCanvas(root, on_success=self.on_authorisation_success)
        self.authorisation_canvas.pack(side="left", fill="both", expand=True)
        
    def run_main(self) -> None:
        """ Show the tk.Canvas for the main program. """
        self.root.title("Playlist Info App")
        self.main_application = MainCanvas(self.root)
        self.main_application.pack(side="left", fill="both", expand=True)


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    app.root.mainloop()
