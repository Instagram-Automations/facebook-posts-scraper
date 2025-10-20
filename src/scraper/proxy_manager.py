from __future__ import annotations

import os
import random
from pathlib import Path
from typing import List, Optional

from .utils import setup_logger

logger = setup_logger("proxy")


class ProxyManager:
    """
    Simple file-based proxy rotator.
    Supports:
      - http://user:pass@host:port
      - http://host:port
    Environment variable PROXY_URL (single) can also be used.
    """

    def __init__(self, proxies_file: Optional[str | Path] = None):
        self._proxies: List[str] = []
        if os.environ.get("PROXY_URL"):
            self._proxies.append(os.environ["PROXY_URL"])
        if proxies_file:
            p = Path(proxies_file)
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            self._proxies.append(line)
            else:
                logger.warning("Proxies file not found: %s", proxies_file)

    def has_proxies(self) -> bool:
        return len(self._proxies) > 0

    def pick(self) -> Optional[str]:
        if not self._proxies:
            return None
        return random.choice(self._proxies)
