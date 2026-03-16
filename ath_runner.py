import subprocess
from pathlib import Path
from config import ATH_EXE_PATH, ATH_CFG_PATH


def run_ath(cfg_path: Path):
    if not ATH_EXE_PATH.exists():
        raise FileNotFoundError(f"找不到 ath.exe：{ATH_EXE_PATH}")

    if not ATH_CFG_PATH.exists():
        raise FileNotFoundError(f"找不到 ath.cfg：{ATH_CFG_PATH}")

    if not cfg_path.exists():
        raise FileNotFoundError(f"找不到 cfg 檔：{cfg_path}")

    exe_dir = ATH_EXE_PATH.parent
    cmd = [str(ATH_EXE_PATH), str(cfg_path)]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(exe_dir)
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }