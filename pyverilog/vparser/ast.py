"""
   Copyright 2013, Shinya Takamaeda-Yamazaki and Contributors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from __future__ import absolute_import
from __future__ import print_function
import sys
import re
import json


class Node(object):
    """ Abstact class for every element in parser """

    def children(self):
        pass

    def dict(self):
        pass

    def show(self, buf=sys.stdout, offset=0, attrnames=False, showlineno=True):
        indent = 2
        lead = ' ' * offset

        buf.write(lead + self.__class__.__name__ + ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self, n)) for n in self.attr_names]
                attrstr = ', '.join('%s=%s' % (n, v) for (n, v) in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showlineno:
            if hasattr(self, 'end_lineno'):
                buf.write(' (from %s to %s)' % (self.lineno, self.end_lineno))
            else:
                buf.write(' (at %s)' % self.lineno)

        buf.write('\n')

        for c in self.children():
            c.show(buf, offset + indent, attrnames, showlineno)


    def show_as_json(self, buf=sys.stdout, offset=0, attrnames=True, showlineno=True, is_child_get_json=False):
        indent = '  '  # 使用两个空格作为缩进
        lead = ' ' * offset

        # 准备节点的基本信息
        node_info = {
            'type': self.__class__.__name__,
        }

        # 添加属性信息
        if self.attr_names:
            attrs = {}
            if attrnames:
                nvlist = [(n, getattr(self, n)) for n in self.attr_names]
                attrs = {n: v for n, v in nvlist}
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrs = {'attr' + str(i): v for i, v in enumerate(vlist)}
            node_info['attrs'] = attrs

        # 添加行号信息
        if showlineno:
            if hasattr(self, 'end_lineno'):
                node_info['lineno'] = ' (from %s to %s)' % (self.lineno, self.end_lineno)
            if hasattr(self, 'end_lineno'):
                node_info['end_lineno'] = ' (at %s)' % self.lineno

        # 添加子节点信息
        node_info['children'] = []
        for c in self.children():
            child_json = c.show_as_json(offset + len(indent), attrnames, is_child_get_json=True)
            node_info['children'].append(child_json)

        if is_child_get_json:
            return node_info
        
        # 转换为JSON字符串并输出
        try:
            json_str = json.dumps(node_info, indent=2)
            # buf.write(json_str)
            buf.write(json_str)
        except:
            buf.write(json_str, node_info)


    def show_as_json_tree(self, buf=sys.stdout, offset=0, attrnames=True, showlineno=True, is_child_get_json=False):
        indent = '  '  # 使用两个空格作为缩进
        lead = ' ' * offset

        # 准备节点的基本信息
        node_info = {
            'type': self.__class__.__name__,
        }

        # 添加属性信息
        if self.attr_names:
            attrs = {}
            if attrnames:
                # 获取属性名和属性值，并存入字典
                nvlist = [(n, getattr(self, n)) for n in self.attr_names]
                attrs = {n: v for n, v in nvlist}
            else:
                # 获取属性值，并存储为字典
                vlist = [getattr(self, n) for n in self.attr_names]
                attrs = {'attr' + str(i): v for i, v in enumerate(vlist)}
            node_info['attrs'] = attrs

        # 添加行号信息
        if showlineno:
            if hasattr(self, 'end_lineno'):
                # 如果存在结束行号，添加行号信息
                node_info['lineno'] = ' (from %s to %s)' % (self.lineno, self.end_lineno)
            if hasattr(self, 'end_lineno'):
                # 如果存在结束行号，添加行号信息
                node_info['end_lineno'] = ' (at %s)' % self.lineno

        # 添加子节点信息
        for c in self.children():
            child_json = c.show_as_json_tree(offset + len(indent), attrnames, is_child_get_json=True)
            if child_json["type"] in node_info:
                # 如果子节点类型已存在于节点信息中，则创建复数形式存储子节点
                if child_json["type"]+"s" in node_info:
                    print("Duplicated child type:", child_json["type"], node_info[child_json["type"]], node_info[child_json["type"]+"s"])
                    assert False
                node_info[child_json["type"]+"s"] = [node_info[child_json["type"]], child_json]
                del node_info[child_json["type"]]
            elif child_json["type"]+"s" in node_info:
                # 如果子节点类型的复数形式已存在于节点信息中，则添加子节点
                node_info[child_json["type"]+"s"].append(child_json)
            else:
                # 如果子节点类型及其复数形式均不存在于节点信息中，则添加子节点
                node_info[child_json["type"]] = child_json
            del child_json["type"]

        if is_child_get_json:
            return node_info
    
        # 转换为JSON字符串并输出
        try:
            json_str = json.dumps(node_info, indent=2)
            # 将JSON字符串写入缓冲区
            # buf.write(json_str)
            buf.write(json_str)
        except:
            # 如果发生异常，尝试写入JSON字符串和节点信息
            buf.write(json_str, node_info)

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        self_attrs = tuple([getattr(self, a) for a in self.attr_names])
        other_attrs = tuple([getattr(other, a) for a in other.attr_names])

        if self_attrs != other_attrs:
            return False

        other_children = other.children()

        for i, c in enumerate(self.children()):
            if c != other_children[i]:
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        s = hash(tuple([getattr(self, a) for a in self.attr_names]))
        c = hash(self.children())
        return hash((s, c))

    def to_json(self):
        return self.__class__.__name__

# ------------------------------------------------------------------------------
class Source(Node):
    attr_names = ('name',)

    def __init__(self, name, description, lineno=0):
        self.lineno = lineno
        self.name = name
        self.description = description

    def children(self):
        nodelist = []
        if self.description:
            nodelist.append(self.description)
        return tuple(nodelist)
    
    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "name": self.name,
            "description": self.description.dict() if hasattr(self.description, 'dict') else self.description,
        }


class Description(Node):
    attr_names = ()

    def __init__(self, definitions, lineno=0):
        self.lineno = lineno
        self.definitions = definitions

    def children(self):
        nodelist = []
        if self.definitions:
            nodelist.extend(self.definitions)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "definitions": [def_.dict() for def_ in self.definitions] if self.definitions else None,
        }


class ModuleDef(Node):
    attr_names = ('name',)

    def __init__(self, name, paramlist, portlist, items, default_nettype='wire', lineno=0):
        self.lineno = lineno
        self.name = name
        self.paramlist = paramlist
        self.portlist = portlist
        self.items = items
        self.default_nettype = default_nettype

    def children(self):
        nodelist = []
        if self.paramlist:
            nodelist.append(self.paramlist)
        if self.portlist:
            nodelist.append(self.portlist)
        if self.items:
            nodelist.extend(self.items)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "name": self.name,
            "paramlist": self.paramlist.dict() if hasattr(self.paramlist, 'dict') else self.paramlist,
            "portlist": self.portlist.dict() if hasattr(self.portlist, 'dict') else self.portlist,
            "items": [item.dict() for item in self.items] if self.items else None,
            "default_nettype": self.default_nettype,
        }

class Paramlist(Node):
    attr_names = ()

    def __init__(self, params, lineno=0):
        self.lineno = lineno
        self.params = params

    def children(self):
        nodelist = []
        if self.params:
            nodelist.extend(self.params)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "params": [param.dict() for param in self.params] if self.params else None,
        }


class Portlist(Node):
    attr_names = ()

    def __init__(self, ports, lineno=0):
        self.lineno = lineno
        self.ports = ports

    def children(self):
        nodelist = []
        if self.ports:
            nodelist.extend(self.ports)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "ports": [port.dict() for port in self.ports] if self.ports else None,
        }


class Port(Node):
    attr_names = ('name', 'type',)

    def __init__(self, name, width, dimensions, type, lineno=0):
        self.lineno = lineno
        self.name = name
        self.width = width
        self.dimensions = dimensions
        self.type = type

    def children(self):
        nodelist = []
        if self.width:
            nodelist.append(self.width)
        return tuple(nodelist)

    def dict(self):
        d = {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "name": self.name,
            "dimensions": self.dimensions.dict() if hasattr(self.dimensions, 'dict') else self.dimensions,
            "type": self.type,
        }
        if self.width:
            d["width"] = self.width.dict() if hasattr(self.width, 'dict') else self.width
        return {**d}

class Width(Node):
    attr_names = ()

    def __init__(self, msb, lsb, lineno=0):
        self.lineno = lineno
        self.msb = msb
        self.lsb = lsb

    def children(self):
        nodelist = []
        if self.msb:
            nodelist.append(self.msb)
        if self.lsb:
            nodelist.append(self.lsb)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "msb": self.msb.dict() if hasattr(self.msb, 'dict') else self.msb,
            "lsb": self.lsb.dict() if hasattr(self.lsb, 'dict') else self.lsb,
        }


class Length(Width):
    pass


class Dimensions(Node):
    attr_names = ()

    def __init__(self, lengths, lineno=0):
        self.lineno = lineno
        self.lengths = lengths

    def children(self):
        nodelist = []
        if self.lengths:
            nodelist.extend(self.lengths)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "lengths": [length.dict() for length in self.lengths] if self.lengths else None,
        }


class Identifier(Node):
    attr_names = ('name',)

    def __init__(self, name, scope=None, lineno=0):
        self.lineno = lineno
        self.name = name
        self.scope = scope

    def children(self):
        nodelist = []
        if self.scope:
            nodelist.append(self.scope)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "name": self.name,
            "scope": self.scope.dict() if hasattr(self.scope, 'dict') else self.scope,
        }

    def __repr__(self):
        if self.scope is None:
            return self.name
        return self.scope.__repr__() + '.' + self.name


class Value(Node):
    attr_names = ()

    def __init__(self, value, lineno=0):
        self.lineno = lineno
        self.value = value

    def children(self):
        nodelist = []
        if self.value:
            nodelist.append(self.value)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "value": self.value if self.value else None,
        }
        

class Constant(Value):
    attr_names = ('value',)

    def __init__(self, value, lineno=0):
        self.lineno = lineno
        self.value = value

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "value": self.value,
        }

    def __repr__(self):
        return str(self.value)


class IntConst(Constant):
    pass


class FloatConst(Constant):
    pass


class StringConst(Constant):
    pass


class Variable(Value):
    attr_names = ('name', 'signed')

    def __init__(self, name, width=None, signed=False, dimensions=None, value=None, lineno=0):
        self.lineno = lineno
        self.name = name
        self.width = width
        self.signed = signed
        self.dimensions = dimensions
        self.value = value

    def children(self):
        nodelist = []
        if self.width:
            nodelist.append(self.width)
        if self.dimensions:
            nodelist.append(self.dimensions)
        if self.value:
            nodelist.append(self.value)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "name": self.name,
            "width": self.width.dict() if hasattr(self.width, 'dict') else self.width,
            "signed": self.signed,
            "dimensions": self.dimensions.dict() if hasattr(self.dimensions, 'dict') else self.dimensions,
            "value": self.value.dict() if hasattr(self.value, 'dict') else self.value,
        }


class Input(Variable):
    pass


class Output(Variable):
    pass


class Inout(Variable):
    pass


class Tri(Variable):
    pass


class Wire(Variable):
    pass


class Reg(Variable):
    pass


class Integer(Variable):
    pass


class Real(Variable):
    pass


class Genvar(Variable):
    pass


class Ioport(Node):
    attr_names = ()

    def __init__(self, first, second=None, lineno=0):
        self.lineno = lineno
        self.first = first
        self.second = second

    def children(self):
        nodelist = []
        if self.first:
            nodelist.append(self.first)
        if self.second:
            nodelist.append(self.second)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "first": self.first.dict() if hasattr(self.first, 'dict') else self.first,
            "second": self.second.dict() if hasattr(self.second, 'dict') else self.second,
        }


class Parameter(Node):
    attr_names = ('name', 'signed')

    def __init__(self, name, value, width=None, signed=False, lineno=0):
        self.lineno = lineno
        self.name = name
        self.value = value
        self.width = width
        self.signed = signed
        self.dimensions = None

    def children(self):
        nodelist = []
        if self.value:
            nodelist.append(self.value)
        if self.width:
            nodelist.append(self.width)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "name": self.name,
            "value": self.value.dict() if hasattr(self.value, 'dict') else self.value,
            "width": self.width.dict() if hasattr(self.width, 'dict') else self.width,
            "signed": self.signed,
        }


class Localparam(Parameter):
    pass


class Supply(Parameter):
    pass


class Decl(Node):
    attr_names = ()

    def __init__(self, list, lineno=0):
        self.lineno = lineno
        self.list = list

    def children(self):
        nodelist = []
        if self.list:
            nodelist.extend(self.list)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "list": [x.dict() for x in self.list],
        }


class Concat(Node):
    attr_names = ()

    def __init__(self, list, lineno=0):
        self.lineno = lineno
        self.list = list

    def children(self):
        nodelist = []
        if self.list:
            nodelist.extend(self.list)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "list": [x.dict() for x in self.list],
        }


class LConcat(Concat):
    pass


class Repeat(Node):
    attr_names = ()

    def __init__(self, value, times, lineno=0):
        self.lineno = lineno
        self.value = value
        self.times = times

    def children(self):
        nodelist = []
        if self.value:
            nodelist.append(self.value)
        if self.times:
            nodelist.append(self.times)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "value": self.value.dict() if hasattr(self.value, 'dict') else self.value,
            "times": self.times.dict() if hasattr(self.times, 'dict') else self.times,
        }


class Partselect(Node):
    attr_names = ()

    def __init__(self, var, msb, lsb, lineno=0):
        self.lineno = lineno
        self.var = var
        self.msb = msb
        self.lsb = lsb

    def children(self):
        nodelist = []
        if self.var:
            nodelist.append(self.var)
        if self.msb:
            nodelist.append(self.msb)
        if self.lsb:
            nodelist.append(self.lsb)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "var": self.var.dict() if hasattr(self.var, 'dict') else self.var,
            "msb": self.msb.dict() if hasattr(self.msb, 'dict') else self.msb,
            "lsb": self.lsb.dict() if hasattr(self.lsb, 'dict') else self.lsb,
        }


class Pointer(Node):
    attr_names = ()

    def __init__(self, var, ptr, lineno=0):
        self.lineno = lineno
        self.var = var
        self.ptr = ptr

    def children(self):
        nodelist = []
        if self.var:
            nodelist.append(self.var)
        if self.ptr:
            nodelist.append(self.ptr)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "var": self.var.dict() if hasattr(self.var, 'dict') else self.var,
            "ptr": self.ptr.dict() if hasattr(self.ptr, 'dict') else self.ptr,
        }


class Lvalue(Node):
    attr_names = ()

    def __init__(self, var, lineno=0):
        self.lineno = lineno
        self.var = var

    def children(self):
        nodelist = []
        if self.var:
            nodelist.append(self.var)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "var": self.var.dict() if hasattr(self.var, 'dict') else self.var,
        }


class Rvalue(Node):
    attr_names = ()

    def __init__(self, var, lineno=0):
        self.lineno = lineno
        self.var = var

    def children(self):
        nodelist = []
        if self.var:
            nodelist.append(self.var)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "var": self.var.dict() if hasattr(self.var, 'dict') else self.var,
        }

# ------------------------------------------------------------------------------
class Operator(Node):
    attr_names = ()

    def __init__(self, left, right, lineno=0):
        self.lineno = lineno
        self.left = left
        self.right = right

    def children(self):
        nodelist = []
        if self.left:
            nodelist.append(self.left)
        if self.right:
            nodelist.append(self.right)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "left": self.left.dict() if hasattr(self.left, 'dict') else self.left,
            "right": self.right.dict() if hasattr(self.right, 'dict') else self.right,
        }


    def __repr__(self):
        ret = '(' + self.__class__.__name__
        for c in self.children():
            ret += ' ' + c.__repr__()
        ret += ')'
        return ret


class UnaryOperator(Operator):
    attr_names = ()

    def __init__(self, right, lineno=0):
        self.lineno = lineno
        self.right = right

    def children(self):
        nodelist = []
        if self.right:
            nodelist.append(self.right)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "right": self.right.dict() if hasattr(self.right, 'dict') else self.right,
        }


# Level 1 (Highest Priority)
class Uplus(UnaryOperator):
    pass


class Uminus(UnaryOperator):
    pass


class Ulnot(UnaryOperator):
    pass


class Unot(UnaryOperator):
    pass


class Uand(UnaryOperator):
    pass


class Unand(UnaryOperator):
    pass


class Uor(UnaryOperator):
    pass


class Unor(UnaryOperator):
    pass


class Uxor(UnaryOperator):
    pass


class Uxnor(UnaryOperator):
    pass


# Level 2
class Power(Operator):
    pass


class Times(Operator):
    pass


class Divide(Operator):
    pass


class Mod(Operator):
    pass


# Level 3
class Plus(Operator):
    pass


class Minus(Operator):
    pass


# Level 4
class Sll(Operator):
    pass


class Srl(Operator):
    pass


class Sla(Operator):
    pass


class Sra(Operator):
    pass


# Level 5
class LessThan(Operator):
    pass


class GreaterThan(Operator):
    pass


class LessEq(Operator):
    pass


class GreaterEq(Operator):
    pass


# Level 6
class Eq(Operator):
    pass


class NotEq(Operator):
    pass


class Eql(Operator):
    pass  # ===


class NotEql(Operator):
    pass  # !==


# Level 7
class And(Operator):
    pass


class Xor(Operator):
    pass


class Xnor(Operator):
    pass


# Level 8
class Or(Operator):
    pass


# Level 9
class Land(Operator):
    pass


# Level 10
class Lor(Operator):
    pass


# Level 11
class Cond(Operator):
    attr_names = ()

    def __init__(self, cond, true_value, false_value, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.true_value = true_value
        self.false_value = false_value

    def children(self):
        nodelist = []
        if self.cond:
            nodelist.append(self.cond)
        if self.true_value:
            nodelist.append(self.true_value)
        if self.false_value:
            nodelist.append(self.false_value)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "cond": self.cond.dict() if hasattr(self.cond, 'dict') else self.cond,
            "true_value": self.true_value.dict() if hasattr(self.true_value, 'dict') else self.true_value,
            "false_value": self.false_value.dict() if hasattr(self.false_value, 'dict') else self.false_value
        }


class Assign(Node):
    attr_names = ()

    def __init__(self, left, right, ldelay=None, rdelay=None, lineno=0):
        self.lineno = lineno
        self.left = left
        self.right = right
        self.ldelay = ldelay
        self.rdelay = rdelay

    def children(self):
        nodelist = []
        if self.left:
            nodelist.append(self.left)
        if self.right:
            nodelist.append(self.right)
        if self.ldelay:
            nodelist.append(self.ldelay)
        if self.rdelay:
            nodelist.append(self.rdelay)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "left": self.left.dict() if hasattr(self.left, 'dict') else self.left,
            "right": self.right.dict() if hasattr(self.right, 'dict') else self.right,
            "ldelay": self.ldelay.dict() if hasattr(self.ldelay, 'dict') else self.ldelay,
            "rdelay": self.rdelay.dict() if hasattr(self.rdelay, 'dict') else self.rdelay
        }


class Always(Node):
    attr_names = ()

    def __init__(self, sens_list, statement, lineno=0):
        self.lineno = lineno
        self.sens_list = sens_list
        self.statement = statement

    def children(self):
        nodelist = []
        if self.sens_list:
            nodelist.append(self.sens_list)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "sens_list": self.sens_list.dict() if hasattr(self.sens_list, 'dict') else self.sens_list,
            "statement": self.statement.dict() if hasattr(self.statement, 'dict') else self.statement,
        }


class AlwaysFF(Always):
    pass


class AlwaysComb(Always):
    pass


class AlwaysLatch(Always):
    pass


class SensList(Node):
    attr_names = ()

    def __init__(self, list, lineno=0):
        self.lineno = lineno
        self.list = list

    def children(self):
        nodelist = []
        if self.list:
            nodelist.extend(self.list)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "list": [l.dict() for l in self.list]
        }


class Sens(Node):
    attr_names = ('type',)

    def __init__(self, sig, type='posedge', lineno=0):
        self.lineno = lineno
        self.sig = sig
        self.type = type  # 'posedge', 'negedge', 'level', 'all' (*)

    def children(self):
        nodelist = []
        if self.sig:
            nodelist.append(self.sig)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "sig": self.sig.dict() if hasattr(self.sig, 'dict') else self.sig,
            "type": self.type
        }


class Substitution(Node):
    attr_names = ()

    def __init__(self, left, right, ldelay=None, rdelay=None, lineno=0):
        self.lineno = lineno
        self.left = left
        self.right = right
        self.ldelay = ldelay
        self.rdelay = rdelay

    def children(self):
        nodelist = []
        if self.left:
            nodelist.append(self.left)
        if self.right:
            nodelist.append(self.right)
        if self.ldelay:
            nodelist.append(self.ldelay)
        if self.rdelay:
            nodelist.append(self.rdelay)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "left": self.left.dict() if hasattr(self.left, 'dict') else self.left,
            "right": self.right.dict() if hasattr(self.right, 'dict') else self.right,
            "ldelay": self.ldelay.dict() if hasattr(self.ldelay, 'dict') else self.ldelay,
            "rdelay": self.rdelay.dict() if hasattr(self.rdelay, 'dict') else self.rdelay
        }


class BlockingSubstitution(Substitution):
    pass


class NonblockingSubstitution(Substitution):
    pass


class IfStatement(Node):
    attr_names = ()

    def __init__(self, cond, true_statement, false_statement, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.true_statement = true_statement
        self.false_statement = false_statement

    def children(self):
        nodelist = []
        if self.cond:
            nodelist.append(self.cond)
        if self.true_statement:
            nodelist.append(self.true_statement)
        if self.false_statement:
            nodelist.append(self.false_statement)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "cond": self.cond.dict() if hasattr(self.cond, 'dict') else self.cond,
            "true_statement": self.true_statement.dict() if hasattr(self.true_statement, 'dict') else self.true_statement,
            "false_statement": self.false_statement.dict() if hasattr(self.false_statement, 'dict') else self.false_statement
        }


class ForStatement(Node):
    attr_names = ()

    def __init__(self, pre, cond, post, statement, lineno=0):
        self.lineno = lineno
        self.pre = pre
        self.cond = cond
        self.post = post
        self.statement = statement

    def children(self):
        nodelist = []
        if self.pre:
            nodelist.append(self.pre)
        if self.cond:
            nodelist.append(self.cond)
        if self.post:
            nodelist.append(self.post)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "pre": self.pre.dict() if hasattr(self.pre, 'dict') else self.pre,
            "cond": self.cond.dict() if hasattr(self.cond, 'dict') else self.cond,
            "post": self.post.dict() if hasattr(self.post, 'dict') else self.post,
            "statement": self.statement.dict() if hasattr(self.statement, 'dict') else self.statement
        }


class WhileStatement(Node):
    attr_names = ()

    def __init__(self, cond, statement, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.statement = statement

    def children(self):
        nodelist = []
        if self.cond:
            nodelist.append(self.cond)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "cond": self.cond.dict() if hasattr(self.cond, 'dict') else self.cond,
            "statement": self.statement.dict() if hasattr(self.statement, 'dict') else self.statement
        }


class CaseStatement(Node):
    attr_names = ()

    def __init__(self, comp, caselist, lineno=0):
        self.lineno = lineno
        self.comp = comp
        self.caselist = caselist

    def children(self):
        nodelist = []
        if self.comp:
            nodelist.append(self.comp)
        if self.caselist:
            nodelist.extend(self.caselist)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "comp": self.comp.dict() if hasattr(self.comp, 'dict') else self.comp,
            "caselist": [c.dict() for c in self.caselist]
        }


class CasexStatement(CaseStatement):
    pass


class CasezStatement(CaseStatement):
    pass


class UniqueCaseStatement(CaseStatement):
    pass


class Case(Node):
    attr_names = ()

    def __init__(self, cond, statement, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.statement = statement

    def children(self):
        nodelist = []
        if self.cond:
            nodelist.extend(self.cond)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "cond": [c.dict() for c in self.cond] if self.cond else [],
            "statement": self.statement.dict() if hasattr(self.statement, 'dict') else self.statement
        }


class Block(Node):
    attr_names = ('scope',)

    def __init__(self, statements, scope=None, lineno=0):
        self.lineno = lineno
        self.statements = statements
        self.scope = scope

    def children(self):
        nodelist = []
        if self.statements:
            nodelist.extend(self.statements)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "statements": [s.dict() for s in self.statements]
        }


class Initial(Node):
    attr_names = ()

    def __init__(self, statement, lineno=0):
        self.lineno = lineno
        self.statement = statement

    def children(self):
        nodelist = []
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "statement": self.statement.dict() if hasattr(self.statement, 'dict') else self.statement
        }


class EventStatement(Node):
    attr_names = ()

    def __init__(self, senslist, lineno=0):
        self.lineno = lineno
        self.senslist = senslist

    def children(self):
        nodelist = []
        if self.senslist:
            nodelist.append(self.senslist)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "senslist": self.senslist.dict() if hasattr(self.senslist, 'dict') else self.senslist
        }


class WaitStatement(Node):
    attr_names = ()

    def __init__(self, cond, statement, lineno=0):
        self.lineno = lineno
        self.cond = cond
        self.statement = statement

    def children(self):
        nodelist = []
        if self.cond:
            nodelist.append(self.cond)
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "cond": self.cond.dict() if hasattr(self.cond, 'dict') else self.cond,
            "statement": self.statement.dict() if hasattr(self.statement, 'dict') else self.statement
        }


class ForeverStatement(Node):
    attr_names = ()

    def __init__(self, statement, lineno=0):
        self.lineno = lineno
        self.statement = statement

    def children(self):
        nodelist = []
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "statement": self.statement.dict() if hasattr(self.statement, 'dict') else self.statement
        }


class DelayStatement(Node):
    attr_names = ()

    def __init__(self, delay, lineno=0):
        self.lineno = lineno
        self.delay = delay

    def children(self):
        nodelist = []
        if self.delay:
            nodelist.append(self.delay)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "delay": self.delay.dict() if hasattr(self.delay, 'dict') else self.delay
        }


class InstanceList(Node):
    attr_names = ('module',)

    def __init__(self, module, parameterlist, instances, lineno=0):
        self.lineno = lineno
        self.module = module
        self.parameterlist = parameterlist
        self.instances = instances

    def children(self):
        nodelist = []
        if self.parameterlist:
            nodelist.extend(self.parameterlist)
        if self.instances:
            nodelist.extend(self.instances)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "module": self.module.dict() if hasattr(self.module, 'dict') else self.module,
            "parameterlist": [p.dict() for p in self.parameterlist],
            "instances": [i.dict() for i in self.instances]
        }


class Instance(Node):
    attr_names = ('name', 'module')

    def __init__(self, module, name, portlist, parameterlist, array=None, lineno=0):
        self.lineno = lineno
        self.module = module
        self.name = name
        self.portlist = portlist
        self.parameterlist = parameterlist
        self.array = array

    def children(self):
        nodelist = []
        if self.array:
            nodelist.append(self.array)
        if self.parameterlist:
            nodelist.extend(self.parameterlist)
        if self.portlist:
            nodelist.extend(self.portlist)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "module": self.module.dict() if hasattr(self.module, 'dict') else self.module,
            "name": self.name.dict() if hasattr(self.name, 'dict') else self.name,
            "parameterlist": [p.dict() for p in self.parameterlist],
            "portlist": [p.dict() for p in self.portlist],
            "array": self.array.dict() if hasattr(self.array, 'dict') else self.array
        }

    def to_json(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "module": self.module.dict() if hasattr(self.module, 'dict') else self.module,
            "name": self.name.dict() if hasattr(self.name, 'dict') else self.name
        }


class ParamArg(Node):
    attr_names = ('paramname',)

    def __init__(self, paramname, argname, lineno=0):
        self.lineno = lineno
        self.paramname = paramname
        self.argname = argname

    def children(self):
        nodelist = []
        if self.argname:
            nodelist.append(self.argname)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "paramname": self.paramname.dict() if hasattr(self.paramname, 'dict') else self.paramname,
            "argname": self.argname.dict() if hasattr(self.argname, 'dict') else self.argname
        }


class PortArg(Node):
    attr_names = ('portname',)

    def __init__(self, portname, argname, lineno=0):
        self.lineno = lineno
        self.portname = portname
        self.argname = argname

    def children(self):
        nodelist = []
        if self.argname:
            nodelist.append(self.argname)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "portname": self.portname.dict() if hasattr(self.portname, 'dict') else self.portname,
            "argname": self.argname.dict() if hasattr(self.argname, 'dict') else self.argname
        }


class Function(Node):
    attr_names = ('name',)

    def __init__(self, name, retwidth, statement, lineno=0):
        self.lineno = lineno
        self.name = name
        self.retwidth = retwidth
        self.statement = statement

    def children(self):
        nodelist = []
        if self.retwidth:
            nodelist.append(self.retwidth)
        if self.statement:
            nodelist.extend(self.statement)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "name": self.name.dict() if hasattr(self.name, 'dict') else self.name,
            "retwidth": self.retwidth.dict() if hasattr(self.retwidth, 'dict') else self.retwidth,
            "statement": [s.dict() for s in self.statement]
        }

    def __repr__(self):
        return self.name.__repr__()


class FunctionCall(Node):
    attr_names = ()

    def __init__(self, name, args, lineno=0):
        self.lineno = lineno
        self.name = name
        self.args = args

    def children(self):
        nodelist = []
        if self.name:
            nodelist.append(self.name)
        if self.args:
            nodelist.extend(self.args)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "name": self.name.dict() if hasattr(self.name, 'dict') else self.name,
            "args": [a.dict() for a in self.args]
        }


    def __repr__(self):
        return self.name.__repr__()


class Task(Node):
    attr_names = ('name',)

    def __init__(self, name, statement, lineno=0):
        self.lineno = lineno
        self.name = name
        self.statement = statement

    def children(self):
        nodelist = []
        if self.statement:
            nodelist.extend(self.statement)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "name": self.name.dict() if hasattr(self.name, 'dict') else self.name,
            "statement": [s.dict() for s in self.statement]
        }


class TaskCall(Node):
    attr_names = ()

    def __init__(self, name, args, lineno=0):
        self.lineno = lineno
        self.name = name
        self.args = args

    def children(self):
        nodelist = []
        if self.name:
            nodelist.append(self.name)
        if self.args:
            nodelist.extend(self.args)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "name": self.name.dict() if hasattr(self.name, 'dict') else self.name,
            "args": [a.dict() for a in self.args]
        }


class GenerateStatement(Node):
    attr_names = ()

    def __init__(self, items, lineno=0):
        self.lineno = lineno
        self.items = items

    def children(self):
        nodelist = []
        if self.items:
            nodelist.extend(self.items)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "items": [i.dict() for i in self.items]
        }


class SystemCall(Node):
    attr_names = ('syscall',)

    def __init__(self, syscall, args, lineno=0):
        self.lineno = lineno
        self.syscall = syscall
        self.args = args

    def children(self):
        nodelist = []
        if self.args:
            nodelist.extend(self.args)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "syscall": self.syscall,
            "args": [a.dict() for a in self.args]
        }

    def __repr__(self):
        ret = []
        ret.append('(')
        ret.append('$')
        ret.append(self.syscall)
        for a in self.args:
            ret.append(' ')
            ret.append(str(a))
        ret.append(')')
        return ''.join(ret)


class IdentifierScopeLabel(Node):
    attr_names = ('name', 'loop')

    def __init__(self, name, loop=None, lineno=0):
        self.lineno = lineno
        self.name = name
        self.loop = loop

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "name": self.name.dict() if hasattr(self.name, 'dict') else self.name,
            "loop": self.loop is not None
        }


class IdentifierScope(Node):
    attr_names = ()

    def __init__(self, labellist, lineno=0):
        self.lineno = lineno
        self.labellist = labellist

    def children(self):
        nodelist = []
        if self.labellist:
            nodelist.extend(self.labellist)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "labellist": [l.dict() for l in self.labellist]
        }


class Pragma(Node):
    attr_names = ()

    def __init__(self, entry, lineno=0):
        self.lineno = lineno
        self.entry = entry

    def children(self):
        nodelist = []
        if self.entry:
            nodelist.append(self.entry)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "entry": self.entry.dict() if hasattr(self.entry, 'dict') else self.entry
        }


class PragmaEntry(Node):
    attr_names = ('name', )

    def __init__(self, name, value=None, lineno=0):
        self.lineno = lineno
        self.name = name
        self.value = value

    def children(self):
        nodelist = []
        if self.value:
            nodelist.append(self.value)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "name": self.name.dict() if hasattr(self.name, 'dict') else self.name,
            "value": self.value.dict() if hasattr(self.value, 'dict') else self.value
        }


class Disable(Node):
    attr_names = ('dest',)

    def __init__(self, dest, lineno=0):
        self.lineno = lineno
        self.dest = dest

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "dest": self.dest.dict() if hasattr(self.dest, 'dict') else self.dest
        }


class ParallelBlock(Node):
    attr_names = ('scope',)

    def __init__(self, statements, scope=None, lineno=0):
        self.lineno = lineno
        self.statements = statements
        self.scope = scope

    def children(self):
        nodelist = []
        if self.statements:
            nodelist.extend(self.statements)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "statements": [s.dict() for s in self.statements],
            "scope": self.scope.dict() if hasattr(self.scope, 'dict') else self.scope
        }


class SingleStatement(Node):
    attr_names = ()

    def __init__(self, statement, lineno=0):
        self.lineno = lineno
        self.statement = statement

    def children(self):
        nodelist = []
        if self.statement:
            nodelist.append(self.statement)
        return tuple(nodelist)

    def dict(self):
        return {
            "lineno": f"{self.lineno}",
            "className": self.__class__.__name__,
            "statement": self.statement.dict() if hasattr(self.statement, 'dict') else self.statement
        }


class EmbeddedCode(Node):
    attr_names = ('code',)

    def __init__(self, code, lineno=0):
        self.code = code

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def dict(self):
        return {"lineno": f"{self.lineno}", "className": self.__class__.__name__, "code": self.code}
