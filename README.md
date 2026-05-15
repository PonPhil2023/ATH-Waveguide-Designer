# ATH Waveguide Designer

ATH Waveguide Designer is a Windows desktop GUI for designing acoustic waveguides with ATH and reviewing basic BEM results in the same workflow.

The project keeps the original ATH-based design workflow and adds:

- graphical editing for OS-SE, Tritonia, and Tritonia-M waveguides
- automatic ATH configuration generation
- one-click ATH execution
- embedded STL preview
- Bempp-cl based BEM analysis from ATH-generated Gmsh meshes
- horizontal and vertical directivity maps
- axial SPL plotting

## Requirements

- Windows
- Python 3.10 or newer when running from source
- ATH installed separately
- Python packages listed in `requirements.txt`

ATH itself is developed by Marcel Batik and is not bundled with this repository. Download and install ATH from the official ATH website before using this GUI:

- ATH website: https://www.at-horns.eu/index.html

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/PonPhil2023/ATH-Waveguide-Designer.git
cd ATH-Waveguide-Designer
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure ATH paths

The GUI reads these optional environment variables:

```powershell
$env:ATH_EXE_PATH="D:\ATH\ath.exe"
$env:ATH_CFG_PATH="D:\ATH\ath.cfg"
$env:ATH_OUTPUT_ROOT="D:\Horns"
```

If they are not set, the program uses these defaults:

```text
D:\ATH_GUI\ath.exe
D:\ATH_GUI\ath.cfg
D:\Horns
```

You can also edit `config.py` directly if you prefer a fixed local configuration.

## Running the GUI

From source:

```powershell
python main.py
```

If you use a packaged build, open the generated executable in `dist`.

## Workflow

1. Select a waveguide family:
   - OS-SE
   - Tritonia
   - Tritonia-M
2. Adjust geometry and mesh parameters in the left panel.
3. Click the ATH run button to:
   - generate an ATH config
   - run ATH
   - create STL and ABEC/BEM-related project files
4. Inspect the generated STL in the embedded 3D viewer.
5. In the Bempp-cl section:
   - use the latest generated `.msh` mesh or choose one manually
   - choose frequency range, frequency count, angle count, distance, and solve quality
   - run BEM analysis
6. Review:
   - horizontal directivity map
   - vertical directivity map
   - axial SPL curve

## Main Features

### ATH design features

- OS-SE, Tritonia, and Tritonia-M parameter editors
- generated ATH config files
- direct ATH execution from the GUI
- embedded STL loading and viewing
- output-folder shortcuts

### BEM analysis features

- Bempp-cl Helmholtz BEM workflow
- import of ATH-generated Gmsh `.msh` files
- support for ATH driver physical group tagging
- horizontal directivity map
- vertical directivity map
- axial SPL plot
- angle coverage from `-180` to `+180` degrees
- logarithmic frequency axis
- quality presets:
  - Fast
  - Standard
  - High precision
- repeated-run acceleration through mesh caching and warm-started GMRES

## Generated Outputs

Depending on the selected ATH mode and settings, the workflow can produce:

- generated ATH configuration files under `generated_cfg/`
- ATH output folders under the configured output root
- STL geometry files for CAD, printing, or inspection
- Gmsh `.msh` meshes for BEM analysis
- ATH/ABEC project-support files such as:
  - `Project.abec`
  - `solving.txt`
  - `observation.txt`
- GUI-rendered BEM plots:
  - horizontal directivity map
  - vertical directivity map
  - axial SPL curve

Generated artifacts are intentionally excluded from Git by default so the repository stays lightweight.

## Project Structure

```text
ATH-Waveguide-Designer/
|-- main.py              # PySide6 desktop GUI
|-- gui.py               # older Tkinter GUI retained from the original project
|-- cfg_generator.py     # ATH config generation
|-- ath_runner.py        # ATH process execution
|-- bem_solver.py        # Bempp-cl BEM workflow
|-- stl_viewer.py        # STL helper utilities
|-- config.py            # local path configuration
|-- templates/           # config templates
`-- README.md
```

## Notes on ATH

This project is a GUI frontend and analysis companion for ATH. It does not replace ATH and does not redistribute ATH itself. Users must obtain ATH separately and comply with ATH licensing terms.

## License and Credits

- ATH / Athena: Marcel Batik
- ATH website: https://www.at-horns.eu/index.html
- This GUI project: independent workflow tooling built around ATH

ATH itself is distributed under its own license. Review the ATH license before using generated models commercially or redistributing ATH-related files.
