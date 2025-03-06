import sys
import os
from pyverilog.vparser.parser import parse
from typing import Dict, List, Tuple

def parse_verilog_modules(file_paths: List[str], top_module: str) -> Dict:
    """解析Verilog文件并提取模块信息

    Args:
        file_paths: Verilog文件路径列表
        top_module: 顶层模块名

    Returns:
        包含解析结果的字典，格式如下：
        {
            'modules_signals': {module_name: {port_name: port_info}},
            'submodules': [instance_names],
            'instances': {instance_name: instance_info},
            'connections': {signal_name: [(instance_name, module_name, port_name)]}
        }
    """
    try:
        # 解析文件
        ast, _ = parse(file_paths)
        
        # 初始化返回数据
        result = {
            'modules_signals': {},
            'submodules': [],
            'instances': {},
            'connections': {}
        }
        
        # 分析模块
        for module_def in ast.description.definitions:
            module_name = module_def.name
            
            # 收集模块的端口信息
            if module_name not in result['modules_signals']:
                result['modules_signals'][module_name] = {}
                for item in module_def.items:
                    if item.__class__.__name__ == 'Decl':
                        for port in item.list:
                            if port.__class__.__name__ in ['Input', 'Output', 'Inout']:
                                result['modules_signals'][module_name][port.name] = port.dict()
            
            # 如果是顶层模块，收集实例信息
            if module_name == top_module:
                for item in module_def.items:
                    if item.__class__.__name__ == 'InstanceList':
                        for instance in item.instances:
                            # 保存实例信息
                            result['instances'][instance.name] = {
                                'module': instance.module,
                                'ports': {}
                            }
                            result['submodules'].append(instance.name)
                            
                            # 保存端口连接信息
                            for port in instance.portlist:
                                result['instances'][instance.name]['ports'][port.portname] = port.argname.name
                                if port.argname.name not in result['connections']:
                                    result['connections'][port.argname.name] = []
                                result['connections'][port.argname.name].append(
                                    (instance.name, instance.module, port.portname)
                                )
        
        return result
    
    except Exception as e:
        raise Exception(f"解析失败: {str(e)}")

def main():
    """命令行入口函数"""
    if len(sys.argv) < 3:
        print("Usage: python verilog_parser.py <top_module> <file1> [file2 ...]")
        sys.exit(1)
    
    top_module = sys.argv[1]
    file_paths = sys.argv[2:]
    
    # 验证文件是否存在
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"错误：文件不存在 {file_path}")
            sys.exit(1)
    
    try:
        result = parse_verilog_modules(file_paths, top_module)
        print(f"解析成功！找到 {len(result['submodules'])} 个子模块")
        for submodule in result['submodules']:
            print(f"  - {submodule}")
    except Exception as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()