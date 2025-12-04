# droneCFD

A modern Python package for running CFD simulations of drone aircraft using OpenFOAM.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPL--2.0--or--later-green.svg)](LICENSE)

## Overview

droneCFD is a comprehensive Python toolkit that simplifies the process of running computational fluid dynamics (CFD) simulations for drone and UAV aircraft. It provides a high-level interface to OpenFOAM, automating the workflow from geometry preparation through mesh generation, solving, and post-processing.

## Features

- **Modern Python 3.9-3.12+ Support** - Fully updated with type hints, pathlib, and modern Python idioms
- **Automated Workflow** - Complete CFD pipeline from STL geometry to results visualization
- **STL Geometry Manipulation** - Load, rotate, scale, and transform aircraft geometries
- **Intelligent Meshing** - Automated blockMesh and snappyHexMesh configuration
- **Parallel Processing** - Built-in support for multi-core simulation execution
- **Post-Processing** - Extract forces, moments, and generate performance reports
- **Visualization** - Create publication-quality plots with matplotlib
- **Error Handling** - Robust error checking and informative error messages

## Requirements

- Python 3.9 or higher
- OpenFOAM (tested with OpenFOAM v2006 and later)
- Required Python packages (automatically installed):
  - numpy >= 1.26.0
  - numpy-stl >= 3.1.0
  - PyFoam >= 2022.9
  - matplotlib >= 3.8.0
  - XlsxWriter >= 3.1.9

## Installation

### Using pip (recommended)

```bash
pip install -e .
```

### Using pip with development dependencies

```bash
pip install -e ".[dev]"
```

### From source

```bash
git clone https://github.com/dronecfd/droneCFD.git
cd droneCFD
python -m pip install -e .
```

## Quick Start

### Single Simulation

```python
from droneCFD import Utilities, stlTools, Meshing, Solver, Visualization

# Setup case directory
case = Utilities.caseSetup('my_simulation')

# Load and configure geometry
model = stlTools.solidSTL(case.stlPath)
model.setaoa(5.0, units='degrees')  # Set 5° angle of attack
model.save(case.stlPath)

# Generate mesh
mesh = Meshing.mesher(case.dir, model)
mesh.blockMesh()
mesh.snappyHexMesh()

# Run simulation
solver = Solver.solver(case.dir)

# Visualize results
viz = Visualization.ResultsVisualizer(case.dir)
viz.load_forces()
viz.plot_forces_history(save_path='forces.png')
```

### Angle of Attack Sweep

```python
from droneCFD import Utilities, stlTools, Meshing, Solver, Visualization

aoa_range = [-6, -4, -2, 0, 2, 4, 6, 8, 10]
lift_values = []
drag_values = []

for aoa in aoa_range:
    case = Utilities.caseSetup(f'sweep/test_{aoa}')
    model = stlTools.solidSTL(case.stlPath)
    model.setaoa(aoa, units='degrees')
    model.save(case.stlPath)

    mesh = Meshing.mesher(case.dir, model)
    mesh.blockMesh()
    mesh.snappyHexMesh()

    solver = Solver.solver(case.dir)

    # Extract converged forces
    viz = Visualization.ResultsVisualizer(case.dir)
    forces = viz.load_forces()
    lift_values.append(forces[-15:, 3].mean())  # Average last 15 iterations
    drag_values.append(forces[-15:, 1].mean())

# Plot results
Visualization.plot_aoa_sweep(aoa_range, lift_values, drag_values)
Visualization.plot_drag_polar(lift_values, drag_values, aoa_list=aoa_range)
```

## Module Documentation

### droneCFD.Utilities

Case setup and parallel processing utilities.

- **caseSetup**: Creates OpenFOAM case directories from templates
- **parallelUtilities**: Manages CPU core detection and allocation

### droneCFD.stlTools

STL geometry manipulation.

- **solidSTL**: Load, transform, and save STL meshes
  - `setaoa()`: Set angle of attack
  - `rotate()`: Apply Euler rotations
  - `scale()`: Scale geometry
  - `translate()`: Translate geometry
  - `centerGeometry()`: Center at origin

### droneCFD.Meshing

Mesh generation interface.

- **mesher**: Generates computational meshes
  - `blockMesh()`: Create base domain
  - `snappyHexMesh()`: Refine around geometry
  - `previewMesh()`: Open in ParaView

### droneCFD.Solver

OpenFOAM solver execution.

- **solver**: Runs CFD simulations
  - Automatic decomposition for parallel runs
  - Executes potentialFoam + simpleFoam
  - Reconstructs parallel results

### droneCFD.PostProcessing

Results extraction and Excel report generation.

- **PostProcessing**: Generates comprehensive Excel reports with charts

### droneCFD.Visualization

Modern visualization tools.

- **ResultsVisualizer**: Create publication-quality plots
  - `plot_forces_history()`: Force vs time
  - `plot_force_components()`: Pressure vs viscous forces
  - `plot_aoa_sweep()`: Lift and drag curves
  - `plot_drag_polar()`: L vs D polar diagram

## Examples

See the `examples/` directory for complete working examples:

- `single_run_example.py` - Single simulation workflow
- `aoa_sweep.py` - Parametric angle of attack study

## Visualizing Results

### Using ParaView

```python
mesh.previewMesh()  # Opens ParaView with the case
```

### Using matplotlib (New!)

```python
from droneCFD.Visualization import ResultsVisualizer

viz = ResultsVisualizer('path/to/case')
viz.load_forces()

# Generate plots
viz.plot_forces_history(save_path='forces_history.png')
viz.plot_force_components(save_path='force_breakdown.png')
```

### Results Include:
- Force history plots (lift and drag vs time)
- Force component breakdown (pressure vs viscous)
- Convergence monitoring
- Angle of attack performance curves
- Drag polar diagrams

## Configuration

The package uses OpenFOAM templates stored in `droneCFD/data/template/`. These include:
- blockMeshDict - Base domain definition
- snappyHexMeshDict - Refinement configuration
- controlDict - Solver settings
- fvSchemes - Numerical schemes
- fvSolution - Linear solver settings

## Troubleshooting

### OpenFOAM not found
Ensure OpenFOAM is properly sourced:
```bash
source /opt/openfoam/etc/bashrc
```

### ParaView not opening
Install ParaView and ensure it's in your PATH:
```bash
which paraview
```

### Import errors
Ensure all dependencies are installed:
```bash
pip install -e ".[dev]"
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is licensed under the GNU General Public License v2.0 or later - see the [LICENSE](LICENSE) file for details.

## Authors

- Chris Paulson - Original author
- Contributors - Modernization and enhancements

## Acknowledgments

- OpenFOAM community
- PyFoam project
- numpy-stl library
- Force parsing code adapted from protarius on cfd-online.com

## Citation

If you use droneCFD in your research, please cite:

```
@software{droneCFD,
  title = {droneCFD: A Python Interface for Drone CFD Simulations},
  author = {Paulson, Chris and Contributors},
  year = {2024},
  url = {http://www.dronecfd.com}
}
```
