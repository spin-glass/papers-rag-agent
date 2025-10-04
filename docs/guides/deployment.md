# Cloud Run Deployment Guide

This document explains the GitHub Actions workflow that deploys the Papers RAG
Agent to Cloud Run and automatically updates the live demo link in the README.

## Automated README updates

The workflow extends `.github/workflows/deploy.yml` with three steps:

1. **Retrieve the deployed URL** using the
   `google-github-actions/deploy-cloudrun@v2` output `url`.
2. **Update the README** between the `<!-- CLOUDRUN_URL_START -->` and
   `<!-- CLOUDRUN_URL_END -->` markers.
3. **Commit changes** back to the repository only when the URL changes.

## Required configuration

- Ensure the workflow has the `contents: write` permission.
- Keep the README markers in place so the URL can be replaced safely.

```markdown
<!-- CLOUDRUN_URL_START -->
🚀 **Live Demo**: [https://your-url.run.app](https://your-url.run.app)
<!-- CLOUDRUN_URL_END -->
```

## Customisation

- Move the marker block anywhere in the README to change where the link
  appears.
- Adjust service name, region, or additional flags inside
  `.github/workflows/deploy.yml` as needed.

## Troubleshooting

1. **URL does not update** – verify the README contains the marker block and
   that the workflow has write permissions.
2. **Commit loops** – mitigated by skipping commits when the URL is
   unchanged.
3. **Workflow errors** – inspect the "Deploy to Cloud Run" logs in the
   GitHub Actions tab.
