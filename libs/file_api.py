import os, re

def create_file(file_path: str) -> None:
    """Create a file if it does not exist."""
    if not os.path.exists(file_path):
        with open(file_path, 'a'):
            pass

def sanitize_filename(filename: str) -> str:
    """Sanitize the input string to be a valid file name."""
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)
    # Remove leading/trailing spaces and make sure it isn't empty
    sanitized = sanitized.strip()
    return sanitized

async def create_folder(folder_path: str) -> bool:
    """Create a folder if it does not exist, return True if successful, False otherwise."""
    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path)  # os.makedirs creates any intermediate directories as needed
            return True
        except OSError as e:
            print(f"Error creating directory {folder_path}: {e}")
            return False
    return True
