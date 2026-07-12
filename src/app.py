"""FastAPI app serving the Phase 1 sentiment model.

Run locally:  uvicorn src.app:app --reload
On Azure:     gunicorn -w 2 -k uvicorn.workers.UvicornWorker src.app:app
"""

from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from .model import load_model
from .preprocessing import clean_text
from .train import DEFAULT_MODEL, PROJECT_ROOT, train

APP_VERSION = "0.1.0"

_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DEFAULT_MODEL.exists():          # fresh clone / fresh Azure instance
        train()
    _state["model"], _state["label_encoder"] = load_model(DEFAULT_MODEL)
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


# Frontend: static/index.html served at "/". Mounted LAST so API routes win.
# Conditional so the API still runs before the frontend page is added.
if (PROJECT_ROOT / "static").is_dir():
    app.mount("/", StaticFiles(directory=PROJECT_ROOT / "static", html=True), name="static")
