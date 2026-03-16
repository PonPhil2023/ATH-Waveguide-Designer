from pathlib import Path
import pyvista as pv


def find_latest_stl(folder: Path) -> Path | None:
    if not folder.exists():
        return None

    stl_files = list(folder.rglob("*.stl"))
    if not stl_files:
        return None

    stl_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return stl_files[0]


def show_stl(stl_path: Path):
    if not stl_path.exists():
        raise FileNotFoundError(f"找不到 STL：{stl_path}")

    mesh = pv.read(str(stl_path))

    plotter = pv.Plotter()

    plotter.add_mesh(mesh, show_edges=True)

    plotter.add_axes()
    plotter.show_grid()

    plotter.show()