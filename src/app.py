"""FastAPI app serving the Phase 1 sentiment model and Phase 2 churn model.

Run locally:  uvicorn src.app:app --reload
On Azure:     gunicorn -w 2 -k uvicorn.workers.UvicornWorker src.app:app
"""

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Literal

import numpy as np
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from .churn import DEFAULT_MODEL as CHURN_MODEL_PATH
from .churn import churn_probability, load_churn_model, train_churn
from .model import load_model
from .preprocessing import clean_text
from .train import DEFAULT_MODEL, PROJECT_ROOT, train

APP_VERSION = "0.2.0"

_state = {}

# One structured line per churn prediction — the seed of a monitoring story
# (probability drift, volume, latency) without any new dependency.
prediction_log = logging.getLogger("churn_predictions")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DEFAULT_MODEL.exists():          # fresh clone / fresh Azure instance
        train()
    _state["model"], _state["label_encoder"] = load_model(DEFAULT_MODEL)
    if not CHURN_MODEL_PATH.exists():
        train_churn()
    _state["churn_model"], _state["churn_threshold"] = load_churn_model(CHURN_MODEL_PATH)
    yield
    _state.clear()


app = FastAPI(title="Customer Feedback Sentiment API", lifespan=lifespan)


class FeedbackIn(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be blank")
        return v


class PredictionOut(BaseModel):
    sentiment: str
    is_positive: bool
    confidence: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {
        "version": APP_VERSION,
        "model_loaded": _state.get("model") is not None,
        "model_path": DEFAULT_MODEL.name,
        "churn_model_loaded": _state.get("churn_model") is not None,
        "churn_model_path": CHURN_MODEL_PATH.name,
    }


@app.post("/predict", response_model=PredictionOut)
def predict(feedback: FeedbackIn):
    model, label_encoder = _state["model"], _state["label_encoder"]
    cleaned = clean_text(feedback.text)
    probs = model.predict_proba([cleaned])[0]
    best = int(np.argmax(probs))
    sentiment = label_encoder.inverse_transform([best])[0]
    return PredictionOut(
        sentiment=sentiment,
        is_positive=(sentiment == "positive"),
        confidence=float(probs[best]),
    )


class CustomerIn(BaseModel):
    """One Telco customer — field names and values match the training data."""

    gender: Literal["Female", "Male"]
    SeniorCitizen: Literal[0, 1]
    Partner: Literal["Yes", "No"]
    Dependents: Literal["Yes", "No"]
    tenure: int = Field(ge=0, description="months with the company")
    PhoneService: Literal["Yes", "No"]
    MultipleLines: Literal["Yes", "No", "No phone service"]
    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: Literal["Yes", "No", "No internet service"]
    OnlineBackup: Literal["Yes", "No", "No internet service"]
    DeviceProtection: Literal["Yes", "No", "No internet service"]
    TechSupport: Literal["Yes", "No", "No internet service"]
    StreamingTV: Literal["Yes", "No", "No internet service"]
    StreamingMovies: Literal["Yes", "No", "No internet service"]
    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: Literal["Yes", "No"]
    PaymentMethod: Literal["Electronic check", "Mailed check",
                           "Bank transfer (automatic)", "Credit card (automatic)"]
    MonthlyCharges: float = Field(ge=0)
    TotalCharges: float = Field(ge=0)


class ChurnOut(BaseModel):
    churn_probability: float
    will_churn: bool
    risk_band: Literal["low", "medium", "high"]


def risk_band(probability: float) -> str:
    """Display bands for humans; the yes/no decision uses the trained threshold."""
    if probability < 0.30:
        return "low"
    if probability < 0.60:
        return "medium"
    return "high"


@app.post("/predict-churn", response_model=ChurnOut)
def predict_churn(customer: CustomerIn):
    model, threshold = _state["churn_model"], _state["churn_threshold"]
    probability = churn_probability(model, customer.model_dump())
    band = risk_band(probability)
    prediction_log.info(json.dumps({
        "ts": time.time(),
        "churn_probability": round(probability, 4),
        "risk_band": band,
        "threshold": threshold,
    }))
    return ChurnOut(
        churn_probability=probability,
        will_churn=(probability >= threshold),
        risk_band=band,
    )


# Frontend: static/index.html served at "/". Mounted LAST so API routes win.
# Conditional so the API still runs before the frontend page is added.
if (PROJECT_ROOT / "static").is_dir():
    app.mount("/", StaticFiles(directory=PROJECT_ROOT / "static", html=True), name="static")
