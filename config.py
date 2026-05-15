import os
from pathlib import Path

# Override these with environment variables or edit the defaults for your PC.
ATH_EXE_PATH = Path(os.getenv("ATH_EXE_PATH", r"D:\ATH_GUI\ath.exe"))
ATH_CFG_PATH = Path(os.getenv("ATH_CFG_PATH", r"D:\ATH_GUI\ath.cfg"))
ATH_OUTPUT_ROOT = Path(os.getenv("ATH_OUTPUT_ROOT", r"D:\Horns"))

# Project directories.
PROJECT_ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = PROJECT_ROOT / "templates"
GENERATED_CFG_DIR = PROJECT_ROOT / "generated_cfg"
LOCAL_OUTPUT_DIR = PROJECT_ROOT / "output"

# Create local folders used by the GUI.
TEMPLATE_DIR.mkdir(exist_ok=True)
GENERATED_CFG_DIR.mkdir(exist_ok=True)
LOCAL_OUTPUT_DIR.mkdir(exist_ok=True)
