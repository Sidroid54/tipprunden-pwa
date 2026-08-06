"""Lokaler Admin-Server für die manuelle Spieltagserfassung."""

from __future__ import annotations

import argparse
import json
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from combine_matchday import load_json
from config import CURRENT_SEASON, PARTICIPANTS, SEASONS
from manual_entry import build_manual_matchday, save_manual_matchday
from publish_changes import publish_generated_data


BACKEND_DIR = Path(__file__).resolve().parent
ADMIN_DIR = BACKEND_DIR / "admin"
PUBLIC_FILE = BACKEND_DIR.parent / "docs" / "data" / f"{CURRENT_SEASON}.json"


class AdminHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ADMIN_DIR), **kwargs)

    def send_json(self, status: int, payload: Any) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 100_000:
            raise ValueError("Ungültige Anfragegröße.")
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Die Anfrage muss ein JSON-Objekt enthalten.")
        return payload

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/state":
            public_payload = load_json(PUBLIC_FILE)
            existing = [item["matchday"] for item in public_payload["matchdays"]]
            self.send_json(
                200,
                {
                    "season": CURRENT_SEASON,
                    "season_label": SEASONS[CURRENT_SEASON]["label"],
                    "participants": PARTICIPANTS,
                    "existing_matchdays": existing,
                },
            )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self.read_json()
            matchday = int(payload.get("matchday"))
            scores = payload.get("scores")
            if not isinstance(scores, dict):
                raise ValueError("Die Punkteliste fehlt.")

            if self.path == "/api/preview":
                _, _, combined = build_manual_matchday(matchday, scores)
                self.send_json(200, {"combined": combined})
                return

            if self.path == "/api/save":
                files = save_manual_matchday(matchday, scores)
                publication = None
                if payload.get("publish") is True:
                    publication = publish_generated_data(matchday)
                self.send_json(
                    200,
                    {"saved": True, "files": files, "publication": publication},
                )
                return

            self.send_json(404, {"error": "Unbekannter API-Endpunkt."})
        except Exception as error:
            self.send_json(400, {"error": str(error)})

    def log_message(self, format: str, *args: Any) -> None:
        print(f"Admin: {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Startet die lokale Admin-Seite.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), AdminHandler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Lokale Admin-Seite: {url}")
    print("Beenden mit Strg+C.")
    if not args.no_browser:
        webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
