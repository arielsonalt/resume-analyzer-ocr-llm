import io
from PIL import Image
import numpy as np

class PaddleOCREngine:
    def __init__(self):
        from paddleocr import PaddleOCR
        self.ocr = PaddleOCR(use_angle_cls=True, lang="en")  # pt pode variar conforme build

    def image_to_text(self, image: Image.Image) -> str:
        arr = np.array(image)
        result = self.ocr.ocr(arr, cls=True)
        lines = []
        for page in result:
            for item in page:
                lines.append(item[1][0])
        return "\n".join(lines)

    def bytes_to_text(self, data: bytes) -> str:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        return self.image_to_text(img)
