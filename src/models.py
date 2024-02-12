import ast
from _console import cons
from _types import *

print = cons.print

def get_full_function_name(node):
    """构造函数的完整名称，例如 'os.system'"""
    if isinstance(node, ast.Attribute):
        return get_full_function_name(node.value) + '.' + node.attr
    elif isinstance(node, ast.Name):
        return node.id
    return ""

class ToAfy(ast.NodeVisitor):
    
    """ Adding father and children attribution to every node so we can reverse travel the AST """
    
    def __init__(self, target_function=None, target_variable=None):
        self.parent = None
        self.last_id = 0
        self.last_node = None
        self.target_function = target_function
        self.target_variable = target_variable
        self.vulnerable_note = None

        
    def generic_visit(self, node):
        # 为节点设置全局唯一ID
        node.node_id = self.last_id
        self.last_id += 1

        # print(f'setting {node.id}')
        
        if self.last_node is not None:
            self.last_node.fwd = node
            node.bck = self.last_node
        else:
            node.bck = None
            
        node.fwd = None
        # 更新last_node为当前节点
        self.last_node = node
        # if node.bck and self.last_node:
        #     print(f'{node.id}: last_node\'s fwd {self.last_node.id}, note\'s bck {node.bck.id}')
        
        # 设置父节点和子节点列表
        if not hasattr(node, 'parent'):
            node.parent = self.parent
        if not hasattr(node, 'children'):
            node.children = []
        
        # 检查是否是目标函数调用
        if isinstance(node, ast.Call):
            full_function_name = get_full_function_name(node.func)
            if full_function_name == self.target_function:
                for arg in node.args:
                    if isinstance(arg, ast.Name) and arg.id == self.target_variable:
                        # 记录漏洞点
                        self.vulnerable_note = node
        
        # 设置父节点并递归访问子节点
        original_parent = self.parent
        self.parent = node
        current_last_node = self.last_node
        for child in ast.iter_child_nodes(node):
            node.children.append(child)
            self.visit(child)
        self.last_node = current_last_node  # 恢复last_node的状态

        
        

class VariableTrace(ast.NodeVisitor):
    
    def __init__(self,root_note,target_variable):
        self.root_note = root_note
        self.target_variable = target_variable
        self.target_tree = []   # Variable change tree
        self.visited = set()    # Make sure no double-visite
        
    def reverse_trace_from_node(self):
        """
        从给定的节点逆向追溯到变量的源头。
        """
        current_node = self.root_note
        while current_node.node_id != 0 and getattr(current_node, 'fwd', None):
            # 处理当前节点的逻辑...
            if isinstance(current_node, ast.Assign):
                for target in current_node.targets:
                    # print(f"[!] target: {self.target_variable}" )
                    if isinstance(target, ast.Name) and target.id == self.target_variable:
                        self.target_tree.append(('Assign', current_node, current_node.node_id))
                        value = current_node.value
                        if isinstance(value, ast.Name):
                            # 直接变量赋值
                            self.target_variable = value.id
                            self.target_tree.append(('UpdateTargetAssign', value.id))
                        elif isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name):
                            # 切片操作或索引访问
                            self.target_variable = value.value.id
                            self.target_tree.append(('UpdateTargetSlice', value.value.id))
                            
                        elif isinstance(value, ast.Call):
                            # 处理函数调用
                            func_name = get_full_function_name(value.func)
                            self.target_variable = value.func.value.id
                            call_info = f"{func_name}({', '.join(ast.dump(arg) for arg in value.args)})"
                            self.target_tree.append(('UpdateTargetCall', call_info))
                            
                # 追踪赋值右侧的表达式
            elif isinstance(current_node, ast.If):
                # 如果是一个决策点
                self.target_tree.append(('If', current_node, current_node.node_id))

            # 移动到父节点
            # current_node = getattr(current_node, 'parent', None)
            # print(f"    [*] Current note_id: {current_node.id}")
            # print(f"    [*] fwd: {current_node.fwd.id}; bck: {current_node.bck.id}")
            current_node = current_node.bck
            
        return self.target_tree
