from typing import List, Dict

class Explainer:
    def build_justification(self, query: str, evidence_snippets: List[str]) -> List[Dict[str, str]]:
        out = []
        for ev in evidence_snippets[:6]:
            out.append({"evidence": ev, "why": "Trecho do currículo alinhado à query"})
        return out
