from pydantic import BaseModel

import typing as t

ASTDumps = str

class NoAsType(BaseModel): 
    class ops:
        des: str
        ops: str
        src: ASTDumps
        
    class statement:
        details: ASTDumps
        
    class input:
        des: str
        input
        


class NoA(BaseModel):
    """
    NoA: Note of Tree-of-Ast
    """
    name: str
    details: NoAsType
    children: t.List['NoA'] = []

    # Method to add a child node to the current node
    def add_child(self, child: 'NoA') -> None:
        self.children.append(child)

class TreeOfAst(BaseModel):
    root: NoA
