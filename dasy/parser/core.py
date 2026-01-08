from typing import Set
import dasy
import vyper.ast.nodes as vy_nodes
from .utils import build_node, next_nodeid, pairwise
from hy import models

from .utils import has_return, process_body
from dasy.exceptions import (
    DasySyntaxError,
    DasyTypeError,
)


def parse_attribute(expr):
    """Parses an attribute and builds a node."""
    if len(expr) < 3:
        raise DasySyntaxError("Expression too short to parse attribute.")

    # If we have more than 3 elements, it's a method call
    if len(expr) > 3:
        # Transform (. obj method args...) to ((. obj method) args...)
        _, obj, attr, *args = expr
        attr_node = build_node(
            vy_nodes.Attribute, attr=str(attr), value=dasy.parser.parse_node_legacy(obj)
        )
        # Create a call node with the attribute as the function
        args_list = [dasy.parser.parse_node_legacy(arg) for arg in args]
        call_node = build_node(
            vy_nodes.Call, func=attr_node, args=args_list, keywords=[]
        )
        return call_node

    # For exactly 3 elements: (. obj attr)
    # Check if this should be a function call or attribute access
    _, obj, attr = expr
    attr_node = build_node(
        vy_nodes.Attribute, attr=str(attr), value=dasy.parser.parse_node_legacy(obj)
    )

    # If obj is an interface constructor call, treat this as a zero-argument method call
    if isinstance(obj, models.Expression) and len(obj) == 2:
        # Check if it looks like (Interface address)
        if isinstance(obj[0], models.Symbol):
            # TODO: EDGE CASE BUG - This heuristic may incorrectly detect non-interface
            # expressions as interface constructors. Examples that would break:
            # (. (get-contract addr) property) - function call returning struct
            # (. (cast SomeType val) field) - type casting
            # (. (self.array idx) attr) - array access
            # Need better detection logic, perhaps checking if first symbol is
            # actually an interface type name, or using explicit syntax.
            # This could be an interface constructor - create a function call
            call_node = build_node(vy_nodes.Call, func=attr_node, args=[], keywords=[])
            return call_node

    # Otherwise, standard attribute access
    return attr_node


def parse_tuple(tuple_tree):
    elements = []
    if tuple_tree[0] == models.Symbol("quote"):
        elements = tuple_tree[1]
    elif tuple_tree[0] == models.Symbol("tuple"):
        elements = tuple_tree[1:]
    else:
        raise DasySyntaxError("Invalid tuple declaration")
    return build_node(
        vy_nodes.Tuple, elements=[dasy.parser.parse_node_legacy(e) for e in elements]
    )


def parse_quote(expr):
    """Support (quote ...) without relying on ALIASES.

    Delegates to parse_tuple which handles both 'quote' and 'tuple' shapes.
    """
    return parse_tuple(expr)


# Known built-in Vyper types that can be used as symbols (without colon prefix)
BUILTIN_TYPES = {
    # Integer types
    "uint256",
    "uint128",
    "uint64",
    "uint32",
    "uint16",
    "uint8",
    "int256",
    "int128",
    "int64",
    "int32",
    "int16",
    "int8",
    # Short aliases
    "u256",
    "u128",
    "u64",
    "u32",
    "u16",
    "u8",
    "i256",
    "i128",
    "i64",
    "i32",
    "i16",
    "i8",
    # Other primitives
    "address",
    "bool",
    "bytes32",
    "bytes4",
    "bytes20",
    "decimal",
    "String",
    "Bytes",
    # Special types
    "Bytes",
    "String",
    "DynArray",
    "HashMap",
}


def _is_type_symbol(sym):
    """Check if a symbol should be treated as a type (not an argument name)."""
    return str(sym) in BUILTIN_TYPES


def _is_canonical_args(args_list):
    """Check if args use canonical [[name type] ...] syntax."""
    if len(args_list) == 0:
        return False
    # Check if first arg is a list/expression with 2 elements (name + type pair)
    first = args_list[0]
    return isinstance(first, models.List) and len(first) == 2


def _parse_type_annotation(typ):
    """Parse a type annotation (keyword, symbol, or expression) into a Vyper node."""
    if isinstance(typ, models.Keyword):
        # built-in types like :uint256 (keyword syntax)
        return build_node(vy_nodes.Name, id=str(typ.name), parent=None)
    elif isinstance(typ, models.Symbol):
        # built-in types like uint256 (symbol syntax - preferred)
        return build_node(vy_nodes.Name, id=str(typ), parent=None)
    elif isinstance(typ, models.Expression):
        # complex types like (HashMap address uint256)
        return dasy.parser.parse_node_legacy(typ)
    else:
        raise DasyTypeError(f"Invalid type annotation: {typ}")


def parse_args_list(args_list) -> list[vy_nodes.arg]:
    """Parse function arguments.

    Supports two syntaxes:
    - Canonical (preferred): [[name type] [name2 type2] ...]
      Example: [[x uint256] [y uint256]]
    - Legacy: [type name name2 type2 name3 ...]
      Example: [:uint256 x y :address sender]
    """
    if len(args_list) == 0:
        return []

    # Detect canonical [[name type] ...] syntax
    if _is_canonical_args(args_list):
        results = []
        for pair in args_list:
            if not isinstance(pair, models.List) or len(pair) != 2:
                raise DasyTypeError(
                    f"Canonical syntax requires [name type] pairs, got: {pair}"
                )
            name, typ = pair
            annotation_node = _parse_type_annotation(typ)
            arg_node = build_node(
                vy_nodes.arg, arg=str(name), parent=None, annotation=annotation_node
            )
            results.append(arg_node)
        return results

    # Legacy syntax: [type name name type2 name ...]
    results = []
    current_type = args_list[0]
    # Accept types as Keywords (:uint256), Expressions ((HashMap address uint256)),
    # or Symbols that are known type names (uint256, address)
    assert isinstance(current_type, (models.Keyword, models.Expression)) or (
        isinstance(current_type, models.Symbol) and _is_type_symbol(current_type)
    )
    # get annotation and name
    for arg in args_list[1:]:
        # check if we hit a new type
        if isinstance(arg, (models.Keyword, models.Expression)):
            current_type = arg
            continue
        # Check if symbol is a type (not an argument name)
        if isinstance(arg, models.Symbol) and _is_type_symbol(arg):
            current_type = arg
            continue
        # get annotation and name
        annotation_node = _parse_type_annotation(current_type)
        arg_node = build_node(
            vy_nodes.arg, arg=str(arg), parent=None, annotation=annotation_node
        )
        results.append(arg_node)
    return results


def parse_fn_args(fn_tree):
    args_node, *rest = fn_tree[2:]
    args_list = parse_args_list(args_node)
    args = build_node(vy_nodes.arguments, args=args_list, defaults=list())
    return args, rest


def parse_fn_decorators(decs):
    if isinstance(decs, models.Keyword):
        return [build_node(vy_nodes.Name, id=str(decs.name))]
    elif isinstance(decs, models.List):
        return [dasy.parser.parse_node_legacy(d) for d in decs]
    return []


def parse_fn_body(body, wrap=False):
    fn_body = [dasy.parser.parse_node_legacy(body_node) for body_node in body[:-1]]
    if wrap and not has_return(body[-1]):
        value_node = dasy.parser.parse_node_legacy(body[-1])
        implicit_return_node = build_node(vy_nodes.Return, value=value_node)
        fn_body.append(implicit_return_node)
    else:
        fn_body.append(dasy.parser.parse_node_legacy(body[-1]))
    return process_body(fn_body)


def _fn_tree_has_return_type(fn_tree):
    # has return type
    # (defn name [args] :uint256 :external ...)
    # (defn name [args] :uint256 [:external :view] ...)
    fn_args = fn_tree[1:]
    fn_args_len = len(fn_args)
    return (
        fn_args_len > 3
        and isinstance(fn_args[0], models.Symbol)
        and isinstance(fn_args[1], models.List)
        and isinstance(fn_args[2], (models.Keyword, models.Expression, models.Symbol))
        and isinstance(fn_args[3], (models.Keyword, models.List))
    )


def _fn_tree_has_no_return_type(fn_tree):
    # no return type
    # (defn name [args] ...)
    fn_args = fn_tree[1:]
    fn_args_len = len(fn_args)
    return (
        fn_args_len > 2
        and isinstance(fn_args[0], models.Symbol)
        and isinstance(fn_args[1], models.List)
        and isinstance(fn_args[2], (models.Keyword, models.List))
    )


def _fn_is_constructor(fn_tree):
    return isinstance(fn_tree[1], models.Symbol) and str(fn_tree[1]) == "__init__"


def parse_defn(fn_tree):
    fn_node_id = (
        next_nodeid()
    )  # we want our fn node to have a lower id than its child node
    assert isinstance(fn_tree, models.Expression)
    assert fn_tree[0] == models.Symbol("defn")
    return_type = None
    from .utils import kebab_to_snake

    name = kebab_to_snake(str(fn_tree[1]))
    args = None
    decorators = []

    fn_args = fn_tree[1:]
    args, rest = parse_fn_args(fn_tree)

    if _fn_is_constructor(fn_tree):
        decorators = [build_node(vy_nodes.Name, id="deploy")]
        fn_body = parse_fn_body(rest[1:])
    elif _fn_tree_has_return_type(fn_tree):
        decorators = parse_fn_decorators(fn_args[3])
        fn_body = parse_fn_body(rest[2:], wrap=True)
        return_type = dasy.parser.parse_node_legacy(fn_args[2])
    elif _fn_tree_has_no_return_type(fn_tree):
        decorators = parse_fn_decorators(fn_args[2])
        fn_body = parse_fn_body(rest[1:])
    else:
        raise DasySyntaxError(f"Invalid fn form {fn_tree}")

    fn_node = build_node(
        vy_nodes.FunctionDef,
        args=args,
        returns=return_type,
        decorator_list=decorators,
        pos=None,
        body=fn_body,
        name=name,
        node_id=fn_node_id,
    )

    return fn_node


def parse_declaration(var, typ, value=None, attrs: Set[str] = set()):
    target = dasy.parser.parse_node_legacy(var)
    annotation_attrs = {"public": False, "immutable": False, "constant": False}
    if attrs is not None:
        for attr in attrs:
            annotation_attrs[attr] = True

    annotation = None

    match typ:
        case [models.Symbol(e), _] if str(e) in annotation_attrs.keys():
            annotation = dasy.parser.parse_node_legacy(typ)
            annotation_attrs[str(e)] = True
        case models.Expression() | models.Keyword():
            for attr in attrs:
                typ = models.Expression((models.Symbol(attr), typ))
            annotation = dasy.parser.parse_node_legacy(typ)
        case models.Symbol():
            for attr in attrs:
                typ = models.Expression((models.Symbol(attr), typ))
            annotation = dasy.parser.parse_node_legacy(typ)
        case _:
            raise DasyTypeError(f"Invalid declaration type {typ}")

    if annotation is None:
        raise DasyTypeError("No valid annotation was found")

    vdecl_node = build_node(
        vy_nodes.VariableDecl,
        target=target,
        annotation=annotation,
        value=value,
        **annotation_attrs,
    )
    return vdecl_node


def parse_defvars(expr):
    if isinstance(expr[1], models.Keyword):
        attrs = {expr[1].name}
        return [
            parse_declaration(var, typ, attrs=attrs) for var, typ in pairwise(expr[2:])
        ]
    return [parse_declaration(var, typ) for var, typ in pairwise(expr[1:])]


def parse_defstorage(expr):
    """Parse (defstorage name type modifier*) form.

    Syntax:
        (defstorage owner address)
        (defstorage balances (hash-map address uint256) :public)
        (defstorage my-imm uint256 :immutable)

    Modifiers: :public, :immutable, :transient
    """
    if len(expr) < 3:
        raise DasyTypeError("defstorage requires at least name and type")

    name = expr[1]
    typ = expr[2]
    modifiers = expr[3:]

    # Collect modifiers
    attrs = set()
    for mod in modifiers:
        if isinstance(mod, models.Keyword):
            attrs.add(mod.name)

    return parse_declaration(name, typ, attrs=attrs)


def parse_defconst(expr, context=None):
    """Parse (defconst name type value) or legacy (defconst name value) form.

    New Syntax (preferred):
        (defconst MAX_DEPOSIT uint256 1000000)

    Legacy Syntax (symbolic expansion, deprecated):
        (defconst MY_CONSTANT 123)
    """
    if len(expr) == 3:
        # Legacy syntax: (defconst NAME value) - symbolic constant
        # Store in context for symbolic expansion (like the old behavior)
        if context is not None:
            context.constants[str(expr[1])] = expr[2]
        return None  # No AST node generated
    elif len(expr) == 4:
        # New syntax: (defconst NAME type value) - Vyper constant
        name = expr[1]
        typ = expr[2]
        value = expr[3]

        # Parse the value
        parsed_value = dasy.parser.parse_node_legacy(value)

        return parse_declaration(name, typ, value=parsed_value, attrs={"constant"})
    else:
        raise DasyTypeError(
            "defconst requires either (defconst name value) or (defconst name type value)"
        )


def create_annotated_node(node_class, var, typ, value=None):
    target = dasy.parser.parse_node_legacy(var)
    if not isinstance(typ, (models.Expression, models.Keyword, models.Symbol)):
        raise DasyTypeError(f"Invalid declaration type {typ}")
    annotation = dasy.parser.parse_node_legacy(typ)
    node = build_node(node_class, target=target, annotation=annotation, value=value)
    return node


def parse_variabledecl(expr) -> vy_nodes.VariableDecl:
    return create_annotated_node(
        vy_nodes.VariableDecl,
        expr[1],
        expr[2],
        value=dasy.parser.parse_node_legacy(expr[3]) if len(expr) == 4 else None,
    )


def parse_annassign(expr) -> vy_nodes.AnnAssign:
    return create_annotated_node(
        vy_nodes.AnnAssign,
        expr[1],
        expr[2],
        value=dasy.parser.parse_node_legacy(expr[3]) if len(expr) == 4 else None,
    )


def parse_structbody(expr):
    return [
        create_annotated_node(vy_nodes.AnnAssign, var, typ)
        for var, typ in pairwise(expr[2:])
    ]


def parse_defcontract(expr):
    body_nodes = []
    expr_body = []

    match expr[1:]:
        case (_, vars, *body) if isinstance(vars, models.List):
            # contract has state
            for var, typ in pairwise(vars):
                body_nodes.append(parse_declaration(var, typ))
            expr_body = body
        case (_, *body):
            # no contract state
            expr_body = body
        case _:
            raise DasySyntaxError(f"Invalid defcontract form: {expr}")

    for node in expr_body:
        body_nodes.append(dasy.parser.parse_node_legacy(node))

    mod_node = vy_nodes.Module(
        body=body_nodes,
        name=str(expr[1]),
        doc_string="",
        ast_type="Module",
        node_id=next_nodeid(),
        path="contract.dasy",
        resolved_path="contract.dasy",
        source_id=0,
        full_source_code="",  # Will be set by parent parser
        is_interface=False,
        # settings will be set by parent parser
    )

    return mod_node


def parse_defstruct(expr):
    struct_node = build_node(
        vy_nodes.StructDef, name=str(expr[1]), body=parse_structbody(expr)
    )
    return struct_node


def parse_sig(f):
    """Parse a sig form inside definterface.

    Syntax:
        (sig name [args] return-type :mutability)
        (sig name [args] :mutability)  ; for void-returning functions

    Examples:
        (sig transfer [:address to :uint256 amount] :bool :external)
        (sig balanceOf [:address owner] :uint256 :view)
        (sig setOwner [:address owner] :nonpayable)
    """
    # f[0] = sig or defn
    # f[1] = name
    # f[2] = args
    # f[3] = return type (if len > 4) or mutability
    # f[-1] = mutability

    rets = None if len(f) == 4 else dasy.parser.parse_node_legacy(f[3])

    args_list = parse_args_list(f[2])
    args_node = build_node(vy_nodes.arguments, args=args_list, defaults=list())

    # in an interface, the body is a single expr node with the visibility
    visibility_node = dasy.parser.parse_node_legacy(f[-1])
    body_node = build_node(vy_nodes.Expr, value=visibility_node)

    fn_node = build_node(
        vy_nodes.FunctionDef,
        args=args_node,
        returns=rets,
        decorator_list=[],
        pos=None,
        body=[body_node],
        name=str(f[1]),
    )
    return fn_node


def parse_definterface(expr):
    """Parse (definterface Name (sig|defn ...)*) form.

    Supports both `sig` (preferred) and `defn` (legacy) for function signatures.

    Syntax:
        (definterface IERC20
          (sig transfer [:address to :uint256 amount] :bool :external)
          (sig balanceOf [:address owner] :uint256 :view))
    """
    name = str(expr[1])
    body = []
    for f in expr[2:]:
        fn_node = parse_sig(f)
        body.append(fn_node)

    interface_node = build_node(vy_nodes.InterfaceDef, body=body, name=name)
    return interface_node


def parse_defevent(expr):
    return build_node(vy_nodes.EventDef, name=str(expr[1]), body=parse_structbody(expr))


def parse_enumbody(expr):
    return [
        build_node(vy_nodes.Expr, value=dasy.parser.parse_node_legacy(x))
        for x in expr[2:]
    ]


def parse_defflag(expr):
    return build_node(vy_nodes.FlagDef, name=str(expr[1]), body=parse_enumbody(expr))


def parse_do(expr):
    calls = [dasy.parser.parse_node_legacy(x) for x in expr[1:]]
    # Use process_body to wrap Calls into Expr nodes but leave Assign/AugAssign etc. intact
    return process_body(calls)


def parse_subscript(expr):
    """(subscript value slice)"""
    slice_node = dasy.parser.parse_node_legacy(expr[2])
    value_node = dasy.parser.parse_node_legacy(expr[1])
    subscript_node = build_node(vy_nodes.Subscript, slice=slice_node, value=value_node)
    return subscript_node
