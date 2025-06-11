# Browser Manager Application

This is a lightweight and efficient Python desktop application with a graphical user interface (GUI) built using PyQt5. It features two main pages: a Browser Detection Dashboard and a Browser Action Center.

## Features

### 1. Browser Detection Dashboard
- Automatically generates detection buttons for major browsers: Google Chrome, Opera, Brave, Epic, Firefox, Edge.
- Does not run detection logic automatically on startup.
- Allows the user to trigger a detection scan with a button click.
- Browser button color codes:
    - **Blue**: Browser is not running.
    - **Green**: Browser is running (normal mode).
    - **Red**: Browser is running with Incognito or Private mode.
- Uses `psutil` and `pygetwindow` for lightweight browser detection.
- Detection runs asynchronously in a separate thread to prevent GUI freezing.

### 2. Browser Action Center
- Displays buttons for all major browsers: Google Chrome, Opera, Brave, Epic, Firefox, Edge.
- Clicking a browser button shows a pop-up with two options:
    - Open `https://office.com` in incognito/private mode
    - Open a custom URL in incognito/private mode
- All URLs are opened in incognito/private mode for enhanced privacy
- If `https://office.com` is already open in the selected browser, it prompts the user with a confirmation dialog to close and reopen it.
- Terminates the browser process (using `taskkill`) and reopens the browser with `https://office.com` in incognito/private mode if confirmed.

## Requirements

- Python 3.x
- PyQt5
- psutil
- pygetwindow

## Setup and Installation

1.  **Clone the repository (or download the files):**

    ```bash
    # If using git
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install dependencies:**

    It is recommended to use a virtual environment.

    ```bash
    python -m venv venv
    .\venv\Scripts\activate   # On Windows
    # source venv/bin/activate # On macOS/Linux
    
    pip install -r requirements.txt
    ```

## Running the Application

After installing the dependencies, run the main application file:

```bash
python app.py
```

## Important Notes

- **Browser Executable Paths**: The application uses hardcoded paths for browser executables in `BrowserActions.BROWSER_PATHS`. If your browser installations are in non-standard locations, you might need to update these paths in `app.py` for the "Browser Action Center" to function correctly.
- **`taskkill`**: The application uses `taskkill` (a Windows command) to terminate browser processes. Ensure your system's PATH includes the directory containing `taskkill.exe` (usually `C:\Windows\System32`).
- **Permissions**: Ensure the application has sufficient permissions to query processes and manage windows. 