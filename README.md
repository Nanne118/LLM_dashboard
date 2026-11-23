# Promptwise LLM usage dashboard

A small local dashboard for tracking LLM runs by project, model, and local-versus-subscription usage. It uses Python's standard library; no packages or VS Code extension are needed.

## The simple workflow

1. Double-click **Promptwise Dashboard** on your desktop, or double-click `Open Promptwise Dashboard.bat` in this repository. Python starts the dashboard and opens it in your browser.
2. Use **Log usage**. Runs are saved directly to `data/usage.json` in this repository. Leave the launcher window running while using the dashboard.
3. When you want a GitHub backup, click **Back up to GitHub** in the dashboard. It commits the usage file and pushes your current branch using your normal GitHub sign-in.
4. Close the black launcher window to stop the local dashboard. GitHub Pages updates after the backup push.

The GitHub backup button stages and commits only `data/usage.json` (not other uncommitted files), then pushes the current branch. Any other commits already waiting on that branch will also be pushed. This repository uses the Git installation bundled with GitHub Desktop when available. Sign in to GitHub Desktop if prompted; do not put a personal access token in this project.

You can still visit GitHub Pages to view the committed data. Runs logged on that hosted site are stored only in that browser; to save them in the project, use the local desktop launcher.

## Publish with GitHub Pages

1. Push the repository to GitHub on the `main` branch.
2. In **Settings → Pages**, choose **GitHub Actions** as the deployment source.
3. Each push to `main` uploads the site artifact in a build job and deploys that same artifact in a separate job. The **Actions** tab shows both steps and the Pages URL.

The workflow deliberately builds the artifact before deploying it. If an earlier run failed with “No artifacts named `github-pages` were found”, push this updated workflow to `main` to start a fresh run; do not just retry the old deployment job.

## Data and privacy

The site does not connect to LLM providers or report actual bills automatically. Enter the token counts and estimated run cost yourself; token efficiency alone does not measure answer quality. Subscription fees may be flat, and local inference still has energy and hardware costs.

The local dashboard listens only on your own computer (`127.0.0.1`) and saves records to `data/usage.json`. The backup button uses your existing Git sign-in and never needs a GitHub token in the browser. A public repository and its Pages site expose committed usage data, including project names and model choices. Do not record prompts, API keys, or other secrets, and use a private repository if this metadata should not be public.

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
