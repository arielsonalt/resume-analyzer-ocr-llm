from dataclasses import dataclass
from typing import Any, Optional, Dict

@dataclass
class LogEntry:
    request_id: str
    user_id: str
    timestamp: str
    query: Optional[str]
    result: Dict[str, Any]
