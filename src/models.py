import ast

class TracebackAnalyzer(ast.NodeVisitor):
    def __init__(self, target_var):
        self.target_var = target_var
        self.traceback_chain = []
        self.assignments = {}
        self.var_mapping = {target_var: [target_var]}

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                value_desc = self.describe_expression(node.value)
                # 更新变量映射
                affected_vars = [var for var in self.var_mapping if var in value_desc]
                if affected_vars:
                    for var in affected_vars:
                        self.var_mapping.setdefault(target.id, []).append(var)
                        self.traceback_chain.append(f"{target.id} = {value_desc}")
        self.generic_visit(node)


    def visit_If(self, node):
        if self.is_target_var_in_expr(node.test):
            condition = self.describe_expression(node.test)
            self.traceback_chain.append(f"if {condition}:")
        self.generic_visit(node)

    def is_target_var_in_expr(self, expr):
        if isinstance(expr, ast.Name) and expr.id in self.var_mapping:
            return True
        elif isinstance(expr, (ast.BinOp, ast.BoolOp, ast.UnaryOp, ast.Compare)):
            for child in ast.iter_child_nodes(expr):
                if self.is_target_var_in_expr(child):
                    return True
        return False


    def describe_expression(self, expr):
        if isinstance(expr, ast.Str):
            return f'"{expr.s}"'
        elif isinstance(expr, ast.Num):
            return str(expr.n)
        # 处理变量名
        elif isinstance(expr, ast.Name):
            return expr.id
        elif isinstance(expr, ast.Call):
            func = self.describe_expression(expr.func)
            args = ", ".join([self.describe_expression(arg) for arg in expr.args])
            return f"{func}({args})"
        elif isinstance(expr, ast.Attribute):
            value = self.describe_expression(expr.value)
            return f"{value}.{expr.attr}"
        elif isinstance(expr, ast.List):
            elements = ", ".join([self.describe_expression(e) for e in expr.elts])
            return f"[{elements}]"
        elif isinstance(expr, ast.BinOp):
            left = self.describe_expression(expr.left)
            op = self.describe_op(expr.op)
            right = self.describe_expression(expr.right)
            return f"({left} {op} {right})"
        else:
            return self.complex_expression_handler(expr)
        # We directly use the ast class to the tree

    def describe_op(self, op):
        if isinstance(op, ast.Add):
            return '+'
        elif isinstance(op, ast.Sub):
            return '-'
        elif isinstance(op, ast.Mult):
            return '*'
        elif isinstance(op, ast.Div):
            return '/'
        else:
            return "op"

    def complex_expression_handler(self, expr):
        """
        处理无法直接转换为简单字符串描述的复杂表达式。
        """
        # 使用ast.dump来获取表达式的原始结构描述
        return f"complex_expression: {ast.dump(expr, indent=4)}"