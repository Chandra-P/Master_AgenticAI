"""Inspect the running local-only demo without approving or publishing any report."""

from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main():
    output = Path("runtime/screenshots")
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto("http://127.0.0.1:8510")
        expect(page.get_by_role("heading", name="Campaign Decision Desk", exact=True)).to_be_visible(
            timeout=60000
        )
        expect(page.get_by_text("Local synthetic demo", exact=False)).to_be_visible()
        page.screenshot(path=str(output / "analyst-workspace.png"), full_page=True)
        page.get_by_role("tab", name="3 · Analyst review").click()
        page.get_by_role("button", name="Generate draft for review").click()
        expect(
            page.get_by_role("tabpanel", name="3 · Analyst review").get_by_text(
                "offline narrative adapter.", exact=False
            )
        ).to_be_visible(timeout=60000)
        page.get_by_role("tab", name="4 · Report").click()
        frame = page.frame_locator("iframe").first
        expect(frame.locator("#hero-result")).to_contain_text("Checking accounts", timeout=30000)
        expect(page.get_by_role("button", name="Publish approved report")).to_be_disabled()
        page.screenshot(path=str(output / "analyst-report-preview.png"), full_page=True)
        page.get_by_role("tab", name="6 · Evals").click()
        expect(page.get_by_role("heading", name="Evaluation evidence", exact=True)).to_be_visible()
        page.get_by_role("button", name="Run local development benchmark · $0 API").click()
        expect(page.get_by_text("Not measured", exact=True)).to_be_visible(timeout=60000)
        expect(page.get_by_text("Review against the pinned evidence", exact=True)).to_be_visible()
        page.screenshot(path=str(output / "analyst-evals.png"), full_page=True)
        assert not errors, errors
        browser.close()
    print(
        "Live analyst screen, draft preview and client-scoped Evals verified; no approval/publication performed."
    )


if __name__ == "__main__":
    main()
