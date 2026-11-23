# Promptwise LLM usage dashboard

A static, local-first dashboard for comparing LLM usage by project, model, and execution type (local or subscription).

## What it does

- Shows token totals, estimated costs, local-versus-hosted usage, and tokens per estimated dollar.
- Filters usage by project and date range; compares models and recent runs.
- Lets you manually log a model run in the browser and export filtered CSV.
- Backs up and restores all usage as versioned JSON.
- Loads the committed `data/usage.json` file when hosted on GitHub Pages.

The dashboard does not connect to LLM providers or report actual bills automatically. Costs are estimates you enter; token efficiency alone does not measure answer quality.

## Publish with GitHub Pages

1. Push this repository to GitHub with the dashboard on the `main` branch.
2. In the repository, open **Settings → Pages** and set the build and deployment source to **GitHub Actions**.
3. Open **Actions** and allow workflows if GitHub prompts you. The Pages workflow deploys on pushes to `main`; you can also start it with **Run workflow**.
4. When the deployment finishes, open the Pages URL shown in the workflow summary.

No build tools or package installation are needed; the site is plain HTML, CSS, and JavaScript.

## Back up and restore usage

1. Use **Backup** in the dashboard to download a `promptwise-usage-YYYY-MM-DD.json` file. It contains all usage rows available in the dashboard, not only the current filters.
2. Copy the backup's `usage` records into `data/usage.json` (keeping the `format` and `version` fields), then commit and push that file. The Pages workflow republishes it, and the dashboard reads it from the repository.
3. Use **Restore** to merge a downloaded Promptwise backup into the current browser's local data. Duplicate record IDs are merged rather than added twice.
4. Exported CSV is for analysis; use the JSON backup to restore or publish dashboard data.

The static site cannot write changes back to GitHub. Logging a run saves it only in that browser; download and commit a JSON backup to share it across devices and preserve it in the repository. Never put GitHub tokens, API keys, prompts, or other secrets in this site or in usage records.

**Privacy:** a public repository and its GitHub Pages site expose committed `data/usage.json` contents to everyone. Use a private repository if project names, model choices, or usage patterns should not be public, and confirm your GitHub Pages access settings before publishing.

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
