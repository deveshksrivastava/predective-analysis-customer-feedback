# Deploying the Sentiment API to Azure App Service

One App Service (Linux, Python) serves both the API and the frontend.

Deploys are automated: every push to `master` runs tests and deploys via
GitHub Actions (see [CI/CD](#cicd-github-actions) below). The `az webapp up`
steps here are only for **first-time provisioning** of the app.

## Prerequisites
- Azure CLI (`brew install azure-cli`), logged in: `az login`
- An Azure subscription

## First deploy

    cd <repo root>
    az webapp up \
      --name feedback-sentiment-api \        # must be globally unique — change it
      --resource-group rg-feedback-prototype \
      --location <nearest-region> \
      --sku B1 \
      --runtime "PYTHON:3.12"

Then set the startup command (once):

    az webapp config set \
      --name feedback-sentiment-api \
      --resource-group rg-feedback-prototype \
      --startup-file "gunicorn -w 2 -k uvicorn.workers.UvicornWorker src.app:app"

## Verify

    curl https://feedback-sentiment-api.azurewebsites.net/health
    # → {"status":"ok"}

Open `https://feedback-sentiment-api.azurewebsites.net/` for the frontend.
First request after a deploy may be slow: the app trains the model
(~5 s on the 30k-review dataset) because `models/` is not shipped.

## Redeploy after changes

Push (or merge a PR) to `master` — the GitHub Action redeploys automatically.
Manual fallback:

    az webapp up --name feedback-sentiment-api --resource-group rg-feedback-prototype

## CI/CD (GitHub Actions)

`.github/workflows/deploy.yml` runs on every push to `master` (plus a manual
"Run workflow" button): a `test` job (pip install + pytest) gates a `deploy`
job that zips `src/`, `static/`, `data/`, `requirements.txt` and pushes the
package to the Web App with `azure/webapps-deploy`. Azure's Oryx build
installs `requirements.txt` on the server, and the app trains the model on
first startup, so no model artifact ships from CI.

One-time setup (after provisioning the app above):

1. Publish profiles need SCM basic auth; newer apps may have it disabled:

       az resource update \
         --resource-group rg-feedback-prototype \
         --name feedback-sentiment-api/basicPublishingCredentialsPolicies/scm \
         --resource-type Microsoft.Web/sites/basicPublishingCredentialsPolicies \
         --set properties.allow=true

2. Download the publish profile and store it as a GitHub secret:

       az webapp deployment list-publishing-profiles \
         --name feedback-sentiment-api \
         --resource-group rg-feedback-prototype \
         --xml > profile.xml
       gh secret set AZURE_WEBAPP_PUBLISH_PROFILE < profile.xml
       rm profile.xml

If you provisioned the app under a different name, update `AZURE_WEBAPP_NAME`
in the workflow to match.

## Tear down (stops billing)

    az group delete --name rg-feedback-prototype

## Notes
- Runtime is `PYTHON:3.12` because App Service may lag behind local 3.13;
  check `az webapp list-runtimes --os linux | grep -i python` and use the
  newest available.
- `jupyter`, `matplotlib`, `seaborn`, `xgboost` in requirements.txt are
  dev/notebook-only; fine for a prototype, trim into a separate
  `requirements-dev.txt` later if deploys feel slow.
