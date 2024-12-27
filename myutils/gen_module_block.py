from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import json
import drawsvg as draw
from optparse import OptionParser
from collections import defaultdict

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyverilog
from pyverilog.vparser.parser import parse

class ModuleBlockDrawer:
    def __init__(self, module_name, instance_name, top_module_name):
        self.module_name = module_name
        self.instance_name = instance_name
        self.top_module_name = top_module_name
        self.one2one = defaultdict(lambda: defaultdict(list))
        self.one2many = defaultdict(list)
        self.noconn = []
        self.one2one_nums = defaultdict(int)
        self.one2many_num = 0
        self.noconn_num = 0

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
        self.self_name_height = self.port_height
        self.top_name_height = self.port_height * 2

    def add_one2one(self, port_name, port_direction, conn_instance, conn_module, conn_port):
        self.one2one[conn_instance][port_direction].append(
            {
                "conn_module": conn_module,
                "conn_port": conn_port,
                "port_name": port_name
            }
        )
        # self.one2one_nums[f"self_{port_direction}"] += 1
        self.one2one_nums[conn_instance] += 1
        # print(f"add_one2one: {conn_instance}, {port_direction}, {self.one2one_nums[conn_instance]}")

    def add_one2many(self, port_name, conn_instance, conn_module, conn_port):
        if port_name not in self.one2many:
            self.one2many_num += 1
        self.one2many[port_name].append(
            {
                "conn_module": conn_module,
                "conn_instance": conn_instance,
                "conn_port": conn_port
            }
        )
    
    def add_noconn(self, port_name):
        self.noconn.append(port_name)
        self.noconn_num += 1
    
    def split_one2one_nums_to_minimize_difference(self):
        # one2many中的模块如果不在one2one中将它加到one2one中，并且port数记为1
        for k, v in self.one2many.items():
            for vv in v:
                if vv["conn_instance"] not in self.one2one_nums:
                    self.one2one_nums[vv["conn_instance"]] = 1
                    self.one2one[vv["conn_instance"]] = {}

        total_sum = sum(self.one2one_nums.values())
        print(f"values: {self.one2one_nums.values()}; total_sum: {total_sum}")
        
        # Initialize dp array where dp[i] will be True if sum i can be formed
        dp = [False] * (total_sum // 2 + 1)
        dp[0] = True
        
        # Populate dp array
        for value in self.one2one_nums.values():
            for j in range(total_sum // 2, value - 1, -1):
                if dp[j - value]:
                    dp[j] = True
        
        # Find the maximum sum that can be achieved
        max_sum = 0
        for i in range(total_sum // 2, -1, -1):
            if dp[i]:
                max_sum = i
                break
        print(f"max_sum: {max_sum}")

        # 构建 dict1，尽可能接近 max_sum
        dict1 = {}
        while max_sum > 0:
            reduced = False
            for k, v in self.one2one_nums.items():
                if max_sum >= v and dp[max_sum - v] and k not in dict1:
                    dict1[k] = v
                    max_sum -= v
                    reduced = True
                    print(f"selected key: {k}, selected value: {v}, remaining sum: {max_sum}")
            if not reduced:
                break
        
        # dict2 就是剩余的部分
        dict2 = {k: v for k, v in self.one2one_nums.items() if k not in dict1}

        return dict1, dict2

    def draw(self):
        one2one_left_num, one2one_right_num = self.split_one2one_nums_to_minimize_difference()
        left_sum = sum(one2one_left_num.values())
        right_sum = sum(one2one_right_num.values())

        need_width = self.margin_port_lr * 2 + self.port_height * max(self.one2many_num, self.noconn_num)
        self_left_height = self.margin_module_td * (len(one2one_left_num) - 1) + self.margin_port_td * 2 * len(one2one_left_num) + self.port_height * left_sum + self.self_name_height
        self_right_height = self.margin_module_td * (len(one2one_right_num) - 1) + self.margin_port_td * 2 * len(one2one_right_num) + self.port_height * right_sum + self.self_name_height

        self_width = max(need_width, self.min_self_width)
        lr_width = max(need_width, self.min_lr_width)
        self_height = max(self_left_height, self_right_height, self.min_height)

        draw_width = lr_width * 2 + self_width + self.margin_module_lr * 4 + 100
        draw_height = self_height + self.top_name_height + self.margin_module_td * 2 + self.port_height * self.one2many_num + 100

        d = draw.Drawing(draw_width, draw_height)
        '''
        添加top矩形
        '''
        d.append(draw.Rectangle(50, 50, draw_width - 100, draw_height - 100, fill='white', stroke='black'))
        # 在矩形中心写模块名字
        d.append(draw.Text(
            self.top_module_name,
            font_size=self.port_height * 2,
            x=draw_width / 2,
            y=50 + self.port_height * 2,
            text_anchor='middle',
            dominant_baseline='middle'
        ))

        '''
        添加self矩形
        '''
        self_left = self.margin_module_lr * 2 + lr_width * 1 + 50
        self_top = self.margin_module_td + self.top_name_height + self.port_height * self.one2many_num + 50
        d.append(draw.Rectangle(
            self_left, 
            self_top, 
            self_width, 
            self_height, 
            fill='white', 
            stroke='black'
        ))
        # 在矩形中心写模块名字
        d.append(draw.Text(
            self.instance_name,
            font_size=self.port_height,
            x=draw_width / 2,
            y=self_top + 10,
            text_anchor='middle',
            dominant_baseline='hanging'
        ))

        '''
        添加left module矩形
        '''
        top = self_top + self.self_name_height
        left = self.margin_module_lr * 1 + 50
        width = lr_width
        for k, v in one2one_left_num.items():
            height = self.port_height * v + self.margin_port_td * 2
            if k[0:4] == "TOP(" and k[-1] == ")":
                line_start_x = 50
            else:
                d.append(draw.Rectangle(
                    left, top, width, height,
                    fill='white',
                    stroke='black'
                ))
                # 在矩形中心写模块名字
                d.append(draw.Text(
                    k,
                    font_size=self.port_height,
                    x=left + width / 2,
                    y=top + height / 2,
                    text_anchor='middle',
                    dominant_baseline='middle'
                ))
                line_start_x = left + width

            signals = self.one2one[k]
            i = 1
            line_end_x = self_left
            if "Input" in signals:
                for signal in signals["Input"]:
                    # 画有向箭头
                    line_start_y = top + self.margin_port_td + self.port_height * (i - 1) + self.port_height / 2
                    line_end_y = top + self.margin_port_td + self.port_height * (i - 1) + self.port_height / 2
                    d.append(draw.Line(
                        line_start_x, line_start_y,
                        line_end_x, line_end_y,
                        stroke='blue'
                    ))
                    # 画折线箭头
                    arrow_height = self.port_height / 3
                    arrow_width = self.port_width / 2
                    d.append(draw.Lines(
                        line_end_x - arrow_width, line_end_y - arrow_height,
                        line_end_x              , line_end_y,
                        line_end_x - arrow_width, line_end_y + arrow_height,
                        stroke='blue'
                    ))
                    # 箭头右侧写信号名
                    d.append(draw.Text(
                        signal["port_name"],
                        font_size=self.port_height / 2 * 1,
                        x=line_end_x + 10,
                        y=line_end_y,
                        text_anchor='start',
                        dominant_baseline='middle'
                    ))
                    i += 1
            if "Output" in signals:
                for signal in signals["Output"]:
                    # 画有向箭头
                    line_start_y = top + self.margin_port_td + self.port_height * (i - 1) + self.port_height / 2
                    line_end_y = top + self.margin_port_td + self.port_height * (i - 1) + self.port_height / 2
                    d.append(draw.Line(
                        line_start_x, line_start_y,
                        line_end_x, line_end_y,
                        stroke='black'
                    ))
                    # 画折线箭头
                    arrow_height = self.port_height / 3
                    arrow_width = self.port_width / 2
                    d.append(draw.Lines(
                        line_start_x + arrow_width, line_start_y + arrow_height,
                        line_start_x              , line_start_y,
                        line_start_x + arrow_width, line_start_y - arrow_height,
                        stroke='black'
                    ))
                    # 箭头右侧写信号名
                    d.append(draw.Text(
                        signal["port_name"],
                        font_size=self.port_height / 2 * 1,
                        x=line_end_x + 10,
                        y=line_end_y,
                        text_anchor='start',
                        dominant_baseline='middle'
                    ))
                    i += 1
            top += height + self.margin_module_td

        '''
        添加right module矩形
        '''
        top = self_top + self.self_name_height
        left = self.margin_module_lr * 3 + lr_width + self_width + 50
        width = lr_width
        for k, v in one2one_right_num.items():
            height = self.port_height * v + self.margin_port_td * 2
            d.append(draw.Rectangle(
                left, top, width, height,
                fill='white',
                stroke='black'
            ))
            signals = self.one2one[k]
            # 在矩形中心写模块名字
            d.append(draw.Text(
                k,
                font_size=self.port_height,
                x=left + width / 2,
                y=top + height / 2,
                text_anchor='middle',
                dominant_baseline='middle'
            ))
            i = 1
            line_start_x = left
            line_end_x = self_left + self_width
            if "Input" in signals:
                for signal in signals["Input"]:
                    # 画有向箭头
                    line_start_y = top + self.margin_port_td + self.port_height * (i - 1) + self.port_height / 2
                    line_end_y = top + self.margin_port_td + self.port_height * (i - 1) + self.port_height / 2
                    d.append(draw.Line(
                        line_start_x, line_start_y,
                        line_end_x, line_end_y,
                        stroke='blue'
                    ))
                    # 画折线箭头
                    arrow_height = self.port_height / 3
                    arrow_width = self.port_width / 2
                    d.append(draw.Lines(
                        line_end_x + arrow_width, line_end_y + arrow_height,
                        line_end_x              , line_end_y,
                        line_end_x + arrow_width, line_end_y - arrow_height,
                        stroke='blue'
                    ))
                    # 箭头右侧写信号名
                    d.append(draw.Text(
                        signal["port_name"],
                        font_size=self.port_height / 2 * 1,
                        x=line_end_x - 10,
                        y=line_end_y,
                        text_anchor='end',
                        dominant_baseline='middle'
                    ))
                    i += 1
            if "Output" in signals:
                for signal in signals["Output"]:
                    # 画有向箭头
                    line_start_y = top + self.margin_port_td + self.port_height * (i - 1) + self.port_height / 2
                    line_end_y = top + self.margin_port_td + self.port_height * (i - 1) + self.port_height / 2
                    d.append(draw.Line(
                        line_start_x, line_start_y,
                        line_end_x, line_end_y,
                        stroke='black'
                    ))
                    # 画折线箭头
                    arrow_height = self.port_height / 3
                    arrow_width = self.port_width / 2
                    d.append(draw.Lines(
                        line_start_x - arrow_width, line_start_y - arrow_height,
                        line_start_x              , line_start_y,
                        line_start_x - arrow_width, line_start_y + arrow_height,
                        stroke='black'
                    ))
                    # 箭头右侧写信号名
                    d.append(draw.Text(
                        signal["port_name"],
                        font_size=self.port_height / 2 * 1,
                        x=line_end_x - 10,
                        y=line_end_y,
                        text_anchor='end',
                        dominant_baseline='middle'
                    ))
                    i += 1
            top += height + self.margin_module_td

        '''
        添加one2many线条
        '''
        p0_x_start = self_left + (self_width - self.port_width * (len(self.one2many) - 1)) / 2
        p2_x_start = self.margin_module_lr * 3 + lr_width + self_width + 50
        p2_x_start += (lr_width - self.port_width * (len(self.one2many) - 1)) / 2
        i = 0
        for k, v in self.one2many.items():
            to_modules = []
            for signal_pkg in v:
                to_modules.append(signal_pkg["conn_instance"])

            # 三个线段，四个点定位
            p0_x = p0_x_start + i * self.port_width
            p0_y = self_top
            p1_x = p0_x
            p1_y = p0_y - self.port_height * (i + 1)
            p2_x = p2_x_start + i * self.port_width
            p2_y = p1_y
            p3_x = p2_x
            cur_module_num = 0
            cur_port_num = 0
            to_module_num = 0
            to_port_num = 0
            arrow_points = [] # 箭头端点
            for inst_name, ports_num in one2one_right_num.items():
                if inst_name in to_modules:
                    to_module_num = cur_module_num
                    to_port_num = cur_port_num
                    arrow_points.append(self_top + self.self_name_height + to_module_num * self.margin_module_td + to_module_num * self.margin_port_td * 2 + to_port_num * self.port_height)
                    print("add to module", inst_name, arrow_points)
                cur_module_num += 1
                cur_port_num += ports_num
            print("to_module_num", to_module_num, to_port_num)
            p3_y = self_top + self.self_name_height
            p3_y += to_module_num * self.margin_module_td + to_module_num * self.margin_port_td * 2 + to_port_num * self.port_height
            # 画线
            d.append(draw.Lines(
                p0_x, p0_y,
                p1_x, p1_y,
                p2_x, p2_y,
                p3_x, p3_y,
                stroke='red',
                fill='none'
            ))
            # 画箭头
            arrow_height = self.port_height / 2
            arrow_width = self.port_width / 3
            for point in arrow_points:
                d.append(draw.Lines(
                    p3_x, point,
                    p3_x + arrow_width, point - arrow_height,
                    p3_x - arrow_width, point - arrow_height,
                    stroke='red',
                    fill='red'
                ))


        d.save_svg('example.svg')

    def to_json(self):

        one2one_left_num, one2one_right_num = self.split_one2one_nums_to_minimize_difference()

        return {
            'module_name': self.module_name,
            'instance_name': self.instance_name,
            'one2one': self.one2one,
            'one2many': self.one2many,
            'noconn': self.noconn,
            'one2one_nums': self.one2one_nums,
            'one2many_num': self.one2many_num,
            'noconn_num': self.noconn_num,
            'one2one_left_num': one2one_left_num,
            'one2one_right_num': one2one_right_num,
        }


def custom_serializer(obj):
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def main():
    INFO = "Verilog code parser"
    VERSION = pyverilog.__version__
    USAGE = "Usage: python example_parser.py file ..."

    def showVersion():
        print(INFO)
        print(VERSION)
        print(USAGE)
        sys.exit()

    optparser = OptionParser()
    optparser.add_option("-v", "--version", action="store_true", dest="showversion",
                         default=False, help="Show the version")
    optparser.add_option("-I", "--include", dest="include", action="append",
                         default=[], help="Include path")
    optparser.add_option("-D", dest="define", action="append",
                         default=[], help="Macro Definition")
    optparser.add_option("-d", "--debug", action="store_true", dest="debug",
                         default=False, help="Debug mode")
    optparser.add_option("-t", "--top", dest="topmodule",
                         default="TOP", help="Top module, Default=TOP")
    optparser.add_option("-i", "--instance", dest="instmodule",
                         default="", help="Instance module")
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f):
            raise IOError("file not found: " + f)
        # try:
        #     ast, directives = parse([f],
        #                         preprocess_include=options.include,
        #                         preprocess_define=options.define)
        #     print(f"{f} parse test passed")
        # except Exception as e:
        #     print(f"{f} parse test failed: {e}")


    if len(filelist) == 0:
        showVersion()

    ast, directives = parse(filelist,
                            preprocess_include=options.include,
                            preprocess_define=options.define)
    # json_f = open('./run.json', 'w')
    # json_tree_f = open('./run_tree.json', 'w')
    # ast.show_as_json     (buf=json_f)
    # ast.show_as_json_tree(buf=json_tree_f)

    # if options.debug:
    #     with open('./run_dict.json', 'w') as f:
    #         f.write(json.dumps(ast.dict(), indent=4))
    #     with open('./run_directives.json', 'w') as f:
    #         f.write(json.dumps(directives, indent=4))

    # for lineno, directive in directives:
    #     print('Line %d : %s' % (lineno, directive))
    modules_signals = {}
    top_signals = defaultdict(list) #(instanse_name, module_name, port_name)
    insts = {}

    for module_def in ast.description.definitions:
        module_name = module_def.name
        if module_name not in modules_signals:
            modules_signals[module_name] = {}
            module_items = module_def.items
            for item in module_items:
                # 判断port是否为Ioport类
                if item.__class__.__name__ == 'Decl':
                    item_list = item.list
                    for port in item_list:
                        if port.__class__.__name__ in ['Input', 'Output', 'Inout']:
                            modules_signals[module_name][port.name] = port.dict()
                # modules_signals[module_name][port["name"]] =

        if module_name == options.topmodule:
            if options.debug:
                with open('./run_dict.json', 'w') as f:
                    f.write(json.dumps(module_def.dict(), indent=4))
            module_items = module_def.items
            for item in module_items:
                if item.__class__.__name__ == 'InstanceList':
                    for instance in item.instances:
                        insts[instance.name] = instance
                        for port in instance.portlist:
                            top_signals[port.argname.name].append((instance.name, instance.module, port.portname))

            index = 0
            for top_port_name, top_port in modules_signals[module_name].items():
                top_signals[top_port_name].append((f'TOP({options.topmodule})', module_name, top_port_name))

                    
    if options.debug:
        with open('./run_modules_signals.json', 'w') as f:
            f.write(json.dumps(modules_signals, default=custom_serializer, indent=4))
        with open('./run_top_signals.json', 'w') as f:
            f.write(json.dumps(top_signals, default=custom_serializer, indent=4))
        with open('./run_insts.json', 'w') as f:
            f.write(json.dumps(insts, default=custom_serializer, indent=4))

    if options.instmodule:
        for instance_name, instance in insts.items():
            if instance_name == options.instmodule:
                connections_flatten = {}
                connections = ModuleBlockDrawer(instance.module, instance_name, options.topmodule)
                for port in instance.portlist:
                    port_connect = top_signals[port.argname.name]
                    port_detail = modules_signals[instance.module][port.portname]
                    if len(port_connect) == 2:
                        for (conn_instance, conn_module, conn_port) in port_connect:
                            if conn_instance != instance_name or conn_port != port.portname:
                                connections_flatten[port.portname] = f"{conn_instance}({conn_module}).{conn_port}"
                                connections.add_one2one(port.portname, port_detail["className"], conn_instance, conn_module, conn_port)
                    elif len(port_connect) > 2:
                        if port_detail["className"] == "Output":
                            connections_flatten[port.portname] = []
                            for (conn_instance, conn_module, conn_port) in port_connect:
                                if conn_instance != instance_name or conn_port != port.portname:
                                    connections_flatten[port.portname].append(f"{conn_instance}({conn_module}).{conn_port}")
                                    connections.add_one2many(port.portname, conn_instance, conn_module, conn_port)
                        else:
                            for (conn_instance, conn_module, conn_port) in port_connect:
                                conn_port_detail = modules_signals[conn_module][conn_port]
                                if conn_port_detail["className"] == "Output" and conn_instance != f'TOP({options.topmodule})':
                                    connections_flatten[port.portname] = f"{conn_instance}({conn_module}).{conn_port}"
                                elif conn_port_detail["className"] == "Input" and conn_instance == f'TOP({options.topmodule})':
                                    connections_flatten[port.portname] = f"{conn_instance}({conn_module}).{conn_port}"
                            if port.portname not in connections_flatten:
                                connections_flatten[port.portname] = "no_output_in_group"
                                connections.add_noconn(port.portname)
                            else:
                                connections.add_one2one(port.portname, port_detail["className"], conn_instance, conn_module, conn_port)
                    else:
                        connections_flatten[port.portname] = "no_connect"
                        connections.add_noconn(port.portname)
                if options.debug:
                    with open('./run_connections_flatten.json', 'w') as f:
                        f.write(json.dumps(connections_flatten, default=custom_serializer, indent=4))
                    with open('./run_connections.json', 'w') as f:
                        f.write(json.dumps(connections, default=custom_serializer, indent=4))

                connections.draw()


if __name__ == '__main__':
    main()
