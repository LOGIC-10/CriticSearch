import base64
from io import BytesIO
from typing import Dict

import requests
from PIL import Image


class ImageAnalyzer:
    def __init__(self, model="gpt-4o-mini"):
        self.model = model

    def analyze_image(self, image_data: str) -> Dict:
        """Analyze an image using the specified vision model."""
        try:
            # Convert image data to base64 if it's a URL or file path
            if isinstance(image_data, str):
                if image_data.startswith("http"):
                    response = requests.get(image_data)
                    image = Image.open(BytesIO(response.content))
                else:
                    image = Image.open(image_data)

                buffered = BytesIO()
                image.save(buffered, format="PNG")
                image_base64 = base64.b64encode(buffered.getvalue()).decode()
            else:
                image_base64 = image_data

            # TODO this is a stand in for later use
            return {
                "description": "Image analysis completed",
                "model_used": self.model,
                "image_format": "base64",
            }
        except Exception as e:
            return {"error": str(e)}
