"""Visit each Streamlit Community Cloud app in a real (headless) browser so it
doesn't go to sleep. If an app is already asleep, click the wake-up button.

Run by .github/workflows/keep-streamlit-awake.yml
"""

import os
import sys

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

APPS = [
    "https://ai-resume-validator.streamlit.app/",
    "https://ai-smart-notes-maker.streamlit.app/",
    "https://haha-funny-bot-h.streamlit.app/",
    "https://rag-for-study-and-reser.streamlit.app/",
    "https://ai-agents-plan-my-trip.streamlit.app/",
]

# Text on the button Streamlit shows for a sleeping app
WAKE_BUTTON = "button:has-text('get this app back up')"


def visit(page, url: str) -> bool:
    print(f"→ {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    except PlaywrightTimeout:
        print("  ✗ page did not load within 60s")
        return False

    # Give the page time to show either the app or the sleep screen
    page.wait_for_timeout(8_000)

    wake = page.locator(WAKE_BUTTON)
    if wake.count() > 0:
        print("  app was asleep, clicking wake-up button")
        wake.first.click()
        # Wait for the app to boot (the button disappears)
        try:
            wake.first.wait_for(state="detached", timeout=240_000)
            print("  ✓ woke up")
        except PlaywrightTimeout:
            print("  ! still starting after 4 min (it will finish on its own)")
        page.wait_for_timeout(15_000)
    else:
        # Stay a little so the visit registers as real activity
        page.wait_for_timeout(15_000)
        print("  ✓ awake")
    return True


def main() -> int:
    failures = 0
    with sync_playwright() as p:
        # BROWSER_CHANNEL=msedge lets you test locally with installed Edge
        channel = os.environ.get("BROWSER_CHANNEL") or None
        browser = p.chromium.launch(channel=channel)
        for url in APPS:
            page = browser.new_page()
            if not visit(page, url):
                failures += 1
            page.close()
        browser.close()
    print(f"\nDone: {len(APPS) - failures}/{len(APPS)} apps visited")
    return 1 if failures == len(APPS) else 0


if __name__ == "__main__":
    sys.exit(main())
