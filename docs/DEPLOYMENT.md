# Deploying the Sentiment API to Azure App Service

One App Service (Linux, Python) serves both the API and the frontend.

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
(seconds — the dataset is 149 rows) because `models/` is not shipped.

## Redeploy after changes

    az webapp up --name feedback-sentiment-api --resource-group rg-feedback-prototype

## Tear down (stops billing)

    az group delete --name rg-feedback-prototype

## Notes
- Runtime is `PYTHON:3.12` because App Service may lag behind local 3.13;
  check `az webapp list-runtimes --os linux | grep -i python` and use the
  newest available.
- `jupyter`, `matplotlib`, `seaborn`, `xgboost` in requirements.txt are
  dev/notebook-only; fine for a prototype, trim into a separate
  `requirements-dev.txt` later if deploys feel slow.
