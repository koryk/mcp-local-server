"""Behavior tests for BirdNet-Pi MCP server.

Tests tool listing, successful calls, and validation failures using
the FastMCP instance's direct methods.
"""

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from server import mcp


class TestBirdNetMCPServer(unittest.TestCase):
    """Test the BirdNet MCP server through FastMCP's direct API."""

    # ---- tools/list ----

    def test_list_tools(self):
        """Server exposes all five tools."""
        tools = asyncio.run(mcp.list_tools())
        names = sorted([t.name for t in tools])
        self.assertEqual(
            names,
            ["generate_report", "get_activity", "get_audio", "get_detections", "get_stats"],
        )

    def test_tools_have_descriptions(self):
        """Every tool has a non-empty description."""
        tools = asyncio.run(mcp.list_tools())
        for tool in tools:
            self.assertTrue(tool.description, f"{tool.name} missing description")

    def test_tools_have_input_schema(self):
        """Every tool has an inputSchema of type object."""
        tools = asyncio.run(mcp.list_tools())
        for tool in tools:
            self.assertIsNotNone(tool.inputSchema, f"{tool.name} missing inputSchema")
            self.assertEqual(tool.inputSchema.get("type"), "object")

    def test_tools_have_annotations(self):
        """Every tool has annotations."""
        tools = asyncio.run(mcp.list_tools())
        for tool in tools:
            self.assertIsNotNone(tool.annotations, f"{tool.name} missing annotations")

    def test_all_tools_read_only(self):
        """All BirdNet tools should be read-only."""
        tools = asyncio.run(mcp.list_tools())
        for tool in tools:
            if tool.annotations:
                self.assertTrue(
                    tool.annotations.readOnlyHint,
                    f"{tool.name} should be readOnlyHint=True",
                )
                self.assertFalse(
                    tool.annotations.destructiveHint,
                    f"{tool.name} should be destructiveHint=False",
                )

    # ---- tools/call - success paths ----

    def _call_tool(self, name: str, arguments: dict):
        """Call a tool and return (content_list, structured_content)."""
        return asyncio.run(mcp.call_tool(name, arguments))

    def test_get_detections_success(self):
        """get_detections returns results for a valid date range."""
        content, structured = self._call_tool(
            "get_detections",
            {"start_date": "2024-11-27", "end_date": "2024-11-28"},
        )
        self.assertTrue(len(content) > 0)
        data = json.loads(content[0].text)
        self.assertIn("total", data)
        self.assertEqual(data["total"], 2)

    def test_get_detections_with_species_filter(self):
        """get_detections filters by species."""
        content, structured = self._call_tool(
            "get_detections",
            {"start_date": "2024-11-27", "end_date": "2024-11-28", "species": "Robin"},
        )
        data = json.loads(content[0].text)
        self.assertEqual(data["total"], 1)

    def test_get_detections_empty_range(self):
        """get_detections returns empty for date range with no data."""
        content, structured = self._call_tool(
            "get_detections",
            {"start_date": "2020-01-01", "end_date": "2020-01-02"},
        )
        data = json.loads(content[0].text)
        self.assertEqual(data["total"], 0)

    def test_get_stats_success(self):
        """get_stats returns statistics."""
        content, structured = self._call_tool("get_stats", {"period": "all"})
        data = json.loads(content[0].text)
        self.assertIn("totalDetections", data)
        self.assertIn("uniqueSpecies", data)

    def test_get_stats_with_confidence_filter(self):
        """get_stats respects min_confidence."""
        content, _ = self._call_tool(
            "get_stats", {"period": "all", "min_confidence": 0.9}
        )
        data = json.loads(content[0].text)
        self.assertEqual(data["minConfidence"], 0.9)

    def test_get_activity_success(self):
        """get_activity returns hourly patterns."""
        content, structured = self._call_tool("get_activity", {"date": "2024-11-27"})
        data = json.loads(content[0].text)
        self.assertIn("hourlyActivity", data)
        self.assertEqual(len(data["hourlyActivity"]), 24)

    def test_get_activity_with_species(self):
        """get_activity filters by species."""
        content, _ = self._call_tool(
            "get_activity", {"date": "2024-11-27", "species": "Cardinal"}
        )
        data = json.loads(content[0].text)
        self.assertEqual(data["species"], "Cardinal")

    def test_generate_report_json(self):
        """generate_report produces JSON output."""
        content, structured = self._call_tool(
            "generate_report",
            {"start_date": "2024-11-27", "end_date": "2024-11-28", "format": "json"},
        )
        data = json.loads(content[0].text)
        self.assertEqual(data.get("format"), "json")

    def test_generate_report_html(self):
        """generate_report produces HTML output."""
        content, structured = self._call_tool(
            "generate_report",
            {"start_date": "2024-11-27", "end_date": "2024-11-28", "format": "html"},
        )
        data = json.loads(content[0].text)
        self.assertEqual(data.get("format"), "html")


if __name__ == "__main__":
    unittest.main()
