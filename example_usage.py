#!/usr/bin/env python3
"""
Example usage of the refactored BaseAgent with automatic tool discovery.

This demonstrates how the BaseAgent can automatically discover and register
tools without hardcoding tool names.
"""

from criticsearch.base_agent import BaseAgent

def main():
    print("=== BaseAgent Auto-Discovery Example ===\n")
    
    # Create agent with auto-discovery enabled (default)
    agent = BaseAgent(auto_discover_tools=True)
    
    print("1. Auto-discovered tools:")
    tool_names = agent.get_tool_names()
    for tool_name in tool_names:
        print(f"   - {tool_name}")
    
    print(f"\nTotal tools discovered: {len(tool_names)}")
    
    print("\n2. Searching for specific tools:")
    search_tools = agent.search_tools("search")
    print(f"   Tools matching 'search': {len(search_tools)}")
    for tool in search_tools:
        # Handle both direct schema and function schema formats
        tool_name = tool.get('name') or tool.get('function', {}).get('name', 'Unknown')
        tool_desc = tool.get('description') or tool.get('function', {}).get('description', 'No description')
        print(f"   - {tool_name}: {tool_desc[:100]}...")
    
    print("\n3. Getting specific tool schema:")
    search_schema = agent.get_tool_schema("search")
    if search_schema:
        # Handle both direct schema and function schema formats
        schema_name = search_schema.get('name') or search_schema.get('function', {}).get('name', 'Unknown')
        print(f"   Found schema for 'search': {schema_name}")
    else:
        print("   'search' tool not found")
    
    print("\n4. Check if tools are available:")
    tools_to_check = ["search", "scrape", "taking_notes", "retrieve_notes"]
    for tool in tools_to_check:
        available = agent.is_tool_available(tool)
        print(f"   {tool}: {'✓' if available else '✗'}")
    
    print("\n=== Legacy Manual Setup Example ===\n")
    
    # Create agent with manual setup (legacy mode)
    legacy_agent = BaseAgent(auto_discover_tools=False)
    
    print("5. Legacy manually registered tools:")
    legacy_tool_names = legacy_agent.get_tool_names()
    for tool_name in legacy_tool_names:
        print(f"   - {tool_name}")
    
    print(f"\nTotal tools in legacy mode: {len(legacy_tool_names)}")
    
    print("\n6. Refreshing auto-discovered tools:")
    agent.refresh_tools()
    
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main() 