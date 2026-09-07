
import os
import sys
import time
import socket
import subprocess
import tempfile
import shutil

APP_DIR = r"D:\Projects\qR_Codes"
APP_FILE = r"D:\Projects\qR_Codes\app.py"

HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}"

# Separate Chrome profile.
# This makes the QR Codes browser window independent from your normal Chrome.
CHROME_PROFILE = os.path.join(
    tempfile.gettempdir(),
    "QR_Codes_Chrome_Profile"
)


def find_chrome():
    locations = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        ),
    ]

    for path in locations:
        if os.path.exists(path):
            return path

    return None


def port_is_open():
    try:
        with socket.create_connection((HOST, PORT), timeout=1):
            return True
    except OSError:
        return False


def wait_for_server(timeout=60):
    print("Waiting for application...")

    start = time.time()

    while time.time() - start < timeout:
        if port_is_open():
            return True

        time.sleep(0.5)

    return False


def start_app():
    print("Starting application...")

    return subprocess.Popen(
        [sys.executable, APP_FILE],
        cwd=APP_DIR,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )


def stop_app(process):
    if process is None:
        return

    if process.poll() is None:
        print("Stopping application...")

        try:
            process.terminate()
            process.wait(timeout=5)

        except subprocess.TimeoutExpired:
            process.kill()

        except Exception:
            pass


def chrome_is_running(chrome_process):
    return chrome_process.poll() is None


def main():

    chrome = find_chrome()

    if not chrome:
        print("ERROR: Google Chrome was not found.")
        input("Press Enter to exit...")
        return

    # -------------------------------------------------
    # Start application
    # -------------------------------------------------

    app_process = start_app()

    # -------------------------------------------------
    # Wait for application
    # -------------------------------------------------

    if not wait_for_server():

        print()
        print("ERROR: Application did not start.")
        print("Check that app.py runs correctly.")
        print()

        stop_app(app_process)

        input("Press Enter to exit...")
        return

    print("Application is ready.")
    print("Opening QR Codes window...")

    # -------------------------------------------------
    # Create isolated Chrome window
    # -------------------------------------------------

    os.makedirs(CHROME_PROFILE, exist_ok=True)

    chrome_process = subprocess.Popen([
        chrome,

        # Completely separate Chrome instance
        "--user-data-dir=" + CHROME_PROFILE,

        # Application window
        "--app=" + URL,

        # Prevent Chrome from restoring old tabs
        "--no-first-run",
        "--no-default-browser-check",

        # Prevent background Chrome processes
        "--disable-background-mode"
    ])

    print()
    print("----------------------------------------")
    print("QR Codes application is running.")
    print("----------------------------------------")
    print()
    print("Close the QR Codes browser window")
    print("to stop the Python application.")
    print()

    try:

        # Wait for the dedicated Chrome process.
        chrome_process.wait()

    except KeyboardInterrupt:
        pass

    finally:

        print()
        print("QR Codes window closed.")

        # Stop Python application
        stop_app(app_process)

        print("Application stopped.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    finally:
        sys.exit(0)

