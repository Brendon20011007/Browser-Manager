import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QWidget, QLabel, QLineEdit, QMessageBox, 
                            QStackedWidget, QInputDialog, QFrame, QScrollArea,
                            QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPalette, QColor, QPainter
import psutil
import pygetwindow as gw
import subprocess
import time

class ModernCard(QFrame):
    """Modern card widget for browser items"""
    clicked = pyqtSignal()  # Add the clicked signal
    
    def __init__(self, browser_name, description="", parent=None):
        super().__init__(parent)
        self.browser_name = browser_name
        self.is_dark_mode = False
        self.setup_ui(description)
        self.apply_light_theme()
        # Make the card clickable
        self.setCursor(Qt.PointingHandCursor)
    
    def setup_ui(self, description):
        self.setFixedHeight(80)
        self.setFrameStyle(QFrame.NoFrame)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Left side - Browser info
        left_layout = QVBoxLayout()
        left_layout.setSpacing(5)
        
        # Browser name
        self.name_label = QLabel(self.browser_name)
        self.name_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        left_layout.addWidget(self.name_label)
        
        # Description
        self.desc_label = QLabel(description or f"Manage {self.browser_name} browser")
        self.desc_label.setFont(QFont('Segoe UI', 9))
        left_layout.addWidget(self.desc_label)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        layout.addWidget(left_widget)
        
        # Spacer
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Right side - Controls
        right_layout = QHBoxLayout()
        right_layout.setSpacing(15)
        
        # Status indicator (for detection page)
        self.status_label = QLabel("●")
        self.status_label.setFont(QFont('Segoe UI', 32))  # Increased font size significantly
        self.status_label.setFixedSize(32, 32)  # Increased fixed size
        self.status_label.setAlignment(Qt.AlignCenter)  # Center the dot
        self.status_label.hide()  # Hidden by default
        right_layout.addWidget(self.status_label)
        
        # Action button (for action page)
        self.action_button = QPushButton("Open")
        self.action_button.setFixedSize(80, 35)
        self.action_button.hide()  # Hidden by default
        right_layout.addWidget(self.action_button)
        
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        layout.addWidget(right_widget)
        
        self.setLayout(layout)
    
    def mousePressEvent(self, event):
        """Handle click events on the card"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()  # Emit the clicked signal
    
    def set_detection_mode(self, enabled=True):
        """Configure card for detection page"""
        self.status_label.setVisible(enabled)
        self.action_button.setVisible(not enabled)
    
    def set_action_mode(self, enabled=True):
        """Configure card for action page"""
        self.action_button.setVisible(enabled)
        self.status_label.setVisible(not enabled)
    
    def update_status(self, status):
        """Update browser status (blue/green/red)"""
        colors = {
            'blue': '#0078d4',
            'green': '#107c10', 
            'red': '#d13438'
        }
        color = colors.get(status, '#0078d4')
        self.status_label.setStyleSheet(f"color: {color};")
    
    def apply_dark_theme(self):
        self.is_dark_mode = True
        self.setStyleSheet("""
            ModernCard {
                background-color: #2d2d2d;
                border-radius: 8px;
                border: 1px solid #404040;
            }
            ModernCard:hover {
                background-color: #353535;
                border: 1px solid #505050;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QScrollArea {
                border: none;
                background-color: #2d2d2d;
            }
            QScrollBar:vertical {
                background-color: #404040;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #505050;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #606060;
            }
        """)
        self.desc_label.setStyleSheet("color: #b3b3b3;")
    
    def apply_light_theme(self):
        self.is_dark_mode = False
        self.setStyleSheet("""
            ModernCard {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e1e1e1;
            }
            ModernCard:hover {
                background-color: #f8f9fa;
                border: 1px solid #d1d1d1;
            }
            QLabel {
                color: #323130;
                background: transparent;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
            QScrollBar:vertical {
                background-color: #e1e1e1;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #c1c1c1;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a1a1a1;
            }
        """)
        self.desc_label.setStyleSheet("color: #666666;")

class BrowserDetector(QThread):
    detection_finished = pyqtSignal(dict)

    def __init__(self, browsers_to_detect):
        super().__init__()
        self.browsers_to_detect = browsers_to_detect
        self._is_running = True

    def run(self):
        results = {}
        for browser_name, exe_name in self.browsers_to_detect.items():
            status = "blue"
            running_processes = [p for p in psutil.process_iter(['name']) if p.info['name'] == exe_name]

            if running_processes:
                status = "green"
                try:
                    for window in gw.getWindowsWithTitle(browser_name):
                        title_lower = window.title.lower()
                        if "incognito" in title_lower or "private" in title_lower or "inprivate" in title_lower:
                            status = "red"
                            break
                except gw.PyGetWindowException:
                    pass
            results[browser_name] = status
            if not self._is_running:
                break

        self.detection_finished.emit(results)

    def stop(self):
        self._is_running = False

class BrowserActions:
    BROWSER_PATHS = {
        "Google Chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "Opera": r"C:\Users\Brendon\AppData\Local\Programs\Opera\opera.exe",
        "Brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "Epic": r"C:\Users\Brendon\AppData\Local\Epic Privacy Browser\Application\epic.exe",
        "Firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "Edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    }
    
    BROWSER_INCOGNITO_FLAGS = {
        "Google Chrome": "--incognito",
        "Opera": "--private",
        "Brave": "--incognito",
        "Epic": "--incognito",
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
        browser_path = BrowserActions.BROWSER_PATHS.get(browser_name)
        incognito_flag = BrowserActions.BROWSER_INCOGNITO_FLAGS.get(browser_name)
        
        if browser_path and incognito_flag:
            try:
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
        try:
            for window in gw.getWindowsWithTitle(browser_name):
                if url_partial.lower() in window.title.lower():
                    return True
        except gw.PyGetWindowException:
            pass
        return False

    @staticmethod
    def terminate_browser_process(browser_name):
        exe_name = BrowserActions.BROWSER_PROCESS_NAMES.get(browser_name)
        if not exe_name:
            return False
        try:
            subprocess.run(["taskkill", "/F", "/IM", exe_name], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error terminating {exe_name}: {e.stderr.decode()}")
            return False
        except FileNotFoundError:
            print("taskkill command not found. Ensure it's in your system PATH.")
            return False

class BrowserDetectionPage(QWidget):
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
        self.browser_cards = {}
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
        
        # Browser cards
        for browser_name in self.browsers.keys():
            card = ModernCard(browser_name)
            card.set_detection_mode(True)
            # Connect the card's clicked signal to the detection function
            card.clicked.connect(lambda checked, b=browser_name: self.detect_single_browser(b))
            content_layout.addWidget(card)
            self.browser_cards[browser_name] = card
        
        # Detection button
        self.detection_button = QPushButton("Run Browser Detection")
        self.detection_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                min-width: 180px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.detection_button.clicked.connect(self.run_detection)
        content_layout.addWidget(self.detection_button, alignment=Qt.AlignCenter)
        
        content.setLayout(content_layout)
        main_layout.addWidget(content)
        
        self.setLayout(main_layout)

    def detect_single_browser(self, browser_name):
        """Detect status for a single browser"""
        exe_name = self.browsers[browser_name]
        status = "blue"
        running_processes = [p for p in psutil.process_iter(['name']) if p.info['name'] == exe_name]

        if running_processes:
            status = "green"
            try:
                for window in gw.getWindowsWithTitle(browser_name):
                    title_lower = window.title.lower()
                    if "incognito" in title_lower or "private" in title_lower or "inprivate" in title_lower:
                        status = "red"
                        break
            except gw.PyGetWindowException:
                pass

        if browser_name in self.browser_cards:
            self.browser_cards[browser_name].update_status(status)

    def run_detection(self):
        """Run detection for all browsers"""
        if self.detection_thread and self.detection_thread.isRunning():
            self.detection_thread.stop()
            self.detection_thread.wait()

        self.detection_button.setEnabled(False)
        self.detection_thread = BrowserDetector(self.browsers)
        self.detection_thread.detection_finished.connect(self.update_browser_status)
        self.detection_thread.start()

    def update_browser_status(self, results):
        """Update status for all browsers"""
        for browser_name, status_color in results.items():
            if browser_name in self.browser_cards:
                self.browser_cards[browser_name].update_status(status_color)
        self.detection_button.setEnabled(True)

class BrowserActionPage(QWidget):
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
        self.browser_cards = {}
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
        
        # Browser cards
        for browser_name in self.browsers:
            card = ModernCard(browser_name)
            card.set_action_mode(True)
            card.action_button.clicked.connect(lambda checked, b=browser_name: self.show_action_dialog(b))
            content_layout.addWidget(card)
            self.browser_cards[browser_name] = card
        
        content.setLayout(content_layout)
        main_layout.addWidget(content)
        
        self.setLayout(main_layout)

    def show_action_dialog(self, browser_name):
        options = ["Open office.com", "Open Custom URL"]
        item, ok = QInputDialog.getItem(self, f"Action for {browser_name}",
                                      "Choose an action:", options, 0, False)

        if ok and item:
            if item == "Open office.com":
                self.handle_office_com_action(browser_name)
            elif item == "Open Custom URL":
                self.handle_custom_url_action(browser_name)

    def handle_office_com_action(self, browser_name):
        office_url = "https://office.com"
        if BrowserActions.is_url_open_in_browser(browser_name, "office.com"):
            reply = QMessageBox.question(self, "Office.com Already Open",
                                       "Office.com is already open. Do you want to close and reopen it?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                if BrowserActions.terminate_browser_process(browser_name):
                    time.sleep(1)
                    BrowserActions.open_url_in_browser(browser_name, office_url)
                else:
                    QMessageBox.warning(self, "Error", f"Failed to terminate {browser_name}.")
        else:
            BrowserActions.open_url_in_browser(browser_name, office_url)

    def handle_custom_url_action(self, browser_name):
        text, ok = QInputDialog.getText(self, f"Open Custom URL in {browser_name}",
                                       "Enter URL:", QLineEdit.Normal, "https://")
        if ok and text:
            BrowserActions.open_url_in_browser(browser_name, text)

class BrowserManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Browser Manager")
        self.setMinimumSize(800, 300)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QWidget {
                font-family: 'Segoe UI', Arial;
                font-size: 10pt;
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
        """)

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