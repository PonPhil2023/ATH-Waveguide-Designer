from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import scipy.sparse.linalg


@dataclass
class BemAnalysisResult:
    frequencies_hz: np.ndarray
    angles_deg: np.ndarray
    horizontal_spl_db: np.ndarray
    vertical_spl_db: np.ndarray
    axial_spl_db: np.ndarray
    mesh_path: Path


def find_bem_mesh(folder: Path) -> Path | None:
    if not folder.exists():
        return None
    meshes = sorted(folder.rglob("*.msh"), key=lambda path: path.stat().st_mtime, reverse=True)
    return meshes[0] if meshes else None


@lru_cache(maxsize=4)
def _load_grid_cached(mesh_path_text: str, modified_ns: int):
    try:
        import bempp_cl.api as bempp
        import meshio
    except ImportError as exc:
        raise RuntimeError(
            "BEM analysis requires bempp-cl, meshio, and gmsh. "
            "Run: python -m pip install bempp-cl meshio gmsh"
        ) from exc

    mesh_path = Path(mesh_path_text)
    mesh = meshio.read(mesh_path)
    triangles = mesh.cells_dict.get("triangle")
    if triangles is None:
        raise ValueError(f"Mesh does not contain triangle cells: {mesh_path}")

    physical_tags = mesh.cell_data_dict.get("gmsh:physical", {}).get("triangle")
    if physical_tags is None:
        physical_tags = np.zeros(len(triangles), dtype=np.uint32)

    vertices_m = mesh.points[:, :3].T / 1000.0
    elements = triangles.T.astype(np.uint32)
    domain_indices = physical_tags.astype(np.uint32)
    return bempp, bempp.Grid(vertices_m, elements, domain_indices=domain_indices)


def _load_grid(mesh_path: Path):
    stat = mesh_path.stat()
    return _load_grid_cached(str(mesh_path.resolve()), stat.st_mtime_ns)


def _sampling_points(radius_m: float, angles_rad: np.ndarray, plane: str) -> np.ndarray:
    if plane == "horizontal":
        return np.vstack(
            (
                radius_m * np.sin(angles_rad),
                np.zeros_like(angles_rad),
                radius_m * np.cos(angles_rad),
            )
        )
    if plane == "vertical":
        return np.vstack(
            (
                np.zeros_like(angles_rad),
                radius_m * np.sin(angles_rad),
                radius_m * np.cos(angles_rad),
            )
        )
    raise ValueError(f"Unknown plane: {plane}")


def _solve_gmres(operator, rhs, tol: float = 1e-5, maxiter: int = 300, initial_guess=None):
    weak_form = operator.weak_form()
    rhs_vector = rhs.projections(operator.dual_to_range)
    gmres_kwargs = {"restart": None, "maxiter": maxiter}

    # SciPy changed gmres from `tol` to `rtol`; support both without forcing
    # the user's Python environment to upgrade.
    if "rtol" in scipy.sparse.linalg.gmres.__code__.co_varnames:
        gmres_kwargs["rtol"] = tol
    else:
        gmres_kwargs["tol"] = tol
    if initial_guess is not None:
        gmres_kwargs["x0"] = initial_guess

    coefficients, info = scipy.sparse.linalg.gmres(weak_form, rhs_vector, **gmres_kwargs)
    return coefficients.ravel(), info


def run_bem_analysis(
    mesh_path: Path,
    frequencies_hz: np.ndarray,
    distance_m: float = 2.0,
    angle_count: int = 361,
    sound_speed_m_s: float = 343.0,
    air_density_kg_m3: float = 1.204,
    driver_domain_index: int = 2,
    driver_velocity_m_s: float = 1.0,
    solver_tolerance: float = 1e-5,
) -> BemAnalysisResult:
    bempp, grid = _load_grid(mesh_path)
    frequencies_hz = np.asarray(frequencies_hz, dtype=float)
    angles_deg = np.linspace(-180.0, 180.0, angle_count)
    angles_rad = np.deg2rad(angles_deg)

    horizontal_points = _sampling_points(distance_m, angles_rad, "horizontal")
    vertical_points = _sampling_points(distance_m, angles_rad, "vertical")
    axial_point = np.array([[0.0], [0.0], [distance_m]])
    all_observation_points = np.hstack((horizontal_points, vertical_points, axial_point))

    space = bempp.function_space(grid, "DP", 0)
    identity = bempp.operators.boundary.sparse.identity(space, space, space)

    horizontal_rows = []
    vertical_rows = []
    axial_values = []
    previous_coefficients = None

    for frequency_hz in frequencies_hz:
        omega = 2.0 * np.pi * frequency_hz
        wavenumber = omega / sound_speed_m_s

        @bempp.complex_callable
        def neumann_data(x, normal, domain_index, result):
            result[0] = (
                -1j * omega * air_density_kg_m3 * driver_velocity_m_s
                if domain_index == driver_domain_index
                else 0.0j
            )

        rhs = bempp.GridFunction(space, fun=neumann_data)
        adjoint_double_layer = bempp.operators.boundary.helmholtz.adjoint_double_layer(
            space,
            space,
            space,
            wavenumber,
        )
        lhs = 0.5 * identity + adjoint_double_layer
        coefficients, info = _solve_gmres(
            lhs,
            rhs,
            tol=solver_tolerance,
            maxiter=300,
            initial_guess=previous_coefficients,
        )
        if info != 0:
            raise RuntimeError(f"GMRES did not converge at {frequency_hz:.1f} Hz (info={info}).")
        density = bempp.GridFunction(space, coefficients=coefficients)
        previous_coefficients = coefficients

        field_operator = bempp.operators.potential.helmholtz.single_layer(
            space,
            all_observation_points,
            wavenumber,
        )
        field_values = field_operator.evaluate(density).ravel()
        horizontal_rows.append(field_values[:angle_count])
        vertical_rows.append(field_values[angle_count : 2 * angle_count])
        axial_values.append(field_values[-1])

    horizontal_pressure = np.vstack(horizontal_rows)
    vertical_pressure = np.vstack(vertical_rows)
    axial_pressure = np.asarray(axial_values)
    reference_pressure = 20e-6

    horizontal_spl = 20.0 * np.log10(np.maximum(np.abs(horizontal_pressure), 1e-12) / reference_pressure)
    vertical_spl = 20.0 * np.log10(np.maximum(np.abs(vertical_pressure), 1e-12) / reference_pressure)
    axial_spl = 20.0 * np.log10(np.maximum(np.abs(axial_pressure), 1e-12) / reference_pressure)

    return BemAnalysisResult(
        frequencies_hz=frequencies_hz,
        angles_deg=angles_deg,
        horizontal_spl_db=horizontal_spl - axial_spl[:, None],
        vertical_spl_db=vertical_spl - axial_spl[:, None],
        axial_spl_db=axial_spl,
        mesh_path=mesh_path,
    )
