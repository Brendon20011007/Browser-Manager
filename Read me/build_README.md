# Browser Manager Build Process

This document explains how to build the Browser Manager application into a standalone executable.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- Windows operating system

## Build Process

The build process is automated through `build.py` and consists of three main steps:

1. Installing required packages
2. Creating the application icon
3. Building the executable

### Required Files

- `build.py` - Main build script
- `browser_manager_modern.py` - Main application code
- `browser_manager.spec` - PyInstaller specification file
- `create_icon.py` - Icon generation script
- `requirements.txt` - Python package dependencies

## How to Build

1. Open a command prompt or PowerShell window
2. Navigate to the project directory
3. Run the build script:
   ```powershell
   python build.py
   ```

The script will:
- Install all required packages from requirements.txt
- Install PyInstaller and Pillow if not already installed
- Create the application icon
- Build the executable using PyInstaller

## Output

After successful build:
- The executable will be created in the `dist` folder
- The executable will be named "Browser Manager.exe"
- All necessary dependencies will be included

## Troubleshooting

If you encounter any issues:

1. Ensure Python is properly installed and in your PATH
2. Check that all required files are present
3. Verify you have write permissions in the project directory
4. Check the error message for specific issues

Common errors and solutions:
- "Module not found": Run `pip install -r requirements.txt` manually
- "Permission denied": Run the command prompt as administrator
- "PyInstaller not found": Run `pip install pyinstaller` manually

## Manual Build Steps

If the automated build fails, you can perform the steps manually:

1. Install requirements:
   ```powershell
   pip install -r requirements.txt
   pip install pyinstaller pillow
   ```

2. Create the icon:
   ```powershell
   python create_icon.py
   ```

3. Build the executable:
   ```powershell
   pyinstaller --clean --noconfirm browser_manager.spec
   ```

## Notes

- The build process creates a single-file executable
- The executable includes all necessary dependencies
- No Python installation is required on the target machine
- The application icon is automatically included
- The executable runs without showing a console window