"""
Angle of Attack Sweep Example - droneCFD

This example demonstrates running multiple CFD simulations across a range
of angles of attack to generate aerodynamic performance data.

The results can be used to:
- Generate lift and drag curves
- Create drag polars
- Determine stall angle
- Calculate aerodynamic derivatives

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

from pathlib import Path
from droneCFD import Utilities, stlTools, Meshing, Solver, Visualization


def main():
    """Run angle of attack sweep."""

    # Configuration
    preview = False  # Set to True to open ParaView for visualization
    base_path = 'sweep'
    aoa_range = [-6, -4, -2, 0, 2, 4, 6, 8, 10]  # degrees
    geometry_path = None  # Use default benchmark aircraft

    print("=" * 70)
    print("droneCFD - Angle of Attack Sweep")
    print("=" * 70)
    print(f"AOA Range: {aoa_range}")
    print(f"Number of simulations: {len(aoa_range)}")
    print(f"Results directory: {base_path}")
    print("=" * 70)

    # Storage for results
    lift_values = []
    drag_values = []

    # Run simulations for each angle of attack
    for i, aoa in enumerate(aoa_range, 1):
        print(f"\n{'=' * 70}")
        print(f"Simulation {i}/{len(aoa_range)}: AOA = {aoa}°")
        print(f"{'=' * 70}")

        # Setup case directory
        case_name = f'{base_path}/test_{aoa}'
        print(f"\n[1/4] Setting up case: {case_name}")
        case = Utilities.caseSetup(
            folderPath=case_name,
            geometryPath=geometry_path
        )

        # Load and rotate geometry
        print(f"[2/4] Configuring geometry at {aoa}° AOA")
        model = stlTools.solidSTL(case.stlPath)
        model.setaoa(aoa, units='degrees')
        model.save(case.stlPath)

        # Generate mesh
        print("[3/4] Generating mesh")
        mesh = Meshing.mesher(case.dir, model)
        mesh.blockMesh()
        mesh.snappyHexMesh()

        if preview:
            mesh.previewMesh()

        # Run solver
        print("[4/4] Running solver")
        solver = Solver.solver(case.dir)

        if preview:
            mesh.previewMesh()

        # Extract results
        try:
            viz = Visualization.ResultsVisualizer(case.dir)
            forces = viz.load_forces()

            # Get time-averaged forces from last 15 iterations
            avg_length = min(15, len(forces))
            drag = forces[-avg_length:, 1] + forces[-avg_length:, 4]  # Pressure + viscous
            lift = forces[-avg_length:, 3] + forces[-avg_length:, 6]  # Pressure + viscous

            drag_avg = float(drag.mean())
            lift_avg = float(lift.mean())

            drag_values.append(drag_avg)
            lift_values.append(lift_avg)

            print(f"  ✓ Lift: {lift_avg:.3f} N, Drag: {drag_avg:.3f} N")
        except Exception as e:
            print(f"  ⚠ Could not extract forces: {e}")
            drag_values.append(0.0)
            lift_values.append(0.0)

    # Generate summary plots
    print(f"\n{'=' * 70}")
    print("Generating summary plots...")
    print(f"{'=' * 70}")

    try:
        # Lift and drag curves
        Visualization.plot_aoa_sweep(
            aoa_range,
            lift_values,
            drag_values,
            save_path=f'{base_path}/aoa_sweep.png',
            show=False
        )
        print(f"  ✓ AOA sweep plot saved to: {base_path}/aoa_sweep.png")

        # Drag polar
        Visualization.plot_drag_polar(
            lift_values,
            drag_values,
            aoa_list=aoa_range,
            save_path=f'{base_path}/drag_polar.png',
            show=False
        )
        print(f"  ✓ Drag polar saved to: {base_path}/drag_polar.png")

    except Exception as e:
        print(f"  ⚠ Plotting failed: {e}")

    # Print summary table
    print(f"\n{'=' * 70}")
    print("RESULTS SUMMARY")
    print(f"{'=' * 70}")
    print(f"{'AOA (°)':>10} {'Lift (N)':>12} {'Drag (N)':>12} {'L/D':>10}")
    print("-" * 70)

    for aoa, lift, drag in zip(aoa_range, lift_values, drag_values):
        ld_ratio = lift / drag if drag != 0 else 0
        print(f"{aoa:>10.1f} {lift:>12.3f} {drag:>12.3f} {ld_ratio:>10.2f}")

    print("=" * 70)
    print(f"All results saved to: {base_path}/")
    print("=" * 70)


if __name__ == '__main__':
    main()