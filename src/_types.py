from pydantic import BaseModel

import typing as t

ASTDumps = str

# class NoAsType(BaseModel): 
#     class ops:
#         src: str
#         des: str
#         ops: ASTDumps
        
#     class statement:
#         details: ASTDumps
        
#     class input:
#         des: str
        

class NoA(BaseModel):
    """
    NoA: Note of Tree-of-Ast
    """
    name: str
    details: ASTDumps
    children: t.List['NoA'] = []

    # Method to add a child node to the current node
    def add_child(self, child: 'NoA') -> None:
        self.children.append(child)

class TreeOfAst(BaseModel):
    root: NoA
