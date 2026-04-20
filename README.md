# mcp-BirdNET-Pi-server

A Model Context Protocol (MCP) server for BirdNET-Pi. Reads detection data directly from BirdNET-Pi's SQLite database and serves audio files from the extracted clips directory.

This is designed to run **on the Raspberry Pi** that hosts BirdNET-Pi, exposed over HTTP, and accessed remotely by Claude Code (or any MCP-compatible client) over your local network.

## How It Works

The server runs on your Pi and speaks streamable-HTTP. Claude Code on your laptop connects to it over the network — no SSH tunneling, no local install of BirdNET-Pi data required.

```
[Claude Code on laptop] --HTTP--> [mcp-server on Pi:8090] --reads--> [birds.db + audio files]
```

## Requirements

- Python 3.10+ on the Pi
- BirdNET-Pi installed (default paths: `~/BirdNET-Pi/scripts/birds.db`, `~/BirdSongs/Extracted/`)

## Setup on the Pi

Clone the repo on your Pi:

```bash
git clone https://github.com/<your-fork>/mcp-birdnet-pi-server ~/BirdNET-Pi/mcp-local-server
cd ~/BirdNET-Pi/mcp-local-server
```

Run it:

```bash
MCP_HTTP_HOST=0.0.0.0 MCP_HTTP_PORT=8090 ./run.sh
```

`run.sh` creates a virtualenv, installs dependencies, and starts the server. After the first run, subsequent starts are fast.

To run it in the background and persist across reboots, add a cron `@reboot` entry or a systemd unit pointing to `run.sh` with the env vars set.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_HTTP_HOST` | `127.0.0.1` | Bind address. Use `0.0.0.0` to accept LAN connections. |
| `MCP_HTTP_PORT` | `8090` | Port to listen on. |
| `BIRDNET_DB` | `~/BirdNET-Pi/scripts/birds.db` | Path to BirdNET-Pi SQLite database. |
| `BIRDNET_AUDIO_DIR` | `~/BirdSongs/Extracted/` | Path to extracted audio clips. |
| `BIRDNET_REPORT_DIR` | `~/BirdSongs/reports/` | Path to write generated reports. |

## Connecting from Claude Code

On your laptop, add the server once:

```bash
claude mcp add --transport http birdnet http://<pi-ip>:8090/mcp
```

Replace `<pi-ip>` with your Pi's local IP (e.g. `192.168.1.107`). The config persists — you don't need to re-run this after the server restarts.

## Available Tools

### `get_detections`
Detections filtered by date range and optional species.
- `start_date` (required): `YYYY-MM-DD`
- `end_date` (required): `YYYY-MM-DD`
- `species` (optional): partial match, case-insensitive

### `get_stats`
Aggregate statistics for a time period.
- `period` (required): `day`, `week`, `month`, or `all`
- `min_confidence` (optional): float 0.0–1.0, default 0.0

### `get_audio`
Audio file for a specific detection.
- `filename` (required): `File_Name` value from a detection record
- `format` (optional): `base64` (default) or `buffer`

### `get_activity`
Hourly detection counts for a specific day.
- `date` (required): `YYYY-MM-DD`
- `species` (optional): partial match, case-insensitive

### `generate_report`
Detection report for a date range.
- `start_date` (required): `YYYY-MM-DD`
- `end_date` (required): `YYYY-MM-DD`
- `format` (optional): `json` (default) or `html`

## Data Source

Reads directly from BirdNET-Pi's SQLite database:

```sql
CREATE TABLE detections (
  Date        DATE,
  Time        TIME,
  Sci_Name    VARCHAR(100),
  Com_Name    VARCHAR(100),
  Confidence  FLOAT,
  ...
  File_Name   VARCHAR(100)
);
```

No JSON export or intermediate files required.

## License

MIT
