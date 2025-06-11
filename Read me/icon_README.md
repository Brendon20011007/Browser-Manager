# Browser Manager Icon Generator

This document explains the icon generation process for the Browser Manager application.

## Overview

The `create_icon.py` script generates a simple, modern icon for the Browser Manager application. The icon is a blue circle on a transparent background, using the Microsoft blue color scheme to match the application's design.

## Requirements

- Python 3.7 or higher
- Pillow (PIL) library

## Icon Specifications

- Format: ICO (Windows icon format)
- Size: 256x256 pixels
- Color: Microsoft blue (RGB: 0, 120, 212)
- Background: Transparent
- Shape: Circle

## How to Generate the Icon

1. Ensure Pillow is installed:
   ```powershell
   pip install pillow
   ```

2. Run the icon generator:
   ```powershell
   python create_icon.py
   ```

The script will create `browser_icon.ico` in the current directory.

## Customization

To modify the icon:

1. Open `create_icon.py`
2. Adjust the following parameters:
   - `size`: Change the icon dimensions
   - `circle_color`: Modify the RGB color values
   - `circle_radius`: Adjust the circle size

Example of changing the color:
```python
# Change to a different color (e.g., green)
circle_color = (0, 255, 0, 255)  # Green with full opacity
```

## Usage in Build Process

The icon is automatically used during the build process:
1. The build script calls `create_icon.py`
2. The generated icon is included in the final executable
3. The icon appears in Windows Explorer and the taskbar

## Manual Icon Creation

If you want to create a custom icon:

1. Create your icon image (256x256 pixels recommended)
2. Convert it to ICO format using an image editor
3. Replace `browser_icon.ico` in the project directory
4. The build process will use your custom icon

## Notes

- The icon is designed to be simple and recognizable
- The transparent background ensures compatibility with different Windows themes
- The ICO format supports multiple sizes, but we use 256x256 for best quality
- The icon is automatically included in the final executable 