"""Collects data from GitHub and PyPI for MQT repositories."""

from __future__ import annotations

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
    {"github_repo": "core", "org": "munich-quantum-toolkit", "pypi_package": "mqt-core"},
    {"github_repo": "ddsim", "org": "munich-quantum-toolkit", "pypi_package": "mqt-ddsim"},
    {"github_repo": "qmap", "org": "munich-quantum-toolkit", "pypi_package": "mqt-qmap"},
    {"github_repo": "qcec", "org": "munich-quantum-toolkit", "pypi_package": "mqt-qcec"},
    {"github_repo": "qecc", "org": "munich-quantum-toolkit", "pypi_package": "mqt-qecc"},
    {"github_repo": "bench", "org": "munich-quantum-toolkit", "pypi_package": "mqt-bench"},
    {"github_repo": "predictor", "org": "munich-quantum-toolkit", "pypi_package": "mqt-predictor"},
    {"github_repo": "syrec", "org": "munich-quantum-toolkit", "pypi_package": "mqt-syrec"},
    {"github_repo": "qusat", "org": "munich-quantum-toolkit", "pypi_package": "mqt-qusat"},
    {"github_repo": "debugger", "org": "munich-quantum-toolkit", "pypi_package": "mqt-debugger"},
    {"github_repo": "yaqs", "org": "munich-quantum-toolkit", "pypi_package": "mqt-yaqs"},
    {"github_repo": "naviz", "org": "munich-quantum-toolkit"},
    {"github_repo": "problemsolver", "org": "munich-quantum-toolkit", "pypi_package": "mqt-problemsolver"},
    {"github_repo": "qudits", "org": "munich-quantum-toolkit", "pypi_package": "mqt-qudits"},
    {"github_repo": "ddvis", "org": "munich-quantum-toolkit"},
    {"github_repo": "workflows", "org": "munich-quantum-toolkit"},
    {"github_repo": "templates", "org": "munich-quantum-toolkit"},
    {"github_repo": ".github", "org": "munich-quantum-toolkit"},
    # Repos still in the cda-tum organization
    {"github_repo": "mqt-qao", "org": "cda-tum", "pypi_package": "mqt-qao"},
    {"github_repo": "mqt-planqk", "org": "cda-tum"},
    {"github_repo": "mqt-qubomaker", "org": "cda-tum", "pypi_package": "mqt-qubomaker"},
    {"github_repo": "mqt-ion-shuttler", "org": "cda-tum", "pypi_package": "mqt-ionshuttler"},
    {"github_repo": "mqt-dasqa", "org": "cda-tum"},
]

github_base_url = "https://api.github.com/repos/"
pypistats_base_url = "https://pypistats.org/api/packages/"
pepy_base_url = "https://api.pepy.tech/api/v2/projects/"

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


def get_pypi_data(package: str) -> dict[str, int | float | None]:
    """Fetch download statistics from PyPI for a given package.

    Args:
        package: The name of the package (e.g., "mqt-core").

    Returns:
        A dictionary containing daily, weekly, monthly, and total downloads.
    """
    recent_downloads_url = f"{pypistats_base_url}{package}/recent"
    downloads_response = requests.get(recent_downloads_url, timeout=60)
    downloads = downloads_response.json()
    downloads_data = downloads.get("data", {})
    pepy_data = get_pepy_data(package)
    return {
        "daily_downloads": downloads_data.get("last_day", 0),
        "weekly_downloads": downloads_data.get("last_week", 0),
        "monthly_downloads": downloads_data.get("last_month", 0),
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
