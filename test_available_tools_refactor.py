#!/usr/bin/env python3
"""
测试available_tools重构后的功能
验证BaseAgent.available_tools是否正常工作
"""

import sys
import json
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_available_tools_refactor():
    try:
        from criticsearch.base_agent import BaseAgent
        
        print("🔧 测试available_tools重构结果")
        print("=" * 50)
        
        # 创建BaseAgent实例
        agent = BaseAgent(auto_discover_tools=True)
        
        print("📊 验证available_tools属性:")
        print("-" * 30)
        
        # 检查BaseAgent.available_tools是否存在
        if hasattr(BaseAgent, 'available_tools'):
            print(f"✅ BaseAgent.available_tools 存在")
            print(f"   工具数量: {len(BaseAgent.available_tools)}")
            
            # 显示所有工具名称
            tool_names = []
            for tool in BaseAgent.available_tools:
                tool_name = tool.get('function', {}).get('name') or tool.get('name', 'Unknown')
                tool_names.append(tool_name)
            
            print(f"   工具列表: {tool_names}")
        else:
            print("❌ BaseAgent.available_tools 不存在!")
            return False
        
        # 检查ConversationManager是否还有available_tools
        print(f"\n📋 验证ConversationManager清理:")
        print("-" * 30)
        
        if hasattr(BaseAgent.conversation_manager, 'available_tools'):
            print("⚠️  ConversationManager仍然有available_tools属性 (应该已移除)")
            return False
        else:
            print("✅ ConversationManager已正确移除available_tools属性")
        
        # 测试工具访问方法
        print(f"\n🔍 测试工具访问方法:")
        print("-" * 30)
        
        # 测试get_tool_names
        names_from_method = agent.get_tool_names()
        print(f"✅ get_tool_names(): {names_from_method}")
        
        # 验证工具数量一致性
        direct_count = len(BaseAgent.available_tools)
        method_count = len(names_from_method)
        
        if direct_count == method_count:
            print(f"✅ 工具数量一致: {direct_count} == {method_count}")
        else:
            print(f"❌ 工具数量不一致: {direct_count} != {method_count}")
            return False
        
        # 测试工具搜索
        search_results = agent.search_tools("search")
        print(f"✅ search_tools('search'): 找到 {len(search_results)} 个工具")
        
        print(f"\n🎉 available_tools重构测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_available_tools_refactor()
    sys.exit(0 if success else 1) 