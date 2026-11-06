"""Real MCP stdio client, invoked by a deterministic LangGraph tool node."""
import asyncio
import json
import sys
import threading
from datetime import timedelta
from pathlib import Path
from typing import TypedDict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langgraph.graph import StateGraph, START, END

TOOLS = {'search_restaurants', 'check_availability', 'create_demo_booking', 'cancel_demo_booking'}
CHILD_SLOTS = threading.BoundedSemaphore(2)


class ToolState(TypedDict):
    tool: str
    arguments: dict
    result: dict
    trace: list


class DemoBookingGateway:
    async def call(self, tool: str, arguments: dict) -> dict:
        if not CHILD_SLOTS.acquire(blocking=False):
            raise RuntimeError('Demo tool capacity reached')
        try:
            return await self._call(tool, arguments)
        finally:
            CHILD_SLOTS.release()

    async def _call(self, tool: str, arguments: dict) -> dict:
        if tool not in TOOLS:
            raise ValueError('Unsupported demo tool')
        async def invoke(state):
            trace = []
            def record(event, name):
                trace.append({'event': event, 'tool': name, 'status': 'ok', 'protocol': 'MCP', 'transport': 'stdio', 'simulation': True})
            params = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).with_name('demo_restaurant_server.py'))], env={'PYTHONUNBUFFERED': '1'})
            async with asyncio.timeout(20):
                async with stdio_client(params) as (read, write):
                    async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=15)) as session:
                        await session.initialize(); record('initialize', 'initialize')
                        listing = await session.list_tools()
                        if TOOLS != {item.name for item in listing.tools}:
                            raise ValueError('Unexpected demo tool registry')
                        record('tools/list', 'tools/list')
                        response = await session.call_tool(state['tool'], state['arguments'])
                        if response.isError:
                            raise ValueError('Demo tool rejected request')
                        payload = response.structuredContent
                        if payload is None:
                            payload = json.loads(next(item.text for item in response.content if item.type == 'text'))
                        if payload.get('simulation') is not True:
                            raise ValueError('Demo tool returned an invalid result')
                        record('tools/call', state['tool'])
                        return {'result': payload, 'trace': trace}
        graph = StateGraph(ToolState)
        graph.add_node('mcp_tool', invoke)
        graph.add_edge(START, 'mcp_tool'); graph.add_edge('mcp_tool', END)
        result = await graph.compile().ainvoke({'tool': tool, 'arguments': arguments})
        return {'result': result['result'], 'trace': result['trace']}
