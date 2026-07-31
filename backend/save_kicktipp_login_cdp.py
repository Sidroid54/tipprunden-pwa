from pathlib import Path

from playwright.sync_api import sync_playwright


BACKEND_DIR = Path(__file__).resolve().parent
AUTH_FILE = BACKEND_DIR / "secrets" / "kicktipp-auth.json"


def main() -> None:
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        print("Verbinde mit dem bereits geöffneten Edge …")

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
            "\nPrüfe, dass du bei Kicktipp angemeldet bist "
            "und die Tippübersicht siehst. "
            "Dann hier Enter drücken …"
        )

        context.storage_state(path=str(AUTH_FILE))

        print()
        print("Kicktipp-Anmeldesitzung gespeichert unter:")
        print(AUTH_FILE)


if __name__ == "__main__":
    main()