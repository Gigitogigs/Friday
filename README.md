# Friday - Offline Personal Assistant

> **Privacy-First AI Assistant** running entirely on your local machine using Ollama

Friday is a comprehensive offline personal assistant that helps with task management, file organization, productivity, and more—all while keeping your data completely private and local.

---

## 🌟 Features

### Currently Implemented (Day 1 & 2)
- ✅ **Permission & Safety Governor** - Security-first architecture with approval workflows
- ✅ **Audit Logging** - Complete action history in append-only JSONL format
- ✅ **Local LLM Integration** - Powered by Ollama
- ✅ **CLI Interface** - Interactive chat and command-line tools
- ✅ **OS Operator & Search** - Full file management with persistent SQLite indexing

### Planned Features (Days 3-24)
- 🔧 Tool Orchestrator - Multi-step action chains
- 💬 Natural Language Interface - Conversational commands
- ✅ Task & Workflow Manager - GTD-style task tracking
- 🧠 Long-Term Memory - Persistent preferences and context
- 📚 Knowledge Base - Index and search local documents
- 🔒 Privacy Guardian - Network blocking and encryption
- 🤖 Developer Assistant - Code generation and debugging
- ...and 16 more modules

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai/) installed and running
- At least one Ollama model (e.g., `deepseek-r1:1.5b`)

### Installation

```bash
# Clone the repository
git clone https://github.com/Gigitogigs/Friday.git
cd Friday

#Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify Ollama is running
ollama list

# Check Friday status
python friday.py status
```

---

## 📖 Usage

### Check Status
```bash
python friday.py status
```
Shows Ollama status, available models, and permission settings.

### Ask Questions
```bash
python friday.py ask "What is the capital of France?"
```

### Interactive Chat
```bash
python friday.py chat
```
Start a conversational session with Friday. Type `exit` or `quit` to end.

### Manage Permissions
```bash
# List current permissions
python friday.py permission list

# Add to blacklist
python friday.py permission blacklist "dangerous_command"

# Add to whitelist
python friday.py permission whitelist "safe_action"
```

### View Audit Log
```bash
python friday.py audit
```
Shows recent actions with timestamps and approval status.

### Switch Models
```bash
# List available models
python friday.py models

# Switch to a different model
python friday.py use llama2
```

---

## 🏗️ Architecture

```
Friday/
├── core/                      # Core infrastructure
│   ├── permission_manager.py  # Security gatekeeper
│   ├── logger.py              # Audit logging
│   └── ollama_client.py       # LLM communication
├── modules/                   # Feature modules (Days 2-24)
├── data/                      # Local data storage
│   └── audit_log.jsonl        # Action history
├── tests/                     # Test suite
├── config.yaml                # Configuration
└── friday.py                  # CLI entry point
```

---

## 🔧 How It Works

Friday operates on a **three-layer architecture** designed for security, transparency, and modularity:

### 1. **Security Layer** (Permission Manager)
Every action flows through the Permission Manager, which:
- Evaluates the action against 6 permission levels (READ → ADMIN)
- Checks blacklist/whitelist patterns
- Requests user approval for destructive operations
- Provides dry-run previews before execution

### 2. **Intelligence Layer** (Ollama Client)
- Communicates with locally-running Ollama LLM
- Processes natural language commands
- Filters reasoning tokens to show clean responses
- Maintains conversation history for context

### 3. **Execution Layer** (Modules)
- OS Operator: File/folder operations
- Task Manager: GTD-style task tracking
- Knowledge Base: Document indexing
- *(24 modules total, incrementally implemented)*

### Data Flow
```
User Input → CLI → LLM (Ollama) → Action Request → Permission Check → Execute/Deny → Audit Log
```

All operations are logged to `data/audit_log.jsonl` for complete transparency.

**For detailed technical documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).**

---

## 🔒 Security & Privacy

Friday is built with **privacy-first** principles:

### Permission Levels
| Level | Name | Description |
|-------|------|-------------|
| 0 | READ | Read-only operations (always allowed) |
| 1 | SUGGEST | Dry-run previews |
| 2 | SAFE_WRITE | Low-risk writes in user directories |
| 3 | SYSTEM_WRITE | System configuration changes |
| 4 | EXECUTE | Shell command execution |
| 5 | ADMIN | Elevated/dangerous operations |
| 6 | SAFE_DELETE | Deleting standard files |
| 7 | DANGEROUS_DELETE | Deleting system or protected files |

### Safety Features
- ✅ **Approval Workflow** - Destructive actions require explicit user approval
- ✅ **Dry-Run Mode** - Preview actions before execution
- ✅ **Blacklist** - Permanently block dangerous commands
- ✅ **Audit Log** - Complete history of all actions
- ✅ **No External Calls** - All processing happens locally (network disabled by default)

---

## ⚙️ Configuration

Edit `config.yaml` to customize Friday's behavior:

```yaml
friday:
  model: deepseek-r1:1.5b
  
permissions:
  default_level: SUGGEST
  auto_approve:
    - list_files
    - read_file
  blacklist:
    - format_disk
    - "rm -rf /"
```

---

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_permission_manager.py -v
```

**Current Status:** 12/12 tests passing ✅

---

## 📅 Development Roadmap

Friday is being built incrementally, one module per day:

| Day | Module | Status |
|-----|--------|--------|
| 1 | Permission & Safety Governor | ✅ Complete |
| 2 | OS Operator & Search Index | ✅ Complete |
| 3 | Tool Orchestrator | 📋 Planned |
| 4 | Natural Language Interface | 📋 Planned |
| 5 | Task & Workflow Manager | 📋 Planned |
| ... | ... | ... |
| 24 | Experimentation & Sandbox | 📋 Planned |

See the full [implementation plan](docs/plans/) for details.

---

## 🤝 Contributing

We welcome contributions from the community! Friday is an open-source project and we'd love your help making it better.

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** and add tests
4. **Run the test suite** (`python -m pytest tests/ -v`)
5. **Commit your changes** (`git commit -m 'Add amazing feature'`)
6. **Push to your branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Friday.git
cd Friday

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v
```

### Contribution Guidelines

- **Code Style**: Follow PEP 8 guidelines
- **Tests**: Add tests for new features
- **Documentation**: Update README.md and docstrings
- **Security**: Never compromise the privacy-first principle
- **Commits**: Use clear, descriptive commit messages

### Areas We Need Help

- 🐛 Bug fixes and testing
- 📚 Documentation improvements
- 🎨 UI/UX enhancements
- 🔧 New module implementations (Days 2-24)
- 🌍 Internationalization
- 🧪 Additional test coverage

### Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build something great together.

---

## 📄 License

MIT License

---

## 🙏 Acknowledgments

- **Ollama** - Local LLM runtime
- **DeepSeek** - R1 model
- **Rich** - Beautiful terminal formatting
- **Click** - CLI framework

---

## 📞 Support

For issues or questions, please [open an issue](https://github.com/Gigitogigs/Friday/issues).

---

**Built with ❤️ for privacy-conscious users who want AI assistance without compromising their data.**
