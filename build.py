import os
import subprocess
import sys

def upgrade_pip():
    """Upgrade pip to the latest version"""
    print("Upgrading pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to upgrade pip: {e}")
        print("Continuing with build process...")

def install_package(package):
    """Install a single package"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing {package}: {e}")
        return False

def install_requirements():
    """Install required packages one by one"""
    print("Installing required packages...")
    packages = [
        "PyQt5==5.15.7",
        "psutil==5.9.4",
        "pygetwindow==0.0.9",
        "pyinstaller==6.14.1",
        "pillow"  # Latest compatible version
    ]
    
    for package in packages:
        if not install_package(package):
            print(f"Failed to install {package}")
            return False
    return True

def verify_icon():
    """Verify that the logo.ico file exists"""
    print("Verifying icon file...")
    if not os.path.exists("logo.ico"):
        raise FileNotFoundError("logo.ico file not found. Please ensure the file exists in the current directory.")

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable...")
    try:
        # First, ensure PyInstaller is in PATH
        pyinstaller_path = os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pyinstaller.exe')
        if not os.path.exists(pyinstaller_path):
            pyinstaller_path = 'pyinstaller'  # Fallback to PATH

        subprocess.check_call([
            pyinstaller_path,
            "--clean",
            "--noconfirm",
            "--icon=logo.ico",
            "--name=Browser Manager",
            "--windowed",
            "--onefile",
            "app.py"
        ])
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        raise

def main():
    """Main build process"""
    try:
        # Upgrade pip first
        upgrade_pip()
        
        # Install requirements
        if not install_requirements():
            raise Exception("Failed to install required packages")
        
        # Verify icon file exists
        verify_icon()
        
        # Build executable
        build_executable()
        
        print("\nBuild completed successfully!")
        print("You can find the executable in the 'dist' folder.")
        
    except Exception as e:
        print(f"\nError during build process: {e}")
        print("\nTroubleshooting steps:")
        print("1. Ensure you have Python 3.7 or higher installed")
        print("2. Try running 'pip install --upgrade pip' manually")
        print("3. Try installing packages manually:")
        print("   pip install PyQt5==5.15.7")
        print("   pip install psutil==5.9.4")
        print("   pip install pygetwindow==0.0.9")
        print("   pip install pyinstaller==6.14.1")
        print("   pip install pillow")
        print("4. Ensure you have write permissions in the current directory")
        print("5. Verify that logo.ico exists in the current directory")
        sys.exit(1)

if __name__ == "__main__":
    main() 