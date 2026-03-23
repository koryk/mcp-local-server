#!/usr/bin/env python3
"""BirdNet-Pi MCP Server — Model Context Protocol interface for bird detection data.

Supports both stdio and streamable-http transports.
"""

import os
import sys
from typing import Optional

from pydantic import BaseModel, Field

from mcp.server.fastmcp import FastMCP

from birdnet.functions import (
    get_bird_detections,
    get_detection_stats,
    get_audio_recording,
    get_daily_activity,
    generate_detection_report,
)

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "birdnet-pi",
    stateless_http=True,
    json_response=True,
)


# ---------------------------------------------------------------------------
# Structured output models
# ---------------------------------------------------------------------------


class ConfidenceStats(BaseModel):
    min: float
    max: float
    average: float


class DetectionResult(BaseModel):
    detections: list = Field(description="Matching detection records")
    stats: ConfidenceStats = Field(description="Confidence statistics for the result set")
    total: int = Field(description="Total number of matching detections")


class DetectionStatsResult(BaseModel):
    totalDetections: int
    uniqueSpecies: int
    detectionsBySpecies: dict = Field(description="Map of species name to detection count")
    topSpecies: list = Field(description="Top 10 species by detection count")
    confidenceStats: ConfidenceStats
    periodCovered: str
    minConfidence: float


class AudioResult(BaseModel):
    audio: str = Field(description="Audio data (base64 or raw)")
    format: str = Field(description="Encoding format: 'base64' or 'buffer'")


class DailyActivityResult(BaseModel):
    date: str
    species: str
    totalDetections: int
    hourlyActivity: list = Field(description="24-element array of detection counts per hour")
    peakHour: int = Field(description="Hour (0-23) with the most detections")
    uniqueSpecies: int


class ReportResult(BaseModel):
    report: object = Field(description="Report content (HTML string or JSON object)")
    format: str = Field(description="Report format: 'html' or 'json'")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def get_detections(
    start_date: str = Field(description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Field(description="End date in ISO format (YYYY-MM-DD)"),
    species: Optional[str] = Field(
        default=None,
        description="Optional species name filter (partial match, case-insensitive)",
    ),
) -> DetectionResult:
    """Get bird detections from BirdNet-Pi filtered by date range and optional species.

    Use this when a user asks about which birds were detected, what was seen on a date,
    or wants raw detection data. Requires start_date and end_date in YYYY-MM-DD format.
    Reads from the local detections JSON file. No network calls. No side effects.
    """
    result = await get_bird_detections(start_date, end_date, species)
    return DetectionResult(**result)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def get_stats(
    period: str = Field(
        description="Time period: 'day', 'week', 'month', or 'all'"
    ),
    min_confidence: float = Field(
        default=0.0,
        description="Minimum confidence threshold (0.0-1.0). Defaults to 0.0.",
    ),
) -> DetectionStatsResult:
    """Get aggregate detection statistics for a time period.

    Use this when a user asks for summaries, species counts, top birds, or general stats.
    Period controls how far back to look. min_confidence filters out low-confidence detections.
    Reads from the local detections file. No side effects.
    """
    result = await get_detection_stats(period, min_confidence)
    return DetectionStatsResult(**result)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def get_audio(
    filename: str = Field(description="Audio filename from a detection record"),
    format: str = Field(
        default="base64",
        description="Output format: 'base64' (default) or 'buffer'",
    ),
) -> AudioResult:
    """Retrieve the audio recording for a specific bird detection.

    Use this when a user wants to hear or inspect a detection's audio.
    Requires the filename from a detection record (e.g. 'robin_20241127_083000.wav').
    Reads from the local audio directory. Returns base64-encoded audio by default.
    No network calls. No side effects.
    """
    result = await get_audio_recording(filename, format)
    return AudioResult(**result)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def get_activity(
    date: str = Field(description="Date in ISO format (YYYY-MM-DD)"),
    species: Optional[str] = Field(
        default=None,
        description="Optional species filter (partial match, case-insensitive)",
    ),
) -> DailyActivityResult:
    """Get hourly bird activity patterns for a specific day.

    Use this when a user asks about activity patterns, peak detection times,
    or wants to see when birds are most active. Returns a 24-element array of
    hourly detection counts and identifies the peak hour.
    Reads from the local detections file. No side effects.
    """
    result = await get_daily_activity(date, species)
    return DailyActivityResult(**result)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def generate_report(
    start_date: str = Field(description="Report start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Field(description="Report end date in ISO format (YYYY-MM-DD)"),
    format: str = Field(
        default="json",
        description="Report format: 'html' or 'json'. Defaults to 'json'.",
    ),
) -> ReportResult:
    """Generate a detection report for a date range.

    Use this when a user asks for a formatted summary or report of detections.
    Returns either HTML or JSON format. Reading from local data, but generates
    content dynamically so not strictly idempotent if data changes between calls.
    No network calls. No destructive side effects.
    """
    result = await generate_detection_report(start_date, end_date, format)
    return ReportResult(**result)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "http" or transport == "streamable-http":
        host = os.environ.get("MCP_HTTP_HOST", "127.0.0.1")
        port = int(os.environ.get("MCP_HTTP_PORT", "8000"))
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        mcp.run(transport="stdio")
