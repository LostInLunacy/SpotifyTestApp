""" 
Module containing code related to the tk.Canvas for the user authentication
This includes the logic for submitting client credentials
And for opening the browser and prompting the user to allow the application
"""

# Standard libary
import base64
import tkinter as tk
import urllib.parse
import webbrowser

# Third party libraries
import requests
from spotipy import SpotifyOAuth

# Local
from file_handler import CustomCacheFileHandler, CredentialsFileHandler
from util import generate_random_str

# Type hinting
from typing import Callable, Dict


# URL user is directed to after giving application permissions
REDIRECT_URI = 'https://github.com/LostInLunacy/'

# Scopes for Spotify API
SCOPES = (
    'user-library-read',
    'playlist-read-private',
    'playlist-read-collaborative',
    'playlist-modify-public',
    'playlist-modify-private',
    'user-library-read'
)


CREDENTIALS_FILE_HANDLER = CredentialsFileHandler()
CACHE_FILE_HANDLER = CustomCacheFileHandler()


def build_auth_url(client_id: str) -> str:
    """ Build an authorisation URL 
    
    Note:
        The user can visit this URL to allow the app
        And obtain an authorisation code. 
    """
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': ' '.join(SCOPES)
    }
    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return auth_url


def create_auth_manager() -> SpotifyOAuth:
    """ 
    Note: required for the creation of a Spotify object. 
    """
    if not CREDENTIALS_FILE_HANDLER.has_credentials:
        raise Exception("No credentials available to build auth manager.")
    
    auth_manager = SpotifyOAuth(
        client_id = CREDENTIALS_FILE_HANDLER.client_id,
        client_secret = CREDENTIALS_FILE_HANDLER.client_secret,
        redirect_uri = REDIRECT_URI,
        state = generate_random_str(32),
        scope = ' '.join(SCOPES),
        cache_handler = CustomCacheFileHandler()
    )
    return auth_manager


class AuthorisationCanvas(tk.Canvas):
    """ Canvas widget containing widgets for user authentication. """

    def __init__(self, window: tk.Tk, on_success: Callable) -> None:
        
        self.on_success = on_success
        
        # Intiialise the canvas with the given window as its master
        super().__init__(master=window)
        
        self.master.geometry('320x240')
        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Setup the UI during the authenticiation process
        
        Note:
            This includes modifying the master window itself
        """
        self.setup_frame()
        self.setup_credentials_input()
        self.setup_authorisation_url_label()
        self.setup_authorisation_code_input()
        self.setup_scrollbar()

    def setup_frame(self) -> None:
        # Create frame
        self.frame = tk.Frame(self)
        # Create window within frame
        self.create_window((0,0), window=self.frame, anchor='nw')

    def setup_credentials_input(self) -> None:
        """
        Set up the input fields for client ID and client secret.
        """
        # Create widgets related to credentials
        self.client_id_label = tk.Label(self.frame, text="Client ID: ")
        self.client_id_entry = tk.Entry(self.frame, width=40)
        self.client_secret_label = tk.Label(self.frame, text="Client Secret: ")
        self.client_secret_entry = tk.Entry(self.frame, show='*', width=40)
        self.submit_credentials_button = tk.Button(self.frame, text="Submit", command=self.submit_credentials)

        # Pack the widgets
        self.client_id_label.pack(anchor="w")
        self.client_id_entry.pack(anchor="w")
        self.client_secret_label.pack(anchor="w")
        self.client_secret_entry.pack(anchor="w")
        self.submit_credentials_button.pack(anchor="w") 

    def setup_authorisation_url_label(self) -> None:
        """
        Set up the label that displays the authorisation URL.
        """
        # Create and pack widget for authorisation URL 
        # (to which user will be redirected after submitting credentials)
        self.authorisation_url_label = tk.Label(self.frame, text="Authorisation URL: Not Available")
        self.authorisation_url_label.pack(anchor="w")
        # When user clicks the URL it will also open the browser 
        # (in case webbrowser fails)
        self.authorisation_url_label.bind("<Button-1>", lambda e: self.open_authorisation_url())

    def setup_authorisation_code_input(self) -> None:
        """
        Set up the input field for the authorisation code.
        """
        # Create widgets related to authorisation code
        self.code_label = tk.Label(self.frame, text="Authorisation Code:")
        self.code_entry = tk.Entry(self.frame, width=40)
        self.submit_button_authorisation_code = tk.Button(self.frame, text="Submit Code", command=self.submit_authorisation_code)

        # Pack the widgets
        self.code_label.pack(anchor="w")
        self.code_entry.pack(anchor="w")
        self.submit_button_authorisation_code.pack(anchor="w")

    def setup_scrollbar(self) -> None:
        """
        Configure the scrollbar for scrolling the UI.
        """
        self.config(scrollregion=self.bbox("all"))
        scroll_y = tk.Scrollbar(self, orient="vertical", command=self.yview)
        scroll_y.pack(side="right", fill="y")
        self.config(yscrollcommand=scroll_y.set)

    ### Logic ###

    def open_authorisation_url(self) -> None:
        """
        Open the authorisation URL in the default web browser.
        """
        # Get the client_id the user has entered
        client_id = self.client_id_entry.get()
        # Build an authorisation_url based on the client_id
        auth_url = build_auth_url(client_id)
        # Display the authorisation_url as the text of the authorisation_url label widget
        self.authorisation_url_label.config(text=f"Authorisation URL: {auth_url}")
        # Automatically open the URL in a browser window
        webbrowser.open(auth_url)

    def submit_credentials(self) -> None:
        """
        Handle the submission of client ID and client secret.
        Saves credentials to a file and opens the authorisation URL.
        """
        client_id = self.client_id_entry.get()
        client_secret = self.client_secret_entry.get()
        credentials = {'client_id': client_id, 'client_secret': client_secret}
        CREDENTIALS_FILE_HANDLER.save_credentials_to_file(credentials)
        # Update the instance with the new credentials
        CREDENTIALS_FILE_HANDLER.retrieve_credentials()
        self.open_authorisation_url()

    def generate_tokens(self, authorisation_code: str) -> Dict[str, str]:
        """ Generates tokens and saves them to file. """
        
        client_id = CREDENTIALS_FILE_HANDLER.client_id
        client_secret = CREDENTIALS_FILE_HANDLER.client_secret

        ### Setup request ###
        token_url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "authorization_code", # has to be US spelling
            "code": authorisation_code,
            "redirect_uri": REDIRECT_URI
        }
        headers = {"Authorization": "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")}

        ### Make request ###
        response = requests.post(token_url, data=data, headers=headers)

        ### Parse data ###
        # Parse the response to get the access token, refresh token, and other data
        token_data = response.json()
        CACHE_FILE_HANDLER.save_token_to_cache(token_data)

    def submit_authorisation_code(self) -> None:
        """
        Handle the submission of the authorisation code.
        Retrieves tokens, saves them.
        """
        auth_code = self.code_entry.get()
        
        if auth_code and CREDENTIALS_FILE_HANDLER.has_credentials:
            self.generate_tokens(authorisation_code=auth_code)
            self.on_success()