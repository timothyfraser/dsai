"""Routes only: parse the input, call logic.py, return JSON."""
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from logic import summarize

app = FastAPI(title="Example API", description="A small API for a React page.", version="1.0.0")

# CORS: which web address may a browser page call this API from?
# CORS_ORIGIN is an environment variable. Unset, it falls back to "*" (anyone),
# which is fine on your own machine. When you deploy, set CORS_ORIGIN on the
# Connect content to the address of your deployed page.
# Locally you can skip CORS altogether with the Vite dev proxy
# (see ../reactfront/vite.config.js).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("CORS_ORIGIN", "*")],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Values(BaseModel):
    values: list[float]


@app.get("/health")
async def health():
    """Is the API up? Returns 200 and a small JSON body."""
    return {"status": "ok", "version": app.version}


@app.post("/summary")
async def summary(body: Values):
    """Count, mean, min and max of a list of numbers."""
    try:
        return summarize(body.values)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))
