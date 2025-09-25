#!/usr/bin/env python3
"""
Bloomberg Data Broker System Status Monitor
"""

import os
import time
import subprocess
from typing import Tuple, List

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def check_bloomberg_api() -> Tuple[bool, str]:
    """Check whether the Bloomberg Desktop API library is importable."""
    try:
        import blpapi  # noqa: F401 - imported only to confirm availability
        return True, "[OK] Bloomberg API Python bindings installed"
    except ImportError:
        return False, "[ERR] Bloomberg API Python bindings missing"


def check_bloomberg_connection() -> Tuple[bool, str]:
    """Attempt to open a short Bloomberg session to confirm connectivity."""
    try:
        import blpapi

        host = os.getenv("BLOOMBERG_HOST", "localhost")
        port = int(os.getenv("BLOOMBERG_PORT", "8194"))

        session_options = blpapi.SessionOptions()
        session_options.setServerHost(host)
        session_options.setServerPort(port)

        session = blpapi.Session(session_options)
        if session.start():
            session.stop()
            return True, f"[OK] Bloomberg Terminal reachable at {host}:{port}"
        return False, "[ERR] Bloomberg Terminal not responding"
    except Exception as exc:  # pragma: no cover - only triggered on failure
        return False, f"[ERR] Bloomberg connection error: {exc}"[:80]


def check_broker_running() -> Tuple[bool, str]:
    """Inspect whether a process is bound to the broker port."""
    port = int(os.getenv("BROKER_PORT", "8000"))
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if f":{port}" in result.stdout:
            return True, f"[OK] Bloomerg broker service listening on port {port}"
        return False, f"[WARN] No process listening on port {port}"
    except Exception:
        return False, "[ERR] Unable to query local ports"


def check_broker_api() -> Tuple[bool, str]:
    """Hit the broker REST API to confirm HTTP availability."""
    port = int(os.getenv("BROKER_PORT", "8000"))
    api_key = os.getenv("API_KEY", "")
    try:
        response = requests.get(
            f"http://localhost:{port}/blp/fields",
            headers={'x-api-key': api_key} if api_key else {},
            timeout=5,
        )
        if response.status_code == 200:
            return True, "[OK] Broker API responding"
        return False, f"[WARN] Broker API returned HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "[ERR] Broker API connection refused"
    except Exception as exc:  # pragma: no cover - unexpected error
        return False, f"[ERR] Broker API error: {exc}"[:80]


def check_cloudflared_running() -> Tuple[bool, str]:
    """Verify that the Cloudflare tunnel process is active."""
    try:
        result = subprocess.run(
            ['tasklist'], capture_output=True, text=True, timeout=5
        )
        if 'cloudflared.exe' in result.stdout:
            return True, "[OK] Cloudflare tunnel running"
        return False, "[WARN] Cloudflare tunnel not detected"
    except Exception:
        return False, "[ERR] Unable to check Cloudflare tunnel"


def check_env_config() -> Tuple[bool, str]:
    """Confirm essential environment variables are present."""
    issues: List[str] = []

    if not os.getenv("API_KEY"):
        issues.append("API_KEY not set")

    if issues:
        return False, "[WARN] Config issues: " + ", ".join(issues)
    return True, "[OK] Environment configuration looks good"


def gather_status() -> Tuple[List[Tuple[str, bool, str]], bool]:
    """Run all health checks and return the combined status."""
    checks = [
        ("Environment", check_env_config),
        ("Bloomberg API", check_bloomberg_api),
        ("Bloomberg Connection", check_bloomberg_connection),
        ("Broker Process", check_broker_running),
        ("Broker API", check_broker_api),
        ("Cloudflare Tunnel", check_cloudflared_running),
    ]

    results: List[Tuple[str, bool, str]] = []
    all_ok = True

    for label, check in checks:
        try:
            status, message = check()
            results.append((label, status, message))
            if not status:
                all_ok = False
        except Exception as exc:  # pragma: no cover - safeguard
            results.append((label, False, f"[ERR] {exc}"[:80]))
            all_ok = False

    return results, all_ok


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    load_dotenv()

    print("Bloomberg Data Broker - System Status Monitor")
    print("=" * 60)
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            clear_screen()
            print("Bloomberg Data Broker - System Status")
            print("=" * 50)
            print(f"Last Update: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

            results, all_ok = gather_status()
            for label, _, message in results:
                print(f"{label:20} {message}")

            print("=" * 50)
            if all_ok:
                print("OVERALL: ALL SYSTEMS OPERATIONAL")
            else:
                print("OVERALL: CHECK WARNINGS ABOVE")
            print()
            print("Commands: start_bloomberg_broker.bat | stop_bloomberg_broker.bat")
            print()

            for remaining in range(10, 0, -1):
                print(f"\rNext update in {remaining} seconds... ", end="", flush=True)
                time.sleep(1)
            print()
    except KeyboardInterrupt:
        print("\nSystem monitoring stopped.")


if __name__ == "__main__":
    main()
