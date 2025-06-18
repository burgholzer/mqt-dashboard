"""Create summary cards for the MQT dashboard."""

from __future__ import annotations

import pandas as pd


def create_summary_cards() -> tuple[list[dict], list[dict], int, str]:  # type: ignore[type-arg]
    """Create summary cards for the MQT dashboard.

    Returns:
        A tuple containing:
        - A list of repositories sorted by stars.
        - A list of repositories sorted by total downloads.
        - The total number of stars across all repositories.
        - The total number of downloads formatted as a string.
    """
    repo_data = pd.read_csv("data/mqt.csv", parse_dates=["timestamp"])
    latest_data = repo_data.groupby("repo").last().reset_index()

    latest_data["published_at"] = pd.to_datetime(latest_data["published_at"], errors="coerce")
    latest_data["published_at"] = latest_data["published_at"].apply(
        lambda x: x.strftime("%d %B %Y") if pd.notna(x) else "No release"  # type: ignore[redundant-expr]
    )

    latest_data["github_link"] = latest_data["repo"].apply(lambda x: f"https://github.com/cda-tum/{x}")
    latest_data["pypi_link"] = latest_data.apply(
        lambda x: f"https://pypi.org/project/{x['repo']}" if x["daily_downloads"] != "N/A" else "",
        axis=1,
    )

    # Sort by total downloads (without formatting)
    latest_data = latest_data.sort_values(by="total_downloads", ascending=False)

    # Format download numbers
    latest_data["total_downloads"] = latest_data["total_downloads"].apply(format_count)
    latest_data["daily_downloads"] = latest_data["daily_downloads"].apply(format_count)
    latest_data["weekly_downloads"] = latest_data["weekly_downloads"].apply(format_count)
    latest_data["monthly_downloads"] = latest_data["monthly_downloads"].apply(format_count)

    sorted_by_downloads = latest_data.to_dict(orient="records")
    sorted_by_stars = latest_data.sort_values(by="stars", ascending=False).to_dict(orient="records")

    total_stars = latest_data["stars"].sum()
    total_downloads = repo_data["total_downloads"].sum()

    return (
        sorted_by_stars,
        sorted_by_downloads,
        total_stars,
        format_count(total_downloads),
    )


def format_count(count: float) -> str:
    """Format a count into a human-readable string.

    Args:
        count: The count to format.

    Returns:
        A formatted string representing the count.
    """
    if count >= 1e6:
        return f"{count / 1e6:.1f}m"
    if count >= 1e3:
        return f"{count / 1e3:.1f}k"
    return f"{count:.0f}"
