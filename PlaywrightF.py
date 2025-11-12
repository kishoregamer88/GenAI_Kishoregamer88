# playwright_google_manual_captcha.py
# Playwright (sync) script that detects Google CAPTCHA, pauses for manual solve,
# persists browser profile to reduce future CAPTCHAs, and scrapes search results.

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import time
import sys

SEARCH_QUERY = "SA vs Aus update"
USER_DATA_DIR = "playwright_user_profile"  # directory to persist cookies/session
HEADLESS = False  # MUST be False so you can see and solve CAPTCHA
MAX_RETRIES = 2
SEARCH_INPUT_XPATH = 'xpath=//*[@id="APjFqb"]'  # as provided by you

def is_captcha_page(page) -> bool:
    """Detect common Google 'sorry' / reCAPTCHA patterns."""
    try:
        url = page.url or ""
        if "/sorry/" in url:
            return True
        # look for visible text elements that indicate a captcha/sorry page
        if page.locator("text=I'm not a robot").count() > 0:
            return True
        if page.locator("text=Our systems have detected unusual traffic").count() > 0:
            return True
    except Exception:
        # if any JS context issues, assume not captcha for now
        return False
    return False

def prompt_manual_solve():
    """Instruct the user, pause, and wait for Enter keystroke after manual solve."""
    print("\n" + "="*60)
    print("⚠️  Google presented a CAPTCHA / anti-bot page.")
    print("→ The browser window is open. Please solve the CAPTCHA manually in the browser.")
    print("→ After you solve the CAPTCHA, come back to this terminal and press Enter to continue.")
    print("="*60 + "\n")
    try:
        input("Press Enter after solving the CAPTCHA to continue the script...")
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
        sys.exit(1)

def safe_wait_for_selector(page, selector, timeout=10000) -> bool:
    """Wait for selector presence; returns True if visible, False if timeout."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except PWTimeoutError:
        return False
    except Exception:
        return False

def collect_search_results(page, selector_list, max_items=10):
    """Collect results using locators and a list of fallback selectors."""
    results = []
    for sel in selector_list:
        # attempt with retries to avoid transient navigation issues
        for attempt in range(MAX_RETRIES):
            try:
                if not safe_wait_for_selector(page, sel, timeout=7000):
                    break  # try next selector in list
                loc = page.locator(sel)
                count = loc.count()
                for i in range(min(count, max_items - len(results))):
                    try:
                        a = loc.nth(i)
                        # attempt to get title from <h3> inside anchor or anchor text
                        title = ""
                        try:
                            title = a.locator("h3").inner_text().strip()
                        except Exception:
                            title = a.inner_text().strip()
                        href = a.get_attribute("href") or ""
                        if title and href:
                            results.append({"title": title, "link": href})
                    except Exception:
                        continue
                # if we have enough results, return
                if len(results) >= max_items:
                    return results
                # otherwise try next selector/fallback
                break
            except Exception as e:
                # common transient: Execution context was destroyed
                if attempt + 1 < MAX_RETRIES:
                    time.sleep(0.8)
                    continue
                else:
                    break
    return results

def try_click_news_tab(page):
    """Try to click the 'News' tab on Google search results (best-effort)."""
    try:
        # This selector tries common 'News' tab anchors (localized strings may differ)
        news_locator = page.locator("a:has-text('News'), a[href*='tbm=nws']")
        if news_locator.count() > 0:
            news_locator.first.click()
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(1.0)
            return True
    except Exception:
        pass
    return False

def main():
    with sync_playwright() as p:
        # Launch a persistent context so cookies and session persist between runs
        print(f"Launching Chromium with persistent profile at ./{USER_DATA_DIR} (headful)...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=HEADLESS,
            args=["--start-maximized"],
            viewport={"width": 1366, "height": 768},
        )

        page = context.new_page()
        # set a common user agent to look more like a normal browser
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117 Safari/537.36"})

        try:
            print("Opening https://www.google.com ...")
            page.goto("https://www.google.com", timeout=30000)
        except Exception as e:
            print("Initial navigation error (continuing):", e)

        # If Google shows a CAPTCHA or 'sorry' page, prompt the user to solve it
        if is_captcha_page(page):
            prompt_manual_solve()
            # give page a moment after manual solve
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

        # Use provided XPath search input if present; otherwise fallback to common input
        if safe_wait_for_selector(page, SEARCH_INPUT_XPATH, timeout=6000):
            print("Typing query into XPath search input...")
            try:
                box = page.locator(SEARCH_INPUT_XPATH)
                box.click(timeout=5000)
                box.fill(SEARCH_QUERY, timeout=5000)
                page.keyboard.press("Enter")
            except Exception as e:
                print("Warning: Failed to type via XPath input, falling back. Error:", e)
                try:
                    page.fill("input[name='q']", SEARCH_QUERY)
                    page.keyboard.press("Enter")
                except Exception as e2:
                    print("Failed fallback search input:", e2)
                    context.close()
                    return
        else:
            print("XPath input not found; using generic search box fallback.")
            try:
                page.fill("input[name='q']", SEARCH_QUERY)
                page.keyboard.press("Enter")
            except Exception as e:
                print("Search input failed:", e)
                context.close()
                return

        # Wait for navigation & dynamic content to load
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        time.sleep(1.0)

        # If we landed on a CAPTCHA page after the search, allow manual solve again
        if is_captcha_page(page):
            prompt_manual_solve()
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

        # Collect organic search results with several fallback selectors
        print("Collecting search results (safe locators)...")
        selectors = [
            "div.yuRUbf > a",      # typical google organic container
            "div.g a",             # alternate organic container
            "h3 > a",              # h3 anchor
            "article h3 a",        # news-like blocks
            "a[href^='http']"      # fallback: any http anchor
        ]
        results = collect_search_results(page, selectors, max_items=12)

        # If not many results, try the News tab
        if len(results) < 6:
            print("Trying the 'News' tab (if available)...")
            if try_click_news_tab(page):
                news_selectors = [
                    "article h3 a",
                    "div.SoaBEf a",   # older google news cards
                    "div.NiLAwe a"    # alternative
                ]
                news_results = collect_search_results(page, news_selectors, max_items=12)
                # merge dedup
                existing_links = {r["link"] for r in results}
                for r in news_results:
                    if r["link"] not in existing_links:
                        results.append(r)

        # Final dedupe & print to terminal
        unique = []
        seen = set()
        for r in results:
            href = r.get("link", "")
            if href and href not in seen:
                unique.append(r)
                seen.add(href)

        if not unique:
            print("\n⚠️ No results collected. Possible causes:")
            print("- You may still be on a CAPTCHA page (check browser window).")
            print("- Google changed its markup; selectors need an update.")
            print("- Network or region-based blocking.\n")
            print("If you see a CAPTCHA in the browser, please solve it and re-run the script or press Enter when prompted.")
        else:
            print(f"\n✅ Found {len(unique)} unique results:\n")
            for i, r in enumerate(unique, start=1):
                print(f"{i}. {r['title']}")
                print(f"   🔗 {r['link']}\n")

        # Keep the browser/profile for future runs
        print("Closing context (profile kept). Next run will reuse same profile to reduce future CAPTCHAs.")
        context.close()

if __name__ == "__main__":
    main()
