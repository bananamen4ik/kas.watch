from fastapi import FastAPI, WebSocket

app = FastAPI(
    docs_url=None,
    redoc_url=None
)


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
