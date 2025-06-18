"""Flask application for the MQT dashboard."""

from __future__ import annotations

from flask import Flask, render_template

from .visualization import create_summary_cards

app = Flask(__name__, template_folder="templates")


@app.route("/")  # type: ignore[misc]
def index() -> str:
    """Return the index page with summary cards."""
    sorted_by_stars, sorted_by_downloads, total_stars, total_downloads = create_summary_cards()
    return render_template(  # type: ignore[no-any-return]
        "index.html",
        sorted_by_stars=sorted_by_stars,
        sorted_by_downloads=sorted_by_downloads,
        total_stars=total_stars,
        total_downloads=total_downloads,
    )


def main() -> None:
    """Run the Flask application."""
    app.run()


if __name__ == "__main__":
    main()
