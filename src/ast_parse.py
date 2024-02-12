from models import *
from _types import *
from _console import cons

print = cons.print
        
def ToAfy_AST(root, target_function, target_variable):
    linker = ToAfy(target_function, target_variable)
    linker.visit(root)
    return root, linker.vulnerable_note

if __name__ == "__main__":
    
    with open("vuln/vuln.py") as fp:
        source_code = fp.read()
    
    AST = ast.parse(source_code)
    target_function = "os.system"
    target_variable = "c"
    
    print("[*] Step one, ToAfy AST by attribute every note father and children, while locating the vulnerabilty id.")
    AST_ROOT, VulneralNote = ToAfy_AST(AST,target_function,target_variable)
    print(f"[*] Now node. id = {VulneralNote.node_id} is the vulnerable note.\n\n{ast.dump(VulneralNote)}")
    
    print(f"\n[*] Step two, Reverse traveling ToA on id = {VulneralNote.node_id}")
    tracer = VariableTrace(VulneralNote,target_variable)
    with cons.status("Reverse traveling", spinner='dots4'):
        chain = tracer.reverse_trace_from_node()
        for node in chain:
            print(f'    Job: [bold]{node[0]}[/bold];\n    details: {node[1] if type(node[1]) is str else ast.dump(node[1])}\n')