# jobs.py
# A queue sketch: accept the job, answer 202 at once, and let a repeat find the first job
# Course kit, module 21
#
# Topic: APIs that sleep
#
# Work that can take more than 30 seconds leaves the request and becomes a job.
# The caller sends an Idempotency-Key; a retry with the same key gets the same job id,
# so a timeout and a retry can never pay a model twice.
# This sketch keeps jobs in memory, so it shows the shape only: a host that sleeps
# would forget them. A real queue lives in a database (Module 6).

from fastapi import FastAPI, Header  # for the app and the key header
from fastapi.responses import JSONResponse  # for the 202
import uuid  # for job ids

app = FastAPI()
jobs, keys = {}, {}


@app.post("/jobs")
def submit(idempotency_key: str = Header(...)):
    if idempotency_key in keys:  # a repeat: return the first job, start nothing
        job_id = keys[idempotency_key]
    else:
        job_id = keys[idempotency_key] = uuid.uuid4().hex[:12]
        jobs[job_id] = {"id": job_id, "status": "queued"}  # a worker picks it up later
    return JSONResponse({"id": job_id, "status_url": f"/jobs/{job_id}"}, status_code=202)


@app.get("/jobs/{job_id}")
def status(job_id: str):
    return jobs.get(job_id, {"id": job_id, "status": "unknown"})
