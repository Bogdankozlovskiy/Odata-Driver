import re
from parsimonious.grammar import Grammar
from django.db import models
from django.db.models import functions
import operator


class ODataException(Exception):
    pass


def django_params(param_dict):
    rv = {}
    processor = FilterProcessor()
    if '$filter' in param_dict:
        rv.update(processor.process(param_dict['$filter'][0]))
    if '$orderby' in param_dict:
        rv.update(processor.order_by(param_dict['$orderby'][0]))
    if '$select' in param_dict:
        rv.update(processor.select(param_dict['$select'][0]))
    if '$top' in param_dict:
        rv.update(top=slice(None, int(param_dict['$top'][0])))
    if '$skip' in param_dict:
        rv.update(skip=slice(int(param_dict['$skip'][0]), None))
    if '$expand' in param_dict:
        rv.update(processor.expand(param_dict['$expand'][0]))
    return rv


grammar = Grammar(
    """
    bool_common_expr     = (not_expr / common_expr ) ( and_expr / or_expr )?
    rel_expr             = (function_param / function_expr) RWS rel_marker RWS function_param 
    math_expr            = function_param RWS math_marker RWS number
    rel_marker           = 'eq' / 'ne' / 'lt' / 'le' / 'gt' / 'ge'
    common_expr          = paren_expr / function_marker_expr / function_expr / rel_expr
    function_marker_expr = (function_expr / math_expr) RWS rel_marker RWS (string / number)
    function_expr        = func_name "(" ~"\s*" function_param  (~"\s*,\s*" function_param)* ~"\s*" ")"
    func_name            = ~"\w+"
    select_path          = ~"[a-zA-Z][\w/]*"
    number               = "-"? ~"[\d\.]+"
    string               = "'" ~"[^']+" "'"
    json_primitive       = "true" / "false" / "null"
    function_param       = function_expr / number / string / json_primitive / select_path
    paren_expr           = "(" ~"\s*" bool_common_expr ~"\s*" ")"
    not_expr             = 'not' RWS? bool_common_expr?
    math_marker          = 'mod' / 'div' / 'mul' / 'sub' / 'add' / 'sqrt'
    and_expr             = RWS 'and' RWS bool_common_expr
    or_expr              = RWS 'or' RWS bool_common_expr
    RWS                  = ~"\s+"
    """
)

function_param = ['select_path', 'number', 'string', 'json_primitive']
good_children = {
    'bool_common_expr': ['not_expr', 'common_expr', 'and_expr', 'or_expr'],
    'common_expr': ['paren_expr', 'function_marker_expr', 'function_expr', 'rel_expr'],
    'function_expr': ['func_name', 'function_expr'] + function_param,
    'function_marker_expr': ['func_name', 'rel_marker', 'function_expr', 'math_expr'] + function_param,
    'rel_expr': ['rel_marker', 'function_expr'] + function_param,
    'paren_expr': ['bool_common_expr'],
    'or_expr': ['bool_common_expr'],
    'and_expr': ['bool_common_expr'],
    'not_expr': ['bool_common_expr'],
    'math_expr': ['math_marker'] + function_param,
}


class FilterProcessor:
    def order_by(self, order_param):
        terms = order_param.split(',')
        final = []
        for t in terms:
            term, *direction = re.split(r'\s+', t)
            ordering = self.field_mapper(term)
            if direction and direction[0] == 'desc':
                ordering = '-%s' % ordering
            final.append(ordering)
        return {"orderby": final}

    @staticmethod
    def select(select_param):
        terms = select_param.split(',')
        final = []
        for t in terms:
            term = t.strip().replace("/", "__")
            final.append(term)
        return {"select": final}

    def process(self, filter_text):
        parsed = grammar.parse(filter_text)
        return self.bool_common_expr(parsed)

    @staticmethod
    def expand(expand_param):
        terms = expand_param.split(',')
        final = []
        for t in terms:
            term = t.strip().replace("/", "__")
            final.append(term)
        return {"expand": final}

    @staticmethod
    def field_mapper(field):
        if isinstance(field, list):
            return "__".join(field)
        if isinstance(field, str):
            return field.replace("/", "__")

    @staticmethod
    def walk(parsed, node_type='bool_common_expr'):
        reduced_stack = []
        good = good_children[node_type]
        for c in parsed.children:
            if c.expr_name in good:
                reduced_stack.append(c)
            else:
                reduced_stack.extend(FilterProcessor.walk(c, node_type))
        return reduced_stack

    def unpack(self, node):
        return self.bool_common_expr(FilterProcessor.walk(node, node.expr_name)[0])

    def bool_common_expr(self, node):
        front, *pieces = FilterProcessor.walk(node, 'bool_common_expr')
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
    def merge_dicts(dict_a: dict, dict_b: dict, op):
        dict_result = {}
        keys = set(dict_a.keys()) & set(dict_b.keys())
        for key in keys:
            dict_result[key] = op(dict_a[key], dict_b[key])
        for key in dict_a:
            if key not in dict_result:
                dict_result[key] = dict_a[key]
        for key in dict_b:
            if key not in dict_result:
                dict_result[key] = dict_b[key]
        return dict_result

    @staticmethod
    def bool_combine(left_expr, op, right_expr=None):
        ops = {
            'not': lambda a, b: {"filter": ~a['filter']},
            'and': lambda a, b: FilterProcessor.merge_dicts(a, b, operator.and_),
            'or': lambda a, b: FilterProcessor.merge_dicts(a, b, operator.or_)
        }
        return ops[op](left_expr, right_expr)

    def common_expr(self, node):
        inner = FilterProcessor.walk(node, 'common_expr')[0]
        if inner.expr_name == 'paren_expr':
            return self.unpack(inner)
        else:
            return getattr(self, inner.expr_name)(inner)

    def rel_expr(self, node):
        pieces = FilterProcessor.walk(node, 'rel_expr')
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

    def primitive(self, node):
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
            return self.function_expr(node)['filter']
        elif node.expr_name == "rel_marker":
            return node.text
        elif node.expr_name == "math_marker":
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
        q_expr = models.Q(**{token: value})
        if op == 'ne':
            q_expr = ~q_expr
        return {"filter": q_expr}

    def basic_function(self, func_name, fields, *args, params=None):
        converter_a = {
            "contains": "contains",
            "substringof": "contains",  # TODO substringof works works not like contains
            "endswith": "endswith",
            "startswith": "startswith",
            "length": "length",
            "year": "year",
            "month": "month",
            "day": "day",
            "hour": "hour",
            "minute": "minute",
            "second": "second",
            "tolower": "lower",
            "toupper": "upper",
            "trim": "trim",
            "ceiling": "ceil",
            "floor": "floor",
            "round": "round",
            "power": "power",        # TODO write the test for this
            "sqtr": "sqtr",          # TODO write the test for this
            "abs": "abs",            # TODO write the test for this
            "mod": "mod"             # TODO write the test for this
        }
        converter_b = {
            "string": lambda n: models.Value(n.text.strip("'")),
            "select_path": lambda n: models.F(n.text.strip("'")),
            "function_expr": self.function_expr
        }
        converted_value = converter_a.get(func_name)
        if converted_value is not None:
            token = self.field_mapper(fields)
            token = f"{token}__{converted_value}"
            if not args:
                return {"filter": token}
            return {"filter": models.Q(**{token: args[0]})}
        if func_name == 'concat':
            try:
                params = [converter_b[i.expr_name](i) for i in params]
                params = [i['filter'] if isinstance(i, dict) else i for i in params]
                return {"filter": functions.Concat(*params)}
            except KeyError as ke:
                raise ODataException(f"type {ke} is not support for function concat")

    def function_expr(self, node):
        func_name, *params = FilterProcessor.walk(node, 'function_expr')
        param_vals = [(p.text.split('/') if p.expr_name == 'select_path' else self.primitive(p)) for p in params]
        return self.basic_function(func_name.text, *param_vals, params=params)

    def math_expr(self, node):
        func_name, *params = FilterProcessor.walk(node, 'math_expr')
        op, val = [(p.text.split('/') if p.expr_name == 'select_path' else self.primitive(p)) for p in params]
        if op == "div":
            op = "truediv"
        return {"filter": getattr(operator, op)(models.F(func_name.text), val)}

    def function_marker_expr(self, node):
        func_name, *params = FilterProcessor.walk(node, 'function_marker_expr')
        if func_name.expr_name == "function_expr":
            func_result = self.function_expr(func_name)
        elif func_name.expr_name == "math_expr":
            func_result = self.math_expr(func_name)
        else:
            raise ODataException(f"function_marker_expr doesn't support type {func_name.expr_name}")
        op, value = [self.primitive(i) for i in params]
        if isinstance(func_result['filter'], str):
            return self.basic_relation(func_result['filter'], op, value)
        else:
            result = {"defer": "annotated_value"}
            result.update(self.basic_relation(["annotated_value"], op, value))
            result.update(annotate={"annotated_value": func_result['filter']})
            return result
