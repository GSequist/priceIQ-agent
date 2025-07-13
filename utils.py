from difflib import get_close_matches
from typing import List, Dict
from PIL import Image
import tiktoken
import base64
import io
import os

############################################################################################################
##tokenizer

tokenizer = tiktoken.get_encoding("cl100k_base")

############################################################################################################


def ensure_user_workspace(user_id: str) -> str:
    """Ensure user workspace directory exists and return its path"""
    user_folder = os.path.join("workspace", user_id)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder


############################################################################################################


def sanitize_and_encode_image(file_path):
    with Image.open(file_path) as img:
        img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        base64_encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{base64_encoded}"


#############################################################################################################
