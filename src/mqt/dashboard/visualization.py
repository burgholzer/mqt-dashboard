import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import matplotlib.cm as cm

# Function to format download counts
def format_count(count):
    if count >= 1e6:
        return f"{count / 1e6:.1f}m"
    elif count >= 1e3:
        return f"{count / 1e3:.1f}k"
    else:
        return f"{count:.0f}"


def generate_vibrant_colors(num_colors):
    colors = cm.get_cmap('tab20', num_colors)
    return [f'#{int(colors(i)[0]*255):02x}{int(colors(i)[1]*255):02x}{int(colors(i)[2]*255):02x}' for i in range(num_colors)]

def create_plots():
    df = pd.read_csv("data/mqt.csv", parse_dates=["timestamp"])

    daily_data = df.groupby(['timestamp', 'repo']).sum().reset_index()

    sum_data = daily_data.groupby('timestamp').sum().reset_index()
    sum_data["repo"] = "All Repos"
    daily_data = pd.concat([daily_data, sum_data])

    num_repos = daily_data["repo"].nunique() - 1
    vibrant_colors = generate_vibrant_colors(num_repos)

    max_stars = daily_data[daily_data["repo"] == "All Repos"]["stars"].max()
    max_downloads = daily_data[daily_data["repo"] == "All Repos"]["total_downloads"].max()

    fig1 = go.Figure()
    for i, repo in enumerate(daily_data["repo"].unique()):
        if repo != "All Repos":
            repo_data = daily_data[daily_data["repo"] == repo]
            fig1.add_trace(go.Scatter(x=repo_data["timestamp"], y=repo_data["stars"], mode='lines+markers', name=f"{repo} Stars", line=dict(color=vibrant_colors[i])))

    fig1.update_layout(
        title_text="GitHub Stars Over Time",
        xaxis_title="Date",
        yaxis_title="Stars",
        template="plotly_dark",
        xaxis=dict(tickformat="%m-%Y", tickvals=daily_data['timestamp'].unique()),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white")
    )

    fig2 = go.Figure()
    for i, repo in enumerate(daily_data["repo"].unique()):
        if repo != "All Repos" and repo != "mqt-ddvis":
            repo_data = daily_data[daily_data["repo"] == repo]
            fig2.add_trace(go.Scatter(x=repo_data["timestamp"], y=repo_data["total_downloads"], mode='lines+markers', name=f"{repo} Downloads", line=dict(color=vibrant_colors[i])))

    fig2.update_layout(
        title_text="PyPI Downloads Over Time",
        xaxis_title="Date",
        yaxis_title="Downloads",
        template="plotly_dark",
        xaxis=dict(tickformat="%m-%Y", tickvals=daily_data['timestamp'].unique()),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white")
    )

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])

    total_data = daily_data[daily_data["repo"] == "All Repos"]
    fig3.add_trace(go.Scatter(x=total_data["timestamp"], y=total_data["stars"], mode='lines+markers', name="Total Stars", line=dict(color=vibrant_colors[0])), secondary_y=False)
    fig3.add_trace(go.Scatter(x=total_data["timestamp"], y=total_data["total_downloads"], mode='lines+markers', name="Total Downloads", line=dict(color=vibrant_colors[1])), secondary_y=True)

    fig3.update_layout(
        title_text="Total GitHub Stars and PyPI Downloads Over Time",
        xaxis_title="Date",
        template="plotly_dark",
        xaxis=dict(tickformat="%m-%Y", tickvals=daily_data['timestamp'].unique()),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white")
    )
    fig3.update_yaxes(title_text="Stars", secondary_y=False, range=[0, max_stars + max_stars*0.1])
    fig3.update_yaxes(title_text="Downloads (Millions)", secondary_y=True, range=[0, max_downloads + max_downloads*0.1])

    return fig1, fig2, fig3


def create_summary_table():
    df = pd.read_csv("data/mqt.csv", parse_dates=["timestamp"])
    latest_data = df.groupby("repo").last().reset_index()

    # Handle 'No release' string properly
    latest_data["published_at"] = pd.to_datetime(
        latest_data["published_at"], errors="coerce"
    )
    latest_data["published_at"] = latest_data["published_at"].apply(
        lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "No release"
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
    latest_data["total_downloads"] = latest_data["total_downloads"].apply(
        lambda x: format_count(x) if pd.notnull(x) else "N/A"
    )

    latest_data.sort_values(
        by="stars", ascending=False, inplace=True
    )  # Sort by stars descending

    # Rename columns for better presentation
    latest_data.rename(
        columns={
            "repo": "Repository",
            "latest_release_version": "Latest Release Version",
            "published_at": "Published At",
            "stars": "Stars",
            "daily_downloads": "Daily Downloads",
            "weekly_downloads": "Weekly Downloads",
            "monthly_downloads": "Monthly Downloads",
            "total_downloads": "Total Downloads",
        },
        inplace=True,
    )

    # Drop the timestamp column
    latest_data = latest_data.drop(columns=["timestamp"])

    summary_table = latest_data.to_html(
        index=False, classes="table table-striped table-bordered", escape=False
    )

    return summary_table
