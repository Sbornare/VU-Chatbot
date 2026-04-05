# VU-Chatbot

A full-stack AI-powered chatbot for college admissions, built with FastAPI (Python) for the backend and React (Vite, TypeScript) for the frontend. It provides information about admissions, programs, fees, campus life, and more, using RAG (Retrieval-Augmented Generation) and IBM Granite models.

---

## Features
- **Conversational AI**: Chatbot answers queries about admissions, programs, fees, campus, placements, and more.
- **Admin Panel**: Manage documents, ingest new data, and monitor chat logs.
- **RAG Pipeline**: Uses document chunking, embeddings, and vector search for accurate answers.
- **Authentication**: JWT-based user authentication and admin access.
- **Course Recommender**: Suggests programs based on user interests.
- **Deadline Service**: Provides important dates and deadlines.

---

## Project Structure

```
VU-Chatbot/
├── backend/         # FastAPI backend (API, Auth, RAG, Services, Utils)
│   ├── api/         # API endpoints (admin, chat, ingest, query)
│   ├── auth/        # Authentication logic
│   ├── data/        # Knowledge base documents
│   ├── granite/     # IBM Granite model integration
│   ├── models/      # Database models
│   ├── rag/         # RAG pipeline and vector store
│   ├── scripts/     # Utility scripts (init DB, create admin, etc.)
│   ├── services/    # Business logic (recommender, deadlines)
│   ├── utils/       # Utility functions
│   ├── main.py      # FastAPI app entrypoint
│   ├── config.py    # Settings and environment config
│   ├── database.py  # Database setup
│   └── requirements.txt
├── Frontend/        # React frontend (Vite, TypeScript, Tailwind)
│   ├── src/         # Source code (components, pages, hooks, services)
│   ├── public/      # Static assets
│   ├── package.json # NPM dependencies
│   └── ...
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## Prerequisites
- **Python 3.10+** (recommended: use a virtual environment)
- **Node.js 18+** and **npm**
- (Optional) **Docker** for containerized deployment

---

## Setup & Running Locally

### 1. Clone the Repository
```bash
git clone <repo-url>
cd VU-Chatbot
```

### 2. Backend Setup
```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
# Create .env file (see .env.example or below)
cp .env.example .env  # or create manually
# (Optional) Initialize DB and admin user
python scripts/init_db.py
python scripts/create_admin.py
# Start backend server
export PYTHONPATH=$PYTHONPATH:$(pwd)/..
uvicorn main:app --reload
```

#### .env Example
```
DATABASE_URL=sqlite:///./test.db
AWS_S3_BUCKET=your-s3-bucket
AWS_REGION=us-east-1
AWS_S3_PREFIX=vu-chatbot-db
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
JWT_SECRET=supersecretkey
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
APP_NAME=College Admission Agent
IBM_CLOUD_API_KEY=your-ibm-api-key
IBM_PROJECT_ID=your-ibm-project-id
IBM_WATSONX_URL=https://your-watsonx-url
GRANITE_EMBEDDING_MODEL=your-embedding-model
GRANITE_CHAT_MODEL=your-chat-model
```

### 3. Frontend Setup
```bash
cd ../Frontend
npm install
npm run dev
```
- The app will be available at [http://localhost:8080](http://localhost:8080) or [http://localhost:8081](http://localhost:8081) if port 8080 is busy.

---

## Usage
- **Chat**: Ask questions about admissions, programs, fees, campus, etc.
- **Admin**: Log in as admin to manage documents and view chat logs.
- **Course Recommender**: Get program suggestions based on your interests.
- **Deadlines**: Ask about important dates and deadlines.

---

## Docker (Optional)
To run both backend and frontend with Docker:
```bash
docker-compose up --build
```

---

## Contributing
1. Fork the repo and create your branch.
2. Make changes and commit.
3. Open a pull request.

---

## License
MIT License

---

## Contact
For questions or support, open an issue or contact the maintainer.
