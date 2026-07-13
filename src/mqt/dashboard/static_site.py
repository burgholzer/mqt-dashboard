"""Build a static version of the dashboard for GitHub Pages."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .app import app


def build_static_site(output_directory: Path) -> None:
    """Render the dashboard and copy its static assets to an output directory.

    Args:
        output_directory: Directory that will contain the deployable site.

    Raises:
        RuntimeError: If rendering the dashboard does not succeed.
    """
    response = app.test_client().get("/")
    if response.status_code != 200:
        msg = f"Failed to render the dashboard (HTTP {response.status_code})"
        raise RuntimeError(msg)

    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "index.html").write_bytes(response.data)
    (output_directory / ".nojekyll").touch()
    static_directory = Path(app.static_folder or "")
    shutil.copytree(static_directory, output_directory / "static", dirs_exist_ok=True)


def main() -> None:
    """Build a static dashboard site."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("site"), help="directory for the static site")
    args = parser.parse_args()
    build_static_site(args.output)


if __name__ == "__main__":
    main()
