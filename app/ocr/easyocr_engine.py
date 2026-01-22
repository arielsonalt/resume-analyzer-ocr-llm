import io
from PIL import Image
import numpy as np

class EasyOCREngine:
    def __init__(self):
        import easyocr
        self.reader = easyocr.Reader(["pt", "en"], gpu=False)

    def image_to_text(self, image: Image.Image) -> str:
        arr = np.array(image)
        parts = self.reader.readtext(arr, detail=0, paragraph=True)
        return "\n".join(parts)

    def bytes_to_text(self, data: bytes) -> str:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        return self.image_to_text(img)
