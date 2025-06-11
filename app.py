import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QWidget, QLabel, QLineEdit, QMessageBox, 
                            QStackedWidget, QInputDialog, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPalette, QColor
import psutil
import pygetwindow as gw
import subprocess
import time

# Custom styles
STYLE_SHEET = """
QMainWindow {
    background-color: #f0f2f5;
}
QWidget {
    font-family: 'Segoe UI', Arial;
    font-size: 10pt;
}
QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    min-width: 120px;
}
QPushButton:hover {
    background-color: #106ebe;
}
QPushButton:pressed {
    background-color: #005a9e;
}
QLabel {
    color: #323130;
}
QFrame#header {
    background-color: #0078d4;
    color: white;
    padding: 10px;
    border-radius: 4px;
}
QFrame#content {
    background-color: white;
    border-radius: 4px;
    padding: 20px;
}
"""

class BrowserDetector(QThread):
    """
    A QThread subclass for detecting browser status in a non-blocking way.
    Emits a signal with detection results.
    """
    detection_finished = pyqtSignal(dict)

    def __init__(self, browsers_to_detect):
        super().__init__()
        self.browsers_to_detect = browsers_to_detect
        self._is_running = True

    def run(self):
        """
        Runs the browser detection logic.
        Checks for running processes and incognito/private windows.
        """
        results = {}
        for browser_name, exe_name in self.browsers_to_detect.items():
            status = "blue"  # Default: Not running (Blue)
            running_processes = [p for p in psutil.process_iter(['name']) if p.info['name'] == exe_name]

            if running_processes:
                status = "green"  # Running (Normal mode - Green)
                # Check for incognito/private windows
                try:
                    for window in gw.getWindowsWithTitle(browser_name):
                        title_lower = window.title.lower()
                        # Specific checks for common incognito/private window titles
                        if "incognito" in title_lower or "private" in title_lower or "inprivate" in title_lower:
                            status = "red"  # Incognito/Private mode (Red)
                            break
                except gw.PyGetWindowException:
                    # Handle cases where pygetwindow might not find windows or permission issues
                    pass
            results[browser_name] = status
            if not self._is_running:
                break # Stop if requested

        self.detection_finished.emit(results)

    def stop(self):
        """
        Stops the detection thread gracefully.
        """
        self._is_running = False

class BrowserDetectionPage(QWidget):
    """
    Page 1: Browser Detection Dashboard.
    Displays buttons for browser detection and updates their status visually.
    """
    def __init__(self):
        super().__init__()
        self.browsers = {
            "Google Chrome": "chrome.exe",
            "Opera": "opera.exe",
            "Brave": "brave.exe",
            "Epic": "epic.exe",
            "Firefox": "firefox.exe",
            "Edge": "msedge.exe"
        }
        self.browser_buttons = {}
        self.detection_thread = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Header
        header = QFrame()
        header.setObjectName("header")
        header_layout = QVBoxLayout()
        title = QLabel("Browser Detection Dashboard")
        title.setFont(QFont('Segoe UI', 14, QFont.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)
        header.setLayout(header_layout)
        main_layout.addWidget(header)

        # Content
        content = QFrame()
        content.setObjectName("content")
        content_layout = QVBoxLayout()
        
        # Browser grid
        browser_grid = QHBoxLayout()
        for browser_name in self.browsers.keys():
            button = QPushButton(browser_name)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton[status="blue"] { background-color: #0078d4; }
                QPushButton[status="green"] { background-color: #107c10; }
                QPushButton[status="red"] { background-color: #d13438; }
            """)
            button.setProperty("status", "blue")
            button.setFixedSize(100, 40)
            browser_grid.addWidget(button)
            self.browser_buttons[browser_name] = button
        
        content_layout.addLayout(browser_grid)
        
        # Detection button
        self.detection_button = QPushButton("Run Browser Detection")
        self.detection_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 150px;
            }
        """)
        self.detection_button.clicked.connect(self.run_detection)
        content_layout.addWidget(self.detection_button, alignment=Qt.AlignCenter)
        
        content.setLayout(content_layout)
        main_layout.addWidget(content)
        
        self.setLayout(main_layout)

    def run_detection(self):
        """
        Starts the browser detection process in a new thread.
        Disables the detection button during the scan.
        """
        if self.detection_thread and self.detection_thread.isRunning():
            self.detection_thread.stop()
            self.detection_thread.wait()

        self.detection_button.setEnabled(False) # Disable button during detection
        self.detection_thread = BrowserDetector(self.browsers)
        self.detection_thread.detection_finished.connect(self.update_browser_status)
        self.detection_thread.start()

    def update_browser_status(self, results):
        """
        Updates the color of browser buttons based on detection results.
        Re-enables the detection button after the scan.
        """
        for browser_name, status_color in results.items():
            if browser_name in self.browser_buttons:
                self.browser_buttons[browser_name].setProperty("status", status_color)
                self.browser_buttons[browser_name].style().unpolish(self.browser_buttons[browser_name])
                self.browser_buttons[browser_name].style().polish(self.browser_buttons[browser_name])
        self.detection_button.setEnabled(True) # Re-enable button

# Helper function to find a browser window containing a specific URL in its title
# This is a best-effort approach, as not all browsers put the full URL in the window title
def find_browser_window_with_url(browser_name, url_partial):
    try:
        for window in gw.getWindowsWithTitle(browser_name):
            if url_partial.lower() in window.title.lower():
                return window
    except gw.PyGetWindowException:
        pass
    return None

class BrowserActions:
    """
    Encapsulates actions related to opening and managing browser instances.
    """
    BROWSER_PATHS = {
        "Google Chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "Opera": r"C:\Users\Brendon\AppData\Local\Programs\Opera\opera.exe",
        "Brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "Epic": r"C:\Users\Brendon\AppData\Local\Epic Privacy Browser\Application\epic.exe",
        "Firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "Edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    }
    
    # Incognito/Private mode flags for each browser
    BROWSER_INCOGNITO_FLAGS = {
        "Google Chrome": "--incognito",
        "Opera": "--private",
        "Brave": "--incognito",
        "Epic": "--incognito",  # Epic is privacy-focused by default
        "Firefox": "-private",
        "Edge": "--inprivate"
    }
    
    BROWSER_PROCESS_NAMES = {
        "Google Chrome": "chrome.exe",
        "Opera": "opera.exe",
        "Brave": "brave.exe",
        "Epic": "epic.exe",
        "Firefox": "firefox.exe",
        "Edge": "msedge.exe"
    }

    @staticmethod
    def open_url_in_browser(browser_name, url):
        """
        Opens the given URL in the specified browser in incognito/private mode.
        """
        browser_path = BrowserActions.BROWSER_PATHS.get(browser_name)
        incognito_flag = BrowserActions.BROWSER_INCOGNITO_FLAGS.get(browser_name)
        
        if browser_path and incognito_flag:
            try:
                # Construct command with incognito flag
                command = [browser_path, incognito_flag, url]
                subprocess.Popen(command)
                return True
            except FileNotFoundError:
                QMessageBox.warning(None, "Browser Not Found",
                                    f"{browser_name} executable not found at {browser_path}")
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to open {browser_name}: {e}")
        else:
            QMessageBox.warning(None, "Browser Not Supported",
                                f"Actions for {browser_name} are not supported yet.")
        return False

    @staticmethod
    def is_url_open_in_browser(browser_name, url_partial):
        """
        Checks if a given URL (partial match) is open in the specified browser.
        This is a best-effort check based on window titles.
        """
        return find_browser_window_with_url(browser_name, url_partial) is not None

    @staticmethod
    def terminate_browser_process(browser_name):
        """
        Terminates all processes associated with the given browser.
        """
        exe_name = BrowserActions.BROWSER_PROCESS_NAMES.get(browser_name)
        if not exe_name:
            return False
        try:
            # Use taskkill for a robust termination on Windows
            subprocess.run(["taskkill", "/F", "/IM", exe_name], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error terminating {exe_name}: {e.stderr.decode()}")
            return False
        except FileNotFoundError:
            print("taskkill command not found. Ensure it's in your system PATH.")
            return False

class BrowserActionPage(QWidget):
    """
    Page 2: Browser Action Center.
    Allows opening URLs and managing browser instances.
    """
    def __init__(self):
        super().__init__()
        self.browsers = [
            "Google Chrome",
            "Opera",
            "Brave",
            "Epic",
            "Firefox",
            "Edge"
        ]
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Header
        header = QFrame()
        header.setObjectName("header")
        header_layout = QVBoxLayout()
        title = QLabel("Browser Action Center")
        title.setFont(QFont('Segoe UI', 14, QFont.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)
        header.setLayout(header_layout)
        main_layout.addWidget(header)

        # Content
        content = QFrame()
        content.setObjectName("content")
        content_layout = QVBoxLayout()
        
        # Browser buttons grid
        browser_grid = QHBoxLayout()
        for browser_name in self.browsers:
            button = QPushButton(f"Open {browser_name}")
            button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    min-width: 100px;
                }
            """)
            button.setFixedSize(100, 40)
            button.clicked.connect(lambda _, b=browser_name: self.show_action_dialog(b))
            browser_grid.addWidget(button)
        
        content_layout.addLayout(browser_grid)
        content.setLayout(content_layout)
        main_layout.addWidget(content)
        
        self.setLayout(main_layout)

    def show_action_dialog(self, browser_name):
        """
        Shows a dialog for the user to choose an action (open office.com or custom URL).
        """
        options = ["Open office.com", "Open Custom URL"]
        item, ok = QInputDialog.getItem(self, f"Action for {browser_name}",
                                      "Choose an action:", options, 0, False)

        if ok and item:
            if item == "Open office.com":
                self.handle_office_com_action(browser_name)
            elif item == "Open Custom URL":
                self.handle_custom_url_action(browser_name)

    def handle_office_com_action(self, browser_name):
        """
        Handles the action to open office.com.
        Checks if office.com is already open and prompts the user if so.
        """
        office_url = "https://office.com"
        if BrowserActions.is_url_open_in_browser(browser_name, "office.com"):
            reply = QMessageBox.question(self, "Office.com Already Open",
                                       "Office.com is already open. Do you want to close and reopen it?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                if BrowserActions.terminate_browser_process(browser_name):
                    time.sleep(1)  # Give some time for the process to terminate
                    BrowserActions.open_url_in_browser(browser_name, office_url)
                else:
                    QMessageBox.warning(self, "Error", f"Failed to terminate {browser_name}.")
        else:
            BrowserActions.open_url_in_browser(browser_name, office_url)

    def handle_custom_url_action(self, browser_name):
        """
        Handles the action to open a custom URL.
        """
        text, ok = QInputDialog.getText(self, f"Open Custom URL in {browser_name}",
                                       "Enter URL:", QLineEdit.Normal, "https://")
        if ok and text:
            BrowserActions.open_url_in_browser(browser_name, text)

class BrowserManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Browser Manager")
        self.setFixedSize(800, 300)  # Fixed window size
        self.setStyleSheet(STYLE_SHEET)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.detection_page = BrowserDetectionPage()
        self.action_page = BrowserActionPage()

        self.stacked_widget.addWidget(self.detection_page)
        self.stacked_widget.addWidget(self.action_page)

        self.create_navigation_bar()

    def create_navigation_bar(self):
        nav_bar = QWidget()
        nav_layout = QHBoxLayout()
        nav_bar.setLayout(nav_layout)

        btn_detection = QPushButton("Browser Detection")
        btn_detection.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.detection_page))
        nav_layout.addWidget(btn_detection)

        btn_action = QPushButton("Browser Action")
        btn_action.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.action_page))
        nav_layout.addWidget(btn_action)

        main_layout = QVBoxLayout()
        main_layout.addWidget(nav_bar)
        main_layout.addWidget(self.stacked_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BrowserManagerApp()
    window.show()
    sys.exit(app.exec_()) 