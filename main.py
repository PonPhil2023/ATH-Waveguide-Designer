import os
import re
import sys
from pathlib import Path

import pyvista as pv
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QLabel,
    QDockWidget,
    QDoubleSpinBox,
    QSpinBox,
    QScrollArea,
    QToolBar,
    QStatusBar,
    QLineEdit,
    QFrame,
    QGridLayout,
    QComboBox,
    QStackedWidget,
)

from pyvistaqt import QtInteractor

from cfg_generator import generate_cfg
from ath_runner import run_ath
from config import GENERATED_CFG_DIR, ATH_OUTPUT_ROOT


MODERN_DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: "Segoe UI", "Microsoft JhengHei", sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #3e3e42;
    border-radius: 4px;
    margin-top: 1.5ex;
    font-weight: bold;
    color: #4daaf1;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
}
QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox {
    background-color: #2d2d30;
    border: 1px solid #3e3e42;
    border-radius: 3px;
    padding: 4px;
    color: #ffffff;
}
QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus, QComboBox:focus {
    border: 1px solid #007acc;
}
QPushButton {
    background-color: #3e3e42;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    color: #ffffff;
}
QPushButton:hover {
    background-color: #4e4e52;
}
QPushButton:pressed {
    background-color: #007acc;
}
QPushButton#btnRun {
    background-color: #007acc;
    font-weight: bold;
    font-size: 14px;
    padding: 10px;
}
QPushButton#btnRun:hover {
    background-color: #0098ff;
}
QDockWidget {
    color: #ffffff;
    font-weight: bold;
}
QDockWidget::title {
    background: #2d2d30;
    padding: 6px;
}
QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #3e3e42;
    font-family: "Consolas", monospace;
    font-size: 12px;
}
QToolBar {
    border-bottom: 1px solid #3e3e42;
    background: #2d2d30;
    spacing: 5px;
}
QStatusBar {
    background: #007acc;
    color: white;
    font-weight: bold;
}
"""


OSSE_GROUPS = {
    "幾何設定 (OS-SE Geometry)": [
        ("throat_diameter", "喉部直徑 (Throat.Diameter)", 25.4, "float"),
        ("throat_angle", "喉部開口半角 (Throat.Angle)", 7.0, "float"),
        ("coverage_angle", "指向角半角 (Coverage.Angle)", 45.0, "float"),
        ("length", "波導深度 (Length)", 94.0, "float"),
    ],
    "終端設定 (OS-SE Terminal)": [
        ("term_s", "終端參數 s (Term.s)", 0.5, "float"),
        ("term_q", "終端參數 q (Term.q)", 0.996, "float"),
        ("term_n", "終端參數 n (Term.n)", 4.0, "float"),
    ],
    "網格解析 (Mesh)": [
        ("mesh_angular_segments", "周向剖面分段數", 64, "int"),
        ("mesh_length_segments", "軸向切片分段數", 20, "int"),
        ("mesh_throat_resolution", "喉部網格解析度", 4.0, "float"),
        ("mesh_mouth_resolution", "口部網格解析度", 8.0, "float"),
    ],
}


TRITONIA_GROUPS = {
    "OSSE 區塊": [
        ("L", "波導深度 L [mm]", 135.0, "float"),
        ("r0", "喉部半徑 r0 [mm]", 36.0, "float"),
        ("a0", "喉部角 a0 [deg]", 4.2, "float"),
        ("a_expr", "指向角公式 a", "48.5 - 7.0*cos(2.0*p)^5.0 - 16.0*sin(p)^12.0", "text"),
        ("s_expr", "參數公式 s", "0.7 + 0.2*cos(p)^2", "text"),
        ("n", "n", 3.7, "float"),
        ("q", "q", 0.995, "float"),
        ("k", "k", 1.0, "float"),
    ],
    "Morph 設定": [
        ("morph_target_shape", "出口形狀 (1=矩形, 2=圓形)", 1, "int"),
        ("morph_fixed_part", "Morph.FixedPart", 0.0, "float"),
        ("morph_rate", "Morph.Rate", 3.0, "float"),
        ("morph_corner_radius", "CornerRadius [mm]", 18.0, "float"),
    ],
    "Mesh 設定": [
        ("mesh_angular_segments", "Mesh.AngularSegments", 80, "int"),
        ("mesh_length_segments", "Mesh.LengthSegments", 26, "int"),
        ("mesh_corner_segments", "Mesh.CornerSegments", 4, "int"),
        ("mesh_throat_resolution", "Mesh.ThroatResolution", 5.0, "float"),
        ("mesh_mouth_resolution", "Mesh.MouthResolution", 10.0, "float"),
        ("mesh_interface_resolution", "Mesh.InterfaceResolution", 7.0, "float"),
        ("mesh_subdomain_slices", "Mesh.SubdomainSlices", 26, "int"),
    ],
    "ABEC 設定": [
        ("abec_sim_type", "ABEC.SimType", 1, "int"),
        ("abec_f1", "ABEC.f1 [Hz]", 400, "int"),
        ("abec_f2", "ABEC.f2 [Hz]", 12000, "int"),
        ("abec_num_frequencies", "ABEC.NumFrequencies", 40, "int"),
        ("abec_mesh_frequency", "ABEC.MeshFrequency", 1000, "int"),
    ],
    "Polar / Report": [
        ("distance_h", "SPL_H Distance [m]", 2.0, "float"),
        ("offset_h", "SPL_H Offset [mm]", 145.0, "float"),
        ("distance_v", "SPL_V Distance [m]", 2.0, "float"),
        ("offset_v", "SPL_V Offset [mm]", 145.0, "float"),
        ("distance_d", "SPL_D Distance [m]", 2.0, "float"),
        ("offset_d", "SPL_D Offset [mm]", 145.0, "float"),
        ("inclination_d", "SPL_D Inclination", 42.0, "float"),
        ("output_abec_project", "Output.ABECProject", 1, "int"),
        ("output_stl", "Output.STL", 1, "int"),
        ("report_title", "Report.Title", "Tritonia", "text"),
        ("report_norm_angle", "Report.NormAngle", 10, "int"),
    ],
}


def find_latest_stl(folder: Path) -> Path | None:
    if not folder.exists():
        return None
    stl_files = list(folder.rglob("*.stl"))
    if not stl_files:
        return None
    stl_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return stl_files[0]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ATH Waveguide Designer Pro")
        self.resize(1600, 950)
        self.setStyleSheet(MODERN_DARK_THEME)

        self.osse_entries = {}
        self.tritonia_entries = {}

        self.last_cfg_path = None
        self.last_output_dir = None
        self.last_stl_path = None

        self._build_ui()
        self._reset_viewer_placeholder()
        self.statusBar().showMessage("就緒 (Ready)")

    def _build_ui(self):
        self.plotter = QtInteractor(self)
        self.plotter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCentralWidget(self.plotter)

        toolbar = QToolBar("主要工具列")
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        action_open_cfg = toolbar.addAction("📂 開啟 CFG 目錄")
        action_open_horns = toolbar.addAction("📁 開啟 D:\\Horns")
        action_open_out = toolbar.addAction("🚀 開啟最新輸出")
        toolbar.addSeparator()
        action_load_stl = toolbar.addAction("📥 手動載入 STL")
        action_reset_view = toolbar.addAction("👁️ 重設視角")

        action_open_cfg.triggered.connect(self.open_generated_cfg_folder)
        action_open_horns.triggered.connect(self.open_ath_output_root)
        action_open_out.triggered.connect(self.open_last_output_folder)
        action_load_stl.triggered.connect(self.load_stl_manually)
        action_reset_view.triggered.connect(self._reset_camera)

        dock_controls = QDockWidget("設計參數與控制", self)
        dock_controls.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock_controls.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )

        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setFrameShape(QFrame.NoFrame)

        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(10, 10, 10, 10)

        # ===== 模式選擇 =====
        mode_group = QGroupBox("設計模式")
        mode_layout = QFormLayout(mode_group)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["OS-SE", "Tritonia"])
        mode_layout.addRow(QLabel("波導類型"), self.mode_combo)

        controls_layout.addWidget(mode_group)

        # ===== 參數堆疊區 =====
        self.param_stack = QStackedWidget()

        osse_page = self.build_param_page(OSSE_GROUPS, self.osse_entries)
        tritonia_page = self.build_param_page(TRITONIA_GROUPS, self.tritonia_entries)

        self.param_stack.addWidget(osse_page)
        self.param_stack.addWidget(tritonia_page)

        controls_layout.addWidget(self.param_stack)

        action_group = QGroupBox("核心操作")
        action_layout = QVBoxLayout(action_group)

        self.btn_run = QPushButton("⚡ 生成並執行 ATH")
        self.btn_run.setObjectName("btnRun")
        self.btn_cfg_only = QPushButton("📄 僅生成 CFG 檔案")

        action_layout.addWidget(self.btn_run)
        action_layout.addWidget(self.btn_cfg_only)
        controls_layout.addWidget(action_group)

        path_group = QGroupBox("目前作用環境")
        path_layout = QFormLayout(path_group)

        self.cfg_path_edit = QLineEdit("-")
        self.output_path_edit = QLineEdit("-")
        self.cfg_path_edit.setReadOnly(True)
        self.output_path_edit.setReadOnly(True)

        path_layout.addRow("CFG:", self.cfg_path_edit)
        path_layout.addRow("OUT:", self.output_path_edit)
        controls_layout.addWidget(path_group)

        controls_layout.addStretch()
        controls_scroll.setWidget(controls_widget)
        dock_controls.setWidget(controls_scroll)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_controls)

        dock_log = QDockWidget("系統輸出日誌", self)
        dock_log.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)

        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)

        btn_clear_log = QPushButton("清除日誌")
        btn_clear_log.clicked.connect(self.clear_log)

        btn_layout = QGridLayout()
        btn_layout.addWidget(btn_clear_log, 0, 0, alignment=Qt.AlignRight)

        log_layout.addWidget(self.log_text)
        log_layout.addLayout(btn_layout)
        dock_log.setWidget(log_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock_log)

        self.btn_run.clicked.connect(self.on_run)
        self.btn_cfg_only.clicked.connect(self.on_generate_only)
        self.mode_combo.currentIndexChanged.connect(self.param_stack.setCurrentIndex)

        self.setStatusBar(QStatusBar(self))

    def build_param_page(self, groups: dict, entry_store: dict) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        for group_name, params in groups.items():
            group_box = QGroupBox(group_name)
            form = QFormLayout(group_box)
            form.setLabelAlignment(Qt.AlignRight)

            for key, label, default, field_type in params:
                if field_type == "float":
                    widget = QDoubleSpinBox()
                    widget.setRange(-999999.0, 999999.0)
                    widget.setDecimals(6)
                    widget.setValue(float(default))
                    widget.setSingleStep(0.1)
                elif field_type == "int":
                    widget = QSpinBox()
                    widget.setRange(-999999, 999999)
                    widget.setValue(int(default))
                    widget.setSingleStep(1)
                else:
                    widget = QLineEdit(str(default))

                widget.setMinimumWidth(140)
                entry_store[key] = widget
                form.addRow(QLabel(label), widget)

            layout.addWidget(group_box)

        layout.addStretch()
        return page

    def current_mode(self) -> str:
        return self.mode_combo.currentText()

    def log(self, text: str):
        self.log_text.append(text)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        QApplication.processEvents()

    def clear_log(self):
        self.log_text.clear()

    def collect_params(self) -> dict:
        mode = self.current_mode()
        params = {}

        entries = self.osse_entries if mode == "OS-SE" else self.tritonia_entries

        for key, widget in entries.items():
            if isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                params[key] = widget.value()
            else:
                params[key] = widget.text().strip()

        return params

    def set_last_cfg(self, path: Path | None):
        self.last_cfg_path = Path(path) if path else None
        self.cfg_path_edit.setText(str(path) if path else "-")

    def set_last_output(self, path: Path | None):
        self.last_output_dir = Path(path) if path else None
        self.output_path_edit.setText(str(path) if path else "-")

    def set_last_stl(self, path: Path | None):
        self.last_stl_path = Path(path) if path else None

    def parse_output_dir(self, stdout: str) -> Path | None:
        match = re.search(r"-destination directory:\s*(.+)", stdout)
        if match:
            return Path(match.group(1).strip())
        return None

    def open_folder(self, path: Path):
        if not path.exists():
            QMessageBox.warning(self, "警告", f"資料夾不存在：\n{path}")
            return
        os.startfile(str(path))

    def open_generated_cfg_folder(self):
        self.open_folder(GENERATED_CFG_DIR)

    def open_ath_output_root(self):
        self.open_folder(ATH_OUTPUT_ROOT)

    def open_last_output_folder(self):
        if self.last_output_dir is None:
            QMessageBox.information(self, "資訊", "目前尚未有可開啟的輸出資料夾。")
            return
        self.open_folder(self.last_output_dir)

    def _reset_viewer_placeholder(self):
        self.plotter.clear()
        self.plotter.set_background(color="#1e1e1e", top="#3a3a3a")
        self.plotter.add_text(
            "Ready for Simulation.\nNo STL loaded.",
            position="upper_left",
            font_size=12,
            color="#a0a0a0"
        )
        self.plotter.show_grid(color="#555555")
        self.plotter.render()

    def _reset_camera(self):
        try:
            self.plotter.reset_camera()
            self.plotter.render()
        except Exception:
            pass

    def show_stl_embedded(self, stl_path: Path):
        if not stl_path.exists():
            raise FileNotFoundError(f"找不到 STL：{stl_path}")

        self.statusBar().showMessage("正在載入 3D 模型...")
        mesh = pv.read(str(stl_path))

        self.plotter.clear()
        self.plotter.set_background(color="#1e1e1e", top="#3a3a3a")

        try:
            self.plotter.add_mesh(
                mesh,
                show_edges=True,
                edge_color="#333333",
                color="#e0e0e0",
                specular=0.5,
                pbr=True,
                metallic=0.2,
                roughness=0.5
            )
        except Exception:
            self.plotter.add_mesh(
                mesh,
                show_edges=True,
                edge_color="#333333",
                color="#e0e0e0",
                specular=0.5
            )

        self.plotter.add_axes()
        self.plotter.show_grid(color="#555555")
        self.plotter.reset_camera()
        self.plotter.render()
        self.statusBar().showMessage(f"模型已載入：{stl_path.name}")

    def load_stl_manually(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇 STL 檔案",
            str(ATH_OUTPUT_ROOT),
            "STL Files (*.stl)"
        )

        if not file_path:
            return

        stl_path = Path(file_path)
        self.set_last_stl(stl_path)

        try:
            self.show_stl_embedded(stl_path)
            self.log(f"[INFO] 已手動載入 STL：{stl_path}")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", str(e))
            self.log(f"[ERROR] {e}")
            self.statusBar().showMessage("手動載入 STL 失敗")

    def on_generate_only(self):
        try:
            mode = self.current_mode()
            self.statusBar().showMessage(f"生成 {mode} CFG 中...")
            params = self.collect_params()
            cfg_path = generate_cfg(mode, params)
            self.set_last_cfg(cfg_path)

            self.log("=" * 72)
            self.log(f"[OK] {mode} CFG 生成成功")
            self.log(f"[INFO] CFG 檔案：{cfg_path}")

            QMessageBox.information(self, "成功", f"{mode} CFG 已生成：\n{cfg_path}")
            self.statusBar().showMessage("CFG 生成成功")

        except Exception as e:
            QMessageBox.critical(self, "錯誤", str(e))
            self.log(f"[ERROR] {e}")
            self.statusBar().showMessage("生成失敗")

    def on_run(self):
        try:
            mode = self.current_mode()
            self.statusBar().showMessage(f"{mode} 運行中...")
            params = self.collect_params()

            self.log("=" * 72)
            self.log(f"[INFO] 模式：{mode}")
            self.log("[INFO] 收集參數並生成配置...")
            QApplication.processEvents()

            cfg_path = generate_cfg(mode, params)
            self.set_last_cfg(cfg_path)
            self.set_last_stl(None)

            self.log(f"[INFO] CFG 檔案：{cfg_path}")
            self.log("[INFO] 執行 ATH 模擬器中...")
            QApplication.processEvents()

            result = run_ath(cfg_path)

            output_dir = self.parse_output_dir(result["stdout"])
            self.set_last_output(output_dir)

            self.log("---------- STDOUT ----------")
            self.log(result["stdout"] if result["stdout"] else "(no stdout)")

            if result["stderr"]:
                self.log("---------- STDERR ----------")
                self.log(result["stderr"])

            self.log(f"[INFO] 程序結束，回傳碼：{result['returncode']}")

            if output_dir is not None:
                self.log(f"[INFO] 輸出資料夾：{output_dir}")
            else:
                self.log("[INFO] 無法解析輸出資料夾")

            if result["returncode"] == 0:
                stl_path = None
                if output_dir is not None and output_dir.exists():
                    stl_path = find_latest_stl(output_dir)

                self.set_last_stl(stl_path)

                if stl_path is not None:
                    self.log(f"[INFO] 找到最新 STL：{stl_path}")
                    self.show_stl_embedded(stl_path)
                    self.statusBar().showMessage("計算完成，模型已更新")
                else:
                    self.log("[WARNING] 執行成功但找不到 STL 檔案")
                    self._reset_viewer_placeholder()
                    self.statusBar().showMessage("完成但未產生 STL")

                QMessageBox.information(self, "成功", f"{mode} 執行完成")
            else:
                QMessageBox.warning(
                    self,
                    "警告",
                    "ATH 執行異常 (回傳碼非 0)，請檢查日誌面板。"
                )
                self.statusBar().showMessage("執行發生錯誤")

        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"執行時發生例外情況：\n{e}")
            self.log(f"[ERROR] {e}")
            self.statusBar().showMessage("執行中斷")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()