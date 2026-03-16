from pathlib import Path

# ===== 請依你的實際路徑修改 =====
ATH_EXE_PATH = Path(r"D:\ATH_GUI\ath.exe")
ATH_CFG_PATH = Path(r"D:\ATH_GUI\ath.cfg")
ATH_OUTPUT_ROOT = Path(r"D:\Horns")

# ===== 專案目錄 =====
PROJECT_ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = PROJECT_ROOT / "templates"
GENERATED_CFG_DIR = PROJECT_ROOT / "generated_cfg"
LOCAL_OUTPUT_DIR = PROJECT_ROOT / "output"

# ===== 自動建立資料夾 =====
TEMPLATE_DIR.mkdir(exist_ok=True)
GENERATED_CFG_DIR.mkdir(exist_ok=True)
LOCAL_OUTPUT_DIR.mkdir(exist_ok=True)