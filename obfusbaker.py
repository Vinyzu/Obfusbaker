import ast
import hashlib
import string
import textwrap
import builtins
import random
import base64


class Helpers:
    def obfuscate_number(num):
        random_int = random.randint(num, 999999)
        substract = random_int - num
        new = f"{random_int} - {substract}"
        return new

    def add_builtins_and_base64(content, obfuscator):
        list_dir_builtins = obfuscator.hashed_random_string()
        obfuscator.imports["builtins_obfuscation"] = list_dir_builtins
        if not any("builtins" in line for line in content.splitlines()):
            content = f"import builtins \nlist_dir_builtins = {list(dir(builtins))} \n" + \
                content
        if not any("base64" in line for line in content.splitlines()):
            content = "import base64 \n" + content
        return content


class Obfuscator(ast.NodeTransformer):
    def __init__(self):
        self.ignores = list(dir(builtins))
        # Append all python methods to ignores
        for builtin in __builtins__.__dict__.values():
            for method in list(dir(builtin)):
                self.ignores.append(method)
        ast.NodeTransformer.__init__(self)
        self.mapping = {}
        self.imports = {}
        self.arguments = {}
        self.count = 0

    def hashed_random_string(self):
        new = "O"
        hashed_int = int(hashlib.sha256(
            str(self.count).encode('utf-8')).hexdigest(), 16) % 10**16
        for num in str(hashed_int):
            if int(num) % 3 == 0:
                new += "0"
            elif int(num) % 2 == 0:
                new += "O"
            else:
                new += "o"
        self.count += 1
        return new

    def rename(self, input, call=False):
        if "self" in input or (input.startswith('__') and input.endswith("__")):
            return
        if input in self.ignores and call:  # and call
            if input in list(dir(builtins)) and call:
                index = list(dir(builtins)).index(input)  # 100
                random_index = random.randint(0, index)  # 90
                random_builtin = list(dir(builtins))[random_index]
                random_builtin = ast.unparse(self.visit(
                    ast.Constant(value=random_builtin)))
                random_builtin = "{" + random_builtin + "}"
                plus = index - random_index
                builtins_obf = self.rename("builtins")
                now = f'getattr({builtins_obf}, {self.rename("list_dir_builtins")}[({Helpers.obfuscate_number(index)})])'
                #  Below is a harder encryption, takes more time
                # now = f'getattr({builtins_obf}, {self.rename("list_dir_builtins")}[{self.rename("list_dir_builtins")}.index(f"{random_builtin}") + {plus}])'
                return now
            return
        elif input in self.imports.keys():
            return self.imports[input]
        elif str(input) in self.arguments.keys():
            return self.arguments[input]
        elif input in self.mapping.keys():
            return self.mapping[input]
        new_name = self.hashed_random_string()
        while new_name in self.mapping.values():
            new_name = self.hashed_random_string()
        self.mapping[input] = new_name
        return new_name

    # def visit_Return(self, node):
    #     node.value = self.visit(node.value)
    #     return node
    #
    # def visit_Compare(self, node):
    #     node.left = self.visit(node.left)
    #     node.comparators = [self.visit(comparator) for comparator in node.comparators]
    #     print(ast.unparse(node))
    #     return node

    def visit_FormattedValue(self, node):
        self.visit(node.value)
        return node

    def visit_Global(self, node):
        new = []
        for name in node.names:
            new.append(self.rename(name) if self.rename(name) else name)
        node.names = new
        return node

    def visit_Lambda(self, node):

        for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs + node.args.kw_defaults + node.args.defaults:
            try:
                new = self.rename(arg.arg)
                if new:
                    arg.arg = new
            except:
                pass
        node.body = self.visit(node.body)
        return node

    def visit_JoinedStr(self, node):
        values = []
        for value in node.values:
            if type(value) == ast.Constant:
                temp = self.visit(value)
                constant = ast.FormattedValue(value=temp, conversion=-1)
                values.append(constant)
            elif type(value) == ast.FormattedValue:
                temp = self.visit(value)
                values.append(temp)
        return ast.JoinedStr(values=values)

    def visit_Constant(self, node):
        returnment = node
        if type(node.value) == str:
            encoded = base64.b64encode(node.value.encode())
            replacement = f"base64.b64decode({encoded}).decode()"
            func_val_func = ast.Attribute(value=ast.Name(
                id='base64', ctx=ast.Load()),  attr='b64decode', ctx=ast.Load())
            func_val = ast.Call(func=func_val_func, args=[
                                ast.Constant(value=encoded)], keywords=[])
            func = ast.Attribute(value=func_val, attr="decode", ctx=ast.Load())
            call = ast.Call(func=func, args=[], keywords=[])
            self.visit(call)
            return call
        elif type(node.value) == int:
            return ast.Name(id=f"({Helpers.obfuscate_number(int(node.value))})")
        return node

    def visit_Call(self, node):
        # print(ast.unparse(node))
        if type(node.func) == ast.Name:
            new_name = self.rename(node.func.id, True)
            if new_name:
                node.func.id = new_name
            # self.visit(node.func)
        elif type(node.func) == ast.Attribute:
            self.visit(node.func.value)
            # Check if function is an import
            if not any(ast.unparse(node.func.value) in item for item in list(self.imports.items())):
                new_name = self.rename(node.func.attr, call=True)
                if new_name:
                    node.func.attr = new_name
        for i, arg in enumerate(node.args):
            if type(arg) == ast.Constant:
                pass
                # print(arg.value)
            elif type(arg) == ast.Name:
                pass
                # print(arg.id)
            else:
                print(type(arg))
            node.args[i] = self.visit(arg)
        for keyword in node.keywords:
            print("!", keyword)
        return node

    def visit_Assign(self, node):
        for target in node.targets:
            self.visit(target)
        if type(node.value) in (ast.List, ast.Tuple):
            node.value.elts = [self.visit(value) for value in node.value.elts]
        else:
            node.value = self.visit(node.value)
        return node

    def visit_Attribute(self, node):
        if type(node.value) == ast.Name:
            if node.value.id != "self":
                new_name = self.rename(node.value.id)
                if new_name:
                    node.value.id = new_name
        elif type(node.value) == ast.Attribute:
            self.visit(node.value)
        new_name = self.rename(node.attr)
        if new_name:
            node.attr = new_name
        return node

    def visit_Name(self, node):
        new_name = self.rename(node.id)
        if new_name:
            node.id = new_name
        return node

    def visit_Import(self, node):
        for name in node.names:
            hashed = self.hashed_random_string()
            self.imports[name.name] = hashed
            name.asname = hashed
        return node

    def visit_ImportFrom(self, node):
        for name in node.names:
            hashed = self.hashed_random_string()
            self.imports[name.name] = hashed
            name.asname = hashed
        return node

    def visit_FunctionDef(self, node):
        if not (node.name.startswith('__') and node.name.endswith("__")):
            new_name = self.rename(node.name)
            if new_name:
                node.name = new_name

        for arg in node.args.args:
            if arg.arg != "self":
                hashed = self.hashed_random_string()
                self.arguments[arg.arg] = hashed
                arg.arg = hashed

        for decorator in node.decorator_list:
            if type(decorator) == ast.Call:
                unparsed = ast.unparse(decorator.func).split(".")
                new_name = self.rename(unparsed[0])
                if new_name:
                    new = f"{new_name}.{'.'.join(i for i in unparsed[1:])}"
                    decorator.func = ast.Name(id=new)

        for line in node.body:
            self.visit(line)
        return node

    def visit_ClassDef(self, node):
        new_name = self.rename(node.name)
        if new_name:
            node.name = new_name
        for base in node.bases:
            self.visit(base)
        for line in node.body:
            self.visit(line)
        return node


class Control_Flow():
    def __init__(self, content):
        self.new_content = ""
        self.obfuscate(content)

    def indentation(self, s, tabsize=4):
        sx = s.expandtabs(tabsize)
        return 0 if sx.isspace() else len(sx) - len(sx.lstrip())

    def obfuscate(self, content):
        for line in content.splitlines():
            if any(c.isalpha() for c in line) and "#" not in line and line[-1] != ":" and line[0] != "@" and line[0] != '"' and random.randint(0, 1) == 1:
                tab = " "*self.indentation(line)
                linee = textwrap.dedent(line)
                print(line, linee)
                self.new_content += f"{tab}while {str(random.randint(1, 999999))}:" + "\n"
                self.new_content += f"{tab}    if {str(random.randint(1, 999999))}: {linee}; break" + "\n"
                self.new_content += f"{tab}    break" + "\n"

                if random.randint(0, 2) == 1 and any(c.isalpha() for c in line):
                    if random.randint(0, 1) == 1:
                        tab = " "*self.indentation(line)
                        self.new_content += f"{tab}while {str(random.randint(1, 999999))}:" + "\n"
                        e = random.choice(
                            ["exec", "print", "bytes", "compile", "dir", "len", "int", "input", "str", "set"])
                        a = random.choice([f"b'{''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(random.randint(5, 30)))}'.decode()", f"'{''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(random.randint(5, 30)))}'",
                                          f"'{''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(random.randint(5, 10)))} = {''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(random.randint(5, 30)))}'"])
                        real_string = f"{''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(random.randint(5, 10)))} = {e}({a})"
                        self.new_content += f"{tab}    if {str(0)}: {real_string}; break" + "\n"
                        self.new_content += f"{tab}    break" + "\n"
                    else:
                        tab = " "*self.indentation(line)
                        self.new_content += f"{tab}while {str(0)}:" + "\n"
                        e = random.choice(
                            ["exec", "print", "bytes", "compile", "dir", "len", "int", "input", "str", "set"])
                        a = random.choice([f"b'{''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(random.randint(5, 30)))}'.decode()", f"'{''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(random.randint(5, 30)))}'",
                                          f"'{''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(random.randint(5, 10)))} = {''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(random.randint(5, 30)))}'"])
                        real_string = f"{''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(random.randint(5, 10)))} = {e}({a})"
                        self.new_content += f"{tab}    if {str(random.randint(1, 999999))}: {real_string}; break" + "\n"
                        self.new_content += f"{tab}    break" + "\n"
            else:
                self.new_content += line + "\n"


def main(file_path, obfuscate_ast=True, add_control_flow=False):
    obfuscator = Obfuscator()
    with open(file_path, "r", encoding="mbcs") as f:
        content = f.read()
    content = Helpers.add_builtins_and_base64(content, obfuscator)
    if add_control_flow:
        content = Control_Flow(content).new_content
    tree = ast.parse(content, type_comments=True)
    if obfuscate_ast:
        obfuscator.visit(tree)
    content = ast.unparse(tree)
    print(content)
    try:
        import pyperclip
        pyperclip.copy(content)
        print("")
        print("(Copied to Clipboard)")
    except:
        pass


if __name__ == "__main__":
    print("Made by Vinyzu with help from svenskithesource!")
    path = input("Input your PythonFile to Obfuscate: ")
    main(path, True, False)
