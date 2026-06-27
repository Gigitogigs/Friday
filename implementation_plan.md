# Friday: 24-Day Development Roadmap & Technical Guide

This document provides a daily breakdown of the Friday project, extending from Day 1 (Core Security) to Day 24 (Sandbox).

---

## 📅 Roadmap Overview

| Day | Module | Permission Level |
|-----|--------|------------------|
| **1** | Permission & Safety Governor | ✅ Done |
| **2** | OS Operator (Files/Folders) | ✅ Done |
| **3** | OS Destroyer-Lite (Safe Delete) | ✅ Done |
| **4** | Tool Orchestrator (Chains) | `EXECUTE` |
| **5** | Natural Language Interface (NLI) | `READ` |
| **6** | Task & Workflow Manager | `SAFE_WRITE` |
| **7** | History Persistent Storage | `READ` |
| **8** | Long-Term Memory (LTM) | `READ` |
| **9** | Memory Context Injection | `READ` |
| **10** | Knowledge Base: Indexer | `READ` |
| **11** | Knowledge Base: RAG | `READ` |
| **12** | Privacy Guardian: Network | `ADMIN` |
| **13** | Privacy Guardian: Encryption | `ADMIN` |
| **14** | Developer Assistant: Git | `EXECUTE` |
| **15** | Developer Assistant: Code | `EXECUTE` |
| **16** | Command Aliases & Macros | `EXECUTE` |
| **17** | Intelligence Selector | `READ` |
| **18** | System Telemetry | `READ` |
| **19** | Personal Journaler | `SAFE_WRITE` |
| **20** | Local Web Archive | `READ` |
| **21** | Plugin SDK | `ADMIN` |
| **22** | API Server Gateway | `ADMIN` |
| **23** | WebSocket Streaming | `READ` |
| **24** | Experimentation Sandbox | `EXECUTE` |

---

## 🛠️ Module Breakdown & Implementation Guide

### Day 2: OS Operator
*Goal: Basic file and folder management.*
- **Sub-tasks**:
    1. Create `modules/os_operator/core.py`.
    2. Implement `list_files`, `read_file`, `write_file`, `move_file`.
    3. Register these actions in `PermissionManager`.
- **Advice**: Always use `Path.resolve()` to prevent "Path Traversal" attacks (e.g., `../../etc/passwd`).
- **Implementation Note**:
```python
def safe_write(path: str, content: str):
    target = Path(path).resolve()
    if not str(target).startswith(str(Path.home())):
        raise PermissionError("Target outside home directory")
    target.write_text(content, encoding='utf-8')
```

### Day 3: OS Destroyer-Lite
*Goal: Safe, reversible deletion.*
- **Sub-tasks**:
    1. Implement `delete_file` with a "Trash" folder option instead of `os.remove`.
    2. Add mandatory `dry_run` logic that lists all files to be impacted.
- **Advice**: Never use `shutil.rmtree` directly. Use a pattern where you move to a `.friday_trash/` folder first.
- **Security**: Actions with `delete_*` MUST return `PermissionLevel.DELETE`.

### Day 4: Tool Orchestrator
*Goal: Sequential action Execution.*
- **Sub-tasks**:
    1. Create a `Pipeline` class.
    2. Implement `execute_chain(actions: List[ActionRequest])`.
- **Advice**: Use an atomic approach. If Step 3 of 5 fails, log the "Dirty State" so the user can see where it stopped.
- **Pattern**: Implement a `BaseAction` protocol (Command Pattern) to ensure all tools have a unified `execute()` interface.

### Day 5: Natural Language Interface (NLI)
*Goal: Converting User Prompt → ActionRequest.*
- **Sub-tasks**:
    1. Refine System Prompt to enforce JSON output.
    2. Implement a `Parser` that extracts `{ "action": "...", "params": { ... } }`.
- **Advice**: DeepSeek-R1 is great at reasoning, but can be "talkative". Force JSON by wrapping the response in ```json tags.

### Day 6: Task & Workflow Manager
*Goal: GTD system for Friday.*
- **Sub-tasks**:
    1. Define `Task` dataclass (id, title, status, due_date).
    2. Create `data/tasks.json` with persistence logic.
- **Advice**: Use `json.dump(indent=2)` for readability. Users might want to edit the file manually.

### Day 7: History Persistent Storage
*Goal: Memory between restarts.*
- **Sub-tasks**:
    1. Create `data/history.db` (SQLite).
    2. Table schema: `sessions`, `messages` (id, session_id, role, content, timestamp).
- **Suggestion**: Use `contextlib.closing` for safe DB connections.
- **Pattern**: Define a `StorageProtocol` and inject it into the History manager to allow swapping backends (e.g., SQLite to VectorDB).

### Day 8 & 9: Long-Term Memory (LTM)
*Goal: User profiles and context.*
- **Sub-tasks**:
    1. Implement "Fact Extraction": LLM scans chat for "My name is X" or "I like Y".
    2. Implement `MemoryStore(SQLite)` for key-value facts.
- **Context Advice**: On every message, query the DB for the top 5 most relevant "facts" and inject them into the system prompt.

### Day 10 & 11: Knowledge Base (Indexer & RAG)
*Goal: Chat with your local documents.*
- **Sub-tasks**:
    1. Use `os.walk` to find text/markdown files.
    2. (Day 11) Implement simple "Keyword" search initially, then upgrade to vector-based search using `FAISS` or `SentenceTransformers`.
- **Warning**: Do not index `venv/`, `.git/`, or `node_modules/`.

### Day 12 & 13: Privacy Guardian
*Goal: The "Paranoid" layer.*
- **Sub-tasks**:
    1. (Day 12) Wrap `subprocess.run` to check for network flags (`curl`, `wget`).
    2. (Day 13) Use `cryptography` library to encrypt `data/tasks.json` using a user-provided passphrase.

### Day 14 & 15: Developer Assistant
*Goal: Friday as a Pair Programmer.*
- **Sub-tasks**:
    1. Git integration: `git log`, `git status`, `git diff`.
    2. Code Analysis: Pass file content to DeepSeek with a "Review" prompt.
- **Implementation**:
```python
# Skeleton for Git interaction
def git_status(repo_path):
    return subprocess.run(["git", "-C", repo_path, "status"], capture_output=True, text=True)
```

### Day 16: Command Aliases
*Goal: `friday shortcut "clean_logs" "rm logs/*.log"`.*
- **Sub-tasks**:
    1. Save aliases in `config.yaml`.
    2. Logic to expand `$1`, `$2` arguments in aliases.

### Day 17: Intelligence Selector
*Goal: Right model for the job.*
- **Advice**: Small tasks (List files) → `Phi-3`. Hard tasks (Refactor code) → `DeepSeek-R1`.
- **Logic**: Use a regex or simple classifier to decide which model to wake up.

### Day 18: System Telemetry
*Goal: `friday sysinfo`.*
- **Sub-tasks**:
    1. Use `psutil` to get CPU, RAM, and Disk usage.
    2. Check if Ollama is using GPU or CPU (via `ollama show`).
- **Pattern**: Inject a centralized `TelemetryService` rather than modules self-reporting to maintain SRP.

### Day 19: Personal Journaler
*Goal: End-of-day summary.*
- **Sub-tasks**:
    1. Aggregate all "executed" actions from the Audit log for the last 24 hours.
    2. Ask LLM: "Based on these logs, what did the user accomplish today?"

### Day 20: Local Web Archive
*Goal: Offline reading.*
- **Sub-tasks**:
    1. Use `trafilatura` or `beautifulsoup4` to strip boilerplates from URLs.
    2. Save as `.md` in the Knowledge Base.

### Day 21 & 22: Plugin System & API
*Goal: Extensibility.*
- **Sub-tasks**:
    1. Dynamic loading of modules via `importlib`.
    2. (Day 22) `fastapi dev server` start/stop commands.

### Day 23: WebSocket Streaming
*Goal: Real-time generation.*
- **Advice**: This requires moving from `subprocess.run` to a persistent `Ollama` process or the HTTP API (`/api/generate`).

### Day 24: Experimentation Sandbox
*Goal: Safe execution of LLM-generated code.*
- **Sub-tasks**:
    1. Create isolated `tempfile.TemporaryDirectory`.
    2. Execute Python with limited permissions (`multiprocessing` or a separate process with network disabled).
- **Pattern**: Use a **Strategy Pattern** for isolation (e.g., `IsolationProvider`) to make sandboxing logic swappable.

---

## ❓ Open Questions & Critical Decisions
- **RAG Accuracy**: Will FAISS be too heavy for an 8GB RAM machine? (Suggestion: Use NMSLIB or just a simple TF-IDF for starts).
- **Encryption**: Should we store the Master Key in Windows Credential Manager?

## ✅ Verification Plan
- **Daily Regression**: Before committing, run `pytest`. 
- **Audit Check**: Check `data/audit_log.jsonl` to see if the new module's actions are correctly categorized under the new Permission Levels.
- **Security Test**: Try to list a file in `C:\Windows` using the OS Operator; it should be blocked by the `Path.resolve()` check.
