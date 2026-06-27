import base64
import re
from pathlib import Path


def convert_html_images_to_data_uris(html_content: str, base_dir: Path) -> str:
    """Find all image paths in the HTML, read them from base_dir,
    and replace with base64 Data URIs.
    """

    def replacer(match: re.Match) -> str:
        img_src = match.group(1)
        img_path = base_dir / img_src
        if img_path.exists():
            with open(img_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            suffix = img_path.suffix.lower().replace(".", "")
            if suffix == "jpg":
                suffix = "jpeg"
            return f'src="data:image/{suffix};base64,{encoded}"'
        return match.group(0)

    pattern = r'src=["\']([^"\']+\.(?:png|jpg|jpeg|gif))["\']'
    return re.sub(pattern, replacer, html_content)
