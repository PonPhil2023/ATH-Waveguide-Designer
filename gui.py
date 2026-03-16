import os
import re
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

from cfg_generator import generate_cfg
from ath_runner import run_ath
from config import GENERATED_CFG_DIR, ATH_OUTPUT_ROOT
from stl_viewer import find_latest_stl, show_stl


DEFAULT_PARAMS = {
    "throat_diameter": 25.4,
    "throat_angle": 7,
    "coverage_angle": 45,
    "length": 94,
    "term_s": 0.5,
    "term_q": 0.996,
    "term_n": 4.0,
    "mesh_angular_segments": 64,
    "mesh_length_segments": 20,
    "mesh_throat_resolution": 4.0,
    "mesh_mouth_resolution": 8.0,
}


FLOAT_FIELDS = {
    "throat_diameter",
    "throat_angle",
    "coverage_angle",
    "length",
    "term_s",
    "term_q",
    "term_n",
    "mesh_throat_resolution",
    "mesh_mouth_resolution",
}

INT_FIELDS = {
    "mesh_angular_segments",
    "mesh_length_segments",
}


class AthGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ATH Waveguide Designer")
        self.root.geometry("950x720")
        self.root.minsize(860, 640)

        self.entries = {}
        self.last_cfg_path = None
        self.last_output_dir = None
        self.last_stl_path = None

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        title_frame = ttk.Frame(main)
        title_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(
            title_frame,
            text="ATH Waveguide Designer",
            font=("Segoe UI", 14, "bold")
        ).pack(side="left")

        # =========================
        # Parameters
        # =========================
        param_frame = ttk.LabelFrame(main, text="Parameters", padding=10)
        param_frame.pack(fill="x", pady=(0, 8))

        for i, (name, value) in enumerate(DEFAULT_PARAMS.items()):
            ttk.Label(param_frame, text=name, width=24).grid(
                row=i, column=0, sticky="w", padx=5, pady=4
            )

            entry = ttk.Entry(param_frame, width=22)
            entry.insert(0, str(value))
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=4)

            self.entries[name] = entry

        # =========================
        # Buttons
        # =========================
        button_frame = ttk.Frame(main)
        button_frame.pack(fill="x", pady=(0, 8))

        ttk.Button(
            button_frame,
            text="Generate & Run",
            command=self.on_run
        ).pack(side="left", padx=4)

        ttk.Button(
            button_frame,
            text="Generate CFG Only",
            command=self.on_generate_only
        ).pack(side="left", padx=4)

        ttk.Button(
            button_frame,
            text="Open generated_cfg",
            command=self.open_generated_cfg_folder
        ).pack(side="left", padx=4)

        ttk.Button(
            button_frame,
            text="Open D:\\Horns",
            command=self.open_ath_output_root
        ).pack(side="left", padx=4)

        ttk.Button(
            button_frame,
            text="Open Last Output",
            command=self.open_last_output_folder
        ).pack(side="left", padx=4)

        ttk.Button(
            button_frame,
            text="Open Last STL",
            command=self.open_last_stl_file
        ).pack(side="left", padx=4)

        ttk.Button(
            button_frame,
            text="Clear Log",
            command=self.clear_log
        ).pack(side="left", padx=4)

        # =========================
        # Path display
        # =========================
        path_frame = ttk.LabelFrame(main, text="Paths", padding=10)
        path_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(path_frame, text="Last CFG:", width=14).grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        self.cfg_var = tk.StringVar(value="(none)")
        ttk.Entry(path_frame, textvariable=self.cfg_var, width=100).grid(
            row=0, column=1, sticky="ew", padx=5, pady=4
        )

        ttk.Label(path_frame, text="Last Output:", width=14).grid(
            row=1, column=0, sticky="w", padx=5, pady=4
        )
        self.output_var = tk.StringVar(value="(none)")
        ttk.Entry(path_frame, textvariable=self.output_var, width=100).grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )

        ttk.Label(path_frame, text="Last STL:", width=14).grid(
            row=2, column=0, sticky="w", padx=5, pady=4
        )
        self.stl_var = tk.StringVar(value="(none)")
        ttk.Entry(path_frame, textvariable=self.stl_var, width=100).grid(
            row=2, column=1, sticky="ew", padx=5, pady=4
        )

        path_frame.columnconfigure(1, weight=1)

        # =========================
        # Log area
        # =========================
        log_frame = ttk.LabelFrame(main, text="Execution Log", padding=10)
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_frame,
            wrap="word",
            font=("Consolas", 10)
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            log_frame,
            orient="vertical",
            command=self.log_text.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def collect_params(self) -> dict:
        params = {}

        for key, entry in self.entries.items():
            raw = entry.get().strip()

            if raw == "":
                raise ValueError(f"{key} 不能為空")

            if key in FLOAT_FIELDS:
                params[key] = float(raw)
            elif key in INT_FIELDS:
                params[key] = int(float(raw))
            else:
                params[key] = raw

        return params

    def log(self, text: str):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.root.update_idletasks()

    def clear_log(self):
        self.log_text.delete("1.0", "end")

    def set_last_cfg(self, path: Path | None):
        self.last_cfg_path = Path(path) if path else None
        self.cfg_var.set(str(path) if path else "(none)")

    def set_last_output(self, path: Path | None):
        self.last_output_dir = Path(path) if path else None
        self.output_var.set(str(path) if path else "(none)")

    def set_last_stl(self, path: Path | None):
        self.last_stl_path = Path(path) if path else None
        self.stl_var.set(str(path) if path else "(none)")

    def parse_output_dir(self, stdout: str) -> Path | None:
        match = re.search(r"-destination directory:\s*(.+)", stdout)
        if match:
            path_str = match.group(1).strip()
            return Path(path_str)
        return None

    def open_folder(self, path: Path):
        if not path.exists():
            messagebox.showwarning("Warning", f"資料夾不存在：\n{path}")
            return
        os.startfile(str(path))

    def open_file(self, path: Path):
        if not path.exists():
            messagebox.showwarning("Warning", f"檔案不存在：\n{path}")
            return
        os.startfile(str(path))

    def open_generated_cfg_folder(self):
        self.open_folder(GENERATED_CFG_DIR)

    def open_ath_output_root(self):
        self.open_folder(ATH_OUTPUT_ROOT)

    def open_last_output_folder(self):
        if self.last_output_dir is None:
            messagebox.showinfo("Info", "目前尚未有可開啟的輸出資料夾。")
            return
        self.open_folder(self.last_output_dir)

    def open_last_stl_file(self):
        if self.last_stl_path is None:
            messagebox.showinfo("Info", "目前尚未有可開啟的 STL 檔。")
            return
        self.open_file(self.last_stl_path)

    def on_generate_only(self):
        try:
            params = self.collect_params()
            cfg_path = generate_cfg(params)

            self.set_last_cfg(cfg_path)

            self.log("=" * 70)
            self.log("[OK] CFG generated successfully")
            self.log(f"[INFO] CFG file: {cfg_path}")

            messagebox.showinfo("Success", f"CFG 已生成：\n{cfg_path}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log(f"[ERROR] {e}")

    def on_run(self):
        try:
            params = self.collect_params()

            self.log("=" * 70)
            self.log("[INFO] Collecting parameters...")

            cfg_path = generate_cfg(params)
            self.set_last_cfg(cfg_path)
            self.set_last_stl(None)

            self.log(f"[INFO] CFG file: {cfg_path}")
            self.log("[INFO] Running ATH...")

            result = run_ath(cfg_path)

            output_dir = self.parse_output_dir(result["stdout"])
            self.set_last_output(output_dir)

            self.log("---------- STDOUT ----------")
            self.log(result["stdout"] if result["stdout"] else "(no stdout)")

            self.log("---------- STDERR ----------")
            self.log(result["stderr"] if result["stderr"] else "(no stderr)")

            self.log(f"[INFO] Return code: {result['returncode']}")

            if output_dir is not None:
                self.log(f"[INFO] Output directory: {output_dir}")
            else:
                self.log("[INFO] Output directory: (not parsed)")

            if result["returncode"] == 0:
                stl_path = None

                if output_dir is not None and output_dir.exists():
                    stl_path = find_latest_stl(output_dir)

                self.set_last_stl(stl_path)

                if stl_path is not None:
                    self.log(f"[INFO] STL found: {stl_path}")
                    show_stl(stl_path)
                else:
                    self.log("[INFO] 找不到 STL 檔案")

                messagebox.showinfo("Success", "ATH 執行完成")
            else:
                messagebox.showwarning(
                    "Warning",
                    "ATH 已執行，但回傳碼非 0，請檢查 log。"
                )

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log(f"[ERROR] {e}")