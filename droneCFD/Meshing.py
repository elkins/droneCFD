"""
Meshing module for droneCFD.

This module handles the mesh generation process for OpenFOAM simulations,
including blockMesh for the base domain and snappyHexMesh for geometry refinement.

Classes:
    mesher: Manages mesh generation for CFD simulations.

Functions:
    which: Locates executable programs in the system PATH.
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

import os
import math
from pathlib import Path
from typing import Optional
import numpy as np
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
from PyFoam.Applications.Runner import Runner
from PyFoam.Applications.MeshUtilityRunner import MeshUtilityRunner
from . import Utilities


def which(program: str) -> Optional[str]:
    """
    Locate an executable in the system PATH.

    Args:
        program: Name of the executable to find.

    Returns:
        Full path to the executable if found, None otherwise.

    Note:
        Based on harmv's StackOverflow answer:
        http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    """
    def is_exe(fpath: str) -> bool:
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ.get("PATH", "").split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


class mesher:

    """
    Manages mesh generation for OpenFOAM CFD simulations.

    This class handles the complete meshing workflow:
    - Base domain generation with blockMesh
    - Geometry refinement with snappyHexMesh
    - Parallel mesh generation support

    Attributes:
        casePath: Path to the OpenFOAM case directory.
        stlSolid: STL geometry object containing aircraft mesh.
        baseCellSize: Base cell size for mesh generation (meters).
        parallel: Whether to use parallel processing.
        nprocs: Number of processors to use.
    """

    def __init__(
        self,
        casePath: str | Path,
        stlSolid,
        nprocs: Optional[int] = None,
        baseCellSize: float = 0.25,
        parserArgs=None
    ) -> None:
        """
        Initialize the mesher with case and geometry information.

        Args:
            casePath: Path to the OpenFOAM case directory.
            stlSolid: STL solid object containing the geometry.
            nprocs: Number of processors for parallel processing (optional).
            baseCellSize: Base cell size for mesh generation in meters.
            parserArgs: Command-line parser arguments (optional).
        """
        self.casePath = Path(casePath)
        self.stlSolid = stlSolid
        self.procsUtil = Utilities.parallelUtilities(nprocs)
        self.baseCellSize = baseCellSize

        # Configure parallel processing
        if self.procsUtil.procs > 1:
            self.parallel = True
            self.nprocs = self.procsUtil.procs
        else:
            self.parallel = False
            self.nprocs = 1

        # Load OpenFOAM dictionary files
        self.blockMeshDict = ParsedParameterFile(
            str(self.casePath / 'constant' / 'polyMesh' / 'blockMeshDict')
        )
        self.snappyHexMeshDict = ParsedParameterFile(
            str(self.casePath / 'system' / 'snappyHexMeshDict')
        )
        self.decomposeParDict = ParsedParameterFile(
            str(self.casePath / 'system' / 'decomposeParDict')
        )

    def blockMeshDomain(self):
        x_verts = []
        y_verts = []
        z_verts = []

        ## Get the vertices from the template blockmeshdict (this ranges from -1,1 for x,y and z)
        for i in self.blockMeshDict['vertices']:
            x_verts.append(i[0])
            y_verts.append(i[1])
            z_verts.append(i[2])
        ##Based on the bounding box of the STL, calculate the domain (12 times the bb length in the downwind direction, 4 in the other two )
        dx = (self.stlSolid.bb[1]-self.stlSolid.bb[0])*12
        dy = (self.stlSolid.bb[3]-self.stlSolid.bb[2])*4
        dz = (self.stlSolid.bb[5]-self.stlSolid.bb[4])*4

        ##Enfore some minimum size constraints if the STL geometry is small
        if dx<2.5: dx = 2.5
        if dy<2.5: dy = 2.5
        if dz<2.5: dz = 2.5

        ## Calculate the number of blocks in each direction based on the option baseCellSize of this class
        block_x = math.ceil(dx/float(self.baseCellSize))
        block_y = math.ceil(dy/float(self.baseCellSize))
        block_z = math.ceil(dz/float(self.baseCellSize))

        ## Set the block sizes in blockMeshDict
        self.blockMeshDict['blocks'][2] = [block_x, block_y, block_z]

        ##Then scale the verts, also notice that the box is moved downwind a bit (the x_verts).
        x_verts = (np.array(x_verts) * dx)+((self.stlSolid.bb[1]-self.stlSolid.bb[0])*6)
        y_verts = np.array(y_verts) * dy
        z_verts = np.array(z_verts) * dz
        new_verts = []
        for enu,i in enumerate(x_verts):
            new_verts.append('(%f %f %f)'%(x_verts[enu],y_verts[enu],z_verts[enu]))

        #set the new verts in blockMeshDict
        self.blockMeshDict['vertices'] = new_verts

    def blockMesh(self):
        '''This functions configures and runs blockMeshDict'''

        ## The first step is to configure the domain for blockMeshDict based on the stl file
        self.blockMeshDomain()
        ## That file gets written to file
        self.blockMeshDict.writeFile()
        ## And we run blockMeshDict
        Runner(args=["--silent","blockMesh","-case",self.casePath])
        Runner(args=["--silent","surfaceFeatureExtract","-case",self.casePath])


    def snappyHexMesh(self):
        '''
        This function runs snappyHexMesh for us
        '''
        ## First, lets add a few refinement regions based on the geometry

        ## The first is a box that surrounds the aircraft and extends downwind by three body lengths
        self.snappyHexMeshDict['geometry']['downwindbox'] = {}
        dwBox = self.snappyHexMeshDict['geometry']['downwindbox']
        dwBox['type'] = 'searchableBox'
        boxenlarge = 2.5
        dwBox['min'] = [boxenlarge*self.stlSolid.bb[0],boxenlarge*self.stlSolid.bb[2],boxenlarge*self.stlSolid.bb[4]]
        dwBox['max'] = [boxenlarge*self.stlSolid.bb[1]+4*(self.stlSolid.bb[1]-self.stlSolid.bb[0]),boxenlarge*self.stlSolid.bb[3],boxenlarge*self.stlSolid.bb[5]]

        self.snappyHexMeshDict['castellatedMeshControls']['refinementRegions']['downwindbox']={}
        self.snappyHexMeshDict['castellatedMeshControls']['refinementRegions']['downwindbox']['mode']='inside'
        self.snappyHexMeshDict['castellatedMeshControls']['refinementRegions']['downwindbox']['levels'] = [[1,4]]
        self.snappyHexMeshDict['castellatedMeshControls']['locationInMesh'][0] = dwBox['min'][0]
        self.snappyHexMeshDict['castellatedMeshControls']['locationInMesh'][1] = dwBox['min'][1]
        self.snappyHexMeshDict['castellatedMeshControls']['locationInMesh'][2] = dwBox['min'][2]

        ## Next we add some refinement regions around the wing tips
        self.snappyHexMeshDict['geometry']['wingtip1'] = {}
        wt1Box = self.snappyHexMeshDict['geometry']['wingtip1']
        wt1Box['type'] = 'searchableCylinder'
        wt1Box['point1'] = self.stlSolid.yminPoint.tolist()
        ## Next point is 6 meters downwind
        wt1Box['point2'] = [sum(x) for x in zip(self.stlSolid.yminPoint, [6,0,0])]
        wt1Box['radius'] = .2

        self.snappyHexMeshDict['castellatedMeshControls']['refinementRegions']['wingtip1']={}
        self.snappyHexMeshDict['castellatedMeshControls']['refinementRegions']['wingtip1']['mode']='inside'
        self.snappyHexMeshDict['castellatedMeshControls']['refinementRegions']['wingtip1']['levels'] = [[1,5]]

        ## Next we add some refinement regions around the wing tips
        self.snappyHexMeshDict['geometry']['wingtip2'] = {}
        wt2Box = self.snappyHexMeshDict['geometry']['wingtip2']
        wt2Box['type'] = 'searchableCylinder'
        wt2Box['point1'] = self.stlSolid.ymaxPoint.tolist()
        ## Next point is 6 meters downwind
        wt2Box['point2'] = [sum(x) for x in zip(self.stlSolid.ymaxPoint, [6,0,0])]
        wt2Box['radius'] = .2


        self.snappyHexMeshDict['castellatedMeshControls']['refinementRegions']['wingtip2']={}
        self.snappyHexMeshDict['castellatedMeshControls']['refinementRegions']['wingtip2']['mode']='inside'
        self.snappyHexMeshDict['castellatedMeshControls']['refinementRegions']['wingtip2']['levels'] = [[1,5]]

        ## Save the snappyHexMeshDict file
        self.snappyHexMeshDict.writeFile()

        ## We need to know if we should run this in parallel
        if self.parallel:
            ## Ok, running in parallel. Lets first configure the decomposePar dict based on the number of processors we have
            self.decomposeParDict['numberOfSubdomains'] = self.nprocs
            self.decomposeParDict.writeFile()
            ## The we decompose the case (Split up the problem into a few subproblems)
            Runner(args=['--silent',"decomposePar","-force","-case",self.casePath])

            ## Then run snappyHexMesh to build our final mesh for the simulation, also in parallel
            print("Starting snappyHexMesh")
            # Runner(args=['--silent', "--proc=%s"%self.nprocs,"snappyHexMesh","-overwrite","-case",str(self.casePath)])
            Runner(args=[f"--proc={self.nprocs}","snappyHexMesh","-overwrite","-case",str(self.casePath)])
            ## Finally, we combine the mesh back into a single mesh. This allows us to decompose it more intelligently for simulation

            Runner(args=['--silent', "reconstructParMesh","-constant","-case",self.casePath])
        else:
            ## No parallel? Ok, lets just run snappyHexMesh
            Runner(args=['--silent' ,"snappyHexMesh","-overwrite","-case",self.casePath])

    def previewMesh(self) -> None:
        """
        Open the mesh in ParaView for visual inspection.

        This utility function launches ParaView to visualize the generated mesh.

        Raises:
            RuntimeWarning: If ParaView is not found in the system PATH.
        """
        if not which('paraview'):
            print('Warning: Could not find paraview in system PATH')
            return

        foam_file = self.casePath / 'openme.foam'
        os.system(f'paraview {foam_file}')

if __name__=='__main__':
    # Example usage
    import stlTools
    import time
    import Utilities
    Utilities.caseSetup('test')
    stlSolid = stlTools.solidSTL('../test_dir/benchmarkAircraft.stl')
    stlSolid.setaoa(5, units='degrees')
    stlSolid.save('test/constant/triSurface/benchmarkAircraft.stl')
    print(f"Bounding box: {stlSolid.bb}")
    a = mesher('test', stlSolid, baseCellSize=0.31)
    a.blockMesh()
    a.snappyHexMesh()
    a.previewMesh()
