"""
Visualization module for droneCFD.

This module provides modern visualization capabilities for CFD simulation results,
including interactive plots and 3D field visualization.

Classes:
    ResultsVisualizer: Handles visualization of CFD results using matplotlib and optional plotly.

Functions:
    plot_forces_history: Plot force and moment coefficient history.
    plot_aoa_sweep: Plot lift and drag curves vs angle of attack.
    plot_convergence: Plot residual convergence history.
"""

__author__ = 'droneCFD Contributors'

from pathlib import Path
from typing import Optional, List, Tuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class ResultsVisualizer:
    """
    Handles visualization of CFD simulation results.

    This class provides methods to create publication-quality plots
    of force data, convergence history, and aerodynamic performance.

    Attributes:
        case_path: Path to the OpenFOAM case directory.
        forces_data: Loaded forces data array.
    """

    def __init__(self, case_path: str | Path) -> None:
        """
        Initialize the visualizer with a case directory.

        Args:
            case_path: Path to the OpenFOAM case directory.

        Raises:
            FileNotFoundError: If the case directory doesn't exist.
        """
        self.case_path = Path(case_path)
        if not self.case_path.exists():
            raise FileNotFoundError(f"Case directory not found: {self.case_path}")

        self.forces_data: Optional[np.ndarray] = None

    def load_forces(self, time_dir: str = "0") -> np.ndarray:
        """
        Load forces data from OpenFOAM postProcessing directory.

        Args:
            time_dir: Time directory containing forces data (default: "0").

        Returns:
            Numpy array with columns: [time, fx_p, fy_p, fz_p, fx_v, fy_v, fz_v, ...]

        Raises:
            FileNotFoundError: If forces file doesn't exist.
            ValueError: If forces file is empty or malformed.
        """
        forces_file = self.case_path / 'postProcessing' / 'forces' / time_dir / 'forces.dat'

        if not forces_file.exists():
            raise FileNotFoundError(f"Forces file not found: {forces_file}")

        data = []
        with open(forces_file, 'r') as f:
            for line in f:
                # Skip comment lines
                if line.startswith('#'):
                    continue

                # Remove parentheses
                line = line.translate(str.maketrans('', '', '()'))
                line_data = line.split()

                if len(line_data) >= 10:
                    try:
                        data.append(np.array(line_data[:10], dtype='float'))
                    except ValueError:
                        continue

        if not data:
            raise ValueError(f"No valid data found in {forces_file}")

        self.forces_data = np.array(data)
        return self.forces_data

    def plot_forces_history(
        self,
        save_path: Optional[str | Path] = None,
        show: bool = True
    ) -> Figure:
        """
        Plot force history (lift and drag vs time).

        Args:
            save_path: Path to save the figure (optional).
            show: Whether to display the plot.

        Returns:
            Matplotlib Figure object.

        Raises:
            ValueError: If forces data hasn't been loaded.
        """
        if self.forces_data is None:
            raise ValueError("Forces data not loaded. Call load_forces() first.")

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        time = self.forces_data[:, 0]
        drag = self.forces_data[:, 1] + self.forces_data[:, 4]  # Pressure + viscous
        lift = self.forces_data[:, 3] + self.forces_data[:, 6]  # Pressure + viscous

        # Plot drag
        ax1.plot(time, drag, 'b-', linewidth=2, label='Drag Force')
        ax1.set_xlabel('Simulation Time (s)', fontsize=12)
        ax1.set_ylabel('Drag Force (N)', fontsize=12)
        ax1.set_title('Drag Force History', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Plot lift
        ax2.plot(time, lift, 'r-', linewidth=2, label='Lift Force')
        ax2.set_xlabel('Simulation Time (s)', fontsize=12)
        ax2.set_ylabel('Lift Force (N)', fontsize=12)
        ax2.set_title('Lift Force History', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Figure saved to: {save_path}")

        if show:
            plt.show()

        return fig

    def plot_force_components(
        self,
        save_path: Optional[str | Path] = None,
        show: bool = True
    ) -> Figure:
        """
        Plot pressure and viscous force components separately.

        Args:
            save_path: Path to save the figure (optional).
            show: Whether to display the plot.

        Returns:
            Matplotlib Figure object.

        Raises:
            ValueError: If forces data hasn't been loaded.
        """
        if self.forces_data is None:
            raise ValueError("Forces data not loaded. Call load_forces() first.")

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        time = self.forces_data[:, 0]

        # Extract force components
        fx_pressure = self.forces_data[:, 1]
        fy_pressure = self.forces_data[:, 2]
        fz_pressure = self.forces_data[:, 3]
        fx_viscous = self.forces_data[:, 4]
        fy_viscous = self.forces_data[:, 5]
        fz_viscous = self.forces_data[:, 6]

        # Plot X forces (drag)
        axes[0, 0].plot(time, fx_pressure, 'b-', label='Pressure', linewidth=2)
        axes[0, 0].plot(time, fx_viscous, 'r-', label='Viscous', linewidth=2)
        axes[0, 0].plot(time, fx_pressure + fx_viscous, 'k--', label='Total', linewidth=2)
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('Fx (N)')
        axes[0, 0].set_title('X-Direction Forces (Drag)', fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].legend()

        # Plot Y forces
        axes[0, 1].plot(time, fy_pressure, 'b-', label='Pressure', linewidth=2)
        axes[0, 1].plot(time, fy_viscous, 'r-', label='Viscous', linewidth=2)
        axes[0, 1].plot(time, fy_pressure + fy_viscous, 'k--', label='Total', linewidth=2)
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Fy (N)')
        axes[0, 1].set_title('Y-Direction Forces', fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].legend()

        # Plot Z forces (lift)
        axes[1, 0].plot(time, fz_pressure, 'b-', label='Pressure', linewidth=2)
        axes[1, 0].plot(time, fz_viscous, 'r-', label='Viscous', linewidth=2)
        axes[1, 0].plot(time, fz_pressure + fz_viscous, 'k--', label='Total', linewidth=2)
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('Fz (N)')
        axes[1, 0].set_title('Z-Direction Forces (Lift)', fontweight='bold')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].legend()

        # Plot pressure vs viscous ratio
        total_drag = fx_pressure + fx_viscous
        pressure_fraction = np.abs(fx_pressure) / (np.abs(fx_pressure) + np.abs(fx_viscous) + 1e-10)
        axes[1, 1].plot(time, pressure_fraction * 100, 'g-', linewidth=2)
        axes[1, 1].set_xlabel('Time (s)')
        axes[1, 1].set_ylabel('Pressure Drag Fraction (%)')
        axes[1, 1].set_title('Pressure vs Viscous Drag Ratio', fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].set_ylim([0, 100])

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Figure saved to: {save_path}")

        if show:
            plt.show()

        return fig


def plot_aoa_sweep(
    aoa_list: List[float],
    lift_list: List[float],
    drag_list: List[float],
    save_path: Optional[str | Path] = None,
    show: bool = True
) -> Figure:
    """
    Plot lift and drag coefficients vs angle of attack.

    Args:
        aoa_list: List of angles of attack (degrees).
        lift_list: List of lift forces/coefficients.
        drag_list: List of drag forces/coefficients.
        save_path: Path to save the figure (optional).
        show: Whether to display the plot.

    Returns:
        Matplotlib Figure object.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Lift curve
    ax1.plot(aoa_list, lift_list, 'ro-', linewidth=2, markersize=8, label='Lift')
    ax1.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax1.axvline(x=0, color='k', linestyle='--', alpha=0.3)
    ax1.set_xlabel('Angle of Attack (degrees)', fontsize=12)
    ax1.set_ylabel('Lift Force (N)', fontsize=12)
    ax1.set_title('Lift vs Angle of Attack', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Drag curve
    ax2.plot(aoa_list, drag_list, 'bo-', linewidth=2, markersize=8, label='Drag')
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax2.axvline(x=0, color='k', linestyle='--', alpha=0.3)
    ax2.set_xlabel('Angle of Attack (degrees)', fontsize=12)
    ax2.set_ylabel('Drag Force (N)', fontsize=12)
    ax2.set_title('Drag vs Angle of Attack', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to: {save_path}")

    if show:
        plt.show()

    return fig


def plot_drag_polar(
    lift_list: List[float],
    drag_list: List[float],
    aoa_list: Optional[List[float]] = None,
    save_path: Optional[str | Path] = None,
    show: bool = True
) -> Figure:
    """
    Plot drag polar (lift vs drag).

    Args:
        lift_list: List of lift forces/coefficients.
        drag_list: List of drag forces/coefficients.
        aoa_list: Optional list of AOA for annotation.
        save_path: Path to save the figure (optional).
        show: Whether to display the plot.

    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    ax.plot(drag_list, lift_list, 'go-', linewidth=2, markersize=8, label='Drag Polar')

    # Annotate with AOA if provided
    if aoa_list:
        for i, (drag, lift, aoa) in enumerate(zip(drag_list, lift_list, aoa_list)):
            ax.annotate(f'{aoa}°', (drag, lift), textcoords="offset points",
                       xytext=(5, 5), ha='left', fontsize=9)

    ax.set_xlabel('Drag Force (N)', fontsize=12)
    ax.set_ylabel('Lift Force (N)', fontsize=12)
    ax.set_title('Drag Polar', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to: {save_path}")

    if show:
        plt.show()

    return fig


if __name__ == "__main__":
    # Example usage
    print("droneCFD Visualization Module")
    print("=" * 50)
    print("\nExample usage:")
    print("  from droneCFD import Visualization")
    print("  viz = Visualization.ResultsVisualizer('path/to/case')")
    print("  viz.load_forces()")
    print("  viz.plot_forces_history(save_path='forces.png')")
