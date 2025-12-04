"""
STL file manipulation tools for droneCFD.

This module provides utilities for loading, manipulating, and transforming
STL geometry files for CFD simulations. Based on arizonat/py-stl-toolkit.

Classes:
    solidSTL: Handles STL file operations including rotation, translation, and scaling.
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
from pathlib import Path
from typing import List, Tuple, Literal, Optional
import math
import numpy as np
from stl import stl as stl
from functools import reduce


class solidSTL:
    """
    Handles STL file operations for CFD preprocessing.

    This class provides methods to load, transform, and save STL geometry files.
    It includes functionality for rotation (angle of attack), translation, scaling,
    and automatic geometry centering.

    Attributes:
        mesh: The STL mesh object from numpy-stl library.
        bb: Bounding box coordinates [xmin, xmax, ymin, ymax, zmin, zmax].
        ymaxPoint: Coordinates of the maximum Y point (typically a wingtip).
        yminPoint: Coordinates of the minimum Y point (typically opposite wingtip).
    """

    def __init__(self, fp: str | Path) -> None:
        """
        Initialize the solidSTL object and load an STL file.

        Args:
            fp: File path to the STL file to load.

        Raises:
            FileNotFoundError: If the STL file doesn't exist.
            ValueError: If the STL file is invalid or corrupted.
        """
        fp = Path(fp)
        if not fp.exists():
            raise FileNotFoundError(f"STL file not found: {fp}")

        print(f'Loading STL file: {fp}')

        try:
            self.mesh = stl.StlMesh(str(fp))
        except Exception as e:
            raise ValueError(f"Failed to load STL file {fp}: {e}") from e

        self.boundingBox()
        self.centerGeometry()

    def boundingBox(self) -> None:
        """
        Calculate and store the bounding box of the mesh.

        Updates the bb attribute with [xmin, xmax, ymin, ymax, zmin, zmax]
        and identifies the extreme Y-coordinate points (typically wingtips).
        """
        xmin = float(self.mesh.x.min())
        xmax = float(self.mesh.x.max())
        ymin = float(self.mesh.y.min())
        ymax = float(self.mesh.y.max())
        zmin = float(self.mesh.z.min())
        zmax = float(self.mesh.z.max())
        self.bb = [xmin, xmax, ymin, ymax, zmin, zmax]

        # Find the actual points at the extremes (typically wingtips)
        where = np.where(self.mesh.data['vectors'] == ymax)
        if len(where[0]) > 0:
            self.ymaxPoint = self.mesh.data['vectors'][where[0][0]][where[1][0]]
        else:
            self.ymaxPoint = np.array([0.0, ymax, 0.0])

        where = np.where(self.mesh.data['vectors'] == ymin)
        if len(where[0]) > 0:
            self.yminPoint = self.mesh.data['vectors'][where[0][0]][where[1][0]]
        else:
            self.yminPoint = np.array([0.0, ymin, 0.0])

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> None:
        """
        Translate the mesh by the specified amounts.

        Args:
            dx: Translation distance in X direction (meters).
            dy: Translation distance in Y direction (meters).
            dz: Translation distance in Z direction (meters).
        """
        self.mesh.data['vectors'] = self.mesh.data['vectors'] + [dx, dy, dz]
        self.boundingBox()  # Update bounding box after translation

    def centerGeometry(self) -> None:
        """
        Center the geometry at the origin (0, 0, 0).

        This method translates the mesh so that its center coincides with
        the coordinate system origin, which is useful for CFD simulations.
        """
        self.boundingBox()
        dx = self.bb[1] - self.bb[0]
        dy = self.bb[3] - self.bb[2]
        dz = self.bb[5] - self.bb[4]
        self.translate(
            dx=-1 * (dx / 2.0 + self.bb[0]),
            dy=-1 * (dy / 2.0 + self.bb[2]),
            dz=-1 * (dz / 2.0 + self.bb[4])
        )

    def scale(self, x: float = 1.0, y: float = 1.0, z: float = 1.0) -> None:
        """
        Scale the mesh by the specified factors.

        Args:
            x: Scaling factor in X direction.
            y: Scaling factor in Y direction.
            z: Scaling factor in Z direction.
        """
        if x <= 0 or y <= 0 or z <= 0:
            raise ValueError("Scale factors must be positive")
        self.mesh.data['vectors'] = self.mesh.data['vectors'] * [x, y, z]
        self.boundingBox()  # Update bounding box after scaling

    def save(self, fp: str | Path) -> None:
        """
        Save the mesh to an STL file.

        Args:
            fp: File path where the STL file should be saved.

        Raises:
            IOError: If the file cannot be written.
        """
        fp = Path(fp)
        print(f'Saving STL file to: {fp}')

        # Ensure parent directory exists
        fp.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(fp, 'wb') as fh:
                self.mesh.save(fp, fh=fh, mode=2, update_normals=True)
            print(f'Successfully saved STL file: {fp}')
        except Exception as e:
            raise IOError(f"Failed to save STL file {fp}: {e}") from e

    def setaoa(self, aoa: float, units: Literal["degrees", "radians"] = "degrees") -> None:
        """
        Set the angle of attack by rotating around the Y axis.

        Args:
            aoa: Angle of attack value.
            units: Unit system for the angle ("degrees" or "radians").
        """
        self.rotate(y=aoa, units=units)

    def rotate(
        self,
        z: float = 0.0,
        y: float = 0.0,
        x: float = 0.0,
        units: Literal["degrees", "radians"] = "degrees"
    ) -> None:
        """
        Rotate the mesh using Euler angles.

        Args:
            z: Rotation around Z axis (yaw).
            y: Rotation around Y axis (pitch/angle of attack).
            x: Rotation around X axis (roll).
            units: Unit system for angles ("degrees" or "radians").

        Raises:
            ValueError: If units parameter is invalid.
        """
        if units == 'degrees':
            z = np.radians(z)
            y = np.radians(y)
            x = np.radians(x)
        elif units == 'radians':
            pass  # Already in radians
        else:
            raise ValueError(f"Invalid units: {units}. Must be 'degrees' or 'radians'")

        rm = self.euler2mat(z, y, x)

        # Apply rotation to all vertices
        for i in range(self.mesh.data['vectors'].shape[0]):
            for j in range(3):  # Each triangle has 3 vertices
                self.mesh.data['vectors'][i][j] = np.dot(self.mesh.data['vectors'][i][j], rm.T)

        self.boundingBox()  # Update bounding box after rotation

    def euler2mat(self, z: float = 0.0, y: float = 0.0, x: float = 0.0) -> np.ndarray:
        """
        Convert Euler angles to a rotation matrix.

        Args:
            z: Rotation around Z axis (radians).
            y: Rotation around Y axis (radians).
            x: Rotation around X axis (radians).

        Returns:
            3x3 rotation matrix as numpy array.
        """
        Ms = []

        # Z rotation (yaw)
        if z != 0:
            cosz = math.cos(z)
            sinz = math.sin(z)
            Ms.append(np.array([
                [cosz, -sinz, 0],
                [sinz, cosz, 0],
                [0, 0, 1]
            ]))

        # Y rotation (pitch)
        if y != 0:
            cosy = math.cos(y)
            siny = math.sin(y)
            Ms.append(np.array([
                [cosy, 0, siny],
                [0, 1, 0],
                [-siny, 0, cosy]
            ]))

        # X rotation (roll)
        if x != 0:
            cosx = math.cos(x)
            sinx = math.sin(x)
            Ms.append(np.array([
                [1, 0, 0],
                [0, cosx, -sinx],
                [0, sinx, cosx]
            ]))

        # Combine rotation matrices
        if Ms:
            return reduce(np.dot, Ms[::-1])
        return np.eye(3)

    def getWingtip(self) -> np.ndarray:
        """
        Get the coordinates of the maximum Y wingtip.

        Returns:
            Numpy array with [x, y, z] coordinates of the wingtip.
        """
        return self.ymaxPoint


# Maintain backward compatibility
SolidSTL = solidSTL


if __name__ == "__main__":
    # Example usage
    model = solidSTL('data/geometries/benchmarkAircraft.stl')
    model.centerGeometry()
    model.setaoa(5, units='degrees')
    model.save('translated.stl')
    print(f"Bounding box: {model.bb}")
