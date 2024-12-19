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
    def __init__(self, module_name, instance_name):
        self.module_name = module_name
        self.instance_name = instance_name
        self.one2one = defaultdict(dict)
        self.one2many = defaultdict(list)
        self.noconn = []
        self.one2one_nums = defaultdict(int)
        self.one2many_num = 0
        self.noconn_num = 0

        self.min_width = 500
        self.min_height = 300
        self.port_width = 50
        self.port_height = 50
        self.port_line_width = 5
        self.port_line_height = 5
        self.margin_port_td = 70
        self.margin_port_lr = 70
        self.margin_module_td = 320
        self.margin_module_lr = 320

    def add_one2one(self, port_name, port_direction, conn_instance, conn_module, conn_port):
        self.one2one[conn_instance][port_direction] = (conn_module, conn_port, port_name)
        self.one2one_nums[f"self_{port_direction}"] += 1
        self.one2one_nums[conn_instance] += 1

    def add_one2many(self, port_name, conn_instance, conn_module, conn_port):
        if port_name not in self.one2many:
            self.one2many_num += 1
        self.one2many[port_name].append((conn_module, conn_instance, conn_port))
    
    def add_noconn(self, port_name):
        self.noconn.append(port_name)
        self.noconn_num += 1
    
    def draw(self):
        # self.min_width       
        # self.min_height      
        # self.port_width      
        # self.port_height     
        # self.port_line_width 
        # self.port_line_height
        # self.margin_port_td  
        # self.margin_port_lr  
        # self.margin_module_td
        # self.margin_module_lr

        self_width = self.margin_port_lr * 2 + self.port_height * max(self.one2many_num, self.noconn_num)
        self_height = self.margin_port_td * 2 + self.port_width * max(self.one2one_nums.values())

        self_width = max(self_width, self.min_width)
        self_height = max(self_height, self.min_height)

        draw_width = self_width * 3 + self.margin_module_lr * 4 + 100
        draw_height = self_height + self.margin_module_td * 2 + self.port_height * self.one2many_num + 100

        d = draw.Drawing(draw_width, draw_height)
        '''
        添加top矩形
        top: 50
        left: 50
        width: draw_width - 100
        height: draw_height - 100
        '''
        d.append(draw.Rectangle(50, 50, draw_width - 100, draw_height - 100, fill='white', stroke='black'))

        '''
        添加self矩形
        top: self.margin_module_td + self.port_height * self.one2many_num + 50
        left: self.margin_module_lr * 2 + self_width * 1 + 50
        width: self_width
        height: self_height
        '''
        d.append(draw.Rectangle(
            self.margin_module_lr * 2 + self_width * 1 + 50, 
            self.margin_module_td + self.port_height * self.one2many_num + 50, 
            self_width, 
            self_height, 
            fill='white', 
            stroke='black'
        ))

        '''
        添加left module矩形
        top: self.margin_module_td + self.port_height * self.one2many_num + 50
        left: self.margin_module_lr * 1 + 50
        width: self_width
        height: self_height
        '''
        d.append(draw.Rectangle(
            self.margin_module_lr * 1 + 50,
            self.margin_module_td + self.port_height * self.one2many_num + 50,
            self_width, self_height,
            fill='white',
            stroke='black'
        ))

        '''
        添加right module矩形
        top: self.margin_module_td + self.port_height * self.one2many_num + 50
        left: self.margin_module_lr * 3 + self_width * 2 + 50
        width: self_width
        height: self_height
        '''
        d.append(draw.Rectangle(
            self.margin_module_lr * 3 + self_width * 2 + 50,
            self.margin_module_td + self.port_height * self.one2many_num + 50,
            self_width, self_height,
            fill='white',
            stroke='black'
        ))

        d.save_svg('example.svg')



    def to_json(self):
        return {
            'module_name': self.module_name,
            'instance_name': self.instance_name,
            'one2one': self.one2one,
            'one2many': self.one2many,
            'noconn': self.noconn,
            'one2one_nums': self.one2one_nums,
            'one2many_num': self.one2many_num,
            'noconn_num': self.noconn_num,
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
                connections = ModuleBlockDrawer(instance.module, instance_name)
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
