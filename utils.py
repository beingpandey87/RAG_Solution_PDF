import base64
from pathlib import Path

def encode_image_to_base64(image_path: str) -> str:
    """Loads an image and converts it to a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
def create_directories(file_path: str,base_path: str):
    '''
    Creates the necessary output directories for extracted assets.
    Input: 
    file_path: str,
    base_path: str

    Output:
    tuple[Path, Path, Path]
    '''
    Filename = Path(file_path).stem
    print(f"File Name : {Filename}")
    images_output_dir = Path(base_path) / Filename / "images"
    tables_output_dir = Path(base_path) / Filename / "tables"
    content_output_dir = Path(base_path) / Filename / "contents"

    images_output_dir.mkdir(parents=True, exist_ok=True)
    tables_output_dir.mkdir(parents=True, exist_ok=True)
    content_output_dir.mkdir(parents=True, exist_ok=True)

    return Filename,images_output_dir, tables_output_dir, content_output_dir