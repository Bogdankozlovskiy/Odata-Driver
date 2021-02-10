import re
from parsimonious.grammar import Grammar
from django.db.models import Q, F, Value
from django.db.models.functions import Concat


class ODataException(Exception):
    pass


def django_params(param_dict):
    rv = {}
    processor = FilterProcessor()
    if '$filter' in param_dict:
        rv['filter'] = processor.process(param_dict['$filter'][0])
    if '$orderby' in param_dict:
        rv['orderby'] = processor.order_by(param_dict['$orderby'][0])
    if '$select' in param_dict:
        rv['select'] = processor.select(param_dict['$select'][0])
    if '$top' in param_dict:
        rv['top'] = slice(None, int(param_dict['$top'][0]))
    if '$skip' in param_dict:
        rv['skip'] = slice(int(param_dict['$skip'][0]), None)
    return rv


grammar = Grammar(
    """
    bool_common_expr     = (not_expr / common_expr ) ( and_expr / or_expr )?
    rel_expr            = (function_param / function_expr) RWS rel_marker RWS function_param
    rel_marker          = 'eq' / 'ne' / 'lt' / 'le' / 'gt' / 'ge'
    common_expr         = paren_expr / function_marker_expr / function_expr / rel_expr
    function_marker_expr = function_expr RWS rel_marker RWS (string / number)
    function_expr       = func_name "(" ~"\s*" function_param  (~"\s*,\s*" function_param)* ~"\s*" ")"
    func_name           = ~"\w+"
    select_path         = ~"[a-zA-Z][\w/]*"
    number             = "-"? ~"[\d\.]+"
    string             = "'" ~"[^']+" "'"
    json_primitive      = "true" / "false" / "null"
    function_param      = function_expr / number / string / json_primitive / select_path
    paren_expr          = "(" ~"\s*" bool_common_expr ~"\s*" ")"
    not_expr            = 'not' RWS bool_common_expr
    and_expr            = RWS 'and' RWS bool_common_expr
    or_expr             = RWS 'or' RWS bool_common_expr
    RWS                = ~"\s+"
    """
)

function_param = ['select_path', 'number', 'string', 'json_primitive']
good_children = {
    'bool_common_expr': ['not_expr', 'common_expr', 'and_expr', 'or_expr'],
    'common_expr': ['paren_expr', 'function_marker_expr', 'function_expr', 'rel_expr'],
    'function_expr': ['func_name', 'function_expr'] + function_param,
    'function_marker_expr': ['func_name', 'rel_marker', 'function_expr'] + function_param,
    'rel_expr': ['rel_marker', 'function_expr'] + function_param,
    'paren_expr': ['bool_common_expr'],
    'or_expr': ['bool_common_expr'],
    'and_expr': ['bool_common_expr'],
    'not_expr': ['bool_common_expr'],
}


def walk(parsed, node_type='bool_common_expr'):
    reduced_stack = []
    good = good_children[node_type]
    for c in parsed.children:
        if c.expr_name in good:
            reduced_stack.append(c)
        else:
            reduced_stack.extend(walk(c, node_type))
    return reduced_stack


class FilterProcessor:
    def __init__(self):
        self.field_mapper = lambda x: x.replace("/", "__") if isinstance(x, str) else "__".join(x)
        self.Q = Q
        self.F = F
        self.Value = Value
        self.Concat = Concat

    def order_by(self, order_param):
        terms = order_param.split(',')
        final = []
        for t in terms:
            term, *direction = re.split(r'\s+', t)
            ordering = self.field_mapper(term)
            if direction and direction[0] == 'desc':
                ordering = '-%s' % ordering
            final.append(ordering)
        return final

    @staticmethod
    def select(select_param):
        terms = select_param.split(',')
        final = []
        for t in terms:
            term = t.strip().replace("/", "__")
            final.append(term)
        return final

    def process(self, filter_text):
        parsed = grammar.parse(filter_text)
        return self.bool_common_expr(parsed)

    def unpack(self, node):
        return self.bool_common_expr(walk(node, node.expr_name)[0])

    def bool_common_expr(self, node):
        front, *pieces = walk(node, 'bool_common_expr')
        if front.expr_name == 'not_expr':
            q_expr = self.bool_combine(self.unpack(front), 'not')
        else:
            q_expr = self.common_expr(front)
        if pieces:
            bin_expr = pieces[0]
            addition = self.unpack(bin_expr)
            q_expr = self.bool_combine(q_expr, 'and' if bin_expr.expr_name == 'and_expr' else 'or', addition)
        return q_expr

    @staticmethod
    def bool_combine(left_expr, op, right_expr=None):
        ops = {
            'not': lambda a, b: ~a,
            'and': lambda a, b: a & b,
            'or': lambda a, b: a | b
        }
        return ops[op](left_expr, right_expr)

    def common_expr(self, node):
        inner = walk(node, 'common_expr')[0]
        if inner.expr_name == 'paren_expr':
            return self.unpack(inner)
        else:
            return getattr(self, inner.expr_name)(inner)

    def rel_expr(self, node):
        pieces = walk(node, 'rel_expr')
        if len(pieces) != 3 \
                or pieces[0].expr_name != 'select_path' \
                or pieces[1].expr_name != 'rel_marker':
            raise ODataException("unexpected expression structure should by 'X or Y'")
        if pieces[0].expr_name == 'select_path':
            op = pieces[1].text
            fields = pieces[0].text.split('/')
            val = self.primitive(pieces[2])
            return self.basic_relation(fields, op, val)
        else:
            raise ODataException("unimplemented relation expression: '{}'".format(node.text))

    @staticmethod
    def primitive(node):
        if node.expr_name == 'string':
            return node.children[1].text
        elif node.expr_name == 'number':
            dd = node.text
            if '.' in dd:
                return float(dd)
            else:
                return int(dd)
        elif node.expr_name == 'json_primitive':
            cases = {
                'true': True,
                'false': False,
                'null': None}
            return cases[node.text]
        elif node.expr_name == "function_expr":
            return node
        elif node.expr_name == "rel_marker":
            return node.text
        raise ODataException("unmatched primitive type '{}'".format(node.text))

    def basic_relation(self, fields, op, value):
        token = self.field_mapper(fields)
        if value is None:
            token = token + '__isnull'
            value = True
        if op in ('lt', 'le', 'gt', 'ge'):
            if op in ('le', 'ge'):
                op = op[0] + 'te'
            token = '{}__{}'.format(token, op)
        q_expr = self.Q(**{token: value})
        if op == 'ne':
            q_expr = ~q_expr
        return q_expr

    def basic_function(self, func_name, fields, *args, params=None):
        converter_a = {
            "contains": "contains",
            "substringof": "contains",
            "endswith": "endswith",
            "startswith": "startswith",
            "length": "length",
            "year": "year",
            "month": "month",
            "day": "day",
            "hour": "hour",
            "minute": "minute",
            "second": "second"
        }
        converter_b = {
            "string": lambda n: self.Value(n.text.strip("'")),
            "select_path": lambda n: self.F(n.text.strip("'")),
            "function_expr": self.function_expr
        }
        converted_value = converter_a.get(func_name)
        if converted_value is not None:
            token = self.field_mapper(fields)
            token = f"{token}__{converted_value}"
            if not args:
                return token
            return self.Q(**{token: args[0]})
        if func_name == 'concat':
            try:
                return self.Concat(*[converter_b[i.expr_name](i) for i in params])
            except KeyError as ke:
                raise ODataException(f"type {ke} is not support for function concat")

    def function_expr(self, node):
        func_name, *params = walk(node, 'function_expr')
        param_vals = [(p.text.split('/') if p.expr_name == 'select_path'
                       else self.primitive(p))
                      for p in params]
        return self.basic_function(func_name.text, *param_vals, params=params)

    def function_marker_expr(self, node):
        func_name, *params = walk(node, 'function_marker_expr')
        func_result = self.function_expr(func_name)
        if isinstance(func_result, str):
            op, value = [self.primitive(i) for i in params]
            return self.basic_relation([func_result], op, value)
        else:
            pass  # TODO
