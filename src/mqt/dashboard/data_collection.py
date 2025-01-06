from dotenv import load_dotenv
import os
import requests
import pandas as pd
import time
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

repos = [
    {"name": "mqt-core", "pypi": True},
    {"name": "mqt-ddsim", "pypi": True},
    {"name": "mqt-qmap", "pypi": True},
    {"name": "mqt-qcec", "pypi": True},
    {"name": "mqt-qecc", "pypi": True},
    {"name": "mqt-bench", "pypi": True},
    {"name": "mqt-predictor", "pypi": True},
    {"name": "mqt-qudits", "pypi": True},
    {"name": "mqt-syrec", "pypi": True},
    {"name": "mqt-qusat", "pypi": True},
    {"name": "mqt-qubomaker", "pypi": True},
    {"name": "mqt-qao", "pypi": True},
    {"name": "mqt-debugger", "pypi": True},  # GitHub-only repository (for now)
    {"name": "mqt-ddvis", "pypi": False},  # GitHub-only repository
    {"name": "mqt-ion-shuttler", "pypi": False},  # GitHub-only repository
    {"name": "mqt-dasqa", "pypi": False},  # GitHub-only repository
    {"name": "mqt-workflows", "pypi": False},  # GitHub-only repository
    {"name": "mqt-planqk", "pypi": False},  # GitHub-only repository
    {"name": "mqt", "pypi": False},  # GitHub-only repository
]

github_org = "cda-tum"
github_base_url = f"https://api.github.com/repos/{github_org}/"
pypistats_base_url = "https://pypistats.org/api/packages/"
pepy_base_url = "https://api.pepy.tech/api/v2/projects/"

github_token = os.getenv("GITHUB_TOKEN")
github_headers = {"Authorization": f"token {github_token}"} if github_token else {}

pepy_api_key = os.getenv("PEPY_API_KEY")
pepy_headers = {"X-Api-Key": pepy_api_key} if pepy_api_key else {}


def get_github_data(repo: str):
    url = f"{github_base_url}{repo}"
    response = requests.get(url, headers=github_headers)
    data = response.json()
    version_url = f"{url}/releases/latest"
    version_response = requests.get(version_url, headers=github_headers)
    version_data = version_response.json()
    return {
        "stars": data.get("stargazers_count", 0),
        "latest_release_version": version_data.get("tag_name", "No release"),
        "published_at": version_data.get("published_at", "No release"),
    }


def get_pepy_data(package: str):
    pepy_url = f"{pepy_base_url}{package}"
    while True:
        pepy_response = requests.get(pepy_url, headers=pepy_headers)
        if pepy_response.status_code == 429:
            print("Rate limit exceeded. Waiting 60 seconds before retrying...")
            time.sleep(60)
        else:
            break
    pepy_data = pepy_response.json()
    return pepy_data


def get_pypi_data(package: str):
    recent_downloads_url = f"{pypistats_base_url}{package}/recent"
    downloads_response = requests.get(recent_downloads_url)
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
    data = []
    timestamp = datetime.now()
    for repo in repos:
        repo_name = repo["name"]
        print(f"Collecting data for {repo_name}...")
        github_data = get_github_data(repo_name)
        if repo["pypi"]:
            pypi_data = get_pypi_data(repo_name)
        else:
            pypi_data = {
                "daily_downloads": None,
                "weekly_downloads": None,
                "monthly_downloads": None,
                "total_downloads": None,
            }
        data.append(
            {
                "timestamp": timestamp,
                "repo": repo_name,
                "stars": github_data["stars"],
                "latest_release_version": github_data["latest_release_version"],
                "published_at": github_data["published_at"],
                "daily_downloads": pypi_data["daily_downloads"],
                "weekly_downloads": pypi_data["weekly_downloads"],
                "monthly_downloads": pypi_data["monthly_downloads"],
                "total_downloads": pypi_data["total_downloads"],
            }
        )
    df = pd.DataFrame(data)
    df.to_csv("data/mqt.csv")
    return df


def main() -> None:
    df = collect_data()
    print("Data collection complete. Latest data:")
    print(df)


if __name__ == "__main__":
    main()
