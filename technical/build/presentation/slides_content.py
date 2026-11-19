"""Slide text and speaker notes: single source for the PPTX and Speaker_Notes.md.
The main talk (slides_main.py) is followed by a divider and the supplementary slides (slides_supp.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from slides_main import SLIDES_MAIN  # noqa: E402
from slides_supp import SLIDES_SUPP  # noqa: E402

SLIDES = SLIDES_MAIN + SLIDES_SUPP
