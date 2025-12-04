##########################################################################################
##  _______  .______        ______   .__   __.  _______      ______  _______  _______   ##
## |       \ |   _  \      /  __  \  |  \ |  | |   ____|    /      ||   ____||       \  ##
## |  .--.  ||  |_)  |    |  |  |  | |   \|  | |  |__      |  ,----'|  |__   |  .--.  | ##
## |  |  |  ||      /     |  |  |  | |  . `  | |   __|     |  |     |   __|  |  |  |  | ##
## |  '--'  ||  |\  \----.|  `--'  | |  |\   | |  |____    |  `----.|  |     |  '--'  | ##
## |_______/ | _| `._____| \______/  |__| \__| |_______|    \______||__|     |_______/  ##
##                                                                                      ##
##########################################################################################

"""
Solver module for droneCFD.

This module handles running OpenFOAM solvers (potentialFoam and simpleFoam)
for CFD simulations, with support for parallel processing.

Classes:
    solver: Manages OpenFOAM solver execution.
"""

__author__ = 'chrispaulson'

import os
import shutil
import glob
from pathlib import Path
from typing import Optional
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
from PyFoam.Applications.Runner import Runner
from PyFoam.Applications.PlotRunner import PlotRunner
from . import Utilities


class solver:
    """
    Manages OpenFOAM solver execution for CFD simulations.

    This class configures and runs OpenFOAM solvers including potentialFoam
    for initialization and simpleFoam for steady-state RANS simulations.

    Attributes:
        casePath: Path to the OpenFOAM case directory.
        parallel: Whether to use parallel processing.
        nprocs: Number of processors to use.
    """

    def __init__(
        self,
        casedir: str | Path,
        nprocs: Optional[int] = None,
        parserArgs=None
    ) -> None:
        """
        Initialize the solver and run the simulation.

        Args:
            casedir: Path to the OpenFOAM case directory.
            nprocs: Number of processors for parallel processing (optional).
            parserArgs: Command-line parser arguments (optional).
        """
        self.casePath = Path(casedir)
        self.procsUtil = Utilities.parallelUtilities(nprocs)
        self.decomposeParDict = ParsedParameterFile(
            str(self.casePath / 'system' / 'decomposeParDict')
        )

        if parserArgs:
            self.modifyDicts(parserArgs)

        if self.procsUtil.procs > 1:
            self.parallel = True
            self.nprocs = self.procsUtil.procs
            print(f'Using {self.nprocs} processors based on procsUtil')
            self.decomposeParDict['numberOfSubdomains'] = self.nprocs
            self.decomposeParDict.writeFile()
        else:
            self.parallel = False
            self.nprocs = 1
        # Run the solver
        if self.parallel:
            # Clean up any existing processor directories
            for file in glob.glob(str(self.casePath / 'processor*')):
                shutil.rmtree(file)

            # Decompose the case for parallel processing
            Runner(args=["decomposePar", "-case", str(self.casePath)])

            # Run potentialFoam for initialization
            Runner(args=[
                f"--proc={self.nprocs}",
                "potentialFoam",
                "-case", str(self.casePath),
                "-noFunctionObjects"
            ])

            # Run simpleFoam for the main simulation
            Runner(args=[
                f"--proc={self.nprocs}",
                "simpleFoam",
                "-case", str(self.casePath)
            ])

            # Reconstruct the parallel mesh and solution
            Runner(args=[
                "reconstructParMesh",
                "-mergeTol", "1e-6",
                "-constant",
                "-case", str(self.casePath)
            ])
            Runner(args=["reconstructPar", "-case", str(self.casePath)])

            # Clean up processor directories
            for file in glob.glob(str(self.casePath / 'processor*')):
                shutil.rmtree(file)
        else:
            # Run simpleFoam in serial mode
            runner = Runner(args=["simpleFoam", "-case", str(self.casePath)])

    def modifyDicts(self, parserArgs) -> None:
        """
        Modify OpenFOAM dictionaries based on command-line arguments.

        Args:
            parserArgs: Parsed command-line arguments containing simulation parameters.
        """
        # Modify airspeed if provided
        if hasattr(parserArgs, 'airspeed') and parserArgs.airspeed:
            file = ParsedParameterFile(str(self.casePath / '0' / 'U'))
            file['internalField'].val.vals[0] = parserArgs.airspeed
            file.writeFile()

            file = ParsedParameterFile(str(self.casePath / 'system' / 'controlDict'))
            file['functions']['forces']['magUInf'] = parserArgs.airspeed
            file['functions']['forceCoeffs1']['magUInf'] = parserArgs.airspeed
            file.writeFile()

        # Modify center of gravity if provided
        if hasattr(parserArgs, 'cofg') and parserArgs.cofg:
            file = ParsedParameterFile(str(self.casePath / 'system' / 'controlDict'))
            file['functions']['forces']['CofR'].vals[0] = parserArgs.cofg
            file['functions']['forceCoeffs1']['CofR'].vals[0] = parserArgs.cofg
            file.writeFile()

        # Modify reference area if provided
        if hasattr(parserArgs, 'refarea') and parserArgs.refarea:
            file = ParsedParameterFile(str(self.casePath / 'system' / 'controlDict'))
            file['functions']['forces']['Aref'] = parserArgs.refarea
            file['functions']['forceCoeffs1']['Aref'] = parserArgs.refarea
            file.writeFile()

        # Modify convergence criteria if provided
        if hasattr(parserArgs, 'convergence') and parserArgs.convergence:
            file = ParsedParameterFile(str(self.casePath / 'system' / 'fvSolution'))
            for i in file['SIMPLE']['residualControl']:
                file['SIMPLE']['residualControl'][i] = parserArgs.convergence
            file.writeFile()


if __name__=='__main__':
    # Example usage
    s = solver('test')
    # print(s.decomposeParDict)  # Example: print decomposition settings
