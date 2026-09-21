"""Optional browser regression: DEWEY_BROWSER_TESTS=1 pytest -q tests/test_explorer_browser.py.

Requires Playwright and its Chromium browser. Uses the checked-in review as a
realistic fixture, exporting fresh HTML and PDF assets into pytest's temp folder.
"""
import os
from pathlib import Path

import pytest

from dewey.html_export import write_explorer
from dewey.repo import DeweyRepo

if os.environ.get('DEWEY_BROWSER_TESTS') != '1':
    pytest.skip('Set DEWEY_BROWSER_TESTS=1 to run Chromium checks', allow_module_level=True)

playwright = pytest.importorskip('playwright.sync_api')


def test_explorer_navigation_search_comparison_and_mobile(tmp_path):
    repo = DeweyRepo(Path(__file__).resolve().parents[1] / 'ai-interviewers-review')
    output = tmp_path / 'index.html'
    write_explorer(repo, output)
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(output.as_uri())
        expect = playwright.expect
        expect(page.locator('.claim-card')).to_have_count(4)
        page.locator('.claim-card h3 a').first.click()
        expect(page.get_by_role('heading', name='Follow the evidence')).to_be_visible()
        assert page.locator('.finding').count() > 0
        page.reload()
        expect(page.get_by_role('heading', name='Follow the evidence')).to_be_visible()
        page.get_by_text('View study design and appraisal →').first.click()
        expect(page.get_by_text('Appraisal and applicability', exact=True)).to_be_visible()
        page.locator('[data-tab=sources]').click()
        expect(page.locator('.card')).to_have_count(17)
        assert 'study=' not in page.url and 'claim=' not in page.url
        page.locator('.card h3 a').first.focus()
        page.keyboard.press('Enter')
        expect(page.get_by_text('Studies and evidence', exact=True)).to_be_visible()
        page.locator('[data-tab=evidence]').click()
        page.locator('[data-study]').nth(0).check()
        page.locator('[data-study]').nth(1).check()
        page.get_by_role('button', name='Compare selected (2)').click()
        expect(page.locator('.compare-table')).to_have_count(1)
        page.reload()
        expect(page.locator('.compare-table')).to_have_count(1)
        with page.expect_download() as downloaded:
            page.get_by_role('button', name='Download evidence CSV').click()
        assert downloaded.value.suggested_filename == 'evidence.csv'
        page.locator('[data-tab=graph]').click()
        expect(page.get_by_role('heading', name='Chronological citation network')).to_be_visible()
        page.locator('#q').fill('Lucas')
        page.wait_for_function("state.q === 'Lucas'")
        expect(page.locator('svg')).to_contain_text('Lucas')
        assert page.locator('.graph-node').count() > 0
        page.locator('[data-tab=candidates]').click()
        expect(page.locator('.card')).to_have_count(25)
        page.get_by_role('link', name='Next →', exact=True).click()
        page.wait_for_url('**/*page=2*')
        page.locator('.card h3 a').first.click()
        expect(page.get_by_text('Screening decisions', exact=True)).to_be_visible()
        assert page.evaluate("safeURL('javascript:alert(1)')") == ''
        assert '<img' not in page.evaluate("markdown('<img src=x onerror=alert(1)>')")
        for tab in ['overview', 'sources', 'evidence', 'graph', 'candidates']:
            page.set_viewport_size({'width': 390, 'height': 844})
            page.locator(f'[data-tab={tab}]').click()
            page.wait_for_function('(tab) => state.tab === tab && !state.candidate', arg=tab)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), tab
            if tab == 'sources':
                assert page.locator('.filter-box').get_attribute('open') is None
                assert page.locator('.card').first.bounding_box()['y'] < 700
        assert not errors, errors
        browser.close()
