import os

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import socketio
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Message
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel


#### App ####

# Initialize App
app = FastAPI()  # Changed from fastapi_app to app

#### Database ####

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Model
class RegisterRequest(BaseModel):
    username: str
    password: str

#### Authentication ####

# JWT config and Password Hashing
SECRET_KEY = os.getenv("SECRET_KEY", "20022")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 Scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Auth Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    return db.query(User).filter(User.username == username).first()

# Acces Token function
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = timedelta(minutes=15)  # Default expiration time
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Login route
@app.post("/token")  # Changed from fastapi_app to app
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Register route
@app.post("/register")  # Changed from fastapi_app to app
async def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    username = request.username
    password = request.password
    user = get_user(db, username)
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User created successfully"}

# Current User
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = get_user(db, username)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

# Get Last Messages
@app.get("/messages/{room}")  # Changed from fastapi_app to app
async def get_messages(room: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = db.query(Message).filter(Message.room == room).order_by(Message.timestamp.asc()).all()
    return [{
        "username": msg.sender.username,
        "content": msg.content,
        "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for msg in messages]

ROOMS = ["General", "Technology", "Sports", "Entertainment"]

@app.get("/rooms")  # Changed from fastapi_app to app
async def get_rooms():
    return ROOMS

#### Views ####

# Files directory
app.mount("/static", StaticFiles(directory="static"), name="static")  # Changed from fastapi_app to app

# Serve HTML
@app.get("/")  # Changed from fastapi_app to app
async def get():
    return FileResponse('static/index.html')


#### Socket.IO ####

# Socket.IO instance
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')  # Added cors_allowed_origins
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)  # Changed from fastapi_app to app

# Dictionary of connected Users
connected_users = {}

# Connect
@sio.event
async def connect(sid, environ, auth):
    token = auth.get('token', None)
    if token is None:
        return False
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return False

        db = SessionLocal()
        user = get_user(db, username)
        if user is None:
            return False
        connected_users[sid] = {'user': user, 'room': None}
        print(f"User {username} connected with session ID {sid}")
    except JWTError:
        return False


# Disconnect
@sio.event
async def disconnect(sid):
    user_info = connected_users.pop(sid, None)
    if user_info:
        room = user_info["room"]
        username = user_info["user"].username
        await sio.emit('notification', f"{username} has left the dialog", room=room)
        print(f"User {username} disconnected.")

# Message
@sio.event
async def message(sid, data):
    user_info = connected_users.get(sid)
    if user_info:
        user = user_info["user"]
        room = user_info["room"]
        timestamp = datetime.utcnow()
        message_data = {
            'username': user.username,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'content': data
        }

        db = SessionLocal()
        new_message = Message(content=data, sender_id=user.id, room=room, timestamp=timestamp)
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        db.close()
        await sio.emit('message', message_data, room=room)

# Join
@sio.event
async def join_room(sid, room):
    user_info = connected_users.get(sid)
    if user_info:
        await sio.enter_room(sid, room)
        user_info['room'] = room
        username = user_info['user'].username

        await sio.emit('notification', f"{username} has joined the conversation", room=room)

        db = SessionLocal()
        messages = db.query(Message).filter(Message.room == room).order_by(Message.timestamp.asc()).limit(50).all()

        message_history = [
            {
                "username": msg.sender.username,
                "content": msg.content,
                "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            for msg in messages
        ]
        db.close()

        await sio.emit('message_history', message_history, to=sid)
        print(f"User {username} joined room {room}")


# Export the socket app as the main application
app = socket_app  # This makes the socket_app the main ASGI application

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
