from transformers import pipeline

class Summarizer:
    def __init__(self):
        
        self.summarize_pipe = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

    def summarize(self, text: str) -> str:
        text = self._trim(text, 3500)
        out = self.summarize_pipe(text, max_length=180, min_length=60, do_sample=False)
        return out[0]["summary_text"].strip()

    def short_summary(self, text: str) -> str:
        text = self._trim(text, 2200)
        out = self.summarize_pipe(text, max_length=80, min_length=30, do_sample=False)
        return out[0]["summary_text"].strip()

    def _trim(self, text: str, max_chars: int) -> str:
        return text[:max_chars] if len(text) > max_chars else text
