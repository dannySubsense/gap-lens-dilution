"""
Playwright acceptance tests — admin-balance-refresh (Slice 7)

Verifies all browser-testable acceptance criteria (AC-01 through AC-14) for the
AskEdgar admin balance refresh feature. Tests navigate to /admin and stub both
the summary and refresh-balance endpoints to avoid real AskEdgar spend.

Acceptance Criteria covered:
  AC-01  test_ac01_refresh_button_present
  AC-02  test_ac02_single_request_on_click
  AC-03  test_ac03_balance_updates_on_success
  AC-04  test_ac04_timestamp_updates_on_success
  AC-05  test_ac05_cost_displayed_on_success
  AC-05  test_ac05b_cost_unavailable_when_null  (G3 degradation: cost_dollars null)
  AC-06  test_ac06_recent_requests_row_added
  AC-07  test_ac07_button_disabled_during_pending
  AC-08  test_ac08_double_click_single_request
  AC-10  test_ac10_no_request_on_page_load
  AC-13  test_ac13_balance_unchanged_on_error
  AC-14  test_ac14_error_indicator_on_failure
  G1 fix test_null_usage_message_distinct_from_api_error
  Flow 1 test_no_value_fallback_button_clickable

AC-11, AC-12 are covered by tests/test_admin_balance_refresh_route.py (backend pytest).
AC-15 is covered by Gate B grep in Slice 3.

Run:
    QC_BASE_URL=http://<tailscale-ip>:3001 python3 -m pytest tests/test_admin_balance_refresh_playwright.py -v
"""

import asyncio
import json
import os
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright, Page, Route, expect


BASE_URL = os.getenv("QC_BASE_URL", "http://localhost:3001")
DEFAULT_TIMEOUT = 20_000

# ── Mock data ──────────────────────────────────────────────────────────────────

_OLD_BALANCE_DOLLARS = 48.28
_OLD_TS = "2026-06-28T10:00:00Z"

_NEW_BALANCE_DOLLARS = 47.00
_NEW_TS = "2026-06-29T12:00:00Z"

_MOCK_SUMMARY_OLD = {
    "balance_dollars": _OLD_BALANCE_DOLLARS,
    "balance_ts": _OLD_TS,
    "alert_triggered": False,
    "alert_threshold_dollars": 5.0,
    "consumer_7day": [],
    "recent_requests": [],
}

_MOCK_SUMMARY_NEW = {
    "balance_dollars": _NEW_BALANCE_DOLLARS,
    "balance_ts": _NEW_TS,
    "alert_triggered": False,
    "alert_threshold_dollars": 5.0,
    "consumer_7day": [],
    "recent_requests": [
        {
            "id": 1,
            "ts": _NEW_TS,
            "consumer": "admin-refresh",
            "ticker": "AAPL",
            "credits_remaining_dollars": _NEW_BALANCE_DOLLARS,
            "cost_microdollars": 12,
            "cost_dollars": 0.000012,
            "endpoint": "/edgar-online/v2/ents/tickers",
        }
    ],
}

_MOCK_SUMMARY_NULL_BALANCE = {
    "balance_dollars": None,
    "balance_ts": None,
    "alert_triggered": False,
    "alert_threshold_dollars": 5.0,
    "consumer_7day": [],
    "recent_requests": [],
}

_MOCK_REFRESH_SUCCESS = {
    "balance_dollars": _NEW_BALANCE_DOLLARS,
    "balance_ts": _NEW_TS,
    "cost_dollars": 0.000012,
}

_MOCK_REFRESH_NULL_COST = {
    "balance_dollars": _NEW_BALANCE_DOLLARS,
    "balance_ts": _NEW_TS,
    "cost_dollars": None,
}


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def abr_browser():
    """Module-scoped Chromium browser instance for admin balance refresh tests.

    Named 'abr_browser' to avoid collision with the session-scoped 'browser'
    fixture in test_playwright_qc.py.
    """
    async with async_playwright() as pw:
        b = await pw.chromium.launch(headless=True)
        yield b
        await b.close()


@pytest_asyncio.fixture(loop_scope="session")
async def page(abr_browser):
    """Function-scoped page. Each test navigates fresh to /admin after registering
    its own route handlers, keeping tests independent.
    """
    ctx = await abr_browser.new_context()
    p = await ctx.new_page()
    p.set_default_timeout(DEFAULT_TIMEOUT)
    yield p
    await p.close()
    await ctx.close()


# ── Helpers ────────────────────────────────────────────────────────────────────


async def _goto_admin(page: Page) -> None:
    """Navigate to /admin and wait for the BalancePanel refresh button to attach."""
    await page.goto(f"{BASE_URL}/admin", wait_until="domcontentloaded")
    await page.wait_for_selector(
        '[data-testid="balance-refresh-button"]',
        state="attached",
        timeout=DEFAULT_TIMEOUT,
    )


# ── Tests ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ac01_refresh_button_present(page: Page):
    """AC-01: balance-refresh-button is present and visible on /admin."""

    async def handle_summary(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_SUMMARY_OLD)
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    try:
        await _goto_admin(page)
        btn = page.get_by_test_id("balance-refresh-button")
        await expect(btn).to_be_visible()
    finally:
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_ac02_single_request_on_click(page: Page):
    """AC-02: clicking balance-refresh-button sends exactly one request to refresh-balance."""
    request_count: list[int] = []

    async def handle_summary(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_SUMMARY_OLD)
        )

    async def handle_refresh(route: Route) -> None:
        request_count.append(1)
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_REFRESH_SUCCESS)
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    await page.route("**/api/v1/admin/refresh-balance", handle_refresh)
    try:
        await _goto_admin(page)
        btn = page.get_by_test_id("balance-refresh-button")
        await btn.click()
        await page.wait_for_timeout(1_000)

        assert len(request_count) == 1, (
            f"Expected exactly 1 request to refresh-balance on click, got {len(request_count)}"
        )
    finally:
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_ac03_balance_updates_on_success(page: Page):
    """AC-03: balance-value span text changes to the new balance after a successful refresh."""
    summary_call_count = [0]

    async def handle_summary(route: Route) -> None:
        payload = _MOCK_SUMMARY_OLD if summary_call_count[0] == 0 else _MOCK_SUMMARY_NEW
        summary_call_count[0] += 1
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(payload)
        )

    async def handle_refresh(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_REFRESH_SUCCESS)
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    await page.route("**/api/v1/admin/refresh-balance", handle_refresh)
    try:
        await _goto_admin(page)
        value_span = page.get_by_test_id("balance-value")
        initial_text = await value_span.text_content()

        btn = page.get_by_test_id("balance-refresh-button")
        await btn.click()

        # Wait for balance-value to update
        await expect(value_span).not_to_have_text(initial_text or "", timeout=DEFAULT_TIMEOUT)
        updated_text = await value_span.text_content()
        assert updated_text != initial_text, (
            f"Expected balance-value to update after successful refresh, "
            f"but it remained '{initial_text}'"
        )
    finally:
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_ac04_timestamp_updates_on_success(page: Page):
    """AC-04: balance-timestamp text changes to a newer timestamp after a successful refresh."""
    summary_call_count = [0]

    async def handle_summary(route: Route) -> None:
        payload = _MOCK_SUMMARY_OLD if summary_call_count[0] == 0 else _MOCK_SUMMARY_NEW
        summary_call_count[0] += 1
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(payload)
        )

    async def handle_refresh(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_REFRESH_SUCCESS)
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    await page.route("**/api/v1/admin/refresh-balance", handle_refresh)
    try:
        await _goto_admin(page)
        ts_el = page.get_by_test_id("balance-timestamp")
        initial_ts = await ts_el.text_content()

        btn = page.get_by_test_id("balance-refresh-button")
        await btn.click()

        await expect(ts_el).not_to_have_text(initial_ts or "", timeout=DEFAULT_TIMEOUT)
        updated_ts = await ts_el.text_content()
        assert updated_ts != initial_ts, (
            f"Expected balance-timestamp to update after successful refresh, "
            f"but it remained '{initial_ts}'"
        )
    finally:
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_ac05_cost_displayed_on_success(page: Page):
    """AC-05: refresh-cost element is visible and contains the cost figure after success."""

    async def handle_summary(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_SUMMARY_OLD)
        )

    async def handle_refresh(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_REFRESH_SUCCESS)
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    await page.route("**/api/v1/admin/refresh-balance", handle_refresh)
    try:
        await _goto_admin(page)
        btn = page.get_by_test_id("balance-refresh-button")
        await btn.click()

        cost_el = page.get_by_test_id("refresh-cost")
        await expect(cost_el).to_be_visible(timeout=DEFAULT_TIMEOUT)
        cost_text = await cost_el.text_content()
        assert cost_text and "0.000012" in cost_text, (
            f"Expected refresh-cost to contain '0.000012', got '{cost_text}'"
        )
    finally:
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_ac05b_cost_unavailable_when_null(page: Page):
    """AC-05 / G3 degradation: when cost_dollars is null, refresh-cost reads 'unavailable'.

    Verifies the null cost_dollars does not render '$null' or crash the component.
    """

    async def handle_summary(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_SUMMARY_OLD)
        )

    async def handle_refresh(route: Route) -> None:
        await route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(_MOCK_REFRESH_NULL_COST),
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    await page.route("**/api/v1/admin/refresh-balance", handle_refresh)
    try:
        await _goto_admin(page)
        btn = page.get_by_test_id("balance-refresh-button")
        await btn.click()

        cost_el = page.get_by_test_id("refresh-cost")
        await expect(cost_el).to_be_visible(timeout=DEFAULT_TIMEOUT)
        cost_text = await cost_el.text_content()
        assert cost_text and "unavailable" in cost_text.lower(), (
            f"Expected refresh-cost to read 'unavailable' when cost_dollars is null, "
            f"got '{cost_text}'"
        )
        assert "$null" not in (cost_text or ""), (
            "Expected '$null' NOT to appear in refresh-cost when cost_dollars is null"
        )
    finally:
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_ac06_recent_requests_row_added(page: Page):
    """AC-06: RecentRequestsSection table gains exactly one new row after a successful refresh."""
    summary_call_count = [0]

    async def handle_summary(route: Route) -> None:
        # First call returns 0 rows; post-refresh call returns 1 row
        payload = _MOCK_SUMMARY_OLD if summary_call_count[0] == 0 else _MOCK_SUMMARY_NEW
        summary_call_count[0] += 1
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(payload)
        )

    async def handle_refresh(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_REFRESH_SUCCESS)
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    await page.route("**/api/v1/admin/refresh-balance", handle_refresh)
    try:
        await _goto_admin(page)
        rows_before = await page.locator("table tbody tr").count()

        btn = page.get_by_test_id("balance-refresh-button")
        await btn.click()

        # Wait for the re-fetch and table re-render to settle
        await page.wait_for_timeout(1_500)
        rows_after = await page.locator("table tbody tr").count()

        assert rows_after == rows_before + 1, (
            f"Expected recent requests table to gain 1 row after refresh, "
            f"but went from {rows_before} to {rows_after}"
        )
    finally:
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_ac07_button_disabled_during_pending(page: Page):
    """AC-07: balance-refresh-button has the disabled attribute while a refresh is in flight."""
    response_gate: asyncio.Event = asyncio.Event()

    async def handle_summary(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_SUMMARY_OLD)
        )

    async def handle_refresh_delayed(route: Route) -> None:
        # Hold the response until the test has checked the disabled state
        await response_gate.wait()
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_REFRESH_SUCCESS)
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    await page.route("**/api/v1/admin/refresh-balance", handle_refresh_delayed)
    try:
        await _goto_admin(page)
        btn = page.get_by_test_id("balance-refresh-button")

        # Click dispatches the event and returns; the fetch remains in flight
        await btn.click()

        # Button must be disabled while the request is pending
        await expect(btn).to_be_disabled(timeout=5_000)
    finally:
        response_gate.set()  # release gate so the handler can complete
        await page.wait_for_timeout(300)
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_ac08_double_click_single_request(page: Page):
    """AC-08: rapid double-click on balance-refresh-button sends exactly one network request.

    The pending guard in handleRefresh absorbs the second click because the button
    is disabled after the first request starts.
    """
    request_count: list[int] = []
    response_gate: asyncio.Event = asyncio.Event()

    async def handle_summary(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_SUMMARY_OLD)
        )

    async def handle_refresh(route: Route) -> None:
        request_count.append(1)
        await response_gate.wait()
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_REFRESH_SUCCESS)
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    await page.route("**/api/v1/admin/refresh-balance", handle_refresh)
    try:
        await _goto_admin(page)
        btn = page.get_by_test_id("balance-refresh-button")

        # Double-click: click_count=2 (triple_click is not valid in Python Playwright)
        await btn.click(click_count=2)

        # Brief pause to allow any second request to materialise
        await page.wait_for_timeout(500)
        response_gate.set()
        await page.wait_for_timeout(500)

        assert len(request_count) == 1, (
            f"Expected exactly 1 request to refresh-balance on double-click (pending guard), "
            f"got {len(request_count)}"
        )
    finally:
        response_gate.set()
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_ac10_no_request_on_page_load(page: Page):
    """AC-10: navigating to /admin does NOT call refresh-balance (no passive refresh)."""
    refresh_call_count: list[int] = []

    async def handle_summary(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_SUMMARY_OLD)
        )

    async def handle_refresh(route: Route) -> None:
        refresh_call_count.append(1)
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_REFRESH_SUCCESS)
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    await page.route("**/api/v1/admin/refresh-balance", handle_refresh)
    try:
        await _goto_admin(page)
        # Wait long enough for any inadvertent passive request to fire
        await page.wait_for_timeout(1_500)

        assert len(refresh_call_count) == 0, (
            f"Expected zero calls to refresh-balance on page load, "
            f"got {len(refresh_call_count)} (anti-requirement AC-10 violated)"
        )
    finally:
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_ac13_balance_unchanged_on_error(page: Page):
    """AC-13: balance-value span is unchanged after a failed refresh (HTTP 502)."""

    async def handle_summary(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_SUMMARY_OLD)
        )

    async def handle_refresh_502(route: Route) -> None:
        await route.fulfill(
            status=502,
            content_type="application/json",
            body=json.dumps({"code": "api_error", "detail": "AskEdgar returned an error."}),
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    await page.route("**/api/v1/admin/refresh-balance", handle_refresh_502)
    try:
        await _goto_admin(page)
        value_span = page.get_by_test_id("balance-value")
        initial_text = await value_span.text_content()

        btn = page.get_by_test_id("balance-refresh-button")
        await btn.click()

        # Wait for error state to settle
        await page.wait_for_timeout(1_000)

        after_text = await value_span.text_content()
        assert after_text == initial_text, (
            f"Expected balance-value to remain '{initial_text}' after failed refresh, "
            f"got '{after_text}'"
        )
    finally:
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_ac14_error_indicator_on_failure(page: Page):
    """AC-14: refresh-error element is visible and non-empty after a failed refresh."""

    async def handle_summary(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_SUMMARY_OLD)
        )

    async def handle_refresh_502(route: Route) -> None:
        await route.fulfill(
            status=502,
            content_type="application/json",
            body=json.dumps({"code": "api_error", "detail": "AskEdgar returned an error."}),
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    await page.route("**/api/v1/admin/refresh-balance", handle_refresh_502)
    try:
        await _goto_admin(page)
        btn = page.get_by_test_id("balance-refresh-button")
        await btn.click()

        error_el = page.get_by_test_id("refresh-error")
        await expect(error_el).to_be_visible(timeout=DEFAULT_TIMEOUT)
        error_text = await error_el.text_content()
        assert error_text and len(error_text.strip()) > 0, (
            "Expected refresh-error to be non-empty after failed refresh"
        )
    finally:
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_null_usage_message_distinct_from_api_error(page: Page):
    """G1 fix: null_usage 502 and api_error 502 produce distinct error messages.

    Both codes return HTTP 502 — the frontend MUST branch on code, not on
    HTTP status. This test verifies the two messages are not equal and each
    contains its expected text.
    """

    async def handle_summary(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_SUMMARY_OLD)
        )

    await page.route("**/api/v1/admin/summary", handle_summary)

    # ── Sub-case A: null_usage ──────────────────────────────────────────────
    async def handle_null_usage(route: Route) -> None:
        await route.fulfill(
            status=502,
            content_type="application/json",
            body=json.dumps({
                "code": "null_usage",
                "detail": "AskEdgar returned usage: null",
            }),
        )

    await page.route("**/api/v1/admin/refresh-balance", handle_null_usage)
    try:
        await _goto_admin(page)
        btn = page.get_by_test_id("balance-refresh-button")
        await btn.click()

        error_el = page.get_by_test_id("refresh-error")
        await expect(error_el).to_be_visible(timeout=DEFAULT_TIMEOUT)
        null_usage_message = await error_el.text_content()

        assert null_usage_message and "balance may be $0.00 or API key exhausted" in null_usage_message, (
            f"Expected null_usage error to contain 'balance may be $0.00 or API key exhausted', "
            f"got '{null_usage_message}'"
        )
    finally:
        await page.unroute("**/api/v1/admin/refresh-balance")

    # ── Sub-case B: api_error ───────────────────────────────────────────────
    async def handle_api_error(route: Route) -> None:
        await route.fulfill(
            status=502,
            content_type="application/json",
            body=json.dumps({
                "code": "api_error",
                "detail": "AskEdgar returned an error",
            }),
        )

    await page.route("**/api/v1/admin/refresh-balance", handle_api_error)
    try:
        # Navigate fresh so refreshState resets to idle
        await _goto_admin(page)
        btn = page.get_by_test_id("balance-refresh-button")
        await btn.click()

        error_el = page.get_by_test_id("refresh-error")
        await expect(error_el).to_be_visible(timeout=DEFAULT_TIMEOUT)
        api_error_message = await error_el.text_content()

        assert api_error_message and "AskEdgar returned an error. Balance not updated." in api_error_message, (
            f"Expected api_error message to contain 'AskEdgar returned an error. Balance not updated.', "
            f"got '{api_error_message}'"
        )

        # The two messages must not be equal — confirms frontend branches on code
        assert null_usage_message != api_error_message, (
            f"Expected null_usage and api_error to produce distinct error messages, "
            f"but both produced: '{null_usage_message}'"
        )
    finally:
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")


@pytest.mark.asyncio
async def test_no_value_fallback_button_clickable(page: Page):
    """Flow 1 Alternate (UI spec): when balance_dollars is null the fallback button fires handleRefresh.

    Asserts:
    - balance-refresh-button is present and visible in the no-value state
    - balance-value span is absent (no dollar amount rendered)
    - clicking the fallback button completes the full success path
    - refresh-cost becomes visible after success
    """
    summary_call_count = [0]

    async def handle_summary(route: Route) -> None:
        # First call: null balance (no-value state). Subsequent: populated.
        payload = _MOCK_SUMMARY_NULL_BALANCE if summary_call_count[0] == 0 else _MOCK_SUMMARY_NEW
        summary_call_count[0] += 1
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(payload)
        )

    async def handle_refresh(route: Route) -> None:
        await route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_MOCK_REFRESH_SUCCESS)
        )

    await page.route("**/api/v1/admin/summary", handle_summary)
    await page.route("**/api/v1/admin/refresh-balance", handle_refresh)
    try:
        await _goto_admin(page)

        # Fallback ↻ button is present and visible
        btn = page.get_by_test_id("balance-refresh-button")
        await expect(btn).to_be_visible()

        # balance-value span is absent in the no-value state
        value_span = page.get_by_test_id("balance-value")
        await expect(value_span).to_have_count(0)

        # Click the fallback ↻ button — handleRefresh fires
        await btn.click()

        # Full success path completes: refresh-cost becomes visible
        cost_el = page.get_by_test_id("refresh-cost")
        await expect(cost_el).to_be_visible(timeout=DEFAULT_TIMEOUT)
    finally:
        await page.unroute("**/api/v1/admin/refresh-balance")
        await page.unroute("**/api/v1/admin/summary")
