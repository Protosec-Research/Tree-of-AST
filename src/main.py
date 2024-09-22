from _toa import ToA

_sinks =  ['eval', 'exec', 'os.system', 'pickle.load', 'pickle.loads', 'importlib.import_module']

def main():
    code = open('vuln/variable-trace.py', 'r').read()
    tree_of_ast = ToA(code, _sinks)
    tree_of_ast.invoke()

if __name__ == "__main__":
    main()