"""
API Key authentication for sensitive endpoints.
Uses a simple API key check via X-API-Key header.
"""
import os
from fastapi import HTTPException, Header, Depends
from functools import wraps

API_KEY = os.getenv("API_KEY", "")

async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Validates the API key from the X-API-Key header."""
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY not configured on server")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key
