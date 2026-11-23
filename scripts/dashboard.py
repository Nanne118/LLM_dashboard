#!/usr/bin/env python3
"""Run the Promptwise dashboard locally and back up usage to its Git repository."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "usage.json"
MAX_REQUEST_BYTES = 10 * 1024 * 1024


def valid_usage_row(row: object) -> bool:
    if not isinstance(row, dict):
        return False
    if not all(isinstance(row.get(key), str) and row[key].strip() for key in ("id", "project", "model", "createdAt")):
        return False
    if row.get("type") not in ("local", "subscription"):
        return False
    if isinstance(row.get("tokens"), bool) or not isinstance(row.get("tokens"), (int, float)) or not math.isfinite(row["tokens"]) or row["tokens"] < 0:
        return False
    if isinstance(row.get("cost"), bool) or not isinstance(row.get("cost"), (int, float)) or not math.isfinite(row["cost"]) or row["cost"] < 0:
        return False
    try:
        datetime.fromisoformat(row["createdAt"].replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_backup(value: object) -> dict:
    if not isinstance(value, dict) or value.get("format") != "promptwise-usage" or value.get("version") != 1:
        raise ValueError("Expected a Promptwise usage backup (format promptwise-usage, version 1).")
    usage = value.get("usage")
    if not isinstance(usage, list):
        raise ValueError("The usage field must be a list.")
    for index, row in enumerate(usage, start=1):
        if not valid_usage_row(row):
            raise ValueError(f"Usage record {index} is invalid.")
    return {"format": "promptwise-usage", "version": 1, "usage": usage}


def read_backup() -> dict:
    if not DATA_FILE.exists():
        return {"format": "promptwise-usage", "version": 1, "usage": []}
    try:
        return validate_backup(json.loads(DATA_FILE.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(f"Cannot read {DATA_FILE.relative_to(ROOT)}: {error}") from error


def write_backup(value: object) -> dict:
    backup = validate_backup(value)
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=DATA_FILE.parent,
        prefix=".usage-", suffix=".tmp", delete=False
    )
    temporary_path = Path(handle.name)
    try:
        with handle:
            json.dump(backup, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary_path, DATA_FILE)
    finally:
        temporary_path.unlink(missing_ok=True)
    return backup


def backup_to_github() -> str:
    read_backup()
    git = shutil.which("git")
    if not git:
        desktop_git = Path(os.environ.get("LOCALAPPDATA", "")) / "GitHubDesktop"
        candidates = sorted(desktop_git.glob("app-*/resources/app/git/cmd/git.exe"), reverse=True)
        if candidates:
            git = str(candidates[0])
    if not git:
        raise RuntimeError("Git was not found. Install Git for Windows or GitHub Desktop, then try again.")

    def run_git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [git, "-C", str(ROOT), *arguments],
            check=False, text=True, capture_output=True, timeout=120
        )
        if check and result.returncode:
            message = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(message or f"git {' '.join(arguments)} failed.")
        return result

    root = Path(run_git("rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if root != ROOT.resolve():
        raise RuntimeError("The dashboard folder is not the Git repository root.")
    branch = run_git("branch", "--show-current").stdout.strip()
    if not branch:
        raise RuntimeError("Git is in a detached-HEAD state. Switch to your main branch in VS Code.")

    run_git("add", "--", "data/usage.json")
    changed = run_git("diff", "--cached", "--quiet", "--", "data/usage.json", check=False)
    if changed.returncode == 0:
        message = "Usage is already backed up."
    elif changed.returncode == 1:
        run_git("commit", "-m", "Update LLM usage backup", "--", "data/usage.json")
        message = f"Committed usage on {branch}."
    else:
        raise RuntimeError("Could not check the staged usage backup.")

    run_git("push", "origin", f"HEAD:refs/heads/{branch}")
    return f"{message} GitHub is up to date."


def run_backup() -> int:
    try:
        print(backup_to_github())
        return 0
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        message = error.stderr.strip() if isinstance(error, subprocess.TimeoutExpired) and error.stderr else str(error)
        print(f"Backup failed: {message}", file=sys.stderr)
        if "not found" in message.lower() or "authentication" in message.lower():
            print("Sign in to GitHub in VS Code or Git Credential Manager, then try again.", file=sys.stderr)
        return 1


class DashboardServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "PromptwiseLocal/1.0"

    def log_message(self, format_string: str, *args: object) -> None:
        print(f"[dashboard] {format_string % args}")

    def send_json(self, value: object, status: int = 200) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        request_path = unquote(urlsplit(self.path).path)
        if request_path == "/api/usage" or request_path == "/data/usage.json":
            try:
                self.send_json(read_backup())
            except RuntimeError as error:
                self.send_json({"error": str(error)}, 500)
            return

        relative_path = "index.html" if request_path in ("", "/") else request_path.lstrip("/")
        file_path = (ROOT / relative_path).resolve()
        try:
            relative_file_path = file_path.relative_to(ROOT.resolve())
        except ValueError:
            self.send_error(404)
            return
        if any(part.startswith(".") for part in relative_file_path.parts) and relative_file_path.as_posix() != ".nojekyll":
            self.send_error(404)
            return
        if not file_path.is_file():
            self.send_error(404)
            return
        content_type = "text/html; charset=utf-8" if file_path.suffix.lower() == ".html" else "application/octet-stream"
        if file_path.suffix.lower() == ".json":
            content_type = "application/json; charset=utf-8"
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        request_path = urlsplit(self.path).path
        if request_path not in ("/api/usage", "/api/backup"):
            self.send_error(404)
            return
        origin = self.headers.get("Origin")
        origin_parts = urlsplit(origin or "")
        origin_port = origin_parts.port or (443 if origin_parts.scheme == "https" else 80)
        if (
            origin_parts.scheme != "http"
            or origin_parts.hostname not in ("localhost", "127.0.0.1")
            or origin_port != self.server.server_port
        ):
            self.send_error(403, "Dashboard actions are only allowed from this local dashboard.")
            return
        if request_path == "/api/backup":
            try:
                message = backup_to_github()
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                detail = error.stderr.strip() if isinstance(error, subprocess.TimeoutExpired) and error.stderr else str(error)
                self.send_json({"error": f"Backup failed: {detail}"}, 500)
                return
            self.send_json({"message": message})
            return
        if self.headers.get_content_type() != "application/json":
            self.send_error(415, "Content-Type must be application/json.")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > MAX_REQUEST_BYTES:
                raise ValueError("Request body must be between 1 byte and 10 MB.")
            payload = json.loads(self.rfile.read(length))
            backup = write_backup(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError, RuntimeError) as error:
            self.send_json({"error": str(error)}, 400)
            return
        self.send_json(backup)


def serve(port: int, open_browser: bool) -> int:
    host = "127.0.0.1"
    server = DashboardServer((host, port), DashboardHandler)
    url = f"http://{host}:{server.server_port}/"
    print(f"Promptwise is running at {url}", flush=True)
    print("Usage is saved in data/usage.json. Press Ctrl+C to stop.", flush=True)
    if open_browser:
        threading.Timer(0.7, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local LLM usage dashboard.")
    subparsers = parser.add_subparsers(dest="command")
    serve_parser = subparsers.add_parser("serve", help="open the dashboard locally")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.add_argument("--no-browser", action="store_true", help="do not open a browser window")
    subparsers.add_parser("backup", help="commit and push data/usage.json to GitHub")
    arguments = parser.parse_args()

    try:
        if arguments.command == "backup":
            return run_backup()
        if arguments.command == "serve":
            return serve(arguments.port, not arguments.no_browser)
        return serve(8765, True)
    except (OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
