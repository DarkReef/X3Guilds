from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from x3guilds_ai.config import Settings
from x3guilds_ai.factory import create_service
from x3guilds_ai.models import ChatRequest, DialogueResponse


settings = Settings.from_env()
service = create_service(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await service.initialize()
    yield


app = FastAPI(title="X3 Guilds AI", version="0.3.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "provider": settings.provider}


@app.post("/v1/chat", response_model=DialogueResponse)
async def chat(request: ChatRequest) -> DialogueResponse:
    try:
        return await service.chat(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/ui", response_class=HTMLResponse)
async def ui() -> str:
    example_path = Path(__file__).resolve().parents[1] / "examples" / "chat-request.json"
    try:
        example = json.loads(example_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        example = {}
    escaped = json.dumps(example, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang='ru'>
<meta charset='utf-8'>
<title>X3 Guilds AI</title>
<style>
body{{font-family:system-ui;max-width:900px;margin:40px auto;padding:0 16px;background:#10141b;color:#e7edf5}}
textarea{{width:100%;min-height:420px;background:#171e28;color:#e7edf5;border:1px solid #39485d;padding:12px}}
button{{padding:10px 18px;margin:12px 0}} pre{{white-space:pre-wrap;background:#171e28;padding:12px}}
</style>
<h1>X3 Guilds · GigaChat bridge</h1>
<textarea id='request'>{escaped}</textarea>
<button onclick='send()'>Отправить</button>
<pre id='response'></pre>
<script>
async function send(){{
 const body=JSON.parse(document.getElementById('request').value);
 const r=await fetch('/v1/chat',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(body)}});
 document.getElementById('response').textContent=JSON.stringify(await r.json(),null,2);
}}
</script>
</html>"""


def run() -> None:
    uvicorn.run("x3guilds_ai.api:app", host="127.0.0.1", port=8787, reload=False)
