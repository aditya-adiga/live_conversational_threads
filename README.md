# Live Conversational Threads

This application is designed to enhance conversation flow by intelligently identifying and managing conversational threads in real-time. The system subtly captures and organizes discussion threads to maintain context and enable a more smoother and coherent conversation, built with FastAPI backend and React frontend.

---

## Table of Contents
- [Demo](#demo)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Running the Application](#running-the-application)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Demo

- [Live Conversational Threads Presentation (YouTube)](https://youtu.be/sflh9t_Y1eQ?feature=shared)

---

## Project Structure

```
live_conversational_threads/
├── lct_python_backend/     # Python FastAPI backend
│   ├── backend.py         # Main backend application
│   ├── db.py              # Database connection
│   ├── db_helpers.py      # Database helper functions
│   └── requirements.txt   # Backend dependencies
├── lct_app/               # React frontend application
│   ├── src/               # Source code
│   ├── package.json       # Frontend dependencies
│   └── vite.config.js     # Vite configuration
├── requirements.txt       # (duplicate of backend requirements)
└── README.md              # This file
```

---

## Prerequisites

- **Python 3.8+** (Conda or venv recommended)
- **Node.js 18+** and **npm 9+**
- **PostgreSQL** (for backend database)

---

## Backend Setup

1. **Create and activate a Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
   Or use Conda:
   ```bash
   conda create -n lct_env python=3.8
   conda activate lct_env
   ```

2. **Install backend dependencies:**
   ```bash
   pip install -r lct_python_backend/requirements.txt
   ```

3. **Configure environment variables:**
   - Set the following environment variables in your shell or system (e.g., export on Unix, set on Windows):
     ```sh
     export ANTHROPIC_API_KEY=your_anthropic_api_key
     export ASSEMBLYAI_API_KEY=your_assemblyai_api_key
     export ASSEMBLYAI_WS_URL=wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000
     export PERPLEXITY_API_KEY=your_perplexity_api_key
     export GOOGLEAI_API_KEY=your_googleai_api_key
     export GCS_BUCKET_NAME=your_gcs_bucket
     export GCS_FOLDER=your_gcs_folder
     export DATABASE_URL=postgresql://user:password@localhost:5432/yourdb
     ```
   - On Windows (PowerShell):
     ```powershell
     $env:ANTHROPIC_API_KEY="your_anthropic_api_key"
     # ...and so on for each variable
     ```
   - These must be set in your environment before starting the backend.

4. **Set up the PostgreSQL database** (see [Database Setup](#database-setup)).

---

## Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd lct_app
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

---

## Running the Application

### 1. Start the Backend Server

From the project root (with your Python environment activated and environment variables set):
```bash
cd lct_python_backend
uvicorn backend:lct_app --reload --port 8080
```
- The backend API will be available at [http://localhost:8080](http://localhost:8080)

### 2. Start the Frontend Development Server

In a new terminal:
```bash
cd lct_app
npm run dev
```
- The frontend will be available at [http://localhost:5173](http://localhost:5173)

---

## Environment Variables

**Backend required variables:**
- `ANTHROPIC_API_KEY` — API key for Anthropic Claude
- `ASSEMBLYAI_API_KEY` — API key for AssemblyAI
- `ASSEMBLYAI_WS_URL` — AssemblyAI websocket URL
- `PERPLEXITY_API_KEY` — API key for Perplexity
- `GOOGLEAI_API_KEY` — API key for Google GenAI
- `GCS_BUCKET_NAME` — Google Cloud Storage bucket name
- `GCS_FOLDER` — GCS folder for storing files
- `DATABASE_URL` — PostgreSQL connection string (e.g., `postgresql://user:password@localhost:5432/yourdb`)

**Frontend:**
- No environment variables required for local development.

---

## Database Setup

- You must have a running PostgreSQL instance.
- The backend expects a `conversations` table. Example schema:
  ```sql
  CREATE TABLE conversations (
      id TEXT PRIMARY KEY,
      file_name TEXT,
      no_of_nodes INTEGER,
      gcs_path TEXT,
      created_at TIMESTAMP
  );
  ```
- Adjust or extend the schema as needed for your use case.

---

## API Documentation

Once the backend server is running, access:
- Swagger UI: [http://localhost:8080/docs](http://localhost:8080/docs)
- ReDoc: [http://localhost:8080/redoc](http://localhost:8080/redoc)

---

## Troubleshooting

- **Database connection errors:**
  - Ensure your `DATABASE_URL` is correct and PostgreSQL is running.
  - The required tables must exist before starting the backend.
- **CORS errors:**
  - The backend is configured to allow requests from `http://localhost:5173`.
- **API key errors:**
  - Double-check all required environment variables are set in your environment.
- **Port conflicts:**
  - Change the ports in the run commands if `8080` or `5173` are in use.

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).

You are free to use, modify, and distribute this software under the terms of the GPLv3.

---

## Commercial Use

If you would like to use this software in a closed-source or commercial product,
or if you're interested in a commercial license with different terms (e.g., without the GPL's copyleft requirements),
please contact me to discuss options:

Email: [adityaadiga6@gmail.com](mailto:adityaadiga6@gmail.com)
GitHub: [https://github.com/aditya-adiga](https://github.com/aditya-adiga)
