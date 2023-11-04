""" 
Module containing code related to the tk.Canvas for the main application
Also contains the logic for extracting data about Spotify playlists
"""

# Standard library
from collections import Counter
import re
import tkinter as tk

# Third party libraries
import spotipy

# Local
from file_handler import CustomCacheFileHandler
from authorisation import create_auth_manager

# Type hinting
from typing import Tuple


CACHE_FILE_HANDLER = CustomCacheFileHandler()


class MainCanvas(tk.Canvas):
    """ Canvas widget containing widgets for user the main app. """
    
    def __init__(self, window: tk.Tk) -> None:

        # Intiialise the canvas with the given window as its master
        super().__init__(master=window)

        self.create_API_object()
        self.setup_ui()

    def create_API_object(self) -> None:
        """ Create a Spotify object and assign it to an instance variable. """
        auth_manager = create_auth_manager()
        self.spotapi = spotipy.Spotify(auth_manager=auth_manager)

    def setup_ui(self) -> None:
        """
        Setup the UI during the authenticiation process
        
        Note:
            This includes modifying the master window itself
        """
        self.create_frame()
        self.configure_columns()
        self.setup_gui_components()
        self.place_gui_components()
        self.create_text_widget()
        self.configure_scrollbars()

    def create_frame(self) -> None:
        self.frame = tk.Frame(self)
        self.create_window((0, 0), window=self.frame, anchor="nw")

    def configure_columns(self) -> None:
        """
        Configure the width of the different columns.

        TODO Given that they're all weight=1, is this necessary?
        """
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.columnconfigure(2, weight=1)

    def setup_gui_components(self) -> None:
        self.playlist_label = tk.Label(self.frame, text="Spotify Playlist URL:")
        self.playlist_entry = tk.Entry(self.frame, width=30)
        self.submit_playlist_button = tk.Button(self.frame, text="Submit", command=self.retrieve_playlist_data)

    def place_gui_components(self) -> None:
        self.playlist_label.grid(row=0, column=0, sticky="w")
        self.playlist_entry.grid(row=0, column=1)
        self.submit_playlist_button.grid(row=0, column=2)

    def create_text_widget(self) -> None:
        self.playlist_data_text = tk.Text(self.frame, wrap=tk.WORD, width=56)
        self.playlist_data_text.grid(row=1, column=0, columnspan=3, sticky="w")

        text_width = self.playlist_data_text.winfo_reqwidth()
        self.master.geometry(f"{text_width+15}x320")

    def configure_scrollbars(self) -> None:
        self.config(scrollregion=self.bbox("all"))
        scroll_y = tk.Scrollbar(self.master, orient="vertical", command=self.yview)
        scroll_y.pack(side="right", fill="y")
        self.config(yscrollcommand=scroll_y.set)

    ### Logic ###

    def retrieve_playlist_data(self) -> None:
        # Get the playlist URL from user input
        playlist_url = self.playlist_entry.get()
        playlist_id = self.extract_playlist_id(playlist_url)
        
        # If tokens exist, proceed to retrieve and display playlist data
        tokens = CACHE_FILE_HANDLER.get_cached_token()
        if tokens:
            playlist_data, track_total = self.get_combined_genres(playlist_id)
            data_total = sum(playlist_data.values())
            genre_total = len(playlist_data.keys())
            sorted_data = sorted(playlist_data.items(), key=lambda item: (item[1], item[0]), reverse=True)
            playlist_data_text = f"Data: {data_total}\n" + f"Tracks: {track_total}\n" + f"Genres: {genre_total}\n" + '\n'.join([f"{key.title()}: {value}" for key, value in sorted_data])

            # Clear previous data and insert the new data into the text widget
            self.playlist_data_text.delete(1.0, tk.END)
            self.playlist_data_text.insert(tk.END, playlist_data_text)
        else:
            self.playlist_data_text.delete(1.0, tk.END)
            self.playlist_data_text.insert(tk.END, "Access token not found. Please authenticate first.")
    
    def get_combined_genres(self, playlist_id: str) -> Tuple[Counter, int]:
        # Initialize data structures
        artists = self.get_artist_counts(playlist_id)
        genres = self.get_genre_counts(artists)
        track_total = self.get_track_total(playlist_id)
        return genres, track_total

    def get_artist_counts(self, playlist_id: str) -> Counter:
        artists = Counter()
        offset = 0
        limit = 100
        
        while True:
            results = self.spotapi.playlist_tracks(playlist_id, offset=offset, limit=limit)
            for track in results['items']:
                for artist in track['track']['artists']:
                    artist_id = artist['id']
                    artists[artist_id] += 1
            if not results['next']:
                break
            offset += limit

        return artists

    def get_genre_counts(self, artists: Counter) -> Counter:
        genres = Counter()
        artist_ids = list(artists.keys())
        batch_size = 50

        for i in range(0, len(artist_ids), batch_size):
            batch = artist_ids[i:i + batch_size]
            response = self.spotapi.artists(batch)
            artists_data = response['artists']

            for artist in artists_data:
                artist_genres = artist.get('genres', [])
                for genre in artist_genres:
                    genres[genre] += artists[artist['id']]

        return genres

    def get_track_total(self, playlist_id: str) -> int:
        results = self.spotapi.playlist_tracks(playlist_id)
        return results['total']
    
    @staticmethod
    def extract_playlist_id(input_str: str) -> str:
        """ 
        Given a Spotify playlist URL, extract its ID
        
        This method also accepts the playlist ID as is; 
        in this case it will return the string unmodified.
        """

        # Define a regular expression pattern to match Spotify playlist URLs
        playlist_url_pattern = r'^https://open\.spotify\.com/playlist/(\w+)'
        # Define a regular expression pattern to match Spotify playlist IDs
        id_pattern = r'^(spotify:playlist:)?[A-Za-z0-9]+$' # TODO verify

        match_id_pattern = re.match(id_pattern, input_str)
        if match_id_pattern:
            return input_str
        
        match_playlist_url_pattern = re.match(playlist_url_pattern, input_str)
        if match_playlist_url_pattern:
            return match_playlist_url_pattern.group(1)
        
        raise ValueError(f"Invalid playlist URL or playlist ID: {input_str}")