# 打开json文件并且读取
import json
with open ('ct_ifu_top_tree.json', 'r') as f:
    tree_data = json.load(f)

Ports = tree_data['Description']['ModuleDef']['Portlist']['Ports']
top_ports_str = []

for port in Ports:
    top_ports_str.append(port['attrs']['name'])

print('top_ports_str', top_ports_str)

InstanceLists = tree_data['Description']['ModuleDef']['InstanceLists']
