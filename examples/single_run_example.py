"""
Single CFD Run Example - droneCFD

This example demonstrates a complete CFD workflow:
1. Setting up a case directory from template
2. Loading and rotating STL geometry to desired angle of attack
3. Generating computational mesh with blockMesh and snappyHexMesh
4. Running the OpenFOAM solver (simpleFoam)
5. Optional visualization with ParaView

Author: cpaulson
Updated for Python 3.12+
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

from droneCFD import Utilities, stlTools, Meshing, Solver, Visualization


def main():
    """Run a single CFD simulation."""

    # Configuration
    preview = False  # Set to True to open ParaView for visualization
    angle_of_attack = 5.0  # degrees
    case_name = 'test'

    print("=" * 70)
    print("droneCFD - Single Run Example")
    print("=" * 70)

    # Step 1: Setup case directory
    print(f"\n[1/5] Setting up case directory: {case_name}")
    case = Utilities.caseSetup(case_name)
    print(f"  ✓ Case directory created at: {case.dir}")

    # Step 2: Load and rotate geometry
    print(f"\n[2/5] Loading geometry and setting angle of attack to {angle_of_attack}°")
    model = stlTools.solidSTL(case.stlPath)
    model.setaoa(angle_of_attack, units='degrees')
    model.save(case.stlPath)
    print(f"  ✓ Geometry configured")
    print(f"  ✓ Bounding box: {model.bb}")

    # Step 3: Generate mesh
    print("\n[3/5] Generating computational mesh")
    mesh = Meshing.mesher(case.dir, model)

    print("  → Running blockMesh...")
    mesh.blockMesh()
    print("  ✓ Block mesh generated")

    print("  → Running snappyHexMesh...")
    mesh.snappyHexMesh()
    print("  ✓ Refined mesh generated")

    if preview:
        print("  → Opening ParaView for mesh inspection...")
        mesh.previewMesh()

    # Step 4: Run solver
    print("\n[4/5] Running OpenFOAM solver")
    solver = Solver.solver(case.dir)
    print("  ✓ Simulation complete")

    # Step 5: Visualize results
    print("\n[5/5] Post-processing results")
    try:
        viz = Visualization.ResultsVisualizer(case.dir)
        viz.load_forces()
        viz.plot_forces_history(save_path=f'{case.dir}/forces_history.png', show=False)
        viz.plot_force_components(save_path=f'{case.dir}/force_components.png', show=False)
        print(f"  ✓ Plots saved to: {case.dir}")
    except Exception as e:
        print(f"  ⚠ Visualization failed: {e}")

    if preview:
        print("  → Opening ParaView for results inspection...")
        mesh.previewMesh()

    print("\n" + "=" * 70)
    print("Simulation complete!")
    print(f"Results available in: {case.dir}")
    print("=" * 70)


if __name__ == '__main__':
    main()