from flask import Flask, render_template
from .visualization import create_plots, create_summary_table

app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    table = create_summary_table()
    fig1, fig2, fig3 = create_plots()
    plot1 = fig1.to_html(full_html=False)
    plot2 = fig2.to_html(full_html=False)
    plot3 = fig3.to_html(full_html=False)
    return render_template(
        "index.html", table=table, plot1=plot1, plot2=plot2, plot3=plot3
    )


def main() -> None:
    app.run(debug=True)


if __name__ == "__main__":
    main()
