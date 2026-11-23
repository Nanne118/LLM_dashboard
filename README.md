# Promptwise LLM usage dashboard

A small local dashboard for tracking LLM runs by project, model, and local-versus-subscription usage. It uses Python's standard library; no packages or VS Code extension are needed.

## The simple workflow

1. Open this repository folder in VS Code.
2. Press **Ctrl+Shift+P**, choose **Tasks: Run Task**, then run **Promptwise: Open local dashboard**. The dashboard opens in your browser.
3. Use **Log usage**. When the dashboard is running locally, each run is saved directly to `data/usage.json` in this folder.
4. When you want a GitHub backup, press **Ctrl+Shift+P**, choose **Tasks: Run Task**, then run **Promptwise: Back up usage to GitHub**. It commits the usage file and pushes it using your normal GitHub sign-in. The dashboard on GitHub Pages updates after the push.
5. To stop the local dashboard, press **Ctrl+C** in its VS Code terminal.

The GitHub backup task stages and commits only `data/usage.json` (not other uncommitted files), then pushes the current branch. Any other commits already waiting on that branch will also be pushed. Git must be installed and this repository must already be connected to GitHub. If GitHub asks you to sign in, use VS Code's Accounts menu or Git Credential Manager—do not put a personal access token in this project.

You can still use the dashboard without the local server by opening `index.html` directly or visiting GitHub Pages. In those cases, newly logged runs are stored only in that browser. Use **Backup** to download JSON or **Restore** to load a backup. To publish those runs, open the repository's local dashboard and restore the JSON there before running the GitHub backup task.

## Publish with GitHub Pages

1. Push the repository to GitHub on the `main` branch.
2. In **Settings → Pages**, choose **GitHub Actions** as the deployment source.
3. Each push to `main` uploads the site artifact in a build job and deploys that same artifact in a separate job. The **Actions** tab shows both steps and the Pages URL.

The workflow deliberately builds the artifact before deploying it. If an earlier run failed with “No artifacts named `github-pages` were found”, push this updated workflow to `main` to start a fresh run; do not just retry the old deployment job.

## Data and privacy

The site does not connect to LLM providers or report actual bills automatically. Enter the token counts and estimated run cost yourself; token efficiency alone does not measure answer quality. Subscription fees may be flat, and local inference still has energy and hardware costs.

The local dashboard listens only on your own computer (`127.0.0.1`) and saves records to `data/usage.json`. The backup task uses your existing Git sign-in and never needs a GitHub token in the browser. A public repository and its Pages site expose committed usage data, including project names and model choices. Do not record prompts, API keys, or other secrets, and use a private repository if this metadata should not be public.

## Usage data format

`data/usage.json` and dashboard backups use this versioned shape:

```json
{
  "format": "promptwise-usage",
  "version": 1,
  "usage": [
    {
      "id": "usage-unique-id",
      "project": "Example project",
      "model": "Local model",
      "type": "local",
      "tokens": 2000,
      "cost": 0.02,
      "createdAt": "2026-11-23T12:00:00.000Z"
    }
  ]
}
```

`type` is `local` or `subscription`; `tokens` is the input and output token total, and `cost` is your estimated allocated cost in USD.
