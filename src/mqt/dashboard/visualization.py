import pandas as pd


def create_summary_cards():
    df = pd.read_csv("data/mqt.csv", parse_dates=["timestamp"])
    latest_data = df.groupby("repo").last().reset_index()

    latest_data["published_at"] = pd.to_datetime(
        latest_data["published_at"], errors="coerce"
    )
    latest_data["published_at"] = latest_data["published_at"].apply(
        lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "No release"
    )

    latest_data["github_link"] = latest_data["repo"].apply(
        lambda x: f"https://github.com/cda-tum/{x}"
    )
    latest_data["pypi_link"] = latest_data.apply(
        lambda x: f"https://pypi.org/project/{x['repo']}"
        if x["daily_downloads"] != "N/A"
        else "",
        axis=1,
    )

    # Sort by total downloads (without formatting)
    latest_data = latest_data.sort_values(by="total_downloads", ascending=False)

    # Format download numbers
    latest_data["total_downloads"] = latest_data["total_downloads"].apply(
        lambda x: format_count(x) if pd.notnull(x) else "N/A"
    )
    latest_data["daily_downloads"] = latest_data["daily_downloads"].apply(
        lambda x: format_count(x) if pd.notnull(x) else "N/A"
    )
    latest_data["weekly_downloads"] = latest_data["weekly_downloads"].apply(
        lambda x: format_count(x) if pd.notnull(x) else "N/A"
    )
    latest_data["monthly_downloads"] = latest_data["monthly_downloads"].apply(
        lambda x: format_count(x) if pd.notnull(x) else "N/A"
    )

    sorted_by_downloads = latest_data.to_dict(orient="records")
    sorted_by_stars = latest_data.sort_values(by="stars", ascending=False).to_dict(
        orient="records"
    )

    total_stars = latest_data["stars"].sum()
    total_downloads = df["total_downloads"].sum()

    return (
        sorted_by_stars,
        sorted_by_downloads,
        total_stars,
        format_count(total_downloads),
    )


def format_count(count):
    if count >= 1e6:
        return f"{count / 1e6:.1f}m"
    elif count >= 1e3:
        return f"{count / 1e3:.1f}k"
    else:
        return f"{count:.0f}"
