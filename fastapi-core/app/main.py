from fastapi import FastAPI, WebSocket

app: FastAPI = FastAPI(
    docs_url=None,
    redoc_url=None
)


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    while True:
        data: str = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
