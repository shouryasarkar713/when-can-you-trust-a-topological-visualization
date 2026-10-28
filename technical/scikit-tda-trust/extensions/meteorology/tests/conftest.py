"""Put the repo root and the weather extension's src/ on sys.path."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "extensions" / "meteorology" / "wx"))
sys.path.insert(0, str(REPO_ROOT / "extensions" / "meteorology" / "scripts"))
