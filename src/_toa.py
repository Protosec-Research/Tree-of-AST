import warnings
import os
from langchain.globals import set_debug
import ast
import astor
from typing import List, Dict, Any, Tuple, Optional
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain.prompts.chat import SystemMessagePromptTemplate
from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings("ignore", category=DeprecationWarning)
set_debug(False)

class VariableNode:
    def __init__(self, value: Any, description: str):
        self.value = value
        self.description = description
        self.prev: Optional[VariableNode] = None
        self.next: Optional[VariableNode] = None

class VariableTrace:
    def __init__(self):
        self.head: Optional[VariableNode] = None
        self.tail: Optional[VariableNode] = None

    def add_node(self, value: Any, description: str):
        new_node = VariableNode(value, description)
        if not self.head:
            self.head = self.tail = new_node
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node

class ToA:
    def __init__(self, code: str, sinks: List[str]):
        self.tree = ast.parse(code)
        self.__add_parent_info(self.tree)
        self.code = code
        self.sinks = sinks
        self.tainted_variables = set()  # Changed from list to set
        self.call_graph = {}
        self.variable_sources = {}
        self.function_defs = {}
        self.function_callers = {}
        self.variable_traces: Dict[str, VariableTrace] = {}
        self.call_chain = []
        
        self.chat_model = ChatOpenAI(
            base_url="https://ai-yyds.com/v1",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o",
        )
        
        class Probabilities(BaseModel):
            probabilities: Dict[str, float] = Field(description="Probabilities of each caller causing user-controllable input source")

        self.output_parser = PydanticOutputParser(pydantic_object=Probabilities)
        
        system_message_prompt = SystemMessagePromptTemplate.from_template(
            "You are a code analysis expert, specializing in analyzing function call relationships and potential user input sources. "
            "Please strictly output in the specified JSON format without any additional explanations or comments."
        )
        human_message_prompt = HumanMessagePromptTemplate.from_template(
            "Given the function '{function_name}' and its potential callers {callers}, evaluate the probability of each caller causing a user-controllable input source."
            "Carefully analyze the implementation of each caller function:"
            "1. If a function uses hardcoded values or constants, it should be considered a low probability source of user-controllable input."
            "2. If a function directly uses user input (e.g., input() function), it should be considered a high probability source of user-controllable input."
            "3. If a function receives values from parameters, consider the possible sources of these parameters."
            "5. Functions that don't directly handle user input or only call other functions should generally have lower probabilities."
            "The sum of all probabilities should equal 1. Avoid extreme high or low probabilities; provide reasonable estimates."
            "Consider the following code context:\n\n{code_context}\n\n"
            "Output in the following format:\n{format_instructions}"
        )
        self.vote_prompt = ChatPromptTemplate.from_messages([
            system_message_prompt,
            human_message_prompt
        ])
        self.vote_chain = LLMChain(llm=self.chat_model, prompt=self.vote_prompt)

    def __add_parent_info(self, node, parent=None):
        node.parent = parent
        for child in ast.iter_child_nodes(node):
            self.__add_parent_info(child, node)

    def __build_call_graph(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                self.function_defs[node.name] = node
                self.call_graph[node.name] = []
            elif isinstance(node, ast.Call):
                func_name = self.__get_func_name(node)
                caller_func = self.__get_enclosing_function(node)
                if func_name and caller_func:
                    if caller_func not in self.call_graph:
                        self.call_graph[caller_func] = []
                    self.call_graph[caller_func].append(func_name)
                    if func_name not in self.function_callers:
                        self.function_callers[func_name] = []
                    self.function_callers[func_name].append(caller_func)
                
                # 只追踪污点函数的参数
                if func_name in self.sinks:
                    for i, arg in enumerate(node.args):
                        arg_source = self.__get_source(arg)
                        self.__trace_variable_source(arg_source, f"{func_name}_arg_{i}")
                        self.tainted_variables.add(frozenset(arg_source.items()))  # 将字典转换为frozenset后添加

            elif isinstance(node, ast.Assign):
                targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
                value = self.__get_source(node.value)
                for target in targets:
                    self.variable_sources[target] = value
                    if isinstance(value, dict):
                        # 如果value是字典,检查它的某个特定键是否在tainted_variables中
                        if any(key in self.tainted_variables for key in value):
                            # 处理污染逻辑
                            pass
                    elif value in self.tainted_variables:
                        # 原有的检查逻辑
                        pass
                    self.__trace_variable_source(value, target)
                    self.tainted_variables.add(target)

    def __get_func_name(self, node):
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            else:
                return node.func.attr
        else:
            return None

    def __get_enclosing_function(self, node):
        while node:
            if isinstance(node.parent, ast.FunctionDef):
                return node.parent.name
            node = node.parent
        return "global"

    def __get_call_info(self, node: ast.Call) -> Dict[str, Any]:
        func_name = self.__get_func_name(node)
        if not func_name:
            return None
        args_info = []
        for arg in node.args:
            arg_source = self.__get_source(arg)
            args_info.append(arg_source)
        return {
            'func': func_name,
            'args': args_info
        }

    def __get_source(self, node):
        if isinstance(node, ast.Name):
            var_name = node.id
            if var_name in self.variable_sources:
                return {var_name: self.variable_sources[var_name]}
            else:
                return var_name
        elif isinstance(node, ast.Call):
            call_info = self.__get_call_info(node)
            self.__trace_variable_source(call_info, f"{call_info['func']}_return")
            return call_info
        elif isinstance(node, ast.Constant):
            return node.value
        else:
            return astor.to_source(node).strip()

    def __trace_variable_source(self, var, var_name=None):
        main_var_name = var_name.split('.')[0] if var_name else 'unknown'
        if main_var_name not in self.variable_traces:
            self.variable_traces[main_var_name] = VariableTrace()
        
        description = f"{var_name}: {var}"
        self.variable_traces[main_var_name].add_node(var, description)
        print(f"[!] {description}")

    def __get_code_context(self, func_name, callers):
        context = f"Function {func_name} definition:\n"
        if func_name in self.function_defs:
            context += astor.to_source(self.function_defs[func_name]) + "\n\n"
        context += "Caller functions tree:\n"
        for caller in callers:
            context += self.__get_caller_tree(caller, 0, max_depth=2)
        return context

    def __get_caller_tree(self, func_name, depth, max_depth=2):
        # a bit of lookahead helps
        tree = "  " * depth + f"- {func_name}\n"
        if func_name in self.function_defs:
            tree += "  " * (depth + 1) + astor.to_source(self.function_defs[func_name]).replace("\n", "\n" + "  " * (depth + 1)) + "\n"
        
        if depth < max_depth and func_name in self.function_callers:
            for caller in self.function_callers[func_name]:
                tree += self.__get_caller_tree(caller, depth + 1, max_depth)
        
        return tree

    def TRACE(self, func_name, path):
        if func_name in self.function_callers:
            voted_caller = self.VOTE(func_name)
            if voted_caller and voted_caller not in path:
                path.append(voted_caller)
                self.TRACE(voted_caller, path)
            else:
                self.call_chain = list(reversed(path))
                print("Possible function call chain: " + " ← ".join(self.call_chain))
        else:
            self.call_chain = list(reversed(path))
            print("Possible function call chain: " + " ← ".join(self.call_chain))

    def VOTE(self, func_name):

        # Here we use the Vote, Value concept from Tree-of-Thought
        callers = self.function_callers.get(func_name, [])
        if callers:
            # Vote part 80% 
            code_context = self.__get_code_context(func_name, callers)
            format_instructions = self.output_parser.get_format_instructions()
            
            response = self.vote_chain.run(
                function_name=func_name, 
                callers=callers, 
                code_context=code_context,
                format_instructions=format_instructions
            )
            
            try:
                parsed_output = self.output_parser.parse(response)
                vote_probabilities = parsed_output.probabilities
                print(f"\nVOTE: {vote_probabilities}")
            except Exception as e:
                print(f"ERROR (VOTE): {response}")
                print(f"{str(e)}")
                vote_probabilities = {caller: 1/len(callers) for caller in callers}

            # Value part 20%
            value_scores = self.__calculate_value_scores(callers)
            print(f"\tVALUE: {value_scores}")
            
            # merge Vote and Value
            final_probabilities = {}
            for caller in callers:
                final_probabilities[caller] = 0.8 * vote_probabilities.get(caller, 0) + 0.2 * value_scores.get(caller, 0)
            
            print(f"\tFinal probabilities: {final_probabilities}")
            
            if final_probabilities:
                return max(final_probabilities, key=final_probabilities.get)
            else:
                return callers[0]
        else:
            return None

    def __calculate_value_scores(self, callers):
        value_scores = {}
        for caller in callers:
            remaining_chain, chain_length = self.__get_remaining_chain(caller)
            value_scores[caller] = chain_length  # 剩余调用链越长，分数越高
            print(f"\t\t{caller}: {chain_length}")
            print(f"\t\t\tChain: {' -> '.join(remaining_chain)}")
        
        # 归一化分数
        total_score = sum(value_scores.values())
        return {caller: score/total_score for caller, score in value_scores.items()}

    def __get_remaining_chain(self, func_name, visited=None):
        if visited is None:
            visited = set()
        
        if func_name in visited:
            return [func_name], 1
        
        visited.add(func_name)
        
        if func_name not in self.function_callers:
            return [func_name], 1
        
        max_chain = []
        max_length = 0
        for caller in self.function_callers[func_name]:
            chain, length = self.__get_remaining_chain(caller, visited.copy())
            if length > max_length:
                max_length = length
                max_chain = chain
        
        return [func_name] + max_chain, max_length + 1

    def LOCATE(self, node: ast.Call) -> bool:
        func_name = self.__get_func_name(node)
        if func_name in self.sinks:
            return True
        return False 

    def trace_variables_along_chain(self):
        traced_vars = set()
        for func in self.call_chain:
            if func in self.function_defs:
                func_node = self.function_defs[func]
                self.__trace_function_variables(func_node, traced_vars)

    def __trace_function_variables(self, func_node, traced_vars):
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        if var_name not in traced_vars:
                            traced_vars.add(var_name)
                            source = self.__get_source(node.value)
                            self.__trace_variable_source(source, var_name)

    def print_variable_traces(self):
        for var_name, trace in self.variable_traces.items():
            print(f"\nVariable: {var_name}")
            current = trace.head
            while current:
                print(f"  {current.description}")
                current = current.next

    def invoke(self):
        self.__build_call_graph()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and self.LOCATE(node):
                sink_info = self.__get_call_info(node)
                print(f"Dangerous function call found: {sink_info['func']}")
                print(f"Starting backward tracing from '{sink_info['func']}':")
                self.TRACE(sink_info['func'], [sink_info['func']])
                self.trace_variables_along_chain()
                from pprint import pprint
                pprint(self.variable_traces)        
                self.print_variable_traces()
