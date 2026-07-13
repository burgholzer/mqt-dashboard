"""Collects data from GitHub and PyPI for MQT repositories."""

from __future__ import annotations

import operator
import os
import time
from datetime import UTC, datetime

import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

repos = [
    # Repos in the munich-quantum-toolkit organization
    {"github_repo": "core", "org": "munich-quantum-toolkit", "pypi_package": "mqt-core", "docs_slug": "core"},
    {"github_repo": "ddsim", "org": "munich-quantum-toolkit", "pypi_package": "mqt-ddsim", "docs_slug": "ddsim"},
    {"github_repo": "qmap", "org": "munich-quantum-toolkit", "pypi_package": "mqt-qmap", "docs_slug": "qmap"},
    {"github_repo": "qcec", "org": "munich-quantum-toolkit", "pypi_package": "mqt-qcec", "docs_slug": "qcec"},
    {"github_repo": "qecc", "org": "munich-quantum-toolkit", "pypi_package": "mqt-qecc", "docs_slug": "qecc"},
    {"github_repo": "bench", "org": "munich-quantum-toolkit", "pypi_package": "mqt-bench", "docs_slug": "bench"},
    {
        "github_repo": "predictor",
        "org": "munich-quantum-toolkit",
        "pypi_package": "mqt-predictor",
        "docs_slug": "predictor",
    },
    {"github_repo": "syrec", "org": "munich-quantum-toolkit", "pypi_package": "mqt-syrec", "docs_slug": "syrec"},
    {"github_repo": "qusat", "org": "munich-quantum-toolkit", "pypi_package": "mqt-qusat", "docs_slug": "qusat"},
    {
        "github_repo": "debugger",
        "org": "munich-quantum-toolkit",
        "pypi_package": "mqt-debugger",
        "docs_slug": "debugger",
    },
    {"github_repo": "yaqs", "org": "munich-quantum-toolkit", "pypi_package": "mqt-yaqs", "docs_slug": "yaqs"},
    {"github_repo": "naviz", "org": "munich-quantum-toolkit", "pypi_package": "mqt-naviz", "docs_slug": "naviz"},
    {
        "github_repo": "problemsolver",
        "org": "munich-quantum-toolkit",
        "pypi_package": "mqt-problemsolver",
        "docs_slug": "problemsolver",
    },
    {"github_repo": "qudits", "org": "munich-quantum-toolkit", "pypi_package": "mqt-qudits", "docs_slug": "qudits"},
    {
        "github_repo": "ionshuttler",
        "org": "munich-quantum-toolkit",
        "pypi_package": "mqt-ionshuttler",
        "docs_slug": "ionshuttler",
    },
    {"github_repo": "ddvis", "org": "munich-quantum-toolkit"},
    {"github_repo": "workflows", "org": "munich-quantum-toolkit"},
    {"github_repo": "templates", "org": "munich-quantum-toolkit"},
    {"github_repo": ".github", "org": "munich-quantum-toolkit"},
]

github_base_url = "https://api.github.com/repos/"
pypistats_base_url = "https://pypistats.org/api/packages/"
pepy_base_url = "https://api.pepy.tech/api/v2/projects/"

# PyPI Stats applies an API-wide IP rate limit. Its documentation asks clients to
# cache requests, and the collector only needs one request per package each run.
pypistats_request_interval_seconds = 12
pypistats_rate_limit_retry_seconds = 60
_last_pypistats_request = 0.0

github_token = os.getenv("GITHUB_TOKEN")
github_headers = {"Authorization": f"token {github_token}"} if github_token else {}

pepy_api_key = os.getenv("PEPY_API_KEY")
pepy_headers = {"X-Api-Key": pepy_api_key} if pepy_api_key else {}


def get_github_data(org: str, repo: str) -> dict[str, int | str | None]:
    """Fetch GitHub data for a given repository.

    Args:
        org: The name of the GitHub organization.
        repo: The name of the repository (e.g., "core").

    Returns:
        A dictionary containing the number of stars, latest release version, and published date.
    """
    url = f"{github_base_url}{org}/{repo}"
    response = requests.get(url, headers=github_headers, timeout=60)
    data = response.json()
    version_url = f"{url}/releases/latest"
    version_response = requests.get(version_url, headers=github_headers, timeout=60)
    version_data = version_response.json()
    return {
        "stars": data.get("stargazers_count", 0),
        "latest_release_version": version_data.get("tag_name", "No release"),
        "published_at": version_data.get("published_at", "No release"),
    }


def get_pepy_data(package: str) -> dict[str, int | float | None]:
    """Fetch download statistics from Pepy for a given package.

    Args:
        package: The name of the package (e.g., "mqt-core").

    Returns:
        A dictionary containing total downloads and other statistics.
    """
    pepy_url = f"{pepy_base_url}{package}"
    while True:
        pepy_response = requests.get(pepy_url, headers=pepy_headers, timeout=60)
        if pepy_response.status_code == 429:
            print("Rate limit exceeded. Waiting 60 seconds before retrying...")
            time.sleep(60)
        else:
            break
    return pepy_response.json()  # type: ignore[no-any-return]


def get_pypistats_data(package: str) -> list[dict[str, int | str]]:
    """Fetch mirror-excluded daily download data while respecting PyPI Stats' limit.

    Returns:
        The daily download records returned by PyPI Stats.
    """
    global _last_pypistats_request  # noqa: PLW0603

    overall_downloads_url = f"{pypistats_base_url}{package}/overall"
    while True:
        elapsed = time.monotonic() - _last_pypistats_request
        if elapsed < pypistats_request_interval_seconds:
            time.sleep(pypistats_request_interval_seconds - elapsed)

        downloads_response = requests.get(
            overall_downloads_url,
            params={"mirrors": "false"},
            timeout=60,
        )
        _last_pypistats_request = time.monotonic()
        if downloads_response.status_code != 429:
            downloads_response.raise_for_status()
            return downloads_response.json().get("data", [])  # type: ignore[no-any-return]

        retry_after = downloads_response.headers.get("Retry-After")
        try:
            retry_seconds = float(retry_after) if retry_after else pypistats_rate_limit_retry_seconds
        except ValueError:
            retry_seconds = pypistats_rate_limit_retry_seconds
        print(f"PyPI Stats rate limit exceeded. Waiting {retry_seconds:g} seconds before retrying...")
        time.sleep(retry_seconds)


def get_pypi_data(package: str) -> dict[str, int | float | None]:
    """Fetch download statistics from PyPI for a given package.

    Args:
        package: The name of the package (e.g., "mqt-core").

    Returns:
        A dictionary containing daily, weekly, monthly, and total downloads.

    Raises:
        ValueError: If PyPI Stats has no daily download data for the package.
    """
    # The /recent endpoint is aggressively IP-rate-limited. The /overall endpoint
    # provides the same daily data, so calculate the documented 1/7/30-day totals
    # locally instead. ``mirrors=false`` keeps the values consistent with /recent.
    daily_downloads = sorted(get_pypistats_data(package), key=operator.itemgetter("date"))
    if not daily_downloads:
        msg = f"PyPI Stats returned no download data for {package}"
        raise ValueError(msg)

    def downloads_for_last_days(days: int) -> int:
        return sum(int(item["downloads"]) for item in daily_downloads[-days:])

    pepy_data = get_pepy_data(package)
    return {
        "daily_downloads": downloads_for_last_days(1),
        "weekly_downloads": downloads_for_last_days(7),
        "monthly_downloads": downloads_for_last_days(30),
        "total_downloads": pepy_data.get("total_downloads", 0),
    }


def collect_data() -> pd.DataFrame:
    """Collect data from GitHub and PyPI for the specified repositories.

    Returns:
        A pandas DataFrame containing the collected data.
    """
    data = []
    timestamp = datetime.now(tz=UTC)
    for repo in repos:
        repo_name = repo["github_repo"]
        repo_org = repo["org"]
        print(f"Collecting data for {repo_org}/{repo_name}...")
        github_data = get_github_data(repo_org, repo_name)
        if "pypi_package" in repo:
            pypi_name = repo["pypi_package"]
            pypi_data = get_pypi_data(pypi_name)
            repo_identifier = pypi_name
        else:
            pypi_data = {
                "daily_downloads": None,
                "weekly_downloads": None,
                "monthly_downloads": None,
                "total_downloads": None,
            }
            repo_identifier = repo_name
        data.append({
            "timestamp": timestamp,
            "repo": repo_identifier,
            "docs_slug": repo.get("docs_slug", None),
            "stars": github_data["stars"],
            "latest_release_version": github_data["latest_release_version"],
            "published_at": github_data["published_at"],
            "daily_downloads": pypi_data["daily_downloads"],
            "weekly_downloads": pypi_data["weekly_downloads"],
            "monthly_downloads": pypi_data["monthly_downloads"],
            "total_downloads": pypi_data["total_downloads"],
        })
    repo_data = pd.DataFrame(data)
    repo_data.to_csv("data/mqt.csv")
    return repo_data


def main() -> None:
    """Main function to collect data and save it to a CSV file."""
    repo_data = collect_data()
    print("Data collection complete. Latest data:")
    print(repo_data)


if __name__ == "__main__":
    main()
