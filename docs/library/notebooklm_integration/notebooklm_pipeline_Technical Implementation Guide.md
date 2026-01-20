Technical Implementation Guide: Bridging the StackThis guide aligns with the studio_core.py and studio_cli_tools.py implementations.1. Core Tool Installation# Install the MCP bridge
uv tool install notebooklm-mcp-server

# Install Gemini CLI
npm install -g @google/gemini-cli

# Authenticate NotebookLM Session
notebooklm-mcp-auth
2. Connecting the Bridge# Add to Gemini CLI
gemini mcp add notebooklm npx -y notebooklm-mcp-server
3. Global Memory (LanceDB Schema)The GlobalMemoryManager uses the following Pydantic schema for cross-notebook routing:FieldTypePurposevectorVector(768)Gemini-compatible embeddings.textstrThe mirrored content.notebook_idstrThe routing target for the "Silo Breaker" logic.source_namestrOrigin file name.tagsList[str]Categorization for filtered retrieval.4. Operational CommandsDefined in studio_cli_tools.py:Heartbeat: python studio_cli_tools.py heartbeat (Checks session status).Pulse Sync: python studio_cli_tools.py sync (Uploads EOD summary).Heritage Seed: python studio_core.py seed "Project Theme" (Generates cross-notebook context).5. Key Dependencieslancedb: Local vector storage.google-generativeai: For gemini-text-embedding-004.notebooklm-mcp-server: Communication bridge.