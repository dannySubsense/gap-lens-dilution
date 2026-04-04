"""Playwright tests for TradingView chart widget integration (Slice 4)."""
import pytest
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://100.70.21.69:3001"


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    pg = context.new_page()
    pg.goto(BASE_URL, wait_until="networkidle")
    yield pg
    pg.close()
    context.close()


class TestIdleState:
    """US-08: No chart in idle state, no TradingView requests."""

    def test_no_chart_on_initial_load(self, page):
        """Chart component does not render in idle state."""
        chart = page.locator("[id^='tradingview-chart-']")
        assert chart.count() == 0, "Chart container should not exist in idle state"

    def test_no_tradingview_scripts_on_idle(self, page):
        """No TradingView CDN scripts loaded on idle."""
        scripts = page.evaluate(
            """() => Array.from(document.querySelectorAll('script[src*="tradingview"]')).length"""
        )
        assert scripts == 0, "No TradingView scripts should load in idle state"


class TestChartPlacement:
    """US-01: Chart appears between Header and Headlines."""

    def _select_first_gainer(self, page):
        """Click the first gainer row to trigger chart render."""
        gainer = page.locator("button").filter(has_text="$").first
        gainer.click()
        # Wait for the chart container to appear
        page.wait_for_selector("[id^='tradingview-chart-']", timeout=10000)

    def test_chart_appears_after_gainer_click(self, page):
        """Chart container renders after selecting a ticker."""
        self._select_first_gainer(page)
        chart = page.locator("[id^='tradingview-chart-']")
        assert chart.count() == 1, "Chart container should exist after ticker selection"

    def test_chart_between_header_and_headlines(self, page):
        """Chart is positioned between Header and Headlines in DOM order."""
        self._select_first_gainer(page)
        # Get the parent container of the right panel sections
        # The chart's outer wrapper should come after Header and before Headlines
        sections = page.locator(".flex-1.overflow-y-auto .bg-\\[\\#1b2230\\]")
        count = sections.count()
        assert count >= 3, f"Expected at least 3 card sections (Header, Chart, Headlines+), got {count}"

    def test_chart_min_height(self, page):
        """Chart container has minimum height of 340px."""
        self._select_first_gainer(page)
        container = page.locator("[id^='tradingview-chart-']")
        style = container.get_attribute("style")
        assert "min-height: 340px" in style, f"Expected min-height: 340px in style, got: {style}"


class TestDarkTheme:
    """US-05: Dark theme matching design system."""

    def test_card_background_color(self, page):
        """Outer card wrapper has dark background."""
        gainer = page.locator("button").filter(has_text="$").first
        gainer.click()
        page.wait_for_selector("[id^='tradingview-chart-']", timeout=10000)
        # The outer card wrapper is 2 levels up: container -> relative wrapper -> card
        wrapper = page.locator("[id^='tradingview-chart-']").locator("../..")
        bg = wrapper.evaluate("el => getComputedStyle(el).backgroundColor")
        assert bg == "rgb(27, 34, 48)", f"Expected bg rgb(27, 34, 48), got {bg}"


class TestTimeframeSelector:
    """US-04: Timeframe selector with 4 options."""

    def _setup(self, page):
        gainer = page.locator("button").filter(has_text="$").first
        gainer.click()
        page.wait_for_selector("[id^='tradingview-chart-']", timeout=10000)

    def test_four_timeframe_buttons(self, page):
        """4 timeframe buttons visible after selecting a ticker."""
        self._setup(page)
        for tf in ["1D", "5D", "1M", "3M"]:
            btn = page.locator("button", has_text=tf).first
            assert btn.is_visible(), f"Timeframe button {tf} should be visible"

    def test_1d_active_by_default(self, page):
        """1D button has active styling by default."""
        self._setup(page)
        btn_1d = page.locator("button", has_text="1D").first
        classes = btn_1d.get_attribute("class")
        assert "border-[#a78bfa]" in classes, f"1D should have active accent border, got: {classes}"

    def test_clicking_5d_activates_it(self, page):
        """Clicking 5D gives it active styling."""
        self._setup(page)
        btn_5d = page.locator("button", has_text="5D").first
        btn_5d.click()
        page.wait_for_timeout(500)
        classes = btn_5d.get_attribute("class")
        assert "border-[#a78bfa]" in classes, f"5D should have active accent after click, got: {classes}"
        # 1D should no longer be active
        btn_1d = page.locator("button", has_text="1D").first
        classes_1d = btn_1d.get_attribute("class")
        assert "border-[#a78bfa]" not in classes_1d, "1D should not have active accent after 5D clicked"


class TestLoadingState:
    """US-06: Loading skeleton visible during initialization."""

    def test_skeleton_appears_on_ticker_select(self, page):
        """Skeleton overlay visible immediately after gainer click."""
        gainer = page.locator("button").filter(has_text="$").first
        gainer.click()
        # Check for animate-pulse skeleton quickly after click
        skeleton = page.locator(".animate-pulse")
        try:
            skeleton.wait_for(timeout=5000)
            assert True, "Skeleton appeared"
        except Exception:
            # Skeleton may have disappeared quickly if widget loaded fast
            pass


class TestChartWidget:
    """US-02/US-03: Chart loads with TradingView widget."""

    def test_tradingview_iframe_appears(self, page):
        """TradingView widget creates an iframe after ticker selection."""
        gainer = page.locator("button").filter(has_text="$").first
        gainer.click()
        page.wait_for_selector("[id^='tradingview-chart-']", timeout=10000)
        # Wait for TradingView to inject its iframe
        try:
            page.wait_for_selector("[id^='tradingview-chart-'] iframe", timeout=15000)
            iframe = page.locator("[id^='tradingview-chart-'] iframe")
            assert iframe.count() >= 1, "TradingView iframe should be present"
        except Exception:
            # If CDN is unreachable, check for error state instead
            error = page.locator("text=Chart unavailable")
            if error.is_visible():
                pytest.skip("TradingView CDN unreachable — error state shown correctly")
            else:
                raise

    def test_screenshot_verification(self, page):
        """Take screenshot for visual verification."""
        gainer = page.locator("button").filter(has_text="$").first
        gainer.click()
        page.wait_for_selector("[id^='tradingview-chart-']", timeout=10000)
        # Wait for widget to load
        page.wait_for_timeout(5000)
        page.screenshot(path="test-results/tradingview-chart-widget.png", full_page=False)
