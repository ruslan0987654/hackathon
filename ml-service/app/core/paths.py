"""Layihənin əsas qovluq yolları (heç bir xarici asılılığı yoxdur)."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_DIR = BASE_DIR / "app" / "models" / "artifacts"
DEFAULT_DATASET_DIR = BASE_DIR / "datasets"
