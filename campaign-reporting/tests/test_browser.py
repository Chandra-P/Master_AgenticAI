from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

from campaign_reporting.contracts import CampaignConfig
from campaign_reporting.delivery import render_report
from campaign_reporting.repository import ActorContext, Repository
from campaign_reporting.review import save_draft
from campaign_reporting.runs import prepare_run


@pytest.mark.browser
@pytest.mark.parametrize("width,height", [(1440, 1000), (390, 844)])
def test_report_all_periods_controls_and_no_network(tmp_path, width, height):
    repo = Repository.local(tmp_path / "runs.sqlite")
    actor = ActorContext("browser-check", "juniper", "review")
    run = prepare_run(repo, CampaignConfig())
    run = save_draft(repo, actor, run["run_id"], {"summary": "Synthetic interpretation awaiting review."})
    report = tmp_path / "report.html"
    report.write_bytes(render_report(run))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        errors, external = [], []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on(
            "request", lambda r: external.append(r.url) if r.url.startswith(("http:", "https:")) else None
        )
        page.goto(report.as_uri())
        expect(page.locator("#hero-result")).to_contain_text("Checking accounts")
        page.locator("#branch-map circle").first.click()
        expect(page.locator("#map-detail")).to_contain_text("accounts")
        page.select_option("#period", "60")
        expect(page.locator("#map-detail")).to_contain_text("Select a branch")
        for period in ["30", "60", "90", "120", "F"]:
            page.select_option("#period", period)
            expect(page.locator("#read-date")).to_contain_text("Final" if period == "F" else period + " day")
            expect(page.locator("#channel-table tr")).to_have_count(5)
            expect(page.locator("#branch-map circle")).to_have_count(12)
            if period in ("30", "60", "90"):
                expect(page.locator("#executive-cards")).to_contain_text("Not yet available")
            else:
                assert "Not yet available" not in page.locator("#executive-cards").inner_text()
        for measure in ["balance", "response_rate", "accounts"]:
            page.locator('[data-map="' + measure + '"]').click()
            page.locator("#branch-map circle").first.click()
            expect(page.locator("#map-detail")).to_contain_text("accounts")
        page.locator('[data-share="both"]').click()
        expect(page.locator(".share-bar")).to_have_count(24)
        for details in page.locator("details").all():
            details.locator("summary").click()
            assert details.get_attribute("open") is not None
        for anchor in page.locator("nav a").all():
            anchor.click()
            assert page.url.endswith(anchor.get_attribute("href"))
        assert not errors
        assert not external
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        target = Path("runtime/screenshots")
        target.mkdir(parents=True, exist_ok=True)
        page.locator("#cover").scroll_into_view_if_needed()
        page.screenshot(path=str(target / f"report-{width}.png"), full_page=True)
        browser.close()
