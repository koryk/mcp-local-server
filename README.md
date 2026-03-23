# BirdNet-Pi MCP Server

A Model Context Protocol (MCP) server for BirdNet-Pi integration. Provides tools to query bird detection data, statistics, audio recordings, activity patterns, and reports from a local BirdNet-Pi installation.

## Features

- Bird detection data retrieval with date and species filtering
- Detection statistics and analysis
- Audio recording access (base64 or buffer)
- Daily activity patterns with hourly breakdowns
- HTML and JSON report generation
- Dual transport: stdio (default) and streamable-http

## Requirements

- Python 3.10+
- MCP Python SDK >= 1.26.0

## Installation

```bash
pip install -r requirements.txt
```

Or with uv:

```bash
uv pip install -r requirements.txt
```

## Configuration

Environment variables:
- `BIRDNET_DETECTIONS_FILE`: Path to detections JSON file (default: `data/detections.json`)
- `BIRDNET_AUDIO_DIR`: Path to audio files directory (default: `data/audio`)
- `BIRDNET_REPORT_DIR`: Path to reports directory (default: `data/reports`)

## Running the Server

### stdio (default)

```bash
python server.py
```

### Streamable HTTP

```bash
MCP_TRANSPORT=http python server.py
```

Or with custom host/port:

```bash
MCP_TRANSPORT=http MCP_HTTP_HOST=0.0.0.0 MCP_HTTP_PORT=8000 python server.py
```

### Docker

```bash
docker build -t birdnet-pi-mcp .
docker run -p 8000:8000 -v /path/to/data:/app/data birdnet-pi-mcp
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "birdnet": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-local-server/server.py"]
    }
  }
}
```

## Available Tools

### `get_detections`
Get bird detections filtered by date range and optional species.
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format
- `species` (optional): Species name filter (partial match, case-insensitive)

### `get_stats`
Get aggregate detection statistics for a time period.
- `period` (required): `day`, `week`, `month`, or `all`
- `min_confidence` (optional): Minimum confidence threshold 0.0-1.0 (default: 0.0)

### `get_audio`
Retrieve the audio recording for a specific bird detection.
- `filename` (required): Audio filename from a detection record
- `format` (optional): `base64` (default) or `buffer`

### `get_activity`
Get hourly bird activity patterns for a specific day.
- `date` (required): Date in YYYY-MM-DD format
- `species` (optional): Species name filter

### `generate_report`
Generate a detection report for a date range.
- `start_date` (required): Report start date
- `end_date` (required): Report end date
- `format` (optional): `json` (default) or `html`

## Testing

```bash
python -m pytest test_server.py -v
```

## Directory Structure

```
mcp-local-server/
├── birdnet/
│   ├── __init__.py
│   ├── config.py
│   ├── functions.py
│   └── utils.py
├── data/
│   └── detections.json
├── server.py
├── test_server.py
├── Dockerfile
├── requirements.txt
└── README.md
```

## License

MIT

---

## Appendix: MCP in Practice (Code Execution, Tool Scale, and Safety)

Last updated: 2026-03-23

### Why This Appendix Exists
Model Context Protocol (MCP) is still one of the most useful interoperability layers for tools and agents. The tradeoff is that large MCP servers can expose many tools, and naive tool-calling can flood context windows with schemas, tool chatter, and irrelevant call traces.

In practice, "more tools" is not always "better outcomes." Tool surface area must be paired with execution patterns that keep token use bounded and behavior predictable.

### The Shift to Code Execution / Code Mode
Recent workflows increasingly move complex orchestration out of chat context and into code execution loops. This reduces repetitive schema tokens and makes tool usage auditable and testable.

Core reading:
- [Cloudflare: Code Mode](https://blog.cloudflare.com/code-mode/)
- [Cloudflare: Code Execution with MCP](https://blog.cloudflare.com/code-execution-with-mcp/)
- [Anthropic: Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)

### Client Fit Guide (Short Version)
- Claude Code / Codex / Cursor: strong for direct MCP workflows, but still benefit from narrow tool surfaces.
- Code execution wrappers (TypeScript/Python CLIs): better when tool count is high or task chains are multi-step.
- Hosted chat clients with weaker MCP controls: often safer via pre-wrapped CLIs or gateway tools.

### Prompt Injection: Risks, Impact, and Mitigations
Prompt injection remains an open security problem for tool-using agents. It is manageable, but not "solved."

Primary risks:
- Malicious instructions hidden in tool output or remote content.
- Secret exfiltration and unauthorized external calls.
- Unsafe state changes (destructive file/system/API actions).

Mitigation baseline:
- Least privilege for credentials and tool scopes.
- Allowlist destinations and enforce egress controls.
- Strict input validation and schema enforcement.
- Human confirmation for destructive/high-risk actions.
- Sandboxed execution with resource/time limits.
- Structured logging, audit trails, and replayable runs.
- Output filtering/redaction before model re-ingestion.

Treat every tool output as untrusted input unless explicitly verified.
