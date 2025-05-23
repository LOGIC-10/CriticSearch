#!/usr/bin/env python3
"""
测试BaseAgent工具自动发现功能
输出所有识别到的工具和对应的schema
"""

import sys
import json
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_base_agent_tools():
    try:
        from criticsearch.base_agent import BaseAgent
        
        print("🔧 创建BaseAgent实例（启用自动发现）...")
        print("=" * 60)
        
        # 创建BaseAgent实例，启用自动工具发现
        agent = BaseAgent(auto_discover_tools=True)
        
        print("\n📊 工具发现结果:")
        print("-" * 40)
        
        # 获取所有工具名称
        tool_names = agent.get_tool_names()
        print(f"总共发现工具数量: {len(tool_names)} 个\n")
        
        if not tool_names:
            print("❌ 没有发现任何工具！")
            return
        
        # 输出工具列表
        print("📋 发现的工具列表:")
        for i, tool_name in enumerate(tool_names, 1):
            print(f"  {i:2d}. {tool_name}")
        
        print("\n" + "=" * 60)
        print("🔍 详细Schema信息:")
        print("=" * 60)
        
        # 输出每个工具的详细schema
        for i, tool_name in enumerate(tool_names, 1):
            print(f"\n{i}. 工具名称: {tool_name}")
            print("-" * 30)
            
            schema = agent.get_tool_schema(tool_name)
            if schema:
                # 格式化输出schema
                print("Schema结构:")
                print(json.dumps(schema, indent=2, ensure_ascii=False))
                
                # 提取关键信息
                if 'function' in schema:
                    func_info = schema['function']
                    print(f"\n描述: {func_info.get('description', 'N/A')}")
                    
                    params = func_info.get('parameters', {})
                    properties = params.get('properties', {})
                    required = params.get('required', [])
                    
                    print(f"参数数量: {len(properties)} 个")
                    if required:
                        print(f"必需参数: {', '.join(required)}")
                    else:
                        print("必需参数: 无")
                        
                    if properties:
                        print("参数详情:")
                        for param_name, param_info in properties.items():
                            param_type = param_info.get('type', 'unknown')
                            param_desc = param_info.get('description', 'No description')
                            print(f"  - {param_name} ({param_type}): {param_desc}")
            else:
                print("❌ 无法获取schema")
            
            print("\n" + "-" * 60)
        
        # 测试工具搜索功能
        print("\n🔎 测试工具搜索功能:")
        print("-" * 30)
        
        search_queries = ["search", "note", "scrape"]
        for query in search_queries:
            matching_tools = agent.search_tools(query)
            print(f"搜索 '{query}': 找到 {len(matching_tools)} 个匹配工具")
            for tool in matching_tools:
                tool_name = tool.get('function', {}).get('name') or tool.get('name', 'Unknown')
                print(f"  - {tool_name}")
        
        # 检查特定工具可用性
        print(f"\n✅ 工具可用性检查:")
        print("-" * 20)
        common_tools = ["search", "scrape", "taking_notes", "retrieve_notes"]
        for tool in common_tools:
            is_available = agent.is_tool_available(tool)
            status = "✓" if is_available else "✗"
            print(f"  {status} {tool}")
        
        print(f"\n🎉 测试完成！BaseAgent成功识别了 {len(tool_names)} 个工具")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_base_agent_tools() 