import re
import os

def sanitize_filename(filename):
    """
    Sanitize the filename by removing invalid characters.
    """
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

def create_dir(path):
    """
    Create directory if it doesn't exist.
    """
    if not os.path.exists(path):
        os.makedirs(path)
