"""Keep the dashboard usable while Pepy is unavailable."""

# ruff: file-ignore[pytest-unittest-assertion, pytest-unittest-raises-assertion]

from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd
import requests

from mqt.dashboard.app import app
from mqt.dashboard.data_collection import get_pepy_data
from mqt.dashboard.visualization import create_summary_cards


class PepyOutageTest(unittest.TestCase):
    """Check the PePy failure path and rendered totals."""

    def test_server_error_keeps_totals_unavailable(self) -> None:
        """A PePy outage should preserve honest download figures."""
        for status in (409, 503):
            with self.subTest(status=status):
                response = requests.Response()
                response.status_code = status
                with patch("mqt.dashboard.data_collection.requests.get", return_value=response):
                    self.assertEqual(get_pepy_data("mqt-core"), {"total_downloads": None})

        data = pd.DataFrame({
            "repo": ["mqt-core", "mqt-ddsim", "ddvis"],
            "timestamp": ["2026-11-02"] * 3,
            "published_at": ["2026-11-01T00:00:00Z"] * 3,
            "docs_slug": ["core", "ddsim", None],
            "stars": [10, 20, 3],
            "daily_downloads": [2, 3, None],
            "weekly_downloads": [10, 12, None],
            "monthly_downloads": [30, 40, None],
            "total_downloads": [None, 100, None],
            "latest_release_version": ["1.0"] * 3,
        })
        with patch("mqt.dashboard.visualization.pd.read_csv", return_value=data):
            _, by_downloads, _, total = create_summary_cards()
            html = app.test_client().get("/").get_data(as_text=True)
        self.assertEqual(total, "Unavailable")
        core = next(repo for repo in by_downloads if repo["repo"] == "mqt-core")
        self.assertEqual(core["total_downloads"], "Unavailable")
        self.assertIn("Total Downloads:</strong> Unavailable", html)
        self.assertNotIn("Downloads:", html.split("<h3>ddvis</h3>", 1)[1].split('<div class="links">', 1)[0])

    def test_authentication_error_still_fails(self) -> None:
        """An invalid key should remain a deployment error."""
        response = requests.Response()
        response.status_code = 401
        with (
            patch("mqt.dashboard.data_collection.requests.get", return_value=response),
            self.assertRaises(requests.HTTPError),
        ):
            get_pepy_data("mqt-core")


if __name__ == "__main__":
    unittest.main()
