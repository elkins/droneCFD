"""
Utility functions and classes for droneCFD case setup and management.

This module provides utilities for:
- Setting up OpenFOAM case directories from templates
- Managing geometry files
- Detecting and utilizing parallel processing capabilities

Classes:
    caseSetup: Manages OpenFOAM case directory setup.
    parallelUtilities: Manages parallel processing configuration.
"""

##########################################################################################
##  _______  .______        ______   .__   __.  _______      ______  _______  _______   ##
## |       \ |   _  \      /  __  \  |  \ |  | |   ____|    /      ||   ____||       \  ##
## |  .--.  ||  |_)  |    |  |  |  | |   \|  | |  |__      |  ,----'|  |__   |  .--.  | ##
## |  |  |  ||      /     |  |  |  | |  . `  | |   __|     |  |     |   __|  |  |  |  | ##
## |  '--'  ||  |\  \----.|  `--'  | |  |\   | |  |____    |  `----.|  |     |  '--'  | ##
## |_______/ | _| `._____| \______/  |__| \__| |_______|    \______||__|     |_______/  ##
##                                                                                      ##
##########################################################################################

__author__ = 'chrispaulson'

import shutil
import os
from pathlib import Path
from typing import Optional
import multiprocessing
from . import stlTools


class caseSetup:
    """
    Manages OpenFOAM case directory setup.

    This class handles:
    - Creating case directories from templates
    - Setting up geometry files
    - Organizing the OpenFOAM directory structure

    Attributes:
        dir: Absolute path to the case directory.
        templatePath: Path to the template directory.
        stlPath: Path to the STL geometry file in the case.
        triSurface: Relative path to triSurface directory.
        system: Relative path to system directory.
        polyMesh: Relative path to polyMesh directory.
    """

    def __init__(
        self,
        folderPath: str | Path,
        geometryPath: Optional[str | Path] = None,
        templatePath: Optional[str | Path] = None,
        parserArgs=None
    ) -> None:
        """
        Initialize case setup and create directory structure.

        Args:
            folderPath: Path where the case directory should be created.
            geometryPath: Path to the STL geometry file (optional).
            templatePath: Path to the OpenFOAM case template (optional).
            parserArgs: Command-line parser arguments (optional).

        Raises:
            ValueError: If folderPath is None.
            FileNotFoundError: If template or geometry paths don't exist.
        """
        # Check if arguments come from command-line parser
        if parserArgs and hasattr(parserArgs, 'geometryPath'):
            geometryPath = parserArgs.geometryPath

        # Validate folder path
        if folderPath is None:
            raise ValueError('Please specify a folder path')

        # Set template path
        if templatePath is None:
            self.templatePath = Path(__file__).parent / 'data' / 'template'
            print(f'Template File Path: {self.templatePath}')
        else:
            self.templatePath = Path(templatePath)

        # Set default geometry if not provided
        if geometryPath is None:
            geometryPath = Path(__file__).parent / 'data' / 'geometries' / 'benchmarkAircraft.stl'

        # Setup case directory (remove if exists)
        self.dir = Path(folderPath).absolute()
        if self.dir.is_dir():
            print(f'Warning: Removing existing directory: {self.dir}')
            shutil.rmtree(self.dir)

        # Define useful directory paths
        self.triSurface = Path('constant') / 'triSurface'
        self.system = Path('system')
        self.polyMesh = Path('polyMesh')

        # Copy template directory
        self.copyTemplate(self.templatePath)

        # Set geometry if supplied
        if geometryPath:
            self.geometryPath = Path(geometryPath).absolute()
            self.setGeometry(self.geometryPath)


    def copyTemplate(self, path: Path) -> None:
        """
        Copy the OpenFOAM case template to the case directory.

        Args:
            path: Path to the template directory.

        Raises:
            FileNotFoundError: If template path doesn't exist.
            ValueError: If template structure is invalid.
        """
        if not path.is_dir():
            raise FileNotFoundError(
                f'Template path {path} is missing. Please check the location.'
            )

        # Validate template structure
        tri_surface_path = path / self.triSurface
        system_path = path / self.system
        if not (tri_surface_path.is_dir() or system_path.is_dir()):
            raise ValueError(
                'Template is not of the correct form. Must contain constant/triSurface and system directories.'
            )

        # Copy template directory
        shutil.copytree(path, self.dir)
        print(f'Copied template from {path} to {self.dir}')

    def setGeometry(self, path: Path) -> None:
        """
        Set and validate the geometry file for the case.

        Args:
            path: Path to the STL geometry file.

        Raises:
            FileNotFoundError: If geometry file doesn't exist.
            ValueError: If STL file is invalid.
        """
        self.geo_base_path = path

        # Validate file exists
        if not path.is_file():
            raise FileNotFoundError(f'Geometry file missing: {path}')

        # Validate STL file by attempting to load it
        try:
            stl_file = stlTools.solidSTL(self.geo_base_path)
        except Exception as e:
            raise ValueError(
                f'droneCFD encountered an error with the STL file: {e}'
            ) from e

        # Set the standard STL path for OpenFOAM template
        self.stlPath = self.dir / self.triSurface / 'Aircraft.stl'
        print(f'Geometry set to: {self.stlPath}')


class parallelUtilities:
    """
    Manages parallel processing configuration for CFD simulations.

    This class detects available CPU cores and configures the number
    of processes to use for parallel OpenFOAM simulations.

    Attributes:
        procs: Number of processor cores to use.
    """

    def __init__(self, procs: Optional[int] = None) -> None:
        """
        Initialize parallel utilities with processor count.

        Args:
            procs: Number of processors to use. If None, uses all available cores.

        Raises:
            ValueError: If procs is less than 1.
        """
        if procs is None:
            print('Evaluating computation hardware')
            self.procs = multiprocessing.cpu_count()
        else:
            if procs < 1:
                raise ValueError('Number of processors must be at least 1')

            print('Running on user specified number of processors')
            self.procs = procs

            available_cores = multiprocessing.cpu_count()
            if self.procs > available_cores:
                print(
                    f'Warning: Requested {self.procs} cores, but only '
                    f'{available_cores} available'
                )

        print(f"Using {self.procs} processors for computation")


if __name__ == '__main__':
    # Example usage
    print("Testing parallelUtilities:")
    a = parallelUtilities()
    b = parallelUtilities(procs=1)
    c = parallelUtilities(procs=2)
    d = parallelUtilities(procs=4)

    print("\nTesting caseSetup:")
    # u = caseSetup(folderPath='test', geometryPath='../test_dir/benchmarkAircraft.stl')
