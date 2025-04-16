<<<<<<< HEAD
# ThoughtCaptcha-backend
Backend part of the project
=======
# ThoughtCaptcha Backend

This directory contains the Python backend code for the ThoughtCaptcha project, built with FastAPI.

## Overview

The backend provides a RESTful API to:
- Accept initial student assignment submissions.
- Interact with the OpenRouter API to generate contextual follow-up questions.
- Store submission details, questions, and responses in a PostgreSQL database.
- Provide endpoints for the frontend application.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd ThoughtCaptcha/backend
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**
    - Copy `.env.example` to `.env`.
    - Edit `.env` and add your `DATABASE_URL`, `OPENROUTER_API_KEY`, and `FRONTEND_ORIGIN_URL`.
      *For Railway deployment, these will typically be set in the Railway service environment variables.*

5.  **Database Migrations (using Alembic - setup needed):**
    *(Instructions to be added once Alembic is configured)*
    ```bash
    # alembic revision --autogenerate -m "Initial migration"
    # alembic upgrade head
    ```

6.  **Run the development server:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    The API will be available at `http://localhost:8000`.

## Deployment

This backend is intended to be deployed on [Railway](https://railway.app/). Connect the GitHub repository containing this code to a Railway service. Configure the necessary environment variables (`DATABASE_URL`, `OPENROUTER_API_KEY`, `FRONTEND_ORIGIN_URL`) in the Railway service settings. Railway typically handles the `DATABASE_URL` automatically when using their PostgreSQL add-on.

## API Endpoints

*(Documentation will be added here as endpoints are developed. FastAPI also provides automatic interactive documentation at `/docs` and `/redoc`)*

- `/api/submit-assignment` (POST)
- `/api/generate-question` (POST)
- `/api/verify-response` (POST) - *Note: Currently stores response, no AI verification.*
- `/api/health` (GET)

## Project Structure

- `app/`: Main application code.
  - `main.py`: FastAPI application instance and API routers.
  - `config.py`: Loads environment variables.
  - `database.py`: Database session management.
  - `models.py`: SQLAlchemy database models.
  - `schemas.py`: Pydantic data validation schemas.
  - `crud.py`: Database create, read, update, delete operations.
  - `openrouter_client.py`: Client for interacting with OpenRouter API.
- `requirements.txt`: Project dependencies.
- `.env.example`: Template for environment variables.
- `README.md`: This file. 
>>>>>>> bbf9d8b (feat: Initial backend structure and API setup)
