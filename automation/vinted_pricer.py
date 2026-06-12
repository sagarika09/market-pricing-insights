"""
Vinted price guidance automation.
Separate accounts for US (vinted.com) and UK (vinted.co.uk).
"""

import time
import os
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

_BASE_URLS = {
    "US": "https://www.vinted.com",
    "UK": "https://www.vinted.co.uk",
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
    email: str,
    password: str,
    marketplace: str = "UK",
) -> bytes | None:
    """
    Navigate Vinted's listing flow to the price / suggested price section.
    Returns a PNG screenshot as bytes, or None on failure.
    """
    base_url = _BASE_URLS.get(marketplace, _BASE_URLS["UK"])

    # Save image to temp file if provided
    image_path = None
    if image_bytes:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(image_bytes)
            image_path = f.name

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
        context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = context.new_page()

        try:
            # ── Step 1: Login ─────────────────────────────────────────────────
            page.goto(f"{base_url}/login", wait_until="domcontentloaded", timeout=30000)
            time.sleep(1)

            # Accept cookies if banner appears
            _try_click(page, [
                'button:has-text("Accept all")',
                'button:has-text("Accept")',
                '[data-testid="cookie-accept-all"]',
            ], timeout=3000)
            time.sleep(0.5)

            _try_fill(page, [
                'input[name="email"]',
                'input[type="email"]',
                '#email',
                '[data-testid="email-input"]',
            ], email)

            _try_fill(page, [
                'input[name="password"]',
                'input[type="password"]',
                '#password',
                '[data-testid="password-input"]',
            ], password)

            _try_click(page, [
                'button[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Sign in")',
                '[data-testid="login-submit-button"]',
            ])
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(2)

            # ── Step 2: Go to new listing page ───────────────────────────────
            page.goto(f"{base_url}/items/new", wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)

            # Accept cookies again if reappears
            _try_click(page, [
                'button:has-text("Accept all")',
                '[data-testid="cookie-accept-all"]',
            ], timeout=2000)

            # ── Step 3: Upload photo if provided ─────────────────────────────
            if image_path:
                file_input = page.query_selector('input[type="file"]')
                if file_input:
                    file_input.set_input_files(image_path)
                    time.sleep(2)

            # ── Step 4: Fill in title ─────────────────────────────────────────
            _try_fill(page, [
                'input[data-testid="title-input"]',
                'input[name="title"]',
                'input[placeholder*="title"]',
                'input[placeholder*="Title"]',
                'textarea[name="title"]',
            ], f"{brand} {title}".strip())
            time.sleep(0.5)

            # ── Step 5: Navigate forward through the form ─────────────────────
            # Vinted has a multi-step or single-page form depending on device/version
            for _ in range(4):
                _try_click(page, [
                    'button:has-text("Next")',
                    'button:has-text("Continue")',
                    '[data-testid="next-button"]',
                    '[data-testid="submit-button"]',
                ], timeout=3000)
                time.sleep(1.5)
                page.wait_for_load_state("domcontentloaded", timeout=10000)

            # ── Step 6: Scroll to and screenshot the price section ────────────
            price_locators = [
                page.locator('[data-testid="price-input"]'),
                page.locator('[data-testid*="price"]').first,
                page.locator('input[name="price"]'),
                page.locator('label:has-text("Price")'),
                page.locator('section:has(label:has-text("Price"))'),
                page.locator('.price-suggestions'),
                page.locator('[data-testid="pricing-tip"]'),
            ]
            for loc in price_locators:
                try:
                    if loc.count() > 0 and loc.first.is_visible():
                        loc.first.scroll_into_view_if_needed()
                        time.sleep(2)
                        break
                except Exception:
                    pass

            return page.screenshot(full_page=False)

        except Exception as e:
            print(f"[Vinted {marketplace}] automation error: {e}")
            try:
                return page.screenshot(full_page=False)
            except Exception:
                return None
        finally:
            browser.close()
            if image_path and os.path.exists(image_path):
                os.unlink(image_path)
