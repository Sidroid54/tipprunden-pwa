print("RICHTIGE DATEI AUS C:\\Users\\Simon\\GitHub\\tipprunden-pwa")

from pathlib import Path

from playwright.sync_api import sync_playwright


BACKEND_DIR = Path(__file__).resolve().parent
AUTH_FILE = BACKEND_DIR / "secrets" / "kicker-auth.json"

KICKER_URL = (
    "https://www.kicker.de/managerspiel/interactive/"
    "se-k00012025/group/round/"
    "rn-k000120250033/"
    "010000000000000000000711"
)


def main() -> None:
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="msedge",
            headless=False,
        )
        context = browser.new_context()
        page = context.new_page()

        print("Kicker wird geöffnet …")
        page.goto(
            KICKER_URL,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        print()
        print("1. Melde dich im geöffneten Browser bei kicker an.")
        print("2. Öffne anschließend wieder eure Liga.")
        print("3. Prüfe, ob die Rangliste sichtbar ist.")
        print()

        input(
            "Erst wenn du angemeldet bist und die Rangliste siehst, "
            "hier Enter drücken …"
        )

        context.storage_state(path=str(AUTH_FILE))

        print()
        print(f"Anmeldesitzung gespeichert unter:")
        print(AUTH_FILE)

        browser.close()


if __name__ == "__main__":
    main()