import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QLabel,
                             QLineEdit, QListWidget, QMessageBox, QSplitter,
                             QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtGui import QWheelEvent
from gen_module_block import parse, ModuleBlockDrawer, custom_serializer
from collections import defaultdict
import json

class ZoomableSvgWidget(QSvgWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_factor = 1.0
        self.setMinimumSize(400, 400)
    
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.scale_factor *= 1.2
            else:
                self.scale_factor *= 0.8
            self.resize(self.sizeHint() * self.scale_factor)
            event.accept()
        else:
            super().wheelEvent(event)
    
    def resetZoom(self):
        self.scale_factor = 1.0
        self.resize(self.sizeHint())

class ModuleBlockGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Verilog Module Block Analyzer')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧SVG查看区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # SVG控制按钮
        svg_controls = QHBoxLayout()
        self.reset_zoom_btn = QPushButton('100%')
        svg_controls.addWidget(self.reset_zoom_btn)
        svg_controls.addStretch()
        left_layout.addLayout(svg_controls)
        
        # SVG显示区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.svg_widget = ZoomableSvgWidget()
        scroll_area.setWidget(self.svg_widget)
        left_layout.addWidget(scroll_area)
        
        # 右侧控制面板
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_label = QLabel('Selected Files:')
        self.file_list = QListWidget()
        file_buttons = QVBoxLayout()
        self.add_file_btn = QPushButton('Add Files')
        self.add_dir_btn = QPushButton('Add Directory')
        self.clear_files_btn = QPushButton('Clear Files')
        self.move_up_btn = QPushButton('Move Up')
        self.move_down_btn = QPushButton('Move Down')
        
        file_buttons.addWidget(self.add_file_btn)
        file_buttons.addWidget(self.add_dir_btn)
        file_buttons.addWidget(self.clear_files_btn)
        file_buttons.addWidget(self.move_up_btn)
        file_buttons.addWidget(self.move_down_btn)
        file_layout.addWidget(self.file_list)
        file_layout.addLayout(file_buttons)
        
        # Top模块设置区域
        top_layout = QHBoxLayout()
        self.top_label = QLabel('Top Module:')
        self.top_input = QLineEdit()
        self.analyze_btn = QPushButton('Analyze')
        top_layout.addWidget(self.top_label)
        top_layout.addWidget(self.top_input)
        top_layout.addWidget(self.analyze_btn)
        
        # 子模块列表区域
        submodule_layout = QVBoxLayout()
        self.submodule_label = QLabel('Submodules:')
        self.submodule_list = QListWidget()
        submodule_layout.addWidget(self.submodule_label)
        submodule_layout.addWidget(self.submodule_list)
        
        # 添加所有布局到右侧布局
        right_layout.addWidget(self.file_label)
        right_layout.addLayout(file_layout)
        right_layout.addLayout(top_layout)
        right_layout.addLayout(submodule_layout)
        
        # 添加左右部件到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        # 连接信号和槽
        self.add_file_btn.clicked.connect(self.add_files)
        self.add_dir_btn.clicked.connect(self.add_directory)
        self.clear_files_btn.clicked.connect(self.clear_files)
        self.analyze_btn.clicked.connect(self.analyze_top_module)
        self.submodule_list.itemDoubleClicked.connect(self.generate_submodule_graph)
        self.move_up_btn.clicked.connect(self.move_file_up)
        self.move_down_btn.clicked.connect(self.move_file_down)
        self.reset_zoom_btn.clicked.connect(self.svg_widget.resetZoom)
        
        # 初始化数据
        self.file_paths = []
        self.modules_signals = {}
        self.top_signals = defaultdict(list)
        self.insts = {}
        self.current_svg_file = None
    
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Verilog Files",
            "",
            "Verilog Files (*.v);;Header Files (*.h);;All Files (*.*)"
        )
        for file in files:
            self.file_paths.append(file)
        self.update_file_list()
    
    def add_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory"
        )
        if directory:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(('.v', '.h')):
                        self.file_paths.append(os.path.join(root, file))
        self.update_file_list()
    
    def clear_files(self):
        self.file_paths.clear()
        self.update_file_list()
    
    def update_file_list(self):
        self.file_list.clear()
        for file in self.file_paths:
            self.file_list.addItem(file)
    
    def move_file_up(self):
        current_row = self.file_list.currentRow()
        if current_row > 0:
            self.file_paths.insert(current_row - 1, self.file_paths.pop(current_row))
            self.update_file_list()
            self.file_list.setCurrentRow(current_row - 1)
    
    def move_file_down(self):
        current_row = self.file_list.currentRow()
        if current_row < len(self.file_paths) - 1:
            self.file_paths.insert(current_row + 1, self.file_paths.pop(current_row))
            self.update_file_list()
            self.file_list.setCurrentRow(current_row + 1)
    
    def analyze_top_module(self):
        if not self.file_paths:
            QMessageBox.warning(self, "Warning", "Please add some files first!")
            return
        
        top_module = self.top_input.text().strip()
        if not top_module:
            QMessageBox.warning(self, "Warning", "Please specify the top module name!")
            return
        
        try:
            # 解析文件
            print("Parsing files...")
            print(list(self.file_paths))
            ast, directives = parse(list(self.file_paths))
            print("Analyzing files...")
            
            # 重置数据
            self.modules_signals.clear()
            self.top_signals.clear()
            self.insts.clear()
            self.submodule_list.clear()
            
            # 分析模块
            for module_def in ast.description.definitions:
                module_name = module_def.name
                if module_name not in self.modules_signals:
                    self.modules_signals[module_name] = {}
                    for item in module_def.items:
                        if item.__class__.__name__ == 'Decl':
                            for port in item.list:
                                if port.__class__.__name__ in ['Input', 'Output', 'Inout']:
                                    self.modules_signals[module_name][port.name] = port.dict()
                
                if module_name == top_module:
                    for item in module_def.items:
                        if item.__class__.__name__ == 'InstanceList':
                            for instance in item.instances:
                                self.insts[instance.name] = instance
                                self.submodule_list.addItem(instance.name)
                                for port in instance.portlist:
                                    self.top_signals[port.argname.name].append(
                                        (instance.name, instance.module, port.portname)
                                    )
            
            QMessageBox.information(self, "Success", "Analysis completed successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Analysis failed: {str(e)}")
    
    def generate_submodule_graph(self, item):
        instance_name = item.text()
        if instance_name not in self.insts:
            return
        
        instance = self.insts[instance_name]
        connections = ModuleBlockDrawer(instance.module, instance_name, self.top_input.text())
        
        for port in instance.portlist:
            port_connect = self.top_signals[port.argname.name]
            port_detail = self.modules_signals[instance.module][port.portname]
            
            if len(port_connect) == 2:
                for (conn_instance, conn_module, conn_port) in port_connect:
                    if conn_instance != instance_name or conn_port != port.portname:
                        connections.add_one2one(port.portname, port_detail["className"],
                                              conn_instance, conn_module, conn_port)
            elif len(port_connect) > 2:
                if port_detail["className"] == "Output":
                    for (conn_instance, conn_module, conn_port) in port_connect:
                        if conn_instance != instance_name or conn_port != port.portname:
                            connections.add_one2many(port.portname, conn_instance,
                                                   conn_module, conn_port)
                else:
                    for (conn_instance, conn_module, conn_port) in port_connect:
                        conn_port_detail = self.modules_signals[conn_module][conn_port]
                        if (conn_port_detail["className"] == "Output" and
                            conn_instance != f'TOP({self.top_input.text()})'):
                            connections.add_one2one(port.portname, port_detail["className"],
                                                  conn_instance, conn_module, conn_port)
                            break
                        elif (conn_port_detail["className"] == "Input" and
                              conn_instance == f'TOP({self.top_input.text()})'):
                            connections.add_one2one(port.portname, port_detail["className"],
                                                  conn_instance, conn_module, conn_port)
                            break
                    else:
                        connections.add_noconn(port.portname)
            else:
                connections.add_noconn(port.portname)
        
        try:
            connections.draw()
            self.current_svg_file = f'{instance_name}.svg'
            self.svg_widget.load(self.current_svg_file)
            QMessageBox.information(self, "Success", f"Generated graph for {instance_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate graph: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = ModuleBlockGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()