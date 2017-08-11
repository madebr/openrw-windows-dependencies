# OpenRW Windows Dependencies

This repository holds the scripts to compile the dependencies of [OpenRW](https://github.com/rwengine/openrw).
It also stores the binaries.


## Dependencies
The scripts need the following dependencies pre-installed:
- [Microsoft Windows](https://www.microsoft.com/windows): Windows 10 or higher
- [Python](https://www.python.org/): Python 3.6 or higher
- Microsoft Compiler: 2017 or higher
  * Microsoft Visual Studio, or
  * Microsoft Build Tools for Visual Studio (stand-alone Microsoft C/C++ compiler)

The scripts download the following dependencies:
- [Microsoft VcPkg](https://github.com/Microsoft/vcpkg): git master
  * [CMake](https://cmake.org/)
  * Sources of all dependencies of OpenRW

## How to

### Set up vcpkg

`python pyvcpkg.py vcpkg install`

### Build dependencies

`python pyvcpkg.py deps build`

### Copy dependencies to triplet folder

`python pyvcpkg.py deps copy`

### Help

`python pyvcpkg.py -h`

## Targets
- x86-windows
- x86-windows-static
- x64-windows
- x64-windows-static
