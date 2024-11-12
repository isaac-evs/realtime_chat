from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.models import OAuth2
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, oauth2
from fastapi.staticfiles import StaticFiles
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
fastapi_app = FastAPI()

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
SECRET_KEY = "20022BA"
ALGORITHM = "HS256"
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
@fastapi_app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Register route
@fastapi_app.post("/register")
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
@fastapi_app.get("/messages")
async def get_messages(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = db.query(Message).order_by(Message.timestamp.desc()).limit(50).all()
    messages.reverse()
    return [{"username": msg.sender.username, "content": msg.content, "timestamp": msg.timestamp} for msg in messages]

#### Views ####

# Files directory
fastapi_app.mount("/static", StaticFiles(directory="static"), name= "static")

# Serve HTML
@fastapi_app.get("/")
async def get():
    return FileResponse('static/index.html')


#### Socket.IO ####

# Socket.IO instance
sio = socketio.AsyncServer(async_mode = 'asgi')
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

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
        connected_users[sid] = user
        print(f"User {username} connected with session ID {sid}")
    except JWTError:
        return False


# Disconnect
@sio.event
async def disconnect(sid):
    user = connected_users.pop(sid, None)
    if user:
        await sio.emit('message', f"{user.username} has left the chat.")
        print(f"User {user.username} disconnected.")

# Message
@sio.event
async def message(sid, data):
    user = connected_users.get(sid)
    if user:
        db = SessionLocal()
        new_message = Message(content=data, sender_id = user.id)
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        db.close
        await sio.emit('message', f"{user.username}: {data}")

# Join
@sio.event
async def join(sid, username):
    connected_users[sid] = username
    await sio.emit('message', f"{username} has joined the chat.")
