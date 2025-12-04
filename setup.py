"""Setup configuration for droneCFD package."""

__author__ = 'cpaulson'

from setuptools import setup, find_packages
from pathlib import Path

here = Path(__file__).parent.absolute()
datadir = Path('droneCFD/data')

# Collect all data files
data_files = []
if datadir.exists():
    for root, folders, files in datadir.walk():
        for file in files:
            filepath = root / file
            data_files.append(str(filepath.relative_to(datadir)))

print(f"Package data files: {data_files}")

setup(
    name='droneCFD',
    version='0.2.0',
    description='A virtual wind tunnel based on OpenFOAM and PyFOAM',
    long_description='Please see dronecfd.com for more information',
    url='http://www.dronecfd.com',
    author='Chris Paulson',
    author_email='dronecfd@gmail.com',
    license='GNU',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    keywords='cfd wind tunnel uav uas suas openfoam',
    python_requires='>=3.9',
    install_requires=[
        'XlsxWriter>=3.1.9',
        'numpy>=1.26.0',
        'numpy-stl>=3.1.0',
        'PyFoam>=2022.9',
        'matplotlib>=3.8.0',
    ],
    packages=find_packages(),
    zip_safe=False,
    package_data={"droneCFD.data": data_files},
    scripts=[
        'scripts/dcCheck',
        'scripts/dcRun',
        'scripts/dcPostProcess'
    ]
)