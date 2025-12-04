"""
Post-processing module for droneCFD.

This module handles post-processing of CFD simulation results, including:
- Force and moment coefficient extraction
- Data aggregation across multiple angle of attack sweeps
- Excel report generation with embedded charts

Classes:
    PostProcessing: Manages post-processing and report generation.

Note:
    Force log parsing code adapted from protarius on cfd-online.com:
    http://www.cfd-online.com/Forums/openfoam-post-processing/79474-how-plot-forces-dat-file-all-brackets.html
"""

__author__ = 'chrispaulson'

import re
import os
import math
import glob
from pathlib import Path
from typing import Optional
import numpy as np
import xlsxwriter


class PostProcessing:
    """
    Handles post-processing of CFD simulation results.

    This class extracts force data from OpenFOAM output files, processes it,
    and generates Excel reports with charts showing lift and drag vs time.

    Attributes:
        casedir: Path to the case directory containing simulation results.
        parserArgs: Optional command-line arguments.
    """

    def __init__(self, casedir: str | Path, parserArgs=None) -> None:
        """
        Initialize post-processing and generate reports.

        Args:
            casedir: Path to the case directory or parent directory containing multiple cases.
            parserArgs: Optional command-line parser arguments.
        """
        self.casedir = Path(casedir)
        self.parserArgs = parserArgs
        workbook = xlsxwriter.Workbook(str(self.casedir / 'RunSummary.xlsx'))
        globalResults = workbook.add_worksheet('Global Results')
        chartGR = workbook.add_chart({'type': 'scatter', 'subtype': 'straight'})
        grRow = 0
        grCol = 0

        for set_path in glob.glob(str(self.casedir)):
            print(f"Processing: {set_path}")
            if not os.path.isdir(set_path):
                continue

            run = Path(set_path).name
            worksheet = workbook.add_worksheet(run)
            column = 0
            row = 0
            chartLift = workbook.add_chart({'type': 'scatter', 'subtype': 'straight'})
            chartDrag = workbook.add_chart({'type': 'scatter', 'subtype': 'straight'})

            for aoa_path in glob.glob(f'{set_path}/*'):
                print(f"  AOA case: {aoa_path}")
                aoatmp = float(Path(aoa_path).name.split('_')[-1])
                print(f"  Angle: {aoatmp}")

                # Write headers
                worksheet.write(row, column, f'{aoatmp} Simulation Time')
                worksheet.write(row, column + 1, f'{aoatmp} Drag')
                worksheet.write(row, column + 2, f'{aoatmp} Lift')
                row += 1

                # Read forces data
                forces_file = Path(aoa_path) / 'postProcessing' / 'forces' / '0' / 'forces.dat'
                if not forces_file.exists():
                    print(f"  Warning: Forces file not found: {forces_file}")
                    continue

                data = []
                with open(forces_file, 'r') as pipefile:
                    for line in pipefile:
                        # Remove parentheses for parsing
                        line = line.translate(str.maketrans('', '', '()'))
                        lineData = line.split()
                        if len(lineData) > 10:
                            try:
                                data.append(np.array(lineData, dtype='float'))
                            except ValueError:
                                continue  # Skip invalid lines

                if not data:
                    print(f"  Warning: No valid data found in {forces_file}")
                    continue

                data = np.array(data)
                # Get cell references for chart creation
                startCellTime = xlsxwriter.utility.xl_rowcol_to_cell(row, column, row_abs=True, col_abs=True)
                startCellDrag = xlsxwriter.utility.xl_rowcol_to_cell(row, column + 1, row_abs=True, col_abs=True)
                startCellLift = xlsxwriter.utility.xl_rowcol_to_cell(row, column + 2, row_abs=True, col_abs=True)

                # Write force data
                for i in data:
                    worksheet.write(row, column, i[0])  # Time
                    worksheet.write(row, column + 1, i[1] + i[4])  # Drag (pressure + viscous)
                    worksheet.write(row, column + 2, i[3] + i[6])  # Lift (pressure + viscous)
                    row += 1

                endCellTime = xlsxwriter.utility.xl_rowcol_to_cell(row - 1, column, row_abs=True, col_abs=True)
                endCellDrag = xlsxwriter.utility.xl_rowcol_to_cell(row - 1, column + 1, row_abs=True, col_abs=True)
                endCellLift = xlsxwriter.utility.xl_rowcol_to_cell(row - 1, column + 2, row_abs=True, col_abs=True)

                # Add series to charts
                chartLift.add_series({
                    'name': f'{aoatmp}',
                    'categories': f'={run}!{startCellTime}:{endCellTime}',
                    'values': f'={run}!{startCellLift}:{endCellLift}'
                })
                chartDrag.add_series({
                    'name': f'{aoatmp}',
                    'categories': f'={run}!{startCellTime}:{endCellTime}',
                    'values': f'={run}!{startCellDrag}:{endCellDrag}'
                })

                # Move to next column set
                column += 3
                row = 0

                # Calculate time-averaged forces (last 15 iterations)
                avgLength = min(15, len(data))
                a = math.sin(math.radians(aoatmp))
                b = math.cos(math.radians(aoatmp))
                zForce = np.mean(data[-avgLength:, 3] + data[-avgLength:, 6])
                xForce = np.mean(data[-avgLength:, 1] + data[-avgLength:, 4])

                # Transform to aircraft reference frame
                planeRefLift = b * zForce + a * xForce
                planeRefDrag = b * xForce - a * zForce

                # Write global results
                globalResults.write(grRow, grCol, aoatmp)
                globalResults.write(grRow, grCol + 1, planeRefLift)
                globalResults.write(grRow, grCol + 2, planeRefDrag)
                grRow += 1

            # Update column for next set
            grCol += 3
            grRow = 0

            # Configure and insert charts
            chartLift.set_y_axis({'date_axis': False, 'min': -15, 'max': 30})
            chartDrag.set_y_axis({'date_axis': False, 'min': 0, 'max': 10})
            worksheet.insert_chart('A1', chartLift)
            worksheet.insert_chart('I1', chartDrag)

        workbook.close()
        print(f"\nPost-processing complete. Report saved to: {self.casedir / 'RunSummary.xlsx'}")





