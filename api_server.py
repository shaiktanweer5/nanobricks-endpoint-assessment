from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from database import (
    get_all_endpoints,
    save_endpoint
)


app = FastAPI(
    title="Nanobricks Endpoint API",
    version="1.1.0"
)


class EndpointPackage(BaseModel):
    agent: dict
    endpoint: dict
    summary: dict
    findings: list


# ============================================================
# API HEALTH
# ============================================================

@app.get("/")
def root():
    return {
        "service": "Nanobricks Endpoint API",
        "status": "running",
        "storage": "database"
    }


# ============================================================
# RECEIVE ENDPOINT ASSESSMENT
# ============================================================

@app.post("/api/endpoints")
def receive_endpoint(
    package: EndpointPackage
):
    package_data = package.model_dump()

    hostname = package_data.get(
        "endpoint",
        {}
    ).get(
        "hostname"
    )

    if not hostname:
        raise HTTPException(
            status_code=400,
            detail="Hostname is required."
        )

    try:
        save_endpoint(
            package_data
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save endpoint "
                f"assessment: {error}"
            )
        )

    return {
        "status": "received",
        "hostname": hostname,
        "stored_as": "database"
    }


# ============================================================
# GET ALL ENDPOINTS
# ============================================================

@app.get("/api/endpoints")
def list_endpoints():
    try:
        endpoints = get_all_endpoints()

        return {
            "count": len(endpoints),
            "endpoints": endpoints
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve endpoints: "
                f"{error}"
            )
        )