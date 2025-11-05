import os
import glob
from typing import Iterable

def walk_files(roots, exts=(".md", ".yaml", ".yml", ".json")):
    files = []
    for root in roots:
        for ext in exts:
            files.extend(glob.glob(os.path.join(root, f"**/*{ext}"), recursive=True))
    return sorted(list({f for f in files if os.path.isfile(f)}))

def chunk_text(text: str, target_tokens: int = 512) -> Iterable[str]:
    # Heurística simplificada: fatias por tamanho ~2k chars
    size = max(512, min(2000, target_tokens * 4))
    for i in range(0, len(text), size):
        yield text[i:i+size]
