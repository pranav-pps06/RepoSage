# RepoSage – AI-Powered Codebase Intelligence Using RAG

RepoSage indexes public GitHub repositories, performs hybrid code search (Semantic Vector Search + BM25 keyword matching + Reciprocal Rank Fusion + Cross-Encoder reranking), and answers codebase questions with verifiable, clickable line-level citations.

---

## 🛠️ System Architecture

- **Backend**: FastAPI, Uvicorn, SQLite (`reposage.db`, `conversations.db`)
- **Ingestion**: GitPython, language-aware filtering, configurable line chunker with overlap
- **Embeddings & Vector Search**: `sentence-transformers` (`all-MiniLM-L6-v2`), local persistent Qdrant database
- **Hybrid Retrieval**: BM25 (`rank-bm25`) + Semantic Search fused via Reciprocal Rank Fusion (RRF)
- **Reranker**: Cross-Encoder (`ms-marco-MiniLM-L-6-v2`)
- **Generation & Conversational Memory**: Google Gemini Flash API + Multi-turn query rewriting
- **Frontend**: React (Vite), Tailwind CSS v4, Lucide Icons, interactive sliding code inspector with line highlighting

---

## 🚀 How to Run the Project

### 1. Configure Environment Variables
In `backend/.env`, set your Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
```

### 2. Start the Backend API Server
Open a terminal in the project root:
```powershell
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs & Swagger UI will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 3. Start the Frontend Application
Open another terminal:
```powershell
cd frontend
npm run dev
```
Open your browser at [http://localhost:5173](http://localhost:5173).

---

## 💡 Features & Capabilities
1. **Repository Dashboard**:
   - Add any public repository URL (`https://github.com/org/repo`).
   - Real-time indexing status, language detection, file count, and chunk count.
   - Switch between multiple indexed repositories.
2. **AI Chat Interface**:
   - Ask architecture, implementation, and flow questions.
   - Suggested prompt chips.
   - Verified file & line citations below each response.
3. **Interactive Source Code Inspector**:
   - Click any citation badge to slide open the source viewer.
   - View the entire file with automatic scrolling and line-range highlighting.
