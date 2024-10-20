from flask import Flask, render_template
from .visualization import create_summary_cards

app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    sorted_by_stars, sorted_by_downloads, total_stars, total_downloads = (
        create_summary_cards()
    )
    return render_template(
        "index.html",
        sorted_by_stars=sorted_by_stars,
        sorted_by_downloads=sorted_by_downloads,
        total_stars=total_stars,
        total_downloads=total_downloads,
    )


def main() -> None:
    app.run(debug=True)


if __name__ == "__main__":
    main()
