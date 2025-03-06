import sys
import os
import json
import drawsvg as draw
from optparse import OptionParser
from collections import defaultdict
from typing import Dict, List, Tuple

class ModuleBlockDrawerConfig:
    def __init__(self, config_file=None):
        # 默认配置
        self.min_self_width = 1600
        self.min_lr_width = 800
        self.min_height = 300
        self.port_width = 50
        self.port_height = 80
        self.port_line_width = 5
        self.port_line_height = 5
        self.margin_port_td = 70
        self.margin_port_lr = 70
        self.margin_module_td = 320
        self.margin_module_lr = 320
        
        # 颜色配置
        self.input_color = 'blue'
        self.output_color = 'black'
        self.one2many_color = 'red'
        self.background_color = 'white'
        self.border_color = 'black'
        
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
    
    def load_config(self, config_file: str):
        """从JSON文件加载配置"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                for key, value in config.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
        except Exception as e:
            print(f"警告：加载配置文件失败 - {str(e)}")

class ModuleBlockDrawer:
    def __init__(self, module_name: str, instance_name: str, top_module_name: str, config: ModuleBlockDrawerConfig = None):
        self.module_name = module_name
        self.instance_name = instance_name
        self.top_module_name = top_module_name
        self.config = config or ModuleBlockDrawerConfig()
        
        # 初始化数据结构
        self.one2one = defaultdict(lambda: defaultdict(list))
        self.one2many = defaultdict(list)
        self.noconn = []
        self.one2one_nums = defaultdict(int)
        self.one2many_num = 0
        self.noconn_num = 0
        
        # 计算尺寸参数
        self.self_name_height = self.config.port_height
        self.top_name_height = self.config.port_height * 2
    
    def add_one2one(self, port_name: str, port_direction: str, conn_instance: str, conn_module: str, conn_port: str):
        """添加一对一连接信息"""
        self.one2one[conn_instance][port_direction].append({
            "conn_module": conn_module,
            "conn_port": conn_port,
            "port_name": port_name
        })
        self.one2one_nums[conn_instance] += 1
    
    def add_one2many(self, port_name: str, conn_instance: str, conn_module: str, conn_port: str):
        """添加一对多连接信息"""
        if port_name not in self.one2many:
            self.one2many_num += 1
        self.one2many[port_name].append({
            "conn_module": conn_module,
            "conn_instance": conn_instance,
            "conn_port": conn_port
        })
    
    def add_noconn(self, port_name: str):
        """添加未连接端口"""
        self.noconn.append(port_name)
        self.noconn_num += 1
    
    def _split_one2one_nums(self) -> Tuple[Dict, Dict]:
        """将一对一连接分为左右两部分，尽量保持平衡"""
        # 处理一对多连接中的模块
        for k, v in self.one2many.items():
            for vv in v:
                if vv["conn_instance"] not in self.one2one_nums:
                    self.one2one_nums[vv["conn_instance"]] = 1
                    self.one2one[vv["conn_instance"]] = {}
        
        total_sum = sum(self.one2one_nums.values())
        
        # 使用动态规划找到最接近总和一半的子集
        dp = [False] * (total_sum // 2 + 1)
        dp[0] = True
        
        for value in self.one2one_nums.values():
            for j in range(total_sum // 2, value - 1, -1):
                if dp[j - value]:
                    dp[j] = True
        
        # 找到最大可能的和
        max_sum = max(i for i in range(total_sum // 2 + 1) if dp[i])
        
        # 构建左侧字典
        left_dict = {}
        remaining_sum = max_sum
        for k, v in self.one2one_nums.items():
            if remaining_sum >= v and k not in left_dict:
                left_dict[k] = v
                remaining_sum -= v
        
        # 构建右侧字典
        right_dict = {k: v for k, v in self.one2one_nums.items() if k not in left_dict}
        
        return left_dict, right_dict
    
    def draw(self, output_file: str = None):
        """绘制模块连接图"""
        # 分割一对一连接
        one2one_left_num, one2one_right_num = self._split_one2one_nums()
        left_sum = sum(one2one_left_num.values())
        right_sum = sum(one2one_right_num.values())
        
        # 计算画布尺寸
        need_width = self.config.margin_port_lr * 2 + self.config.port_height * max(self.one2many_num, self.noconn_num)
        self_width = max(need_width, self.config.min_self_width)
        lr_width = max(need_width, self.config.min_lr_width)
        
        # 计算高度
        self_left_height = self._calculate_module_height(one2one_left_num, left_sum)
        self_right_height = self._calculate_module_height(one2one_right_num, right_sum)
        self_height = max(self_left_height, self_right_height, self.config.min_height)
        
        # 创建画布
        draw_width = lr_width * 2 + self_width + self.config.margin_module_lr * 4 + 100
        draw_height = self_height + self.top_name_height + self.config.margin_module_td * 2 + self.config.port_height * self.one2many_num + 100
        d = draw.Drawing(draw_width, draw_height)
        
        # 绘制各个部分
        self._draw_top_frame(d, draw_width, draw_height)
        self._draw_self_frame(d, self_width, self_height, lr_width)
        self._draw_left_modules(d, one2one_left_num, lr_width)
        self._draw_right_modules(d, one2one_right_num, lr_width, self_width)
        self._draw_one2many_connections(d, one2one_right_num, lr_width, self_width)
        
        # 保存SVG文件
        output_file = output_file or f'{self.instance_name}.svg'
        d.save_svg(output_file)
        return output_file
    
    def _calculate_module_height(self, modules: Dict, total_ports: int) -> int:
        """计算模块区域高度"""
        return (self.config.margin_module_td * (len(modules) - 1) + 
                self.config.margin_port_td * 2 * len(modules) + 
                self.config.port_height * total_ports + 
                self.self_name_height)

def main():
    parser = OptionParser(usage="Usage: %prog [options] module_name instance_name top_module_name")
    parser.add_option("-c", "--config", dest="config_file",
                      help="配置文件路径")
    parser.add_option("-o", "--output", dest="output_file",
                      help="输出SVG文件路径")
    
    options, args = parser.parse_args()
    
    if len(args) != 3:
        parser.error("需要提供三个参数：module_name, instance_name, top_module_name")
    
    module_name, instance_name, top_module_name = args
    
    try:
        config = ModuleBlockDrawerConfig(options.config_file)
        drawer = ModuleBlockDrawer(module_name, instance_name, top_module_name, config)
        output_file = drawer.draw(options.output_file)
        print(f"成功生成SVG文件：{output_file}")
    except Exception as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()