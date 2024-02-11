from models import *
from rich import print

        
def analyze_traceback(code, target_var):
    tree = ast.parse(code)
    analyzer = TracebackAnalyzer(target_var)
    analyzer.visit(tree)
    return analyzer.traceback_chain

with open("vuln/vuln.py") as fp:
    code = fp.read()

# 追踪'user_input'变量
traceback_chain = analyze_traceback(code, 'c')
num = 0
for step in reversed(traceback_chain):
    num += 1
    print(f"\n##########TREE{num}##########")
    print(step)
    print("#########################")