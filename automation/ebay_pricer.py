"""
eBay price guidance automation.
One eBay account works for both US and UK — marketplace is controlled by the URL.
"""

import time
import tempfile
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Category name → eBay category ID (shared across US/UK for the Browse API,
# but eBay's sell form uses its own category tree — we use keyword search instead)
_CONDITION_MAP = {
    "New":  "New",
    "Used": "Used",
    "All":  "Used",
}


def _try_click(page, selectors: list[str], timeout: int = 3000) -> bool:
    for sel in selectors:
        try:
            el = page.wait_for_selector(sel, timeout=timeout)
            if el and el.is_visible():
                el.click()
                return True
        except Exception:
            pass
    return False


def _try_fill(page, selectors: list[str], value: str, timeout: int = 3000) -> bool:
    for sel in selectors:
        try:
            el = page.wait_for_selector(sel, timeout=timeout)
            if el and el.is_visible():
                el.click()
                el.fill(value)
                return True
        except Exception:
            pass
    return False


def get_price_guidance(
    title: str,
    category: str,
    condition: str,
    brand: str,
    image_bytes: bytes | None,
    username: str,
    password: str,
    marketplace: str = "US",
) -> bytes | None:
    """
    Navigate eBay's listing flow to the price guidance / sold prices section.
    Returns a PNG screenshot as bytes, or None on failure.
    """
    base_url = "https://www.ebay.co.uk" if marketplace == "UK" else "https://www.ebay.com"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        # Hide webdriver flag
        context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = context.new_page()

        try:
            # ── Step 1: Login ─────────────────────────────────────────────────
            page.goto(f"{base_url}/signin/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(1)

            _try_fill(page, ["#userid", 'input[type="text"][name="userid"]'], username)
            _try_click(page, [
                "#signin-continue-btn",
                '[data-testid="signin-continue-button"]',
                'button:has-text("Continue")',
            ])
            time.sleep(1)

            _try_fill(page, ["#pass", 'input[type="password"]'], password)
            _try_click(page, [
                "#sgnBt",
                '[data-testid="signin-submit-button"]',
                'button:has-text("Sign in")',
            ])
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(2)

            # ── Step 2: Go to sell / create listing ───────────────────────────
            page.goto(f"{base_url}/sl/sell", wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)

            # ── Step 3: Enter item title ──────────────────────────────────────
            filled = _try_fill(page, [
                'input[placeholder*="Tell us"]',
                'input[placeholder*="Search for your item"]',
                'input[aria-label*="category"]',
                'input[data-testid="search-query-input"]',
                ".sell-home__search input",
                'input[type="search"]',
                '#gh-ac',
            ], f"{brand} {title}".strip())

            if not filled:
                # Fallback: screenshot whatever we have
                return page.screenshot(full_page=False)

            time.sleep(0.5)
            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle", timeout=20000)
            time.sleep(2)

            # ── Step 4: Click through any category or listing-type screens ────
            # Try "Continue listing" / "Start listing" / first category result
            _try_click(page, [
                'button:has-text("Start listing")',
                'button:has-text("Continue listing")',
                'button:has-text("List it")',
                'a:has-text("Start listing")',
                '[data-testid="start-listing-button"]',
                '[data-testid="category-confirm-button"]',
                # Click first category result if a grid appeared
                '.category-selection__item:first-child',
                '[data-category-id]:first-child',
            ], timeout=5000)
            page.wait_for_load_state("networkidle", timeout=20000)
            time.sleep(2)

            # ── Step 5: If a listing form opened, scroll to the pricing section
            price_locators = [
                page.locator('[data-testid="PRICE"]'),
                page.locator('[data-testid="price-section"]'),
                page.locator('section:has(label:has-text("Price"))'),
                page.locator('#price'),
                page.locator('.field-price'),
                page.locator('label:has-text("Buy It Now price")'),
            ]
            for loc in price_locators:
                try:
                    if loc.count() > 0 and loc.first.is_visible():
                        loc.first.scroll_into_view_if_needed()
                        time.sleep(2)
                        break
                except Exception:
                    pass

            # ── Step 6: Screenshot the visible viewport ───────────────────────
            return page.screenshot(full_page=False)

        except Exception as e:
            print(f"[eBay {marketplace}] automation error: {e}")
            try:
                return page.screenshot(full_page=False)
            except Exception:
                return None
        finally:
            browser.close()
