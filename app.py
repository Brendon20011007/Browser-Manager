import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLabel, QStackedWidget, QMessageBox,
                            QLineEdit, QHBoxLayout, QFrame, QSizePolicy,
                            QFileDialog, QDialog, QFormLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QIcon, QPixmap
import psutil
import pygetwindow as gw
import subprocess
import time
import winreg
import json

class AddBrowserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Custom Browser")
        self.setMinimumWidth(400)
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout(self)
        
        # Browser name input
        self.name_input = QLineEdit()
        layout.addRow("Browser Name:", self.name_input)
        
        # Browser path input
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_exe)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        layout.addRow("Browser Path:", path_layout)
        
        # Incognito flag input
        self.incognito_input = QLineEdit()
        self.incognito_input.setPlaceholderText("e.g., --incognito, --private")
        layout.addRow("Incognito Flag:", self.incognito_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow("", button_layout)
    
    def browse_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Browser Executable",
            "",
            "Executable Files (*.exe)"
        )
        if file_path:
            self.path_input.setText(file_path)
    
    def get_browser_info(self):
        return {
            'name': self.name_input.text(),
            'path': self.path_input.text(),
            'incognito_flag': self.incognito_input.text()
        }

class BrowserDetector(QThread):
    detection_complete = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.custom_browsers = self.load_custom_browsers()
        self.browser_paths = self.get_browser_paths()
    
    def load_custom_browsers(self):
        try:
            with open('custom_browsers.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_custom_browsers(self):
        with open('custom_browsers.json', 'w') as f:
            json.dump(self.custom_browsers, f, indent=4)
    
    def add_custom_browser(self, browser_info):
        self.custom_browsers[browser_info['name']] = {
            'path': browser_info['path'],
            'incognito_flag': browser_info['incognito_flag']
        }
        self.save_custom_browsers()
        # Recalculate browser paths after adding a custom browser
        self.browser_paths = self.get_browser_paths()
    
    def get_browser_paths(self):
        paths = {}
        
        # Common browser paths
        common_paths = {
            'Chrome': [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe')
            ],
            'Opera': [
                r'C:\Program Files\Opera\launcher.exe',
                r'C:\Program Files (x86)\Opera\launcher.exe',
                os.path.expanduser(r'~\AppData\Local\Programs\Opera\launcher.exe')
            ],
            'Brave': [
                r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
                r'C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe',
                os.path.expanduser(r'~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe')
            ],
            'Epic': [
                r'C:\Program Files (x86)\Epic Privacy Browser\epic.exe',
                os.path.expanduser(r'~\AppData\Local\Epic Privacy Browser\epic.exe')
            ],
            'Firefox': [
                r'C:\Program Files\Mozilla Firefox\firefox.exe',
                r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe',
                os.path.expanduser(r'~\AppData\Local\Mozilla Firefox\firefox.exe')
            ],
            'Edge': [
                r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'
            ]
        }
        
        # Try to get paths from registry
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths') as key:
                for browser in common_paths.keys():
                    try:
                        with winreg.OpenKey(key, f'{browser.lower()}.exe') as browser_key:
                            path = winreg.QueryValue(browser_key, None)
                            if path and os.path.exists(path):
                                paths[browser] = path
                    except WindowsError:
                        pass
        except WindowsError:
            pass
        
        # Check common paths if registry lookup failed
        for browser, possible_paths in common_paths.items():
            if browser not in paths:
                for path in possible_paths:
                    if os.path.exists(path):
                        paths[browser] = path
                        break
        
        # Add custom browsers
        paths.update({name: info['path'] for name, info in self.custom_browsers.items()})
        
        return paths
    
    def is_browser_running(self, browser_name):
        try:
            browser_path = self.browser_paths.get(browser_name, '')
            if not browser_path:
                return False

            for proc in psutil.process_iter(['name', 'exe']):
                if proc.info['exe'] and os.path.exists(proc.info['exe']):
                    # Compare the base executable name for a match
                    if os.path.basename(proc.info['exe']).lower() == os.path.basename(browser_path).lower():
                        return True
            return False
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
    
    def run(self):
        results = {}
        # Include both built-in and custom browsers for detection
        all_browsers = set(self.browser_paths.keys()) # Use keys from already updated browser_paths
        for browser in all_browsers:
            results[browser] = self.is_browser_running(browser)
        self.detection_complete.emit(results)

class BrowserActions(QThread):
    def __init__(self, detector):
        super().__init__()
        self.detector = detector  # Use the shared detector instance
        self.browser_paths = self.detector.get_browser_paths()
        self.custom_browsers = self.detector.load_custom_browsers()
        self.browser_incognito_flags = {
            'Chrome': '--incognito',
            'Opera': '--private',
            'Brave': '--incognito',
            'Epic': '--incognito',
            'Firefox': '-private',
            'Edge': '--inprivate'
        }
        # Add custom browser incognito flags
        self.browser_incognito_flags.update(
            {name: info['incognito_flag'] for name, info in self.custom_browsers.items()}
        )
    
    def add_custom_browser(self, browser_info):
        self.detector.add_custom_browser(browser_info)
        # Update browser paths and incognito flags after adding custom browser
        self.browser_paths = self.detector.get_browser_paths()
        self.browser_incognito_flags[browser_info['name']] = browser_info['incognito_flag']
    
    def is_url_open(self, url):
        try:
            windows = gw.getAllWindows()
            for window in windows:
                if url in window.title:
                    return True
            return False
        except Exception:
            return False
    
    def open_url_in_browser(self, browser_name, url):
        if browser_name not in self.browser_paths:
            return False, f"Browser {browser_name} not supported"
        
        browser_path = self.browser_paths[browser_name]
        incognito_flag = self.browser_incognito_flags.get(browser_name, '')
        
        if not os.path.exists(browser_path):
            return False, f"{browser_name} is not installed"
        
        try:
            command = [browser_path, incognito_flag, url] if incognito_flag else [browser_path, url]
            subprocess.Popen(command)
            return True, f"Opening {url} in {browser_name}"
        except Exception as e:
            return False, f"Error opening {browser_name}: {str(e)}"

class BrowserDetectionPage(QWidget):
    def __init__(self, detector):
        super().__init__()
        self.detector = detector  # Use the shared detector instance
        self.init_ui()
        self.detector.detection_complete.connect(self.update_browser_status)
        self.detector.start()
        
        # Set up timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_detection)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Browser Detection")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Status container
        self.status_container = QWidget()
        self.status_layout = QVBoxLayout(self.status_container)
        layout.addWidget(self.status_container)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Detection")
        refresh_btn.clicked.connect(self.refresh_detection)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
    
    def update_browser_status(self, results):
        # Clear existing status widgets
        while self.status_layout.count():
            item = self.status_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add status for each browser
        for browser, is_running in results.items():
            status_frame = QFrame()
            status_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 8px;
                    padding: 10px;
                    margin: 5px;
                }
            """)
            
            status_layout = QHBoxLayout(status_frame)
            
            # Browser name
            name_label = QLabel(browser)
            name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            status_layout.addWidget(name_label)
            
            # Status indicator
            status_label = QLabel("Running" if is_running else "Not Running")
            status_label.setStyleSheet(f"""
                color: {'#28a745' if is_running else '#dc3545'};
                font-weight: bold;
            """)
            status_layout.addWidget(status_label)
            
            self.status_layout.addWidget(status_frame)
    
    def refresh_detection(self):
        self.detector.start()

class BrowserActionPage(QWidget):
    def __init__(self, browser_actions):
        super().__init__()
        self.browser_actions = browser_actions  # Use the shared actions instance
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Browser Actions")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # URL input
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL (e.g., https://office.com)")
        self.url_input.setText("https://office.com")
        url_layout.addWidget(self.url_input)
        
        # Open button
        open_btn = QPushButton("Open URL")
        open_btn.clicked.connect(self.open_url)
        url_layout.addWidget(open_btn)
        
        layout.addLayout(url_layout)
        
        # Browser buttons container
        self.browser_container = QWidget()
        self.browser_layout = QVBoxLayout(self.browser_container)
        layout.addWidget(self.browser_container)
        
        # Add browser buttons
        self.update_browser_buttons()
        
        # Add custom browser button
        add_browser_btn = QPushButton("Add Custom Browser")
        add_browser_btn.clicked.connect(self.add_custom_browser)
        layout.addWidget(add_browser_btn)
        
        layout.addStretch()
    
    def update_browser_buttons(self):
        # Clear existing buttons
        while self.browser_layout.count():
            item = self.browser_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add buttons for each browser
        for browser in self.browser_actions.detector.browser_paths.keys(): # Get paths from the shared detector
            btn = QPushButton(f"Open in {browser}")
            btn.clicked.connect(lambda checked, b=browser: self.open_in_browser(b))
            self.browser_layout.addWidget(btn)
    
    def add_custom_browser(self):
        dialog = AddBrowserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            browser_info = dialog.get_browser_info()
            if browser_info['name'] and browser_info['path']:
                self.browser_actions.add_custom_browser(browser_info)
                self.update_browser_buttons()
                QMessageBox.information(self, "Success", f"Added {browser_info['name']} successfully!")
                # Trigger a refresh on the detection page to show the new browser
                self.parent().parent().detection_page.refresh_detection() # Access the detection page from parent
            else:
                QMessageBox.warning(self, "Error", "Please provide both browser name and path!")
    
    def open_url(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        if self.browser_actions.is_url_open(url):
            reply = QMessageBox.question(
                self, 'URL Already Open',
                f'{url} is already open. Do you want to close and reopen it in incognito mode?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Close existing window
                try:
                    windows = gw.getAllWindows()
                    for window in windows:
                        if url in window.title:
                            window.close()
                except Exception:
                    pass
        
        # Open in default browser (Chrome)
        success, message = self.browser_actions.open_url_in_browser('Chrome', url)
        if not success:
            QMessageBox.warning(self, "Error", message)
    
    def open_in_browser(self, browser_name):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        success, message = self.browser_actions.open_url_in_browser(browser_name, url)
        if not success:
            QMessageBox.warning(self, "Error", message)

class BrowserManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Browser Manager")
        self.setMinimumSize(800, 300)  # Set minimum size instead of fixed size
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create shared instances
        self.detector = BrowserDetector()
        self.browser_actions = BrowserActions(self.detector)

        # Create stacked widget for pages
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Create pages, passing shared instances
        self.detection_page = BrowserDetectionPage(self.detector)
        self.action_page = BrowserActionPage(self.browser_actions)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.detection_page)
        self.stacked_widget.addWidget(self.action_page)
        
        # Create navigation buttons
        nav_layout = QHBoxLayout()
        
        self.detection_btn = QPushButton("Browser Detection")
        self.detection_btn.setCheckable(True)
        self.detection_btn.setChecked(True)
        self.detection_btn.clicked.connect(lambda: self.switch_page(0))
        
        self.action_btn = QPushButton("Browser Actions")
        self.action_btn.setCheckable(True)
        self.action_btn.clicked.connect(lambda: self.switch_page(1))
        
        nav_layout.addWidget(self.detection_btn)
        nav_layout.addWidget(self.action_btn)
        layout.addLayout(nav_layout)
        
        # Apply styles
        self.apply_styles()
    
    def apply_styles(self):
        """Apply custom styles to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:checked {
                background-color: #005A9E;
            }
            QLabel {
                font-size: 14px;
                color: #333333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                font-size: 14px;
            }
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
        """)
        
        # Style navigation buttons
        nav_style = """
            QPushButton {
                background-color: #F0F0F0;
                color: #333333;
                border: 1px solid #CCCCCC;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
            QPushButton:checked {
                background-color: #0078D7;
                color: white;
                border: none;
            }
        """
        self.detection_btn.setStyleSheet(nav_style)
        self.action_btn.setStyleSheet(nav_style)

    def switch_page(self, index):
        """Switch between pages"""
        self.stacked_widget.setCurrentIndex(index)
        self.detection_btn.setChecked(index == 0)
        self.action_btn.setChecked(index == 1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application-wide icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    
    window = BrowserManagerApp()
    window.show()
    sys.exit(app.exec_()) 