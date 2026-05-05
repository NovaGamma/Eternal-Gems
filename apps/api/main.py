from fastapi import FastAPI, Request, Header, HTTPException
import httpx
from core.db.mongo import DB
from core.services.contributions import add_message_contribution
from core.config import TRACKSCAPE_URL, settings

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
    if verification_code != settings.API_CODE:
        raise HTTPException(status_code=403, detail="Invalid verification code")
    
    data = await request.json()
    print(data)

    # redirecting to original API for Trackscape connector
    incoming_headers = dict(request.headers)
    forwarded_headers = filter_headers(incoming_headers)

    db = DB()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TRACKSCAPE_URL,
                json=data,
                headers=forwarded_headers
            )
            if response.status_code != 200:
                db.logger(0, 'error', {'trackscape': f'non 200 response: {response.status_code}', 'source': 'API'})
    except:
        db.logger(0, 'error', {'trackscape': 'general error', 'source': 'API'})

    await add_message_contribution(data[0])