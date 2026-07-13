# MQT Dashboard

## GitHub Pages deployment

The production dashboard is rebuilt daily at 05:00 CET (06:00 CEST) and on each
push to `main`. The workflow collects current data, renders a static site, and
publishes it to the `gh-pages` branch.

Before the first deployment, add these Actions secrets:

- `PEPY_API_KEY`: the existing Pepy API key for total download counts.
- `PAGES_DEPLOY_TOKEN`: a fine-grained personal access token limited to this
  repository with **Contents: Read and write** permission. GitHub does not build
  a Pages source branch when it is updated with the default `GITHUB_TOKEN`, so
  this token is required for daily publishing and PR previews.

Run the deployment workflow once to create `gh-pages`, then set **Settings →
Pages → Build and deployment → Source** to **Deploy from a branch**, selecting
`gh-pages` and `/ (root)`.

For pull requests from branches in this repository, the preview workflow deploys
to `/pr-preview/pr-<number>/`, posts the preview URL as a PR comment, and
removes it when the PR closes. Fork pull requests do not receive previews because
GitHub does not expose write credentials or repository secrets to them.
