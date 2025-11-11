# Live Conversational Threads

**A multi-scale conversation analysis platform for Google Meet transcripts with AI-powered insights, cognitive bias detection, and advanced visualization.**

Live Conversational Threads transforms conversation transcripts into interactive, multi-scale graph visualizations that reveal both temporal flow and thematic relationships. The application supports Google Meet transcripts with speaker diarization, allowing users to explore conversations at five discrete zoom levels—from individual sentences to narrative arcs—while simultaneously viewing both timeline and contextual network views.

Built with **FastAPI** (Python backend) and **React + TypeScript** (frontend), the platform leverages LLM-powered analysis to detect Simulacra levels, identify cognitive biases, extract implicit frames, and generate comprehensive speaker analytics.

---

## Table of Contents
- [Key Features](#key-features)
- [Demo](#demo)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Running the Application](#running-the-application)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [API Documentation](#api-documentation)
- [Documentation](#documentation)
- [Development Roadmap](#development-roadmap)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Key Features

### Core Capabilities

**🎯 Google Meet Transcript Import**
- Parse PDF/TXT transcripts with speaker diarization
- Automatic speaker detection and turn segmentation
- Timestamp extraction and duration calculation

**📊 Dual-View Visualization**
- **Timeline View** (15%): Linear temporal progression of conversation
- **Contextual Network View** (85%): Thematic clustering and idea relationships
- Synchronized navigation and selection across views
- Resizable split with user-customizable proportions

**🔍 5-Level Zoom System**
- **Level 1 (Sentence)**: Individual utterances and speaker turns
- **Level 2 (Turn)**: Aggregated speaker contributions
- **Level 3 (Topic)**: Semantic topic segments
- **Level 4 (Theme)**: Major thematic clusters
- **Level 5 (Arc)**: Narrative arcs and conversation structure

**🎭 Advanced AI Analysis**
- **Simulacra Level Detection**: Classify utterances by communication intent (Levels 1-4)
- **Cognitive Bias Detection**: Identify 25+ types of biases and logical fallacies
- **Implicit Frame Analysis**: Uncover hidden worldviews and normative assumptions
- **Speaker Analytics**: Role detection, time distribution, topic dominance

**⚙️ Customizable AI Prompts**
- Externalized prompts in JSON configuration
- User-editable via Settings UI
- A/B testing support for prompt variations
- Version history and rollback capability
- Performance metrics per prompt (cost, latency, accuracy)

**📈 Cost Tracking & Instrumentation**
- Real-time LLM API cost tracking
- Latency monitoring (p50, p95, p99)
- Token usage analytics by feature
- Cost per conversation dashboards
- Automated alerts for threshold breaches

**✏️ Edit Mode & Training Data Export**
- Manual correction of AI-generated nodes/edges
- All edits logged for future model training
- Export formats: JSONL (fine-tuning), CSV (analysis), Markdown (review)
- Feedback annotation for continuous improvement

---

## Demo

- [Live Conversational Threads Presentation (YouTube)](https://youtu.be/sflh9t_Y1eQ?feature=shared)

*Note: Video reflects earlier version of the application. Current version includes dual-view architecture, zoom levels, and advanced analysis features.*

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                     │
│  ┌────────────────┐  ┌─────────────────────────────────┐   │
│  │ Timeline View  │  │  Contextual Network View        │   │
│  │ (15% height)   │  │  (85% height)                   │   │
│  │                │  │                                  │   │
│  │ ●──●──●──●──●  │  │      ┌──┐      ┌──┐            │   │
│  │                │  │      │  │──────│  │            │   │
│  └────────────────┘  │      └──┘      └──┘            │   │
│                      │         ↘      ↗                 │   │
│                      │          ┌──┐                   │   │
│                      │          │  │                   │   │
│                      │          └──┘                   │   │
│                      └─────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST API
┌──────────────────────────────┴──────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Parsers     │  │  AI Services │  │  Instrumentation │  │
│  │ - Google Meet│  │ - Clustering │  │  - Cost Tracking │  │
│  │              │  │ - Bias Det.  │  │  - Metrics       │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└──────────────────────────────┬──────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   ┌────▼────┐          ┌──────▼──────┐      ┌───────▼──────┐
   │PostgreSQL│          │ OpenAI API │      │ GCS Storage  │
   │ Database │          │ Anthropic  │      │ (Transcripts)│
   └──────────┘          └─────────────┘      └──────────────┘
```

### Data Flow

1. **Import**: User uploads Google Meet transcript (PDF/TXT)
2. **Parsing**: Backend extracts speakers, utterances, timestamps
3. **AI Analysis**: LLM generates nodes, edges, clusters (via prompts.json)
4. **Storage**: Conversation data saved to PostgreSQL, files to GCS
5. **Visualization**: Frontend fetches graph data, renders dual-view
6. **Interaction**: User explores zoom levels, selects nodes, views analytics
7. **Editing**: User corrections logged to `edits_log` table
8. **Export**: Training data exported in JSONL format for fine-tuning

---

## Project Structure

```
live_conversational_threads/
├── lct_python_backend/          # Python FastAPI backend
│   ├── backend.py              # Main FastAPI application
│   ├── db.py                   # Database connection & ORM
│   ├── db_helpers.py           # Database helper functions
│   ├── requirements.txt        # Backend dependencies
│   ├── config/
│   │   └── prompts.json        # Externalized LLM prompts
│   ├── services/
│   │   ├── graph_generation_service.py
│   │   ├── prompts_service.py
│   │   ├── simulacra_detector.py
│   │   └── cognitive_bias_detector.py
│   ├── parsers/
│   │   └── google_meet_parser.py
│   ├── instrumentation/
│   │   ├── decorators.py       # @track_api_call
│   │   └── cost_calculator.py
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
├── lct_app/                     # React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── DualView/
│   │   │   │   ├── DualViewCanvas.tsx
│   │   │   │   ├── TimelineView.tsx
│   │   │   │   └── ContextualNetworkView.tsx
│   │   │   ├── NodeDetail/
│   │   │   ├── Analytics/
│   │   │   └── Settings/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── tests/
│   ├── package.json
│   └── vite.config.ts
├── docs/                        # Comprehensive documentation
│   ├── ROADMAP.md              # 14-week implementation plan
│   ├── TIER_1_DECISIONS.md     # Foundational design decisions
│   ├── TIER_2_FEATURES.md      # Detailed feature specifications
│   ├── FEATURE_SIMULACRA_LEVELS.md
│   ├── FEATURE_ROADMAP.md
│   ├── DATA_MODEL_V2.md
│   ├── PRODUCT_VISION.md
│   └── adr/                    # Architecture Decision Records
│       ├── ADR-001-google-meet-transcript-support.md
│       ├── ADR-002-hierarchical-coarse-graining.md
│       ├── ADR-003-observability-and-storage-foundation.md
│       ├── ADR-004-dual-view-architecture.md
│       └── ADR-005-prompts-configuration-system.md
├── README.md                    # This file
└── requirements.txt
```

---

## Prerequisites

- **Python 3.11+** (with `venv` or Conda)
- **Node.js 18+** and **npm 9+**
- **PostgreSQL 14+**
- **API Keys**:
  - OpenAI API key (for GPT-4, GPT-3.5-turbo)
  - Anthropic API key (for Claude Sonnet-4)
  - Google Cloud Storage credentials (for transcript storage)
  - AssemblyAI API key (optional, for future audio support)

---

## Backend Setup

### 1. Create and activate Python environment

**Using venv:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Or using Conda:**
```bash
conda create -n lct_env python=3.11
conda activate lct_env
```

### 2. Install backend dependencies

```bash
cd lct_python_backend
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root or export variables:

```bash
# LLM API Keys
export OPENAI_API_KEY=your_openai_api_key
export ANTHROPIC_API_KEY=your_anthropic_api_key

# Google Cloud Storage
export GCS_BUCKET_NAME=your_gcs_bucket
export GCS_FOLDER=conversations
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Database
export DATABASE_URL=postgresql://user:password@localhost:5432/lct_db

# Optional (for future features)
export ASSEMBLYAI_API_KEY=your_assemblyai_api_key
export PERPLEXITY_API_KEY=your_perplexity_api_key
export GOOGLEAI_API_KEY=your_googleai_api_key
```

**On Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your_openai_api_key"
$env:DATABASE_URL="postgresql://user:password@localhost:5432/lct_db"
# ...and so on
```

### 4. Set up PostgreSQL database

See [Database Setup](#database-setup) section below.

---

## Frontend Setup

### 1. Navigate to frontend directory

```bash
cd lct_app
```

### 2. Install Node.js dependencies

```bash
npm install
```

### 3. Configure frontend (optional)

The frontend uses environment variables for API endpoints. Create `lct_app/.env`:

```
VITE_API_BASE_URL=http://localhost:8080
```

Default is `http://localhost:8080`, so this step is optional for local development.

---

## Running the Application

### 1. Start the Backend Server

From the project root (with Python environment activated):

```bash
cd lct_python_backend
uvicorn backend:lct_app --reload --port 8080
```

The backend API will be available at [http://localhost:8080](http://localhost:8080)

**Verify backend is running:**
- Visit [http://localhost:8080/docs](http://localhost:8080/docs) for Swagger UI
- Check [http://localhost:8080/health](http://localhost:8080/health) for health status

### 2. Start the Frontend Development Server

In a new terminal:

```bash
cd lct_app
npm run dev
```

The frontend will be available at [http://localhost:5173](http://localhost:5173)

### 3. Import a Google Meet Transcript

1. Navigate to [http://localhost:5173](http://localhost:5173)
2. Click "Import Transcript" button
3. Upload a Google Meet transcript (PDF or TXT format)
4. Wait for AI-powered graph generation (~30-60 seconds)
5. Explore the conversation using dual-view interface!

---

## Environment Variables

### Backend Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4/GPT-3.5-turbo | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude Sonnet-4 | `sk-ant-...` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/lct_db` |
| `GCS_BUCKET_NAME` | Google Cloud Storage bucket name | `my-lct-bucket` |
| `GCS_FOLDER` | GCS folder for transcript storage | `conversations` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCS service account JSON | `/path/to/credentials.json` |

### Backend Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_CONVERSATION_SIZE_MB` | Max transcript size | `10` |
| `ENABLE_COST_ALERTS` | Enable cost threshold alerts | `true` |
| `DAILY_COST_LIMIT_USD` | Daily spending limit | `100.0` |

### Frontend Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8080` |

---

## Database Setup

### 1. Create PostgreSQL Database

```bash
createdb lct_db
```

### 2. Run Migrations

The application uses Alembic for database migrations. From `lct_python_backend/`:

```bash
# Generate initial migration (if needed)
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### 3. Database Schema

The application uses the following core tables (see `docs/DATA_MODEL_V2.md` for full schema):

```sql
-- Conversations metadata
CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  title VARCHAR(255),
  source VARCHAR(50),  -- 'google_meet', 'manual', etc.
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Speaker-diarized utterances
CREATE TABLE utterances (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id),
  speaker_name TEXT,
  text TEXT,
  start_time FLOAT,
  end_time FLOAT,
  audio_segment_id UUID  -- For future audio support
);

-- AI-generated conversation nodes
CREATE TABLE nodes (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id),
  summary TEXT,
  node_type VARCHAR(50),
  utterance_ids JSONB,  -- Array of utterance UUIDs
  created_by VARCHAR(10),  -- 'ai' or 'user'
  edited BOOLEAN DEFAULT FALSE,
  zoom_level_visible INTEGER,  -- 1-5
  position JSONB,  -- {x, y} coordinates
  created_at TIMESTAMP
);

-- Edges between nodes
CREATE TABLE edges (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id),
  from_node_id UUID REFERENCES nodes(id),
  to_node_id UUID REFERENCES nodes(id),
  relationship_type VARCHAR(20),  -- 'temporal' or 'contextual'
  label TEXT,
  created_by VARCHAR(10),
  created_at TIMESTAMP
);

-- Hierarchical clusters for zoom levels
CREATE TABLE clusters (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id),
  label TEXT,
  child_node_ids JSONB,
  zoom_level_min INTEGER,
  zoom_level_max INTEGER,
  position JSONB
);

-- Edit history (training data)
CREATE TABLE edits_log (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id),
  user_id UUID,
  edit_type VARCHAR(50),
  before_value JSONB,
  after_value JSONB,
  feedback TEXT,
  timestamp TIMESTAMP
);

-- API call instrumentation
CREATE TABLE api_calls_log (
  id UUID PRIMARY KEY,
  conversation_id UUID,
  endpoint TEXT,
  model VARCHAR(50),
  input_tokens INTEGER,
  output_tokens INTEGER,
  total_tokens INTEGER,
  cost_usd DECIMAL(10, 6),
  latency_ms INTEGER,
  timestamp TIMESTAMP,
  success BOOLEAN,
  error_message TEXT
);
```

---

## API Documentation

Once the backend server is running:

- **Swagger UI**: [http://localhost:8080/docs](http://localhost:8080/docs)
- **ReDoc**: [http://localhost:8080/redoc](http://localhost:8080/redoc)

### Key Endpoints

```
POST   /import/google-meet          # Import Google Meet transcript
GET    /conversations/{id}          # Get conversation graph
POST   /conversations/{id}/analyze  # Run AI analysis (bias, Simulacra)
GET    /conversations/{id}/analytics # Get speaker analytics
PATCH  /nodes/{id}                  # Edit node summary
GET    /prompts/                    # List all prompts
PATCH  /prompts/{id}                # Update prompt configuration
GET    /cost-dashboard              # View cost tracking metrics
```

---

## Documentation

### Core Documentation

| Document | Description |
|----------|-------------|
| **[ROADMAP.md](docs/ROADMAP.md)** | 14-week implementation plan with instrumentation, metrics, storage, and testing strategies |
| **[TIER_1_DECISIONS.md](docs/TIER_1_DECISIONS.md)** | Foundational architectural decisions (Google Meet format, zoom levels, dual-view, prompts) |
| **[TIER_2_FEATURES.md](docs/TIER_2_FEATURES.md)** | Detailed specifications for 6 major features (Node Detail Panel, Speaker Analytics, Prompts Config, etc.) |
| **[FEATURE_SIMULACRA_LEVELS.md](docs/FEATURE_SIMULACRA_LEVELS.md)** | Simulacra level detection, cognitive bias analysis, implicit frames, rhetorical profiling |
| **[DATA_MODEL_V2.md](docs/DATA_MODEL_V2.md)** | Complete database schema with all tables, indexes, and relationships |
| **[PRODUCT_VISION.md](docs/PRODUCT_VISION.md)** | High-level product strategy and user personas |
| **[FEATURE_ROADMAP.md](docs/FEATURE_ROADMAP.md)** | ROI analysis and feature prioritization |

### Architecture Decision Records (ADRs)

| ADR | Title | Status |
|-----|-------|--------|
| **[ADR-001](docs/adr/ADR-001-google-meet-transcript-support.md)** | Google Meet Transcript Support | Approved |
| **[ADR-002](docs/adr/ADR-002-hierarchical-coarse-graining.md)** | Hierarchical Coarse-Graining for Multi-Scale Visualization | Proposed |
| **[ADR-003](docs/adr/ADR-003-observability-and-storage-foundation.md)** | Observability, Metrics, and Storage Baseline | Proposed |
| **[ADR-004](docs/adr/ADR-004-dual-view-architecture.md)** | Dual-View Architecture (Timeline + Contextual Network) | Approved |
| **[ADR-005](docs/adr/ADR-005-prompts-configuration-system.md)** | Externalized Prompts Configuration System | Approved |

---

## Development Roadmap

### Phase 1: Foundation & Infrastructure (Weeks 1-4)
- ✅ Database schema migration (DATA_MODEL_V2)
- ✅ Instrumentation & cost tracking
- 🚧 Google Meet transcript parser
- 🚧 Initial graph generation with prompt engineering

### Phase 2: Core Features (Weeks 5-7)
- 📅 Dual-view architecture (Timeline + Contextual)
- 📅 5-level zoom system
- 📅 Node detail panel with editing

### Phase 3: Analysis Features (Weeks 8-10)
- 📅 Speaker analytics view
- 📅 Prompts configuration UI
- 📅 Edit history & training data export

### Phase 4: Advanced Features (Weeks 11-14)
- 📅 Simulacra level detection
- 📅 Cognitive bias detection (25 types)
- 📅 Implicit frame analysis
- 📅 Final integration & polish

**Legend:**
- ✅ Completed
- 🚧 In Progress
- 📅 Planned

See [docs/ROADMAP.md](docs/ROADMAP.md) for detailed sprint-by-sprint breakdown.

---

## Troubleshooting

### Backend Issues

**Database connection errors:**
```bash
# Check PostgreSQL is running
pg_ctl status

# Test connection
psql -U your_user -d lct_db
```

**LLM API errors:**
```bash
# Verify API keys are set
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Check API key validity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Import errors:**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check Python version (must be 3.11+)
python --version
```

### Frontend Issues

**Port conflicts:**
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9

# Or use different port
npm run dev -- --port 3000
```

**CORS errors:**
- Backend is configured to allow `http://localhost:5173`
- If using different port, update CORS settings in `backend.py`

**Build errors:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Performance Issues

**Slow graph generation:**
- Check `api_calls_log` table for high latency
- Consider using GPT-3.5-turbo for cheaper/faster clustering
- Reduce max_tokens in `prompts.json`

**High LLM costs:**
- Check `/cost-dashboard` endpoint
- Review `prompts.json` for token-heavy templates
- Enable prompt caching (coming in Week 9)

---

## Contributing

We welcome contributions! Please follow these guidelines:

### Pull Request Process

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Follow commit message format** (see `.claude/CLAUDE.md`):
   ```
   [TYPE]: Brief summary (50 chars max)

   MOTIVATION:
   - Why this change was needed

   APPROACH:
   - How the solution works

   CHANGES:
   - file1.py: Specific changes made

   IMPACT:
   - What functionality is added/changed

   TESTING:
   - How to verify the changes work
   ```

3. **Write tests**:
   - Unit tests: `pytest tests/unit/test_your_feature.py`
   - Integration tests: `pytest tests/integration/`
   - Maintain 85%+ coverage

4. **Run linters**:
   ```bash
   # Python
   black .
   flake8 .
   mypy .

   # TypeScript
   npm run lint
   npm run typecheck
   ```

5. **Create Pull Request** to `main`:
   - Fill out PR template
   - Link related issues
   - Request review from maintainers

### Development Guidelines

- **No direct commits to main** – all changes via PR
- **Test coverage**: 85%+ for new code
- **Documentation**: Update relevant docs/ files
- **ADRs**: Create ADR for significant architectural decisions
- **Prompts**: Externalize new LLM prompts to `prompts.json`

### Code Style

**Python:**
- Black formatter (line length 100)
- Type hints for all functions
- Docstrings (Google style)

**TypeScript:**
- Prettier formatter
- ESLint rules enforced
- Prefer functional components with hooks

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.

You are free to use, modify, and distribute this software under the terms of the GPLv3, which ensures that derivative works remain open source.

**Key Points:**
- ✅ Use freely for personal, academic, or open-source projects
- ✅ Modify and distribute under GPLv3 terms
- ❌ Cannot use in proprietary/closed-source software without commercial license

### Commercial Use

If you would like to use this software in a **closed-source or commercial product**, or if you need a **commercial license** without the GPL's copyleft requirements, please contact:

**Email**: [adityaadiga6@gmail.com](mailto:adityaadiga6@gmail.com)
**GitHub**: [https://github.com/aditya-adiga](https://github.com/aditya-adiga)

---

## Contact & Support

**Maintainer**: Aditya Adiga
**Email**: [adityaadiga6@gmail.com](mailto:adityaadiga6@gmail.com)
**GitHub**: [@aditya-adiga](https://github.com/aditya-adiga)

**Issues**: [GitHub Issues](https://github.com/aditya-adiga/live_conversational_threads/issues)
**Discussions**: [GitHub Discussions](https://github.com/aditya-adiga/live_conversational_threads/discussions)

---

## Acknowledgments

- **Zvi Mowshowitz** – Simulacra Levels framework
- **LessWrong Community** – Cognitive bias taxonomies
- **OpenAI & Anthropic** – LLM APIs powering analysis
- **React Flow** – Graph visualization library
- **FastAPI** – Python web framework

---

**Last Updated**: 2025-11-11
**Version**: 2.0.0 (Major redesign with Google Meet support)
