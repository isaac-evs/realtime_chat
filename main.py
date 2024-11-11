from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import socketio

# Initialize App
fastapi_app = FastAPI()

# Files directory
fastapi_app.mount("/static", StaticFiles(directory="static"), name= "static")

# Serve HTML
@fastapi_app.get("/")
async def get():
    return FileResponse('static/index.html')

# Socket.IO instance
sio = socketio.AsyncServer(async_mode = 'asgi')
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)


# Events

users = {}

@sio.event
async def connect(sid, environ):
    print('Client connected', sid)

@sio.event
async def join(sid, username):
    users[sid] = username
    await sio.emit('message', f"{username} has joined the chat.")

@sio.event
async def disconnect(sid):
    username = users.get(sid, 'Unknown')
    await sio.emit('message', f"{username} has left the chat.")
    users.pop(sid, None)

@sio.event
async def message(sid, data):
    username = users.get(sid, 'Anonymous')
    await sio.emit('message', f"{username}: {data}")
