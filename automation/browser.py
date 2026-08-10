"""
Chromium resolution for Playwright.

The bundled browser build in this environment does not always match the
revision the installed Playwright package expects, so the executable is
resolved explicitly instead of relying on the default lookup.
"""
from __future__ import annotations

import glob
import os

LAUNCH_ARGS = ["--no-sandbox", "--disable-dev-shm-usage"]


def chromium_executable() -> str | None:
    """Return an explicit Chromium path, or None to use Playwright's default."""
    env_path = os.environ.get("CHROMIUM_EXECUTABLE")
    if env_path and os.path.exists(env_path):
        return env_path

    roots = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")]
    for root in roots:
        matches = sorted(glob.glob(os.path.join(root, "chromium-*/chrome-linux/chrome")))
        if matches:
            return matches[-1]
    return None


def launch_chromium(playwright, headless: bool = True):
    """Launch Chromium with the resolved executable."""
    return playwright.chromium.launch(
        headless=headless,
        executable_path=chromium_executable(),
        args=LAUNCH_ARGS,
    )
