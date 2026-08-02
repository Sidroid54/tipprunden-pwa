import traceback


def main() -> None:
    print("1: Programm wurde gestartet.", flush=True)

    try:
        print("2: Importiere Playwright …", flush=True)
        from playwright.sync_api import sync_playwright

        print("3: Playwright wurde importiert.", flush=True)

        with sync_playwright() as playwright:
            print("4: Playwright wurde gestartet.", flush=True)

            print("5: Starte Chromium …", flush=True)
            browser = playwright.chromium.launch(headless=False)

            print("6: Chromium wurde geöffnet.", flush=True)
            page = browser.new_page()

            print("7: Öffne kicker.de …", flush=True)
            page.goto(
                "https://www.kicker.de",
                wait_until="domcontentloaded",
                timeout=60_000,
            )

            print(f"8: Seitentitel: {page.title()}", flush=True)

            input("Drücke Enter, um den Browser zu schließen …")
            browser.close()

    except Exception:
        print("\nEs ist ein Fehler aufgetreten:\n", flush=True)
        traceback.print_exc()
        input("\nDrücke Enter zum Beenden …")


if __name__ == "__main__":
    main()
