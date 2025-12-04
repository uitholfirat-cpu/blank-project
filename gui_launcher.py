import threading
import socket
import time

import uvicorn
import webview

from api import app


HOST = "127.0.0.1"
PORT = 4321


def run_api() -> None:
    """
    Run the FastAPI application with Uvicorn on a background thread.
    """
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


def wait_for_server(host: str, port: int, timeout: float = 15.0) -> bool:
    """
    Wait until a TCP server is accepting connections on (host, port),
    or until timeout (in seconds) expires.
    """
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            if time.time() - start > timeout:
                return False
            time.sleep(0.1)


def main() -> None:
    server_thread = threading.Thread(target=run_api, daemon=True)
    server_thread.start()

    # Give the API server a moment to start up
    wait_for_server(HOST, PORT, timeout=15.0)

    webview.create_window("MasterGrader", f"http://{HOST}:{PORT}")
    webview.start()


if __name__ == "__main__":
    main()