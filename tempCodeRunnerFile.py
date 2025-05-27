from flask import Flask, request, jsonify, render_template
import re
import logging

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
            if i >= len(self.tokens) or self.tokens[i][0] not in ["LITERAL", "IDENTIFIER"]:
                self.errors.append(f"Line {type_token[2]}: Invalid value after '='")
                return i, None
            value = self.tokens[i][1]
            i += 1
            if i >= len(self.tokens) or self.tokens[i][1] != ";":
                self.errors.append(f"Line {type_token[2]}: Missing ';' after declaration")
                return i, None
            i += 1
            return i, ("DECLARATION", "int", var_name, value)
        else:
            if i >= len(self.tokens) or self.tokens[i][1] != ";":
                self.errors.append(f"Line {type_token[2]}: Missing ';' after declaration")
                return i, None
            i += 1
            return i, ("DECLARATION", "int", var_name, None)

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
        elif len(expr) == 3 and expr[1][0] == "OPERATOR" and expr[0][0] == "IDENTIFIER" and expr[2][0] in ["LITERAL", "IDENTIFIER"]:
            value = f"{expr[0][1]} {expr[1][1]} {expr[2][1]}"
        else:
            self.errors.append(f"Line {line_num}: Invalid assignment expression")
            return i, None
        return i, ("ASSIGNMENT", var_name, value)

    def parse_for(self, i):
        line_num = self.tokens[i][2]
        i += 1
        if i >= len(self.tokens) or self.tokens[i][1] != "(":
            self.errors.append(f"Line {line_num}: Missing '(' after 'for'")
            return i, None
        i += 1
        i, init = self.parse_declaration(i)
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
            if self.tokens[i][0] == "IDENTIFIER":
                i, stmt = self.parse_assignment(i)
                if stmt:
                    body.append(stmt)
            else:
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
        return i, ("RETURN", value)

    def semantic_analyzer(self, nodes=None):
        if nodes is None:
            nodes = self.ast
        for node in nodes:
            if node[0] == "DECLARATION" or node[0] == "FUNCTION":
                var_type, var_name = node[1], node[2]
                value = node[3] if node[0] == "DECLARATION" else None
                if var_name in self.symbol_table:
                    self.errors.append(f"Line {self.tokens[0][2]}: Redeclaration of '{var_name}'")
                else:
                    self.symbol_table[var_name] = {"type": var_type, "value": int(value) if value and value.isnumeric() else None}
                if node[0] == "FUNCTION" and len(node) > 3:
                    self.semantic_analyzer(node[3])
            elif node[0] == "ASSIGNMENT":
                var_name, value = node[1], node[2]
                if var_name not in self.symbol_table:
                    self.errors.append(f"Line {self.tokens[0][2]}: Undeclared variable '{var_name}'")
                elif " " in value:
                    parts = value.split()
                    if parts[0] not in self.symbol_table:
                        self.errors.append(f"Line {self.tokens[0][2]}: Undeclared variable '{parts[0]}' in expression")
                    if len(parts) > 2 and parts[2] not in self.symbol_table:
                        self.errors.append(f"Line {self.tokens[0][2]}: Undeclared variable '{parts[2]}' in expression")
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

    def generate_intermediate_code(self):
        self.intermediate_code = []
        def process_nodes(nodes):
            for node in nodes:
                if node[0] == "DECLARATION" and node[3]:
                    self.intermediate_code.append(f"{node[2]} = {node[3]}")
                elif node[0] == "ASSIGNMENT":
                    self.intermediate_code.append(f"{node[1]} = {node[2]}")
                elif node[0] == "FUNCTION":
                    if len(node) > 3:
                        process_nodes(node[3])
                elif node[0] == "RETURN":
                    self.intermediate_code.append(f"return {node[1]}")
        process_nodes(self.ast)
        return self.intermediate_code

    def optimize(self):
        self.optimized_code = self.intermediate_code.copy()
        return self.optimized_code

    def generate_assembly(self):
        self.assembly_code = [
            "section .text",
            "global _start",
            "_start:"
        ]
        for line in self.optimized_code:
            if "=" in line and "return" not in line:
                parts = line.split(" = ")
                var, expr = parts[0], parts[1]
                if " " in expr:
                    op_parts = expr.split()
                    self.assembly_code.append(f"mov eax, [{op_parts[0]}]")
                    self.assembly_code.append(f"add eax, [{op_parts[2]}]")
                    self.assembly_code.append(f"mov [{var}], eax")
                else:
                    self.assembly_code.append(f"mov eax, {expr}")
                    self.assembly_code.append(f"mov [{var}], eax")
            elif "return" in line:
                value = line.split()[1]
                self.assembly_code.append(f"mov eax, {value}")
        self.assembly_code.append("int 0x80")
        return self.assembly_code

    def assemble(self):
        return "\n".join(self.assembly_code)

    def link(self):
        return "Linked executable generated (simulated)"

    def compile(self, code):
        self.reset_state()  # Reset state before each compilation
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
        output = [
            "Tokens:",
            str(self.tokens),
            "",
            "AST:",
            str(self.ast),
            "",
            "Intermediate Code:",
            "\n".join(self.intermediate_code),
            "",
            "Optimized Code:",
            "\n".join(self.optimized_code),
            "",
            "Assembly Code:",
            "\n".join(self.assembly_code)
        ]
        return "\n".join(output)

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