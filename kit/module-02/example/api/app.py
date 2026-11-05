# FIXTURE: hand-written to show a passing folder. No model produced it.
from fastapi import FastAPI  # for the routes
from fastapi.middleware.cors import CORSMiddleware  # for letting the page read answers

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/rows")
def rows():
    return [{"name": "Luke Skywalker", "height": 172}]
