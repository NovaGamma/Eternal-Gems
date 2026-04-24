from fastapi import FastAPI, Request, Header, HTTPException
import httpx
from core.services.contributions import add_message_contribution
from core.config import API_CODE, TRACKSCAPE_URL

app = FastAPI()

def filter_headers(headers: dict) -> dict:
    excluded = {
        "host",
        "content-length",
        "transfer-encoding",
        "connection",
        "accept-encoding"
    }
    return {
        k: v for k, v in headers.items()
        if k.lower() not in excluded
    }

@app.post("/message")
async def receive_contribution(request: Request, verification_code: str = Header(None)):
    print(request)
    if verification_code != API_CODE:
        raise HTTPException(status_code=403, detail="Invalid verification code")
    
    data = await request.json()
    print(data)

    # redirecting to original API for Trackscape connector
    incoming_headers = dict(request.headers)
    forwarded_headers = filter_headers(incoming_headers)

    async with httpx.AsyncClient() as client:
        await client.post(
            TRACKSCAPE_URL,
            json=data,
            headers=forwarded_headers
        )

    await add_message_contribution(data[0])