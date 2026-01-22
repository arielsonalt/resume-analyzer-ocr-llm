import io
from PIL import Image
import pytesseract

class TesseractOCREngine:
    def image_to_text(self, image: Image.Image) -> str:
        return pytesseract.image_to_string(image, lang="por+eng")

    def bytes_to_text(self, data: bytes) -> str:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        return self.image_to_text(img)
