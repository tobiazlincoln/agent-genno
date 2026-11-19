#!/usr/bin/env python3
"""Record Agent Genno demo synced to VO segments.
Usage: python3 hackathon/record-demo.py /tmp/demo.webm
"""
import sys
from playwright.sync_api import sync_playwright

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/demo.webm"
BASE = "http://localhost:8099"
# shot durations aligned to VO segments (s1..s5 + breath room)
SHOTS = [12.6, 12.6, 21.0, 15.0, 12.0]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 810},
        record_video_dir="/tmp/genno-video",
        record_video_size={"width": 1440, "height": 810},
    )
    page = ctx.new_page()

    # Shot 1 — hero, live stats (s1)
    page.goto(f"{BASE}/index.html", wait_until="domcontentloaded")
    page.wait_for_timeout(800)
    page.wait_for_timeout(SHOTS[0] * 1000)

    # Shot 2 — claim steps + copy prompt (s2)
    page.locator("text=claim in 3 steps").scroll_into_view_if_needed()
    page.wait_for_timeout(SHOTS[1] * 1000)

    # Shot 3 — agent terminal animation (s3)
    page.goto(f"{BASE}/demo.html", wait_until="domcontentloaded")
    page.wait_for_timeout(400)
    page.wait_for_timeout(SHOTS[2] * 1000)

    # Shot 4 — leaderboard (s4)
    page.goto(f"{BASE}/index.html", wait_until="domcontentloaded")
    page.wait_for_timeout(800)
    page.locator("text=live leaderboard").scroll_into_view_if_needed()
    page.wait_for_timeout(SHOTS[3] * 1000)

    # Shot 5 — trust model + risk note (s5)
    page.locator("text=trust model").scroll_into_view_if_needed()
    page.wait_for_timeout(SHOTS[4] * 1000)

    video = page.video
    ctx.close()
    path = video.path()
    browser.close()

import shutil
shutil.move(path, OUT)
print("saved:", OUT)
