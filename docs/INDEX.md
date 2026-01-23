# Studio Mode Documentation Index

Welcome! This guide provides a suggested reading order for understanding the Studio Mode multi-agent system.

## 🚀 Getting Started

1. **[README.md](../README.md)** - Quick start and project overview
2. **[SYSTEM_DOCUMENTATION.md](SYSTEM_DOCUMENTATION.md)** - Full system architecture
3. **[MULTI_AGENT_GUIDE.md](MULTI_AGENT_GUIDE.md)** - How agents work together

## 🏗️ Architecture

4. **[architecture/](architecture/)** - Detailed design documents
5. **[STUDIO_MANIFESTO.md](STUDIO_MANIFESTO.md)** - Design philosophy and principles

## 📚 Deep Dives

6. **[system_context/](system_context/)** - Context and constraints
7. **[research/](research/)** - Background research and exploration
8. **[library/](library/)** - Reference materials and patterns

## 📁 Directory Guide

| Directory         | Contents               |
| ----------------- | ---------------------- |
| `architecture/`   | System design docs     |
| `archive/`        | Legacy/deprecated docs |
| `library/`        | Reference materials    |
| `research/`       | Exploration notes      |
| `system_context/` | Project context        |

## 🔧 Key Files for Developers

| What You Want      | Where to Look                    |
| ------------------ | -------------------------------- |
| Start the system   | `./start_hive.ps1`               |
| Add a new agent    | `.core/services/base_service.py` |
| Configure settings | `.core/config/settings.py`       |
| Understand state   | `.core/models/state.py`          |
| Run tests          | `pytest tests/ -v`               |
