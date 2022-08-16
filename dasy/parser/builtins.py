import vyper.ast.nodes as vy_nodes
from .utils import next_nodeid

def parse_builtin(node):
    match str(node):
        case '+':
            op_node = vy_nodes.Add(node_id=next_nodeid(), ast_type='Add', _pretty="+", _description="addition")
            return op_node
        case '-':
            op_node = vy_nodes.Sub(node_id=next_nodeid(), ast_type='Sub', _pretty="-", _description="subtraction")
            return op_node
        case '*':
            op_node = vy_nodes.Mult(node_id=next_nodeid(), ast_type='Mult', _pretty="*", _description="multiplication")
            return op_node
        case '/':
            op_node = vy_nodes.Div(node_id=next_nodeid(), ast_type='Div', _pretty="/", _description="multiplication")
            return op_node
        case '<':
            op_node = vy_nodes.Lt(node_id=next_nodeid(), ast_type='Lt', _pretty="<", _description="less than")
            return op_node
        case '<=':
            op_node = vy_nodes.LtE(node_id=next_nodeid(), ast_type='LtE', _pretty="<=", _description="less than equal")
            return op_node
        case '>':
            op_node = vy_nodes.Gt(node_id=next_nodeid(), ast_type='Gt', _pretty="<", _description="greater than")
            return op_node
        case '>=':
            op_node = vy_nodes.GtE(node_id=next_nodeid(), ast_type='GtE', _pretty=">=", _description="greater than equal")
            return op_node
        case '==':
            op_node = vy_nodes.Eq(node_id=next_nodeid(), ast_type='Eq', _pretty="==", _description="equality")
            return op_node
        case '!=':
            op_node = vy_nodes.NotEq(node_id=next_nodeid(), ast_type='NotEq', _pretty="!=", _description="inequality")
            return op_node
        case 'not':
            op_node = vy_nodes.Not(node_id=next_nodeid(), ast_type='Not', _pretty="not", _description="negation")
            return op_node
        case 'and':
            op_node = vy_nodes.And(node_id=next_nodeid(), ast_type='And', _pretty="and", _description="boolean and")
            return op_node
        case 'or':
            op_node = vy_nodes.Or(node_id=next_nodeid(), ast_type='Or', _pretty="or", _description="boolean or")
            return op_node
