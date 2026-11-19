#!/usr/bin/env python3
"""Record the Agent Genno product demo (75s) with Playwright.

Usage: python3 hackathon/record-demo.py /tmp/demo.webm
Requires: site served at localhost:8099 (see DEMO-SCRIPT.md) and playwright chromium.
"""
import sys, time
from playwright.sync_api import sync_playwright

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/demo.webm"
BASE = "http://localhost:8099"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 810},
        record_video_dir="/tmp/genno-video",
        record_video_size={"width": 1440, "height": 810},
    )
    page = ctx.new_page()

    # Shot 1+2 — hero live stats + steps + prompt (18s)
    page.goto(f"{BASE}/index.html", wait_until="networkidle")
    page.wait_for_timeout(8000)
    page.locator("text=claim in 3 steps").scroll_into_view_if_needed()
    page.wait_for_timeout(6000)
    page.locator("text=trust model").scroll_into_view_if_needed()
    page.wait_for_timeout(4000)
    page.locator("text=claim in 3 steps").scroll_into_view_if_needed()

    # Shot 3 — agent terminal animation (28s)
    page.goto(f"{BASE}/demo.html")
    page.wait_for_timeout(17000)

    # Shot 4+5 — back to site: leaderboard + compliance (25s)
    page.goto(f"{BASE}/index.html", wait_until="networkidle")
    page.locator("text=live leaderboard").scroll_into_view_if_needed()
    page.wait_for_timeout(12000)
    page.locator("text=trust model").scroll_into_view_if_needed()
    page.wait_for_timeout(8000)
    page.locator(".warn").scroll_into_view_if_needed()
    page.wait_for_timeout(5000)

    video = page.video
    ctx.close()
    path = video.path()
    browser.close()

import shutil
shutil.move(path, OUT)
print("saved:", OUT)
