import json
import asyncio
from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import whisper
import aiohttp


app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])


MODEL = whisper.load_model('small')
GURBANI_API_BASE = 'https://api.gurbanidb.com/v1' # Example endpoint; check actual API docs


async def transcribe_bytes(audio_bytes: bytes):
import tempfile
with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
tmp.write(audio_bytes)
tmp.flush()
tmp_path = tmp.name
try:
res = MODEL.transcribe(tmp_path, language='pa')
return res.get('text', '').strip()
finally:
try:
import os
os.remove(tmp_path)
except Exception:
pass


async def get_best_match_line(transcribed_text: str):
# Query GurbaniDB API to find closest line by text search
async with aiohttp.ClientSession() as session:
params = {'q': transcribed_text, 'limit': 1}
async with session.get(f'{GURBANI_API_BASE}/lines/search', params=params) as resp:
data = await resp.json()
if data and 'results' in data and len(data['results']) > 0:
line = data['results'][0]
return {
'ang': line.get('ang'),
'id': line.get('id'),
'line_gurmukhi': line.get('line'),
'translation_en': line.get('translation')
}
return None


@app.websocket('/ws/akhand')
async def ws_endpoint(websocket: WebSocket):
await websocket.accept()
buffer = bytearray()
try:
while True:
data = await websocket.receive()
if 'bytes' in data:
chunk = data['bytes']
buffer.extend(chunk)
if len(buffer) > 200_000:
buf = bytes(buffer)
buffer.clear()
txt = await transcribe_bytes(buf)
match = await get_best_match_line(txt)
await websocket.send_text(json.dumps({'transcript': txt, 'match': match}, ensure_ascii=False))
elif 'text' in data:
obj = data['text']
except Exception as e:
print('ws closed', e)
return {'transcript': txt, 'match': match}