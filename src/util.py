""" 
Utility functions that didn't fit into other modules
"""

# Standard library
import secrets
import string
import os

# Third party libraries
from cryptography.fernet import Fernet

# Type checking 
from typing import ByteString


def generate_random_str(length: int) -> str:
    """ Generates a random string of specified length. """
    # Define chars allowed in random string
    chars = string.ascii_letters + string.digits
    # Generate a random string of the specified length
    random_string = ''.join(secrets.choice(chars) for _ in range(length))
    return random_string


def get_fernet_key() -> ByteString:
    """ 
    Return a fernet key from file
    If one doesn't exist, create it and save to the file.
    """
    key_file = '../cache/keys/spotify.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as kf:
            return Fernet(kf.read())
    else:
        # Generate a new key and save it to the file
        key = Fernet.generate_key()
        with open(key_file, 'wb') as kf:
            kf.write(key)
        return Fernet(key)






