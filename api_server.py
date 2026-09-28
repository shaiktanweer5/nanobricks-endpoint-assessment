from pathlib import Path
import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(
    title="Nanobricks Endpoint API",
    version="1.0.0"
)

DATA_DIR = Path("api-data")
DATA_DIR.mkdir(exist_ok=True)


class EndpointPackage(BaseModel):
    agent: dict
    endpoint: dict
    summary: dict
    findings: list


@app.get("/")
def root():
    return {
        "service": "Nanobricks Endpoint API",
        "status": "running"
    }


@app.post("/api/endpoints")
def receive_endpoint(package: EndpointPackage):
    hostname = package.endpoint.get(
        "hostname"
    )

    if not hostname:
        raise HTTPException(
            status_code=400,
            detail="Hostname is required."
        )

    safe_hostname = "".join(
        character
        if character.isalnum()
        or character in "-_"
        else "_"
        for character in hostname
    )

    file_path = (
        DATA_DIR
        / f"{safe_hostname}-assessment.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            package.model_dump(),
            file,
            indent=4
        )

    return {
        "status": "received",
        "hostname": hostname,
        "stored_as": file_path.name
    }