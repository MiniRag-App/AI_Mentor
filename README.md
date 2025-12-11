# AI Mentor

AI Mentor is a minimal Retrieval-Augmented Generation (RAG) application that provides context-aware question answering and guidance using a small, easy-to-run FastAPI service.
 
## Requirements
- Python 3.8+
- Recommended: use a virtual environment (conda or venv)

## Installation (conda)
1. Create and activate environment:
```bash
conda create -n ai-mentor python=3.8 -y
conda activate ai-mentor
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment
1. Copy the example env file:
```bash
cp .env.example .env
```
2. Edit `.env` and set required keys (API keys, model/config flags).

## Run the server
Start the FastAPI server locally:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

 

## Project structure (actual)
```
src/
├── __pycache__/                  # Python cache files
├── .deepeval/                    # DeepEval cache and evaluation state
├── assets/                       # Static files, examples, Postman collections
├── controllers/                  # Request handlers and business logic controllers
├── evaluation/                   # Evaluation scripts and DeepEval configs
├── helpers/                      # Utility helper functions
├── models/                       # Data models and Pydantic schemas
├── routes/                       # FastAPI route definitions and endpoints
├── stores/                       # External service integrations
│   ├── llm/                      # Ollama LLM service wrapper
│   └── vectordb/                 # Vector database (FAISS, etc.) wrapper
├── utils/                        # Common utilities (text processing, I/O, logging)
│   └── __init__.py
├── __init__.py                   # Package initialization
├── .env                          # Local environment variables (git ignored)
├── .env.example                  # Example env template
├── .gitignore
├── main.py                       # FastAPI app entry point
├── requirements.txt              # Python dependencies
├── evaluation_dataset.json       # Benchmark QA dataset
└── README.md                     # Application README
```
 
 

 