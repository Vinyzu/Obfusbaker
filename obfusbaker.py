"""Build standalone, obfuscated Python source."""

import argparse
import ast
import builtins
import io
import itertools
import keyword
import marshal
import random
import re
import sys
import tokenize
import unicodedata
import zlib
from collections import defaultdict
from pathlib import Path
from types import CodeType

from python_minifier import UnstableMinification, unparse as minified_source
from python_minifier.ast_annotation import add_parent, get_parent
from python_minifier.rename import add_namespace
from python_minifier.rename.bind_names import NameBinder
from python_minifier.rename.binding import BuiltinBinding, NameBinding
from python_minifier.rename.util import get_nonlocal_namespace


FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
SUITE_EXITS = (ast.Return, ast.Raise, ast.Break, ast.Continue)
NAMED_BINDINGS = (*FUNCTIONS, ast.ClassDef, ast.ExceptHandler, ast.MatchAs, ast.MatchStar)
DOCSTRING_SCOPES = (ast.Module, ast.ClassDef, *FUNCTIONS)
IDENTIFIER = re.compile(r"[^\W\d]\w*")
BUILTIN_NAMES = frozenset(dir(builtins))
NAMESPACE_BUILTINS = {"exec", "eval", "locals", "globals", "vars"}
FRAME_ATTRIBUTES = {"_getframe", "currentframe", "f_globals", "f_locals"}
IDENTIFIER_STARTS = "𑻠𑻢𑻤𑻧𑻪𑻮𑻱"
IDENTIFIER_MARKS = "𝨗𝨨𝨻𑻵"
MASK_DIGITS = "𘠀𘠁𘠂𘠃𘠄𘠅𘠆𘠇𘠈𘠉𘠊𘠋𘠌𘠍𘠎𘠏"
HEX_DIGITS = "0123456789abcdef"
# Obtain the singleton without looking up a builtin or consulting a class namespace.
NONE_SOURCE = "().__init__()"
# Keep the palette valid on CPython 3.10 even when building on a newer interpreter.
GLYPH_SELECTION = {
    "A": "ᴬ𝒜𝓐𝔄𝕬", "B": "ᴮℬ𝓑𝔅𝔹𝕭", "C": "ℭ𝒞𝓒𝕮", "D": "ᴰⅅ𝒟𝓓𝔇𝕯",
    "E": "ᴱ𝓔𝔈𝕰", "F": "ℱ𝓕𝔉𝕱", "G": "ᴳ𝒢𝓖𝔊𝔾𝕲", "H": "ᴴℋℌ𝓗𝕳",
    "I": "ℐℑ𝓘𝕀𝕴", "J": "𝒥𝓙𝔍𝕁𝕵", "K": "ᴷ𝒦𝓚𝔎𝕶", "L": "ᴸℒ𝓛𝔏𝕃𝕷",
    "M": "ℳ𝓜𝔐𝕄𝕸", "N": "𝒩𝓝𝔑𝕹", "O": "ᴼ𝒪𝓞𝔒𝕺𝙾", "P": "ᴾ𝒫𝓟𝔓𝕻",
    "Q": "𝒬𝓠𝔔𝕼", "R": "ℛℜ𝓡𝕽", "S": "𝒮𝓢𝔖𝕊𝕾", "T": "𝒯𝓣𝔗𝕋𝕿",
    "U": "ᵁ𝒰𝓤𝔘𝖀", "V": "𝒱𝓥𝔙𝖁", "W": "𝐖𝒲𝓦𝔚𝖂𝚆", "X": "𝒳𝓧𝔛𝕏𝖃",
    "Y": "𝒴𝓨𝔜𝕐𝖄", "Z": "ℨ𝒵𝓩𝖅",
    "a": "ª𝒶𝓪𝔞𝖆", "b": "ᵇ𝒷𝓫𝔟𝖇", "c": "𝒸𝓬𝔠𝖈", "d": "𝒹𝓭𝔡𝖉",
    "e": "ᵉⅇ𝓮𝕖𝖊", "f": "𝑓𝒻𝓯𝔣𝖋", "g": "ᵍℊ𝓰𝔤𝖌", "h": "𝒽𝓱𝔥𝖍",
    "i": "ⁱ𝒾𝓲𝔦𝕚𝖎𝙞", "j": "ʲⅉ𝒿𝓳𝕛", "k": "ᵏ𝓀𝓴𝔨𝖐", "l": "ˡℓⅼ𝓁𝓵𝖑",
    "m": "𝓂𝓶𝔪𝖒", "n": "ⁿ𝓃𝓷𝔫𝖓", "o": "ºᵒ𝓸𝔬𝕠𝖔", "p": "ᵖ𝓅𝓹𝔭𝕡𝖕",
    "q": "𝓆𝓺𝔮𝖖", "r": "ʳ𝓇𝓻𝔯𝖗", "s": "ſˢ𝓈𝓼𝔰𝕤", "t": "ᵗ𝓉𝓽𝔱𝖙",
    "u": "ᵘ𝓊𝓾𝔲𝖚", "v": "ᵛ𝓋𝓿𝔳𝖛", "w": "ʷ𝓌𝔀𝔴𝕨𝖜", "x": "𝓍𝔁𝔵𝕩𝖝",
    "y": "𝓎𝔂𝔶𝖞", "z": "𝓏𝔃𝔷𝖟",
    "DZ": "Ǳ", "Dz": "ǲ", "dz": "ǳ", "IJ": "Ĳ", "ij": "ĳ",
    "LJ": "Ǉ", "Lj": "ǈ", "lj": "ǉ", "NJ": "Ǌ", "Nj": "ǋ", "nj": "ǌ",
    "II": "Ⅱ", "III": "Ⅲ", "IV": "Ⅳ", "VI": "Ⅵ", "VII": "Ⅶ", "VIII": "Ⅷ",
    "IX": "Ⅸ", "XI": "Ⅺ", "XII": "Ⅻ",
    "ii": "ⅱ", "iii": "ⅲ", "iv": "ⅳ", "vi": "ⅵ", "vii": "ⅶ", "viii": "ⅷ",
    "ix": "ⅸ", "xi": "ⅺ", "xii": "ⅻ",
    "ff": "ﬀ", "fi": "ﬁ", "fl": "ﬂ", "ffi": "ﬃ", "ffl": "ﬄ", "st": "ﬅﬆ",
    "_": "︳︴﹍﹎﹏＿",
}
MASKED_IDENTIFIER_PARTS = {
    part: tuple(glyph for glyph in glyphs if unicodedata.normalize("NFKC", glyph) == part
                and (("a" + glyph).isidentifier() if part == "_" else glyph.isidentifier()))
    for part, glyphs in GLYPH_SELECTION.items()
}
# Match the longest expansion first. Alternate underscores are only valid after the first character.
IDENTIFIER_PARTS = re.compile("|".join([
    *sorted((part for part, glyphs in MASKED_IDENTIFIER_PARTS.items() if len(part) > 1 and glyphs),
            key=len, reverse=True),
    r"[A-Za-z]",
    r"(?!\A)_",
]))
STRING_OPEN = {"FSTRING_START", "TSTRING_START"}
STRING_CLOSE = {"FSTRING_END", "TSTRING_END"}
BRACE_ESCAPES = re.compile(r"\\\\|\\(?=[{}])")
LITERAL_ESCAPES = re.compile(r"\\(?:[0-7]{1,3}|.|\Z)", re.DOTALL)
COMPARISONS = dict(zip(
    (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn),
    ("==", "!=", "<", "<=", ">", ">=", "is", "is not", "in", "not in"),
))


class HexInteger(int):
    def __repr__(self):
        return hex(self)


def is_docstring(node):
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)


def is_private(name):
    return name.startswith("__") and not name.endswith("__")


def shuffle_order(items, rng):
    # Sattolo's shuffle moves every item in a group of at least two.
    for index in range(len(items) - 1, 0, -1):
        other = rng.randrange(index)
        items[index], items[other] = items[other], items[index]


def has_inert_signature(function):
    args = function.args
    return not (
        function.decorator_list or getattr(function, "type_params", ()) or function.returns is not None
        or args.defaults or any(value is not None for value in args.kw_defaults)
        or any(isinstance(arg, ast.arg) and arg.annotation is not None for arg in ast.iter_child_nodes(args))
    )


def is_direct_call(node):
    parent = get_parent(node)
    return isinstance(parent, ast.Call) and parent.func is node


def negate_condition(test):
    # Only use this where Python already branches on the result. A Boolean
    # expression used as a value can return the original operand object.
    if isinstance(test, ast.BoolOp):
        operator = ast.Or() if isinstance(test.op, ast.And) else ast.And()
        return ast.copy_location(ast.BoolOp(op=operator, values=[negate_condition(value) for value in test.values]), test)
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return test.operand
    return ast.copy_location(ast.UnaryOp(op=ast.Not(), operand=test), test)


class Names:
    def __init__(self, reserved, rng):
        self.reserved = set(reserved)
        first = rng.sample(IDENTIFIER_STARTS, len(IDENTIFIER_STARTS))
        tail = rng.sample(IDENTIFIER_MARKS, len(IDENTIFIER_MARKS))
        self.candidates = (
            "".join(characters)
            for size in itertools.count(2)
            for characters in itertools.product(first, *([tail] * size))
        )

    def take(self, private=False):
        for name in self.candidates:
            if private:
                name = "_" + name
            if name not in self.reserved:
                return name


class Bindings(NameBinder):
    """Index the minifier's lexical bindings by scope and spelling."""

    def __init__(self, module, nodes):
        self.module = module
        self.scopes = defaultdict(dict)
        add_parent(module)
        add_namespace(module)
        self(module)
        for node in nodes:
            self.add_reference(node)

    def get_binding(self, name, scope):
        if name in scope.global_names:
            scope = self.module
        bindings = self.scopes[scope]
        binding = bindings.get(name)
        if binding is None:
            binding = bindings[name] = NameBinding(name)
        if name in BUILTIN_NAMES or isinstance(scope, ast.ClassDef):
            binding.disallow_rename()
        return binding

    def resolve(self, name, scope):
        while scope is not self.module:
            if name in scope.global_names:
                break
            if name not in scope.nonlocal_names:
                binding = self.scopes[scope].get(name)
                if binding is not None:
                    return binding
            scope = get_nonlocal_namespace(scope)

        globals_ = self.scopes[self.module]
        # An assignment to a global can occur after an earlier load has fallen
        # back to the builtin, or can fail to execute at all.
        if name in NAMESPACE_BUILTINS:
            self.module.tainted = True
        binding = globals_.get(name)
        if binding is None:
            if name in BUILTIN_NAMES:
                binding = BuiltinBinding(name, self.module)
            else:
                binding = NameBinding(name)
                binding.disallow_rename()
            globals_[name] = binding
        return binding

    def add_reference(self, node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            self.resolve(node.id, node.namespace).add_reference(node)
            return

        if isinstance(node, ast.Nonlocal):
            for name in node.names:
                self.resolve(name, node.namespace).add_reference(node)
            return

        if isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, NAMED_BINDINGS):
            name = node.name
        elif isinstance(node, ast.MatchMapping):
            name = node.rest
        elif isinstance(node, ast.alias):
            name = node.asname or node.name.partition(".")[0]
        else:
            return

        if name is not None and name in node.namespace.nonlocal_names:
            binding = self.resolve(name, node.namespace)
            binding.add_reference(node)
            if isinstance(node.namespace, ast.ClassDef) or (
                isinstance(node, ast.alias) and node.asname is None and "." in node.name
            ):
                binding.disallow_rename()


def annotation_expressions(node):
    if isinstance(node, (ast.arg, ast.AnnAssign)) and node.annotation is not None:
        yield node.annotation
    if isinstance(node, FUNCTIONS) and node.returns is not None:
        yield node.returns
    type_params = getattr(node, "type_params", ())
    yield from type_params
    if type_params and isinstance(node, ast.ClassDef):
        yield from node.bases
        yield from node.keywords
    if type(node).__name__ == "TypeAlias":
        yield node.value


def observes_dynamic_namespace(nodes):
    builtins_modules = {"__builtins__"}
    for node in nodes:
        if isinstance(node, ast.Import):
            builtins_modules.update(alias.asname or alias.name for alias in node.names if alias.name == "builtins")
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if node.module == "builtins" and any(alias.name in NAMESPACE_BUILTINS for alias in node.names):
                return True
            if node.module in {"sys", "inspect"} and any(alias.name in FRAME_ATTRIBUTES for alias in node.names):
                return True

    for node in nodes:
        if not isinstance(node, ast.Attribute):
            continue
        if node.attr in FRAME_ATTRIBUTES or (
            node.attr in NAMESPACE_BUILTINS and isinstance(node.value, ast.Name) and node.value.id in builtins_modules
        ):
            return True
    return False


def namespace_constraints(nodes):
    """Find names that are also used as source text or in a class namespace."""
    # CPython recognizes the spelling self when collecting class metadata.
    protected = {"self"}
    for node in nodes:
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.isidentifier():
            protected.add(node.value)
        if isinstance(node, ast.AnnAssign) and node.simple and isinstance(node.namespace, ast.Module):
            protected.add(node.target.id)
        if isinstance(node, ast.ClassDef):
            # A class body uses a mapping that a metaclass can populate at runtime.
            # Changing a lookup there could bypass a key in that mapping.
            for name in node.nonlocal_names:
                protected.add(name)
        for annotation in annotation_expressions(node):
            for part in ast.walk(annotation):
                if isinstance(part, ast.Name):
                    protected.add(part.id)
                elif isinstance(part, ast.Constant) and isinstance(part.value, str):
                    protected.update(IDENTIFIER.findall(part.value))
        if type(node).__name__ == "Interpolation":
            protected.update(part.id for part in ast.walk(node.value) if isinstance(part, ast.Name))
    return protected


def has_dynamic_exports(export, nodes):
    if export is None:
        return False

    static_targets = set()
    for node in nodes:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, (ast.Tuple, ast.List)):
            if all(isinstance(item, ast.Constant) and isinstance(item.value, str) for item in node.value.elts):
                static_targets.update(node.targets if isinstance(node, ast.Assign) else [node.target])
    # Computed values and mutations may introduce export names that never appear
    # as literals. Preserve all globals in that case.
    return any(reference not in static_targets for reference in export.references)


def is_simple_class_statement(statement):
    if isinstance(statement, ast.Pass) or is_docstring(statement):
        return True
    if isinstance(statement, FUNCTIONS):
        return not statement.decorator_list
    if isinstance(statement, ast.Assign):
        targets = statement.targets
    elif isinstance(statement, ast.AnnAssign):
        targets = [statement.target]
    else:
        return False
    if any(not isinstance(target, ast.Name) or target.id in {"__qualname__", "__init_subclass__"}
           for target in targets):
        return False
    value = statement.value
    return value is None or all(
        isinstance(node, (ast.Constant, ast.Tuple, ast.List, ast.Load)) for node in ast.walk(value)
    )


def has_private_members(cls):
    for node in ast.walk(cls):
        if isinstance(node, ast.Name):
            spelling = node.id
        elif isinstance(node, ast.Attribute):
            spelling = node.attr
        elif isinstance(node, ast.arg):
            spelling = node.arg
        elif isinstance(node, NAMED_BINDINGS):
            spelling = node.name
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.isidentifier():
            spelling = node.value
        else:
            continue
        if spelling and is_private(spelling):
            return True
    return False


def has_private_slots(cls):
    for statement in cls.body:
        if isinstance(statement, ast.Assign):
            targets = statement.targets
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            targets = [statement.target]
        else:
            continue
        if any(isinstance(target, ast.Name) and target.id == "__slots__" for target in targets):
            if any(isinstance(node, ast.Constant) and isinstance(node.value, str) and is_private(node.value)
                   for node in ast.walk(statement.value)):
                return True
    return False


def class_renaming_candidates(tree, nodes, module_bindings):
    mangled_owners = set()
    for node in nodes:
        if isinstance(node, ast.Attribute):
            spelling = node.attr
        elif isinstance(node, ast.Name):
            spelling = node.id
        elif isinstance(node, ast.keyword):
            spelling = node.arg
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            spelling = node.value
        else:
            continue
        if spelling and spelling.startswith("_") and not spelling.startswith("__"):
            for marker in re.finditer(r"(?=__)", spelling[1:]):
                mangled_owners.add(spelling[1:1 + marker.start()])

    plain_bases = {"object"} if isinstance(module_bindings.get("object"), BuiltinBinding) else set()
    inherited_hooks = any(isinstance(node, ast.Attribute) and node.attr == "__init_subclass__"
                          and not isinstance(node.ctx, ast.Load) for node in nodes)
    reflective_names = {"getattr", "hasattr", "setattr", "delattr", "dir", "vars"}
    reflective_attributes = reflective_names | {"__dict__", "__static_attributes__", "attrgetter"}
    observes_members = any(
        isinstance(node, ast.Name) and node.id in reflective_names
        or isinstance(node, ast.Attribute) and node.attr in reflective_attributes
        for node in nodes
    )
    candidates = set()
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.keywords or getattr(node, "type_params", ()):
            continue
        if any(not isinstance(base, ast.Name) or base.id not in plain_bases for base in node.bases):
            continue
        # A descriptor's __set_name__ must see the original class at creation.
        if not all(is_simple_class_statement(statement) for statement in node.body):
            continue
        if node.name.lstrip("_") not in mangled_owners and not (observes_members and has_private_members(node)):
            candidates.add(node)
        binding = module_bindings[node.name]
        if not inherited_hooks and not node.decorator_list and all(
            reference is node or isinstance(reference, ast.Name) and isinstance(reference.ctx, ast.Load)
            for reference in binding.references
        ) and not any(isinstance(statement, FUNCTIONS) and statement.name == "__init_subclass__" for statement in node.body):
            plain_bases.add(node.name)
    return candidates


def nested_code(code):
    for constant in code.co_consts:
        if isinstance(constant, CodeType):
            yield constant
            yield from nested_code(constant)


def shuffle_local_declarations(scopes, compiled, nodes, rng):
    frames = {}
    for code in nested_code(compiled):
        key = code.co_firstlineno, code.co_name
        # A same-line type alias can share its enclosing function's key.
        frames[key] = None if key in frames else code
    # An interpreter that inlines a comprehension can add slots to its frame.
    inlined_frames = {node.namespace for node in nodes if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp))}
    for scope, bindings in scopes.items():
        # A decorated function's code starts on the decorator line.
        if not isinstance(scope, FUNCTIONS) or scope.decorator_list or scope in inlined_frames:
            continue
        # CPython's fused local loads and stores need both slots below 16.
        frame = frames.get((scope.lineno, scope.name))
        if frame is None or frame.co_nlocals > 16:
            continue
        start = 0
        group = []
        for index, statement in enumerate(scope.body):
            if (isinstance(statement, ast.Assign) and len(statement.targets) == 1
                    and isinstance(statement.value, ast.Constant)):
                target = statement.targets[0]
                name = target.id if isinstance(target, ast.Name) else None
            elif isinstance(statement, FUNCTIONS) and has_inert_signature(statement):
                function = frames.get((statement.lineno, statement.name))
                target = statement
                name = statement.name if function is not None and not function.co_freevars else None
            else:
                name = None

            # Move only unbound fast locals. Keep function objects that can
            # escape in their original frame slots to preserve cleanup order.
            if name is not None and not (name.startswith("_") and "__" in name):
                binding = bindings.get(name)
                if binding is not None and target in binding.references and all(
                    ref is target or (
                        isinstance(ref, ast.Name) and isinstance(ref.ctx, ast.Load) and ref.namespace is scope
                        and (isinstance(target, ast.Name) or is_direct_call(ref))
                    )
                    for ref in binding.references
                ):
                    group.append(statement)
                    continue

            if len(group) > 1:
                shuffle_order(group, rng)
                scope.body[start:index] = group
            group.clear()
            start = index + 1
        if len(group) > 1:
            shuffle_order(group, rng)
            scope.body[start:] = group


def rename_bindings(tree, module_bindings, bindings, nodes, names, rng, keep, keep_globals):
    protected = namespace_constraints(nodes)
    protected.update(keep)
    protected.update(tree.preserved)
    keep_globals = keep_globals or has_dynamic_exports(module_bindings.get("__all__"), nodes)
    class_candidates = class_renaming_candidates(tree, nodes, module_bindings)
    renamed_classes = {}
    builtin_references = set()
    rng.shuffle(bindings)
    for scope, binding in bindings:
        name = binding.name
        if isinstance(binding, BuiltinBinding):
            if name not in protected and name not in {"object", "super"} and not name.startswith("__"):
                builtin_references.update(binding.references)
            continue
        if not binding.allow_rename:
            continue
        if name in protected or (name.startswith("_") and "__" in name) or isinstance(scope, ast.ClassDef):
            continue
        if scope is tree and keep_globals:
            continue
        if any(isinstance(ref, ast.arg) or (isinstance(ref, FUNCTIONS) and ref.decorator_list)
               for ref in binding.references):
            continue
        classes = [ref for ref in binding.references if isinstance(ref, ast.ClassDef)]
        if classes:
            if any(node not in class_candidates for node in classes):
                continue
            for node in classes:
                renamed_classes[node] = node.name
                # Private slot descriptors must use the public class name for copy and pickle.
                if not has_private_slots(node):
                    node.name = names.take(private=True)
            continue
        binding.rename(names.take(private=scope is tree and name.startswith("_")))
    return renamed_classes, builtin_references


def may_use_custom_namespace(node):
    scope = node.namespace
    return isinstance(scope, ast.ClassDef) and (scope.bases or scope.keywords)


class ProtectedSource(ast.NodeTransformer):
    def __init__(self, names, rng, docstrings, renamed_classes, builtin_references, slot_references, native_bootstrap):
        self.names = names
        self.rng = rng
        self.docstrings = docstrings
        self.renamed_classes = renamed_classes
        self.builtin_references = builtin_references
        self.slot_references = slot_references
        self.native_bootstrap = native_bootstrap
        self.values = {}
        self.operators = {}
        self.builtin_lookup = None
        self.byte_decoder = None
        self.digits = None
        self.digit_encoding = None
        self.runtime_modules = defaultdict(list)
        self.module_import = None
        self.import_member = None
        self.pattern_holder = None
        self.pattern_members = {}
        self.getter = None
        self.setter = None
        self.set_value_first = None
        self.class_namer = None
        self.method_publisher = None
        self.class_locals = None
        self.deleter = None
        self.owner = None

    def reference(self, value):
        # Type matters for equal literals such as 1 and 1.0.
        key = type(value), value
        if type(value) is float:
            key = float, value.hex()
        elif type(value) is complex:
            key = complex, value.real.hex(), value.imag.hex()
        if key not in self.values:
            self.values[key] = self.names.take(private=True), value
        return ast.Name(id=self.values[key][0], ctx=ast.Load())

    def visit_Constant(self, node):
        if may_use_custom_namespace(node):
            if node.value is None:
                return ast.copy_location(ast.parse(NONE_SOURCE, mode="eval").body, node)
            if type(node.value) is bool:
                # CPython folds both expressions to booleans without a namespace lookup.
                literal = ast.Constant(value="" if node.value else Ellipsis)
                return ast.copy_location(ast.UnaryOp(op=ast.Not(), operand=literal), node)
            return node
        if type(node.value) in (str, bytes, float, complex, int, bool, type(None), type(Ellipsis)):
            return ast.copy_location(self.reference(node.value), node)
        return node

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Constant):
            if node in self.docstrings:
                return node
            return ast.copy_location(ast.Pass(), node)
        return self.generic_visit(node)

    def import_module(self, path, members=None, level=0):
        if self.module_import is None:
            self.module_import = self.names.take(private=True)
        return ast.Call(func=ast.Name(id=self.module_import, ctx=ast.Load()), args=[
            self.reference(path), self.reference(members), self.reference(level),
        ], keywords=[])

    def import_attribute(self, module, member):
        if self.import_member is None:
            self.import_member = self.names.take(private=True)
        return ast.Call(func=ast.Name(id=self.import_member, ctx=ast.Load()),
                        args=[module, self.reference(member)], keywords=[])

    def visit_Import(self, node):
        if not isinstance(node.namespace, ast.Module) or getattr(node, "is_lazy", False):
            return node
        statements = []
        for alias in node.names:
            root, *parts = alias.name.split(".")
            value = self.import_module(alias.name)
            if alias.asname:
                for part in parts:
                    value = self.import_attribute(value, part)
            target = ast.Name(id=alias.asname or root, ctx=ast.Store())
            statements.append(ast.copy_location(ast.Assign(targets=[target], value=value), node))
        return statements

    def visit_ImportFrom(self, node):
        if (not isinstance(node.namespace, ast.Module) or getattr(node, "is_lazy", False)
                or node.module == "__future__" and not node.level
                or any(alias.name == "*" for alias in node.names)):
            return node
        module = self.import_module(node.module or "", tuple(alias.name for alias in node.names), node.level)
        if len(node.names) == 1:
            alias = node.names[0]
            target = ast.Name(id=alias.asname or alias.name, ctx=ast.Store())
            return ast.copy_location(ast.Assign(targets=[target], value=self.import_attribute(module, alias.name)), node)

        temporary = self.names.take(private=True)
        assign = ast.Assign(targets=[ast.Name(id=temporary, ctx=ast.Store())], value=module)
        statements = []
        for alias in node.names:
            target = ast.Name(id=alias.asname or alias.name, ctx=ast.Store())
            value = self.import_attribute(ast.Name(id=temporary, ctx=ast.Load()), alias.name)
            statements.append(ast.Assign(targets=[target], value=value))
        cleanup = ast.Delete(targets=[ast.Name(id=temporary, ctx=ast.Del())])
        return [assign, ast.Try(body=statements, handlers=[], orelse=[], finalbody=[cleanup])]

    def visit_FunctionDef(self, node):
        # Parameter and return annotations can be observed as source text.
        self.visit(node.args)
        node.decorator_list = [self.visit(decorator) for decorator in node.decorator_list]
        self.visit_suite(node.body)
        tail = node.body[-1]
        if isinstance(tail, ast.Return) and tail.value is None:
            node.body[-1] = ast.copy_location(ast.Pass(), tail)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_arguments(self, node):
        node.defaults = [self.visit(value) for value in node.defaults]
        node.kw_defaults = [self.visit(value) if value is not None else None for value in node.kw_defaults]
        return node

    def visit_AnnAssign(self, node):
        node.target = self.visit(node.target)
        if node.value is not None:
            node.value = self.visit(node.value)
        return node

    def visit_TypeAlias(self, node):
        return node

    def visit_TemplateStr(self, node):
        return node

    def visit_Match(self, node):
        self.generic_visit(node)
        if len(node.cases) < 2:
            return node
        fallback = node.cases[-1]
        pattern = fallback.pattern
        if (fallback.guard is None and isinstance(pattern, ast.MatchAs)
                and pattern.name is None and pattern.pattern is None
                and all(isinstance(case.body[-1], SUITE_EXITS) for case in node.cases[:-1])):
            node.cases.pop()
            return [node, *fallback.body]
        return node

    def visit_match_case(self, node):
        if not may_use_custom_namespace(node):
            for pattern in ast.walk(node.pattern):
                if isinstance(pattern, ast.MatchValue):
                    pattern.value = self.pattern_reference(pattern.value)
                elif isinstance(pattern, ast.MatchMapping):
                    pattern.keys = [self.pattern_reference(key) for key in pattern.keys]
        if node.guard is not None:
            node.guard = self.rewrite_condition(self.visit(node.guard))
        self.visit_suite(node.body)
        return node

    def pattern_reference(self, node):
        if not isinstance(node, (ast.Constant, ast.UnaryOp, ast.BinOp)):
            return node
        value = ast.literal_eval(node)
        if type(value) not in (str, bytes, int, float, complex, bool, type(None)):
            return node

        # Value patterns and mapping keys can use dotted names. Singleton
        # patterns keep their native identity checks.
        if self.pattern_holder is None:
            self.pattern_holder = self.names.take(private=True)
        name = self.reference(value).id
        self.pattern_members[name] = None
        return ast.copy_location(ast.Attribute(
            value=ast.Name(id=self.pattern_holder, ctx=ast.Load()), attr=name, ctx=ast.Load(),
        ), node)

    def visit_suite(self, body):
        rewritten = []
        for statement in body:
            result = self.visit(statement)
            rewritten.extend(result if isinstance(result, list) else [result])
        if len(rewritten) >= 2 and isinstance(rewritten[-1], SUITE_EXITS):
            guard = rewritten[-2]
            if (isinstance(guard, ast.If) and not guard.orelse and isinstance(guard.body[-1], SUITE_EXITS)
                    and not (guard.namespace.global_names or guard.namespace.nonlocal_names)
                    and self.can_swap_branches(guard.body, [rewritten[-1]])
                    and self.rng.randrange(2)):
                # Both paths end here. Put the fallthrough path behind the guard.
                guard.test = negate_condition(guard.test)
                fallthrough = rewritten.pop()
                rewritten.extend(guard.body)
                guard.body = [fallthrough]
        body[:] = rewritten

    def visit_JoinedStr(self, node):
        if may_use_custom_namespace(node):
            return node
        # Leave format-spec literals in place. Adding another replacement field
        # there can exceed Python's nesting limit for format specifications.
        node.values = [
            ast.copy_location(
                ast.FormattedValue(value=self.reference(part.value), conversion=-1), part
            )
            if isinstance(part, ast.Constant)
            else self.visit(part)
            for part in node.values
        ]
        return node

    def visit_FormattedValue(self, node):
        node.value = self.visit(node.value)
        if node.format_spec is not None:
            for part in node.format_spec.values:
                if isinstance(part, ast.FormattedValue):
                    self.visit(part)
        return node

    def visit_ClassDef(self, node):
        # Generic headers are evaluated in a separate annotation scope with
        # different private-name mangling rules from the containing class.
        if not getattr(node, "type_params", ()):
            node.bases = [self.visit(base) for base in node.bases]
            node.keywords = [self.visit(keyword) for keyword in node.keywords]
        node.decorator_list = [self.visit(decorator) for decorator in node.decorator_list]
        original = self.renamed_classes.get(node)
        previous_owner = self.owner
        self.owner = node.name
        try:
            self.visit_suite(node.body)
            if original is not None:
                node.body = self.rename_methods(node.body, original)
        finally:
            self.owner = previous_owner
        if original is not None and node.name != original:
            if self.class_namer is None:
                self.class_namer = self.names.take(private=True)
            if self.setter is None:
                self.setter = self.names.take(private=True)
            node.decorator_list.append(ast.Call(
                func=ast.Name(id=self.class_namer, ctx=ast.Load()),
                args=[self.reference(original), self.reference("__name__"), self.reference("__qualname__")],
                keywords=[],
            ))
            if "__qualname__" in node.nonlocal_names:
                index = int(bool(node.body and is_docstring(node.body[0])))
                node.body.insert(index, ast.Assign(
                    targets=[ast.Name(id="__qualname__", ctx=ast.Store())], value=self.reference(original),
                ))
            # Store the finished class under the name used by its restored qualname.
            publish = ast.Assign(
                targets=[ast.Name(id=original, ctx=ast.Store())], value=ast.Name(id=node.name, ctx=ast.Load()),
            )
            cleanup = ast.Delete(targets=[ast.Name(id=node.name, ctx=ast.Del())])
            return [node, ast.copy_location(publish, node), ast.copy_location(cleanup, node)]
        return node

    def rename_methods(self, body, owner):
        statements = []
        methods = []
        publication = []

        def flush_methods():
            # Shuffle the private declarations and preserve the insertion order
            # of the final keys in the class namespace.
            shuffle_order(methods, self.rng)
            statements.extend(methods)
            statements.extend(publication)
            methods.clear()
            publication.clear()

        for statement in body:
            if (not isinstance(statement, FUNCTIONS) or getattr(statement, "type_params", ())
                    or (statement.name.startswith("__") and statement.name.endswith("__"))):
                flush_methods()
                statements.append(statement)
                continue
            publish = self.publish_method(statement, owner)
            if has_inert_signature(statement):
                methods.append(statement)
                publication.extend(publish)
            else:
                flush_methods()
                statements.extend([statement, *publish])
        flush_methods()
        return statements

    def publish_method(self, method, owner):
        original = method.name
        if self.method_publisher is None:
            self.method_publisher = self.names.take(private=True)
            self.class_locals = self.names.take(private=True)
        method.name = self.names.take(private=True)
        namespace = ast.Call(func=ast.Name(id=self.class_locals, ctx=ast.Load()), args=[], keywords=[])
        publish = ast.Call(
            func=ast.Name(id=self.method_publisher, ctx=ast.Load()),
            args=[namespace, self.attribute_name(original), ast.Name(id=method.name, ctx=ast.Load()),
                  self.reference(original), self.reference(f"{owner}.{original}")],
            keywords=[],
        )
        return ast.Expr(value=publish), ast.Delete(targets=[ast.Name(id=method.name, ctx=ast.Del())])

    def get_attribute(self, receiver, name):
        if self.getter is None:
            self.getter = self.names.take(private=True)
        return ast.Call(func=ast.Name(id=self.getter, ctx=ast.Load()), args=[receiver, name], keywords=[])

    def visit_Name(self, node):
        if node not in self.builtin_references or isinstance(node.namespace, ast.ClassDef):
            return node
        if self.builtin_lookup is None:
            self.builtin_lookup = self.names.take(private=True)
        call = ast.Call(func=ast.Name(id=self.builtin_lookup, ctx=ast.Load()),
                        args=[self.reference(node.id)], keywords=[])
        return ast.copy_location(call, node)

    def operation(self, symbol, left, right):
        if symbol not in self.operators:
            self.operators[symbol] = self.names.take(private=True)
        return ast.Call(func=ast.Name(id=self.operators[symbol], ctx=ast.Load()), args=[left, right], keywords=[])

    def visit_Compare(self, node):
        self.generic_visit(node)
        if len(node.ops) != 1 or may_use_custom_namespace(node):
            return node
        symbol = COMPARISONS[type(node.ops[0])]
        return ast.copy_location(self.operation(symbol, node.left, node.comparators[0]), node)

    def rewrite_condition(self, test):
        if isinstance(test, ast.BoolOp) and self.rng.randrange(2):
            return ast.copy_location(ast.UnaryOp(op=ast.Not(), operand=negate_condition(test)), test)
        return test

    def can_swap_branches(self, left, right):
        # Even a load can set the compiler's local slot order. Moving a slot
        # can change the order in which the frame releases its references.
        return not any(
            part in self.slot_references
            or (isinstance(part, ast.Name) and part.id.startswith("_") and "__" in part.id)
            for branch in (left, right) for node in branch for part in ast.walk(node)
        )

    def visit_If(self, node):
        self.generic_visit(node)
        if (node.orelse and not (node.namespace.global_names or node.namespace.nonlocal_names)
                and not isinstance(node.body[-1], SUITE_EXITS)
                and self.can_swap_branches(node.body, node.orelse)
                and (isinstance(node.orelse[-1], SUITE_EXITS) or self.rng.randrange(2))):
            node.test = negate_condition(node.test)
            node.body, node.orelse = node.orelse, node.body
        else:
            node.test = self.rewrite_condition(node.test)
        if node.orelse and isinstance(node.body[-1], SUITE_EXITS):
            following, node.orelse = node.orelse, []
            return [node, *following]
        return node

    def visit_IfExp(self, node):
        self.generic_visit(node)
        if self.can_swap_branches([node.body], [node.orelse]) and self.rng.randrange(2):
            node.test = negate_condition(node.test)
            node.body, node.orelse = node.orelse, node.body
        return node

    def visit_While(self, node):
        self.generic_visit(node)
        node.test = self.rewrite_condition(node.test)
        return node

    def visit_comprehension(self, node):
        self.generic_visit(node)
        node.ifs = [self.rewrite_condition(test) for test in node.ifs]
        return node

    def attribute_name(self, spelling):
        if self.owner and is_private(spelling) and self.owner.lstrip("_"):
            spelling = f"_{self.owner.lstrip('_')}{spelling}"
        return self.reference(spelling)

    def visit_Attribute(self, node):
        node.value = self.visit(node.value)
        if not isinstance(node.ctx, ast.Load) or may_use_custom_namespace(node):
            return node
        call = self.get_attribute(node.value, self.attribute_name(node.attr))
        return ast.copy_location(call, node)

    def visit_Assign(self, node):
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Attribute):
            return self.generic_visit(node)

        target = node.targets[0]
        if may_use_custom_namespace(node) or (
            self.owner and isinstance(target.value, ast.Name) and target.value.id == "self"
        ):
            # CPython uses direct self.attr stores to build __static_attributes__.
            return self.generic_visit(node)

        node.value = self.visit(node.value)
        name = self.attribute_name(target.attr)
        if self.setter is None:
            self.setter = self.names.take(private=True)
        if self.set_value_first is None:
            self.set_value_first = self.names.take(private=True)
        # An assignment evaluates the right-hand side before the receiver.
        call = ast.Call(
            func=ast.Name(id=self.set_value_first, ctx=ast.Load()),
            args=[node.value, self.visit(target.value), name],
            keywords=[],
        )
        return ast.copy_location(ast.Expr(value=call), node)

    def visit_Delete(self, node):
        if (len(node.targets) != 1 or not isinstance(node.targets[0], ast.Attribute)
                or may_use_custom_namespace(node)):
            return self.generic_visit(node)

        target = node.targets[0]
        if self.deleter is None:
            self.deleter = self.names.take(private=True)
        call = ast.Call(
            func=ast.Name(id=self.deleter, ctx=ast.Load()),
            args=[self.visit(target.value), self.attribute_name(target.attr)],
            keywords=[],
        )
        return ast.copy_location(ast.Expr(value=call), node)

    def prelude(self):
        lines = []
        if self.values:
            lines.extend(self.pool_source())

        if self.pattern_holder:
            members = ",".join(f"{unicodedata.normalize('NFKC', name)!r}:{name}" for name in self.pattern_members)
            lines.append(f"{self.pattern_holder}=().__class__.__class__({self.pattern_holder!r},(),{{{members}}})")
        if self.getter:
            self.runtime_member("builtins", "getattr", self.getter)
        if self.builtin_lookup:
            lines.extend(self.builtin_source())
        if self.module_import:
            lines.extend(self.module_import_source())
        if self.import_member:
            lines.extend(self.import_member_source())
        if self.deleter:
            self.runtime_member("builtins", "delattr", self.deleter)
        if self.setter:
            self.runtime_member("builtins", "setattr", self.setter)
        if self.class_namer:
            spelling, name, qualname, cls = (self.names.take() for _ in range(4))
            lines.append(f"{self.class_namer}=lambda {spelling},{name},{qualname}: lambda {cls}: "
                         f"({self.setter}({cls},{name},{spelling}),{self.setter}({cls},{qualname},{spelling}),{cls})"
                         "[~().__len__()]")
        if self.method_publisher:
            namespace, key, method, name, qualname = (self.names.take() for _ in range(5))
            self.runtime_member("builtins", "locals", self.class_locals)
            lines.append(f"def {self.method_publisher}({namespace},{key},{method},{name},{qualname}):\n"
                         f"    {method}.__name__={name}\n"
                         f"    {method}.__qualname__={qualname}\n"
                         f"    {namespace}[{key}]={method}")
        if self.set_value_first:
            value, receiver, attribute = (self.names.take() for _ in range(3))
            lines.append(f"{self.set_value_first}=lambda {value},{receiver},{attribute}: "
                         f"{self.setter}({receiver},{attribute},{value})")
        operators = list(self.operators.items())
        shuffle_order(operators, self.rng)
        for symbol, alias in operators:
            left, right = self.names.take(), self.names.take()
            lines.append(f"{alias}=lambda {left},{right}: {left} {symbol} {right}")
        runtime = self.runtime_source()
        if self.byte_decoder:
            lines.append(f"del {self.byte_decoder}")
        return ast.parse("\n".join(self.decoder_source() + runtime + lines)).body

    def runtime_member(self, path, member, target=None):
        members = self.runtime_modules[path]
        if target is None:
            for existing_member, alias in members:
                if existing_member == member:
                    return alias
            target = self.names.take(private=True)
        members.append((member, target))
        return target

    def runtime_source(self):
        if not self.runtime_modules:
            return []
        importer, namespace, module_globals, module_locals = (self.names.take(private=True) for _ in range(4))
        if self.native_bootstrap:
            lines = [f"from builtins import __import__ as {importer}, globals as {module_globals}, locals as {module_locals}",
                     f"{module_globals},{module_locals}={module_globals}(),{module_locals}()"]
            cleanup = [importer, module_globals, module_locals]
        else:
            key = self.bootstrap_text("__import__")
            lines = [f"{namespace}=__builtins__",
                     f"try: {importer}={namespace}[{key}]",
                     f"except TypeError: {namespace}={namespace}.__dict__;{importer}={namespace}[{key}]",
                     f"{module_globals}={namespace}[{self.bootstrap_text('globals')}]()",
                     f"{module_locals}={namespace}[{self.bootstrap_text('locals')}]()"]
            cleanup = [importer, namespace, module_globals, module_locals]
        module = self.names.take(private=True)
        get = self.names.take(private=True)
        import_args = f"{module_globals},{module_locals},{NONE_SOURCE},().__len__()"
        lines.append(f"{module}={importer}({self.bootstrap_text('builtins')},{import_args})")
        lines.append(f"{get}={module}.__dict__[{self.bootstrap_text('getattr')}]")
        lines.extend(f"{target}={get}({module},{self.bootstrap_text(member)})"
                     for member, target in self.runtime_modules["builtins"])
        for path, members in self.runtime_modules.items():
            if path != "builtins":
                lines.append(f"{module}={importer}({self.bootstrap_text(path)},{import_args})")
                lines.extend(f"{target}={get}({module},{self.bootstrap_text(member)})" for member, target in members)
        lines.append("del " + ",".join([*cleanup, module, get]))
        return lines

    def bootstrap_text(self, text):
        return f"{self.mask_bytes(text.encode('ascii'))}.decode()"

    def mask_bytes(self, data):
        if self.byte_decoder is None:
            self.byte_decoder = self.names.take(private=True)
            self.digits = "".join(self.rng.sample(MASK_DIGITS, len(MASK_DIGITS)))
            self.digit_encoding = str.maketrans(HEX_DIGITS, self.digits)
        mask = self.rng.getrandbits(len(data) * 8)
        masked = int.from_bytes(data, "big") ^ mask
        fields = ",".join(repr(format(value, "x").translate(self.digit_encoding))
                          for value in (masked, mask, len(data)))
        return f"{self.byte_decoder}({fields})"

    def decoder_source(self):
        if self.byte_decoder is None:
            return []
        data, mask, size, table, integer, radix = (self.names.take() for _ in range(6))
        return [
            f"{self.byte_decoder}=lambda {data},{mask},{size},"
            f"{table}=''.maketrans({self.digits!r},{HEX_DIGITS!r}),"
            f"{integer}=().__len__().__class__,{radix}={self.digits!r}.__len__():"
            f"({integer}({data}.translate({table}),{radix})^{integer}({mask}.translate({table}),{radix}))"
            f".to_bytes({integer}({size}.translate({table}),{radix}),'big')",
        ]

    def module_import_source(self):
        frame = self.runtime_member("sys", "_getframe")
        missing_key = self.runtime_member("builtins", "KeyError")
        missing_import = self.runtime_member("builtins", "ImportError")
        base_error = self.runtime_member("builtins", "BaseException")
        path, members, level, caller, importer, key, set_cause = (self.names.take() for _ in range(7))
        defaults = ",".join(f"{alias}={alias}" for alias in (frame, missing_key, missing_import))
        missing_import_error = f"{missing_import}('__import__ not found')"
        return [f"def {self.module_import}({path},{members},{level},{defaults},"
                f"{key}={self.bootstrap_text('__import__')},{set_cause}={base_error}.__cause__.__set__):\n"
                f"    {caller}={frame}(((),).__len__())\n"
                f"    try: {importer}={caller}.f_builtins[{key}]\n"
                f"{self.suppressed_raise(missing_key, missing_import_error, set_cause)}\n"
                f"    return {importer}({path},{caller}.f_globals,{caller}.f_locals,{members},{level})"]

    def import_member_source(self):
        get = self.runtime_member("builtins", "getattr")
        missing_attribute = self.runtime_member("builtins", "AttributeError")
        missing_import = self.runtime_member("builtins", "ImportError")
        is_instance = self.runtime_member("builtins", "isinstance")
        modules = self.runtime_member("sys", "modules")
        module, member, name, candidate, path = (self.names.take() for _ in range(5))
        defaults = ",".join(f"{alias}={alias}" for alias in (get, missing_attribute, missing_import, is_instance, modules))
        return [f"def {self.import_member}({module},{member},{defaults}):\n"
                f"    try: return {get}({module},{member})\n"
                f"    except {missing_attribute}: pass\n"
                f"    {name}={get}({module},'__name__',{NONE_SOURCE})\n"
                f"    {candidate}=''.join(({name},'.',{member})) if {is_instance}({name},''.__class__) "
                f"else {NONE_SOURCE}\n"
                f"    if {candidate} is not {NONE_SOURCE} and {candidate} in {modules}: return {modules}[{candidate}]\n"
                f"    {path}={get}({module},'__file__',{NONE_SOURCE})\n"
                f"    raise {missing_import}('cannot import name %r from %r (%s)' % "
                f"({member},{name},{path} or 'unknown location'),name={name},path={path})"]

    def builtin_source(self):
        get_frame = self.runtime_member("sys", "_getframe")
        missing_key = self.runtime_member("builtins", "KeyError")
        missing_name = self.runtime_member("builtins", "NameError")
        base_error = self.runtime_member("builtins", "BaseException")
        frame, module, primitives = (self.names.take(private=True) for _ in range(3))
        key, set_cause = (self.names.take() for _ in range(2))
        defaults = ",".join(f"{alias}={alias}" for alias in (module, primitives, missing_key, missing_name))
        missing_name_error = f"{missing_name}('name %r is not defined' % {key},name={key})"
        return [
            f"{frame}={get_frame}()",
            f"{module},{primitives}={frame}.f_globals,{frame}.f_builtins",
            f"del {frame}",
            f"def {self.builtin_lookup}({key},{defaults},{set_cause}={base_error}.__cause__.__set__):\n"
            f"    if {key} in {module}: return {module}[{key}]\n"
            f"    try: return {primitives}[{key}]",
            self.suppressed_raise(missing_key, missing_name_error, set_cause),
        ]

    def suppressed_raise(self, caught, constructor, set_cause):
        # Use the BaseException descriptor so subclass hooks cannot intercept the cause assignment.
        error = self.names.take()
        return (f"    except {caught}:\n"
                f"        {error}={constructor}\n"
                f"        {set_cause}({error},{NONE_SOURCE})\n"
                f"        raise {error}")

    def pool_source(self):
        items = list(self.values.values())
        self.rng.shuffle(items)
        groups = min(6, max(1, len(items) // 7))
        group_size = (len(items) + groups - 1) // groups
        load = self.runtime_member("marshal", "loads")
        lines = []
        cleanup = [load]
        inflate = None
        for offset in range(0, len(items), group_size):
            chunk = items[offset:offset + group_size]
            targets = ",".join(name for name, _ in chunk) + ","
            # Format 2 stores binary numbers but omits reference flags that can
            # depend on how many other objects hold the same literal in the builder.
            payload = marshal.dumps(tuple(value for _, value in chunk), 2)
            compressed = zlib.compress(payload, level=1)
            use_compression = len(compressed) + 16 < len(payload)
            if use_compression:
                payload = compressed
                if inflate is None:
                    inflate = self.runtime_member("zlib", "decompress")
                    cleanup.append(inflate)
            data = self.mask_bytes(payload)
            if use_compression:
                data = f"{inflate}({data})"
            lines.append(f"{targets}={load}({data})")
        lines.append("del " + ",".join(cleanup))
        return lines


def add_prelude(tree, statements):
    index = 0
    if tree.body and is_docstring(tree.body[0]):
        index = 1
    while index < len(tree.body):
        statement = tree.body[index]
        if not isinstance(statement, ast.ImportFrom) or statement.module != "__future__" or statement.level:
            break
        index += 1
    tree.body[index:index] = statements


def escape_text(value):
    parts = ['"']
    for character in value:
        code = ord(character)
        if code <= 0xFF:
            parts.append(f"\\x{code:02x}")
        elif code <= 0xFFFF:
            parts.append(f"\\u{code:04x}")
        else:
            parts.append(f"\\U{code:08x}")
    parts.append('"')
    return "".join(parts)


def restore_keyword_spellings(tree):
    # The parser normalizes a name like 𝖎𝖋 to "if". Restore a valid source spelling.
    keyword_names = {name: MASKED_IDENTIFIER_PARTS[name[0]][0] + name[1:] for name in keyword.kwlist}
    identifier_fields = {"id", "name", "arg", "attr", "asname", "module", "rest"}

    def spelling(name):
        return ".".join(keyword_names.get(part, part) for part in name.split("."))

    originals = []
    for node in ast.walk(tree):
        for field, value in ast.iter_fields(node):
            if field in identifier_fields and isinstance(value, str):
                replacement = spelling(value)
            elif field == "kwd_attrs" or (field == "names" and isinstance(node, (ast.Global, ast.Nonlocal))):
                replacement = [spelling(name) for name in value]
            else:
                continue
            if replacement != value:
                originals.append((node, field, value))
                setattr(node, field, replacement)
    return originals


def unparse_source(tree):
    restore_keyword_spellings(tree)
    return ast.unparse(tree)


def brace_safe_tokens(source):
    # The lexer itself can warn on "\{" before it yields the opening brace.
    # Replacing only that backslash keeps the offsets usable on the original text.
    shadow = BRACE_ESCAPES.sub(lambda match: " " if match[0] == "\\" else match[0], source)
    return tokenize.generate_tokens(io.StringIO(shadow).readline)


def normalize_literal_escapes(text, is_bytes):
    valid = "\\'\"abfnrtvx\n\r" + ("" if is_bytes else "NuU")

    def replace(match):
        escape = match[0][1:]
        if escape and escape[0] in "01234567":
            value = int(escape, 8)
            if value > 255:
                return f"\\x{value & 255:02x}" if is_bytes else f"\\u{value:04x}"
        elif not escape or (escape.isascii() and escape not in valid):
            return "\\" + match[0]
        return match[0]

    return LITERAL_ESCAPES.sub(replace, text)


def template_validation_source(source):
    """Normalize warning-producing escapes in a copy used only for validation."""
    offsets = list(itertools.accumulate((len(line) + 1 for line in source.split("\n")), initial=0))
    raw_strings = []
    edits = []
    for token in brace_safe_tokens(source):
        kind = tokenize.tok_name[token.type]
        if kind == "STRING" or kind in STRING_OPEN:
            prefix = re.match(r"[A-Za-z]*", token.string)[0].lower()
            if kind in STRING_OPEN:
                raw_strings.append("r" in prefix)
                continue
            if "r" in prefix:
                continue
            is_bytes = "b" in prefix
        elif kind in STRING_CLOSE:
            raw_strings.pop()
            continue
        elif kind in {"FSTRING_MIDDLE", "TSTRING_MIDDLE"} and not raw_strings[-1]:
            is_bytes = False
        else:
            continue

        start = offsets[token.start[0] - 1] + token.start[1]
        end = offsets[token.end[0] - 1] + token.end[1]
        literal = source[start:end]
        replacement = normalize_literal_escapes(literal, is_bytes)
        if replacement != literal:
            edits.append((start, end, replacement))
    return apply_source_edits(source, edits)


def apply_source_edits(source, edits):
    parts = []
    offset = 0
    for start, end, replacement in sorted(edits):
        parts.extend((source[offset:start], replacement))
        offset = end
    parts.append(source[offset:])
    return "".join(parts)


def mask_layout(source, rng, indent_masking=True, *, soft_keywords=frozenset(keyword.softkwlist), template_escapes=False):
    """Edit token boundaries so string contents and Python syntax stay intact."""
    lengths = (len(line) + 1 for line in source.split("\n"))
    offsets = list(itertools.accumulate(lengths, initial=0))
    indentation = [0]
    first = True
    padded = False
    string_depth = 0
    previous = None
    edits = []
    tokens = brace_safe_tokens(source) if template_escapes else tokenize.generate_tokens(io.StringIO(source).readline)
    for token in tokens:
        kind = tokenize.tok_name[token.type]
        if string_depth:
            if kind in STRING_OPEN:
                string_depth += 1
            if kind in STRING_CLOSE:
                string_depth -= 1
            continue
        if kind == "INDENT":
            indentation.append(indentation[-1] + rng.randint(1, 17))
            continue
        if kind == "DEDENT":
            indentation.pop()
            continue
        if kind == "NEWLINE":
            first, padded = True, False
        if kind in {"NEWLINE", "NL", "ENDMARKER", "COMMENT"}:
            previous = None
            continue

        row, column = token.start
        start = offsets[row - 1] + column
        end = offsets[token.end[0] - 1] + token.end[1]
        if first and column:
            width = indentation[-1] if indent_masking else 4 * (len(indentation) - 1)
            edits.append((offsets[row - 1], start, " " * width))
        first = False

        if kind in STRING_OPEN:
            string_depth = 1
            previous = None
            continue
        if not padded and previous and previous.end[0] == row:
            previous_kind = tokenize.tok_name[previous.type]
            if previous_kind == "NAME" and kind in {"NAME", "OP", "NUMBER", "STRING"}:
                # Keep the glyph choices identical for the same seed in both layouts.
                width = rng.randint(700, 8500)
                if indent_masking:
                    boundary = offsets[row - 1] + previous.end[1]
                    edits.append((boundary, boundary, " " * width))
                padded = True

        spelling = token.string
        if kind == "NAME" and spelling == "pass":
            edits.append((start, end, "..."))
        elif kind == "NAME" and spelling.isascii() and not keyword.iskeyword(spelling) and spelling not in soft_keywords:
            glyphs = IDENTIFIER_PARTS.sub(lambda match: rng.choice(MASKED_IDENTIFIER_PARTS[match[0]]), spelling)
            if glyphs != spelling:
                edits.append((start, end, glyphs))
        elif kind == "STRING" and spelling.startswith(('"', "'")) and (
            spelling.isascii() or spelling.startswith(('"""', "'''"))
        ):
            edits.append((start, end, escape_text(ast.literal_eval(spelling))))
        previous = token

    return apply_source_edits(source, edits)


def obfuscate(source, *, seed=None, keep=(), keep_globals=False, indent_masking=True, filename="<source>"):
    """Return standalone Python source built from a string or Python source bytes."""
    tree = ast.parse(source, filename=filename)
    try:
        compiled = compile(tree, filename, "exec", dont_inherit=True)
    except ValueError:
        # Older parsers accept some Unicode names that their AST validator rejects.
        originals = restore_keyword_spellings(tree)
        try:
            compiled = compile(tree, filename, "exec", dont_inherit=True)
        finally:
            for node, field, value in originals:
                setattr(node, field, value)
    rng = random.Random(seed)
    nodes = list(ast.walk(tree))
    observes_namespace = observes_dynamic_namespace(nodes)
    if not observes_namespace:
        scopes = Bindings(tree, nodes).scopes
        observes_namespace = tree.tainted

    if not observes_namespace:
        if not any(isinstance(node, ast.Attribute) and node.attr == "co_varnames"
                   or isinstance(node, ast.Constant) and node.value == "co_varnames" for node in nodes):
            shuffle_local_declarations(scopes, compiled, nodes, rng)
        del compiled
        bindings = [(scope, binding) for scope, indexed in scopes.items() for binding in indexed.values()]
        slot_references = {
            ref for scope, binding in bindings
            if not isinstance(scope, (ast.Module, ast.ClassDef))
            and not any(isinstance(ref, ast.arg) for ref in binding.references)
            for ref in binding.references
        }
        names = Names(itertools.chain(BUILTIN_NAMES, (binding.name for _, binding in bindings)), rng)
        renamed_classes, builtin_references = rename_bindings(
            tree, scopes[tree], bindings, nodes, names, rng, keep, keep_globals,
        )
        docstrings = {
            node.body[0]
            for node in nodes
            if isinstance(node, DOCSTRING_SCOPES) and node.body and is_docstring(node.body[0])
        }
        native_bootstrap = any(
            isinstance(node, ast.ImportFrom) and node.module == "__future__" and node.level == 0
            and any(alias.asname in {"__builtins__", "TypeError"} for alias in node.names)
            for node in tree.body
        )
        transform = ProtectedSource(
            names, rng, docstrings, renamed_classes, builtin_references, slot_references, native_bootstrap,
        )
        transform.visit(tree)
        add_prelude(tree, transform.prelude())

    soft_keywords = set()
    for node in nodes:
        # ast.unparse normally uses decimal, which may be rejected by Python's
        # integer digit limit even though the original hexadecimal input was valid.
        if isinstance(node, ast.Constant) and type(node.value) is int and node.value.bit_length() >= 2048:
            node.value = HexInteger(node.value)
        elif isinstance(node, ast.Match):
            soft_keywords.update(("match", "case"))
        elif type(node).__name__ == "TypeAlias":
            soft_keywords.add("type")
        elif isinstance(node, (ast.Import, ast.ImportFrom)) and getattr(node, "is_lazy", False):
            soft_keywords.add("lazy")
    ast.fix_missing_locations(tree)
    template_escapes = False
    if any(type(node).__name__ == "TemplateStr" for node in nodes):
        # Template interpolations expose their original expression text. The
        # compact printer can change its spacing while preserving the rest of the AST.
        result = unparse_source(tree)
        template_escapes = any(
            type(node).__name__ == "Interpolation" and node.str and "\\" in node.str for node in nodes
        )
    else:
        try:
            result = minified_source(tree, prefer_single_line=True)
        except UnstableMinification:
            result = unparse_source(tree)
    result = mask_layout(
        result + "\n", rng, indent_masking=indent_masking, soft_keywords=soft_keywords, template_escapes=template_escapes,
    )
    validation_source = template_validation_source(result) if template_escapes else result
    compile(validation_source, filename, "exec", dont_inherit=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, help="Python input file")
    parser.add_argument("-o", "--output", type=Path, default=Path("obfuscated.py"))
    parser.add_argument("--no-indent", action="store_true", help="skip irregular indentation and horizontal padding")
    parser.add_argument("--seed", type=int, help="reproduce a build")
    parser.add_argument("--keep", action="append", default=[], metavar="NAME", help="preserve a name")
    parser.add_argument("--keep-globals", action="store_true", help="preserve module-level names")
    args = parser.parse_args(argv)
    source = args.source
    if source is None:
        try:
            entered_path = input("Input a filepath or leave empty for the default input: ")
        except EOFError:
            entered_path = ""
        source = Path(entered_path or "to_obfuscate.py")
        if not entered_path and not source.is_file():
            source = Path(__file__).resolve().parent / "examples" / "nqueens" / "source.py"

    try:
        if source.resolve() == args.output.resolve() or (args.output.exists() and source.samefile(args.output)):
            parser.error("input and output must be different files")
        data = source.read_bytes()
        encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
        text = data.decode(encoding)
        output = obfuscate(
            text, seed=args.seed, keep=args.keep,
            keep_globals=args.keep_globals, indent_masking=not args.no_indent,
            filename=str(source),
        )
        if text.startswith("#!"):
            output = text.splitlines()[0] + "\n" + output
        args.output.write_text(output, encoding="utf-8")
    except (OSError, SyntaxError, UnicodeError, ValueError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
