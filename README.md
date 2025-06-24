# Live Conversational Threads

This application is designed to enhance conversation flow by intelligently identifying and managing conversational threads in real-time. The system subtly captures and organizes discussion threads to maintain context and enable a more smoother and coherent conversation, built with FastAPI backend and React frontend.

## Demo

Check out our application demo:

[Live Conversational Threads Demo](https://youtu.be/sflh9t_Y1eQ?feature=shared)

For detailed documentation and understanding of conversational threading concepts, please refer to our [project writeup](https://docs.google.com/document/d/11sC8fKkNCs09fFBztFqq6rp8b83UQiX2qA1kKF2GpYM/edit?usp=sharing). `// needs to be added.`

## Project Structure

```
live_conversational_threads/
├── lct_python_backend/     # Python FastAPI backend
│   └── backend.py         # Main backend application
├── lct_app/               # React frontend application
│   ├── src/              # Source code
│   ├── package.json      # Frontend dependencies
│   └── vite.config.js    # Vite configuration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Prerequisites

- Miniconda (Python 3.8+)
- Node.js 14+
- npm 6+

## Installation

### Backend Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/live_conversational_threads.git
cd live_conversational_threads
```

2. Create and activate a Conda environment:

```bash
conda create -n lct_env python=3.8
conda activate lct_env
```

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

4. Set up below environment variable on your computer:

```
ANTHROPIC_API_KEY=your_api_key_here
```

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd lct_app
```

2. Install Node.js dependencies:

```bash
npm install
```

## Running the Application

### Start the Backend Server

1. From the root directory, with the conda environment activated:

```bash
cd lct_python_backend
uvicorn backend:lct_app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`

### Start the Frontend Development Server

1. In a new terminal, navigate to the frontend directory:

```bash
cd lct_app
```

2. Start the development server:

```bash
npm run dev
```

The frontend application will be available at `http://localhost:5173`

## API Documentation

Once the backend server is running, you can access:

- Swagger UI documentation at `http://localhost:8000/docs`
- ReDoc documentation at `http://localhost:8000/redoc`

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
