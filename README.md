# Realtime Chat

A simple, real-time chat application to connect users instantly. This project demonstrates the use of Socket.IO to enable live communication.

### Live Demo

Check out the live application: [Realtime Chat on Render](https://realtime-chat-lnq2.onrender.com)

### Features

- Real-time messaging with WebSockets
- Lightweight and easy-to-deploy application
- Runs on FastAPI with Uvicorn for high-performance communication

### Running the Project Locally

1. **Clone the Repository**
   ```bash
   git clone https://github.com/isaac-evs/realtime_chat.git
   cd realtime_chat
   ```
   ```bash
   pip install -r requirements.txt
   ```
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Open your web browser and navigate to http://localhost:8000 to start using the real-time chat.

### Technologies Used

	•	FastAPI: A modern, fast (high-performance) web framework for building APIs with Python 3.6+ based on standard Python type hints.
	•	Uvicorn: A lightning-fast ASGI server implementation, using uvloop and httptools.
	•	Socket.IO: Real-time communication for seamless user interactions.
