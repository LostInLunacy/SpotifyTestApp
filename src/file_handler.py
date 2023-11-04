""" 
Module containing code related to the handling of (encrypting, decrypting, writing, reading) of data

Classes:
    CredentialsFileHandler: handles user credentials (client_id, client_secret)

    CustomCacheFileHandler: handles tolens (access_token, refresh_token); inherits from spotipy's CacheFileHandler
        Customises its parents behaviour by altering destination of caching, and adding encryption for sensitive data
"""

# Standard library
import json
import os
import time

# Third party libraries
from spotipy.cache_handler import CacheFileHandler

# Local
from util import get_fernet_key

# Type hinting
from typing import Dict, Optional


class CredentialsFileHandler:
    """ 
    Class with methods for getting credentials (client_id, client_secret) 
    And saving them to a file. 
    """

    def __init__(self):
        """ 
        Get the fernet key required to encrypt/decrypt the data
        And retrieve existing credentials from file if they exist
        """
        self.fernet_key = get_fernet_key()
        self.retrieve_credentials()

    @property
    def has_credentials(self) -> bool:
        return self.client_id and self.client_secret

    @property
    def client_id(self) -> Optional[str]:
        if self.credentials:
            return self.credentials['client_id']

    @property
    def client_secret(self) -> Optional[str]:
        if self.credentials:
            return self.credentials['client_secret']
    
    def retrieve_credentials(self) -> Optional[Dict]:
        """ Retrieve the client_id and client_secret for Spotify API. """
        fernet_key = get_fernet_key()
        try:
            with open("../cache/spotify_credentials.json", "r") as credentials_file:
                credentials_data = json.load(credentials_file)
        except (FileNotFoundError, json.JSONDecodeError):
            # Couldn't get details
            credentials = None
        else:
            credentials = {k: fernet_key.decrypt(v.encode()).decode() for k,v in credentials_data.items()}
        finally:
            self.credentials = credentials
            return credentials
        
    def save_credentials_to_file(self, credentials: Optional[Dict] = None) -> None:
        if not credentials:
            credentials = self.credentials
        # Encrypt and save credentials to a JSON file
        encrypted_credentials = {k: self.fernet_key.encrypt(v.encode()).decode() for k,v in credentials.items()}
        with open("../cache/spotify_credentials.json", "w") as credentials_file:
            json.dump(encrypted_credentials, credentials_file)


class CustomCacheFileHandler(CacheFileHandler):
    """ 
    Custom CacheFileHandler class 
    - Saves cache to customised location
    - Encrypts some of the data when saving to file; decrypts the same data when loading from file.
    """

    CUSTOM_CACHE_PATH = '../cache/token_cache.json'

    # Attributes that actually require encrypting - everyting else will remain enuncrypted
    ATTRS_TO_ENCRYPT = ('access_token', 'refresh_token')

    REFRESH_INTERVAL = 100

    def __init__(self):
        """ Initialise the instance of CacheFileHandler, call the parent. """
        super().__init__(self.CUSTOM_CACHE_PATH)
        self.fernet_key = get_fernet_key()

    def is_cache_fresh(self) -> bool:
        """
        Check if the cache file has been updated within the refresh interval.
        """
        if os.path.exists(self.cache_path):
            file_modification_time = os.path.getmtime(self.cache_path)
            current_time = time.time()
            return (current_time - file_modification_time) < self.REFRESH_INTERVAL
        return False

    def save_token_to_cache(self, token_info) -> None:
        # Encrypt the token info
        if not self.is_cache_fresh():    

            # Saving token to cache
            encrypted_token_info = {k: self.fernet_key.encrypt(v.encode()).decode() if v in self.ATTRS_TO_ENCRYPT else v for k, v in token_info.items()}

            # ??? Thanks Obama
            encrypted_token_info['expires_at'] = encrypted_token_info.pop('expires_in')

            with open(self.cache_path, 'w') as token_file:
                json.dump(encrypted_token_info, token_file)
                # Successfully saved the token

    def get_cached_token(self) -> Optional[Dict]:
        # Getting data from save file
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'r') as token_file:
                token_info = json.load(token_file)
                # Decrypt the token info
                decrypted_token_info = {k: self.fernet_key.decrypt(v.encode()).decode() if v in self.ATTRS_TO_ENCRYPT else v for k, v in token_info.items()}
                return decrypted_token_info
        else:
            return None
        
