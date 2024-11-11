from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from typing import List

from sqlalchemy.sql import expression

# Initialize App
app = FastAPI()

# Connection Manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.activate_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.activate_connections.append(websocket)
        print(f"Connection established: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        self.activate_connections.remove(websocket)
        print(f"Connection closed: {websocket.client}")

    async def broadcast(self, message: str):
        for connection in self.activate_connections:
            await connection.send_text(message)


# WebSocket Endpoint
manager = ConnectionManager()

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client Says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Serve HTML
@app.get("/")
async def get(request: Request):
    return HTMLResponse(open("index.html").read())
