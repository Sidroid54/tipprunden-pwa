from pathlib import Path

from playwright.sync_api import sync_playwright


BACKEND_DIR = Path(__file__).resolve().parent
AUTH_FILE = BACKEND_DIR / "secrets" / "kicker-auth.json"


def main() -> None:
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        print("Verbinde mit dem bereits geöffneten Browser …")

        browser = playwright.chromium.connect_over_cdp(
            "http://127.0.0.1:9222"
        )

        if not browser.contexts:
            raise RuntimeError("Kein Browser-Kontext gefunden.")

        context = browser.contexts[0]

        print(f"Gefundene Tabs: {len(context.pages)}")

        for index, page in enumerate(context.pages):
            print(f"{index}: {page.url}")

        input(
            "Prüfe, dass die kicker-Liga im Browser sichtbar ist. "
            "Dann hier Enter drücken …"
        )

        context.storage_state(path=str(AUTH_FILE))

        print()
        print("Anmeldesitzung gespeichert unter:")
        print(AUTH_FILE)


if __name__ == "__main__":
    main()