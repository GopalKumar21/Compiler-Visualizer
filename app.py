from flask import Flask, request, jsonify, render_template
import re
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class CCompiler:
    def __init__(self):
        self.reset_state()

    def reset_state(self):
        self.tokens = []
        self.ast = []
        self.symbol_table = {}
        self.errors = []
        self.intermediate_code = []
        self.optimized_code = []
        self.assembly_code = []
        self.code = ""

    def lexer(self, code):
        self.code = code
        self.tokens = []
        self.errors = []
        keywords = {"int", "for", "if", "else", "while", "return"}
        operators = {"+", "-", "*", "/", "=", "<", ">", ";", "{", "}", "(", ")"}
        token_pattern = r'//.*$|/\*.*?\*/|\s+|\w+|[{}();+\-*/=<>]'
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            tokens = re.findall(token_pattern, line, re.MULTILINE | re.DOTALL)
            for token in tokens:
                if token.startswith('//') or token.startswith('/*') or token.isspace():
                    continue
                elif token in keywords:
                    self.tokens.append(("KEYWORD", token, line_num))
                elif token in operators:
                    self.tokens.append(("OPERATOR", token, line_num))
                elif re.match(r'^\d+$', token):
                    self.tokens.append(("LITERAL", token, line_num))
                elif re.match(r'^[a-zA-Z_]\w*$', token):
                    self.tokens.append(("IDENTIFIER", token, line_num))
                else:
                    self.errors.append(f"Line {line_num}: Invalid token '{token}'")
        return self.tokens

    def parser(self):
        self.ast = []
        i = 0
        while i < len(self.tokens):
            token_type, token_value, line_num = self.tokens[i]
            if token_type == "KEYWORD" and token_value == "int":
                i, decl = self.parse_declaration(i)
                if decl:
                    self.ast.append(decl)
            elif token_type == "KEYWORD" and token_value == "for":
                i, stmt = self.parse_for(i)
                if stmt:
                    self.ast.append(stmt)
            elif token_type == "IDENTIFIER":
                i, assign = self.parse_assignment(i)
                if assign:
                    self.ast.append(assign)
            elif token_type == "KEYWORD" and token_value == "return":
                i, ret = self.parse_return(i)
                if ret:
                    self.ast.append(ret)
            else:
                i += 1
        return self.ast

    def parse_declaration(self, i):
        type_token = self.tokens[i]
        i += 1
        if i >= len(self.tokens) or self.tokens[i][0] != "IDENTIFIER":
            self.errors.append(f"Line {type_token[2]}: Expected identifier after 'int'")
            return i, None
        var_name = self.tokens[i][1]
        line_num = self.tokens[i][2]
        i += 1
        if i < len(self.tokens) and self.tokens[i][1] == "(":
            i += 1
            if i >= len(self.tokens) or self.tokens[i][1] != ")":
                self.errors.append(f"Line {type_token[2]}: Expected ')' after '(' in function declaration")
                return i, None
            i += 1
            if i >= len(self.tokens) or self.tokens[i][1] != "{":
                self.errors.append(f"Line {type_token[2]}: Expected '{{' after function declaration")
                return i, None
            i += 1
            body = []
            while i < len(self.tokens) and self.tokens[i][1] != "}":
                if self.tokens[i][0] == "KEYWORD" and self.tokens[i][1] == "int":
                    i, decl = self.parse_declaration(i)
                    if decl:
                        body.append(decl)
                elif self.tokens[i][0] == "IDENTIFIER":
                    i, assign = self.parse_assignment(i)
                    if assign:
                        body.append(assign)
                elif self.tokens[i][0] == "KEYWORD" and self.tokens[i][1] == "for":
                    i, stmt = self.parse_for(i)
                    if stmt:
                        body.append(stmt)
                elif self.tokens[i][0] == "KEYWORD" and self.tokens[i][1] == "return":
                    i, ret = self.parse_return(i)
                    if ret:
                        body.append(ret)
                else:
                    i += 1
            if i >= len(self.tokens):
                self.errors.append(f"Line {type_token[2]}: Missing '}}' in function body")
                return i, None
            i += 1
            return i, ("FUNCTION", "int", var_name, body)
        elif i < len(self.tokens) and self.tokens[i][1] == "=":
            i += 1
            expr = []
            while i < len(self.tokens) and self.tokens[i][1] != ";":
                expr.append(self.tokens[i])
                i += 1
            if i >= len(self.tokens):
                self.errors.append(f"Line {type_token[2]}: Missing ';' after declaration")
                return i, None
            i += 1
            if len(expr) == 1 and expr[0][0] in ["LITERAL", "IDENTIFIER"]:
                value = expr[0][1]
                return i, ("DECLARATION", "int", var_name, value, line_num)
            elif len(expr) == 3 and expr[1][0] == "OPERATOR" and expr[1][1] in ["+", "-", "*", "/"]:
                return i, ("DECLARATION", "int", var_name, (expr[1][1], expr[0][1], expr[2][1]), line_num)
            else:
                self.errors.append(f"Line {type_token[2]}: Invalid expression in declaration")
                return i, None
        else:
            if i >= len(self.tokens) or self.tokens[i][1] != ";":
                self.errors.append(f"Line {type_token[2]}: Missing ';' after declaration")
                return i, None
            i += 1
            return i, ("DECLARATION", "int", var_name, None, line_num)

    def parse_assignment(self, i):
        var_name = self.tokens[i][1]
        line_num = self.tokens[i][2]
        i += 1
        if i >= len(self.tokens) or self.tokens[i][1] != "=":
            return i, None
        i += 1
        expr = []
        while i < len(self.tokens) and self.tokens[i][1] != ";":
            expr.append(self.tokens[i])
            i += 1
        if i >= len(self.tokens):
            self.errors.append(f"Line {line_num}: Missing ';' after assignment")
            return i, None
        i += 1
        if len(expr) == 1 and expr[0][0] in ["LITERAL", "IDENTIFIER"]:
            value = expr[0][1]
            return i, ("ASSIGNMENT", var_name, value, line_num)
        elif len(expr) == 3 and expr[1][0] == "OPERATOR" and expr[1][1] in ["+", "-", "*", "/"]:
            return i, ("ASSIGNMENT", var_name, (expr[1][1], expr[0][1], expr[2][1]), line_num)
        else:
            self.errors.append(f"Line {line_num}: Invalid expression in assignment")
            return i, None

    def parse_for(self, i):
        line_num = self.tokens[i][2]
        i += 1
        if i >= len(self.tokens) or self.tokens[i][1] != "(":
            self.errors.append(f"Line {line_num}: Missing '(' after 'for'")
            return i, None
        i += 1
        if self.tokens[i][0] == "KEYWORD" and self.tokens[i][1] == "int":
            i, init = self.parse_declaration(i)
        elif self.tokens[i][0] == "IDENTIFIER":
            i, init = self.parse_assignment(i)
        else:
            self.errors.append(f"Line {line_num}: Invalid for loop initialization")
            return i, None
        if not init:
            return i, None
        cond_start = i
        while i < len(self.tokens) and self.tokens[i][1] != ";":
            i += 1
        if i >= len(self.tokens):
            self.errors.append(f"Line {line_num}: Missing first ';' in 'for' loop")
            return i, None
        condition = self.tokens[cond_start:i]
        i += 1
        incr_start = i
        while i < len(self.tokens) and self.tokens[i][1] != ")":
            i += 1
        if i >= len(self.tokens):
            self.errors.append(f"Line {line_num}: Missing ')' in 'for' loop")
            return i, None
        increment = self.tokens[incr_start:i]
        i += 1
        if i >= len(self.tokens) or self.tokens[i][1] != "{":
            self.errors.append(f"Line {line_num}: Missing '{{' after 'for'")
            return i, None
        i += 1
        body = []
        while i < len(self.tokens) and self.tokens[i][1] != "}":
            if self.tokens[i][0] == "KEYWORD" and self.tokens[i][1] == "int":
                i, decl = self.parse_declaration(i)
                if decl:
                    body.append(decl)
            elif self.tokens[i][0] == "IDENTIFIER":
                i, assign = self.parse_assignment(i)
                if assign:
                    body.append(assign)
            elif self.tokens[i][0] == "KEYWORD" and self.tokens[i][1] == "for":
                i, stmt = self.parse_for(i)
                if stmt:
                    body.append(stmt)
            elif self.tokens[i][0] == "KEYWORD" and self.tokens[i][1] == "return":
                i, ret = self.parse_return(i)
                if ret:
                    body.append(ret)
            else:
                self.errors.append(f"Line {self.tokens[i][2]}: Unexpected token '{self.tokens[i][1]}' in for loop body")
                i += 1
        if i >= len(self.tokens):
            self.errors.append(f"Line {line_num}: Missing '}}' in 'for' loop")
            return i, None
        i += 1
        return i, ("FOR", init, condition, increment, body)

    def parse_return(self, i):
        line_num = self.tokens[i][2]
        i += 1
        if i >= len(self.tokens) or self.tokens[i][0] not in ["LITERAL", "IDENTIFIER"]:
            self.errors.append(f"Line {line_num}: Expected value after 'return'")
            return i, None
        value = self.tokens[i][1]
        i += 1
        if i >= len(self.tokens) or self.tokens[i][1] != ";":
            self.errors.append(f"Line {line_num}: Missing ';' after 'return'")
            return i, None
        i += 1
        return i, ("RETURN", value, line_num)

    def semantic_analyzer(self, nodes=None):
        if nodes is None:
            nodes = self.ast
        for node in nodes:
            if node[0] == "DECLARATION" or node[0] == "FUNCTION":
                var_type, var_name = node[1], node[2]
                value = node[3] if node[0] == "DECLARATION" else None
                line_num = node[-1]
                if var_name in self.symbol_table:
                    self.errors.append(f"Line {line_num}: Redeclaration of '{var_name}'")
                else:
                    self.symbol_table[var_name] = {"type": var_type, "value": None}
                if node[0] == "FUNCTION" and len(node) > 3:
                    self.semantic_analyzer(node[3])
            elif node[0] == "ASSIGNMENT":
                var_name, value = node[1], node[2]
                line_num = node[-1]
                if var_name not in self.symbol_table:
                    self.errors.append(f"Line {line_num}: Undeclared variable '{var_name}'")
                if isinstance(value, tuple):
                    op, left, right = value
                    if left not in self.symbol_table and not left.isnumeric():
                        self.errors.append(f"Line {line_num}: Undeclared variable '{left}'")
                    if right not in self.symbol_table and not right.isnumeric():
                        self.errors.append(f"Line {line_num}: Undeclared variable '{right}'")
            elif node[0] == "FOR":
                init, cond, incr, body = node[1], node[2], node[3], node[4]
                self.semantic_analyzer([init])
                for t in cond:
                    if t[0] == "IDENTIFIER" and t[1] not in self.symbol_table:
                        self.errors.append(f"Line {t[2]}: Undeclared variable '{t[1]}' in condition")
                for t in incr:
                    if t[0] == "IDENTIFIER" and t[1] not in self.symbol_table:
                        self.errors.append(f"Line {t[2]}: Undeclared variable '{t[1]}' in increment")
                self.semantic_analyzer(body)
            elif node[0] == "RETURN":
                value = node[1]
                line_num = node[-1]
                if value not in self.symbol_table and not value.isnumeric():
                    self.errors.append(f"Line {line_num}: Undeclared variable '{value}' in return")

    def generate_intermediate_code(self):
        self.intermediate_code = []
        def process_nodes(nodes):
            for node in nodes:
                if node[0] == "DECLARATION" and node[3]:
                    if isinstance(node[3], tuple):
                        op, left, right = node[3]
                        self.intermediate_code.append(("binop", node[2], op, left, right, node[4]))
                    else:
                        self.intermediate_code.append(("assign", node[2], node[3], node[4]))
                elif node[0] == "ASSIGNMENT":
                    if isinstance(node[2], tuple):
                        op, left, right = node[2]
                        self.intermediate_code.append(("binop", node[1], op, left, right, node[3]))
                    else:
                        self.intermediate_code.append(("assign", node[1], node[2], node[3]))
                elif node[0] == "FUNCTION":
                    if len(node) > 3:
                        process_nodes(node[3])
                elif node[0] == "RETURN":
                    self.intermediate_code.append(("return", node[1], node[2]))
                elif node[0] == "FOR":
                    process_nodes([node[1]])
                    process_nodes(node[4])
        process_nodes(self.ast)
        return self.intermediate_code

    def optimize(self):
        self.optimized_code = []
        constants = {}
        used_vars = set()

        # Collect used variables recursively
        def collect_used_vars(var):
            if var in used_vars:
                return
            used_vars.add(var)
            for op in self.intermediate_code:
                if op[0] == "assign" and op[1] == var and op[2].isalpha():
                    collect_used_vars(op[2])
                elif op[0] == "binop" and op[1] == var:
                    if op[3].isalpha():
                        collect_used_vars(op[3])
                    if op[4].isalpha():
                        collect_used_vars(op[4])

        # Start from return statement
        for op in self.intermediate_code:
            if op[0] == "return":
                collect_used_vars(op[1])
                break

        # Constant folding and propagation
        for op in self.intermediate_code:
            if op[0] == "assign":
                var, value, _ = op[1], op[2], op[3]
                if value.isnumeric():
                    constants[var] = int(value)
                elif value in constants:
                    constants[var] = constants[value]
            elif op[0] == "binop":
                var, op_type, left, right, line_num = op[1], op[2], op[3], op[4], op[5]
                left_val = int(left) if left.isnumeric() else constants.get(left)
                right_val = int(right) if right.isnumeric() else constants.get(right)
                if left_val is not None and right_val is not None:
                    if op_type == "+":
                        constants[var] = left_val + right_val
                    elif op_type == "-":
                        constants[var] = left_val - right_val
                    elif op_type == "*":
                        constants[var] = left_val * right_val
                    elif op_type == "/":
                        if right_val != 0:
                            constants[var] = left_val // right_val
                        else:
                            self.errors.append(f"Line {line_num}: Division by zero")

        # Generate optimized code
        for op in self.intermediate_code:
            if op[0] == "return":
                value, line_num = op[1], op[2]
                final_value = str(constants.get(value, value))
                self.optimized_code.append(("return", final_value, line_num))
                break

        return self.optimized_code

    def generate_assembly(self):
        self.assembly_code = ["section .text", "global _start", "_start:"]
        for op in self.optimized_code:
            if op[0] == "assign":
                self.assembly_code.append(f"mov eax, {op[2]}")
                self.assembly_code.append(f"mov [{op[1]}], eax")
            elif op[0] == "binop":
                self.assembly_code.append(f"mov eax, {'[' + op[3] + ']' if not isinstance(op[3], int) and not op[3].isnumeric() else op[3]}")
                if op[2] == "+":
                    self.assembly_code.append(f"add eax, {'[' + op[4] + ']' if not isinstance(op[4], int) and not op[4].isnumeric() else op[4]}")
                elif op[2] == "*":
                    self.assembly_code.append(f"imul eax, {'[' + op[4] + ']' if not isinstance(op[4], int) and not op[4].isnumeric() else op[4]}")
                self.assembly_code.append(f"mov [{op[1]}], eax")
            elif op[0] == "return":
                self.assembly_code.append(f"mov eax, {op[1]}")
        self.assembly_code.append("int 0x80")
        return self.assembly_code

    def assemble(self):
        return "\n".join(self.assembly_code)

    def link(self):
        return "Linked executable generated (simulated)"

    def compile(self, code):
        self.reset_state()
        self.lexer(code)
        if self.errors:
            return self.errors
        self.parser()
        if self.errors:
            return self.errors
        self.semantic_analyzer()
        if self.errors:
            return self.errors
        self.generate_intermediate_code()
        self.optimize()
        self.generate_assembly()
        self.assemble()
        self.link()
        return []

    def run(self):
        if self.errors:
            return "\n".join(self.errors)
        return "\n".join([
            "Tokens:", str(self.tokens), "",
            "AST:", str(self.ast), "",
            "Intermediate Code:", "\n".join(str(op) for op in self.intermediate_code), "",
            "Optimized Code:", "\n".join(str(op) for op in self.optimized_code), "",
            "Assembly Code:", "\n".join(self.assembly_code)
        ])

compiler = CCompiler()

@app.route('/')
def serve_index():
    logger.info("Serving index.html from templates")
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_code():
    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({'output': 'No code provided'}), 400
        code = data.get('code', '')
        logger.info("Running compiled code")
        compiler.compile(code)
        output = compiler.run()
        return jsonify({'output': output})
    except Exception as e:
        logger.error(f"Error in /run: {str(e)}")
        return jsonify({'output': f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    logger.info("Starting Flask server on 0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
