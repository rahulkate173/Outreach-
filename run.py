#!/usr/bin/env python3
"""Single command to start the Cold Outreach Engine (SMB 02). Backend + frontend on localhost."""
import sys
import threading
import time

def main():
    try:
        import uvicorn
    except ImportError:
        print("Install dependencies first: pip install -r requirements.txt")
        sys.exit(1)

    # Open frontend in browser once server is up
    def open_browser():
        time.sleep(2.5)
        try:
            import webbrowser
            webbrowser.open("http://localhost:8000")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    # Run from project root so backend.* and static/ resolve
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

if __name__ == "__main__":
    main()
