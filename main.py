import base64, json, os, time
from collections import defaultdict
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(title="KrishiMitra")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
LIMIT_PER_HOUR = int(os.getenv("LIMIT_PER_HOUR", "30"))
_hits = defaultdict(list)


def rate_ok(ip: str) -> bool:
    now = time.time()
    _hits[ip] = [t for t in _hits[ip] if now - t < 3600]
    if len(_hits[ip]) >= LIMIT_PER_HOUR:
        return False
    _hits[ip].append(now)
    return True


def system_prompt(lang, crop, place, stage, forecast):
    language = "simple Hindi (Devanagari)" if lang == "hi" else "simple English"
    return (
        "You are KrishiMitra, an agronomy helper for small farmers in India. "
        f"Reply in {language}. Use 3 to 5 short, practical points, under 120 words. "
        "Give no specific pesticide doses; for chemicals, tell the farmer to confirm with the "
        "local KVK or agriculture officer. "
        f"Farmer context: crop {crop}, location {place}, growth stage {stage}. "
        f"Next 5 days forecast (max C, min C, rain mm): {json.dumps(forecast)}."
    )


def ask_model(system, content):
    from anthropic import Anthropic  # reads ANTHROPIC_API_KEY from the environment
    msg = Anthropic().messages.create(
        model=MODEL, max_tokens=600, system=system, messages=[{"role": "user", "content": content}]
    )
    return "".join(b.text for b in msg.content if b.type == "text")


class Ask(BaseModel):
    question: str = Field(max_length=500)
    crop: str
    place: str
    stage: str
    lang: str = "en"
    forecast: list = []


@app.post("/api/ask")
def ask(body: Ask, request: Request):
    if not rate_ok(request.client.host):
        return JSONResponse({"error": "rate limit"}, status_code=429)
    try:
        text = ask_model(system_prompt(body.lang, body.crop, body.place, body.stage, body.forecast),
                         f"Farmer question: {body.question}")
        return {"text": text}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=502)


@app.post("/api/scan")
async def scan(request: Request, image: UploadFile = File(...), crop: str = Form(...), place: str = Form(...),
               stage: str = Form(...), lang: str = Form("en"), forecast: str = Form("[]")):
    if not rate_ok(request.client.host):
        return JSONResponse({"error": "rate limit"}, status_code=429)
    data = await image.read()
    if len(data) > 5_000_000 or image.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        return JSONResponse({"error": "Use a JPG/PNG/WEBP image under 5 MB"}, status_code=400)
    prompt = (
        "This is a photo of a crop leaf or plant. Give a preliminary screening only: 1) what you can see, "
        "2) the most likely causes (say clearly this is not a confirmed diagnosis), 3) what the farmer can "
        "safely do now, 4) when to contact the KVK or agriculture officer. If the photo is unclear or not "
        "a plant, say so."
    )
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": image.content_type,
                                     "data": base64.b64encode(data).decode()}},
        {"type": "text", "text": prompt},
    ]
    try:
        fc = json.loads(forecast)
    except Exception:
        fc = []
    try:
        return {"text": ask_model(system_prompt(lang, crop, place, stage, fc), content)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=502)


app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"), html=True), name="static")
