from ast import *
from ItemList import item_table
from State import State
import re


escaped_items = {}
for item in item_table:
    escaped_items[re.sub(r'[\'()[\]]', '', item.replace(' ', '_'))] = item


class Rule_AST_Transformer(NodeTransformer):

    def __init__(self, world):
        self.world = world


    def visit_Name(self, node):
        if node.id in escaped_items:
            return Call(
                func=Attribute(
                    value=Name(id='state', ctx=Load()),
                    attr='has',
                    ctx=Load()),
                args=[Str(escaped_items[node.id])],
                keywords=[])
        elif node.id in self.world.__dict__:
            return Attribute(
                value=Attribute(
                    value=Name(id='state', ctx=Load()),
                    attr='world',
                    ctx=Load()),
                attr=node.id,
                ctx=Load())
        elif node.id in State.__dict__:
            return Call(
                func=Attribute(
                    value=Name(id='state', ctx=Load()),
                    attr=node.id,
                    ctx=Load()),
                args=[],
                keywords=[])
        else:
            return node


    def visit_Tuple(self, node):
        if len(node.elts) != 2:
            raise Exception('Parse Error: Tuple must has 2 values')

        item, count = node.elts

        if isinstance(item, Str):
            item = Name(id=item.s, ctx=Load())

        if not isinstance(item, Name):
            raise Exception('Parse Error: first value must be an item. Got %s' % item.__class__.__name__)

        if not (isinstance(count, Name) or isinstance(count, Num)):
            raise Exception('Parse Error: second value must be a number. Got %s' % item.__class__.__name__)

        if isinstance(count, Name):
            count = Attribute(
                value=Attribute(
                    value=Name(id='state', ctx=Load()),
                    attr='world',
                    ctx=Load()),
                attr=count.id,
                ctx=Load())

        if item.id in escaped_items:
            item.id = escaped_items[item.id]

        if not item.id in item_table:
            raise Exception('Parse Error: invalid item name')

        return Call(
            func=Attribute(
                value=Name(id='state', ctx=Load()),
                attr='has',
                ctx=Load()),
            args=[Str(item.id), count],
            keywords=[])


    def visit_Call(self, node):
        new_args = []
        for child in node.args:
            if isinstance(child, Name):
                if child.id in self.world.__dict__:
                    child = Attribute(
                        value=Attribute(
                            value=Name(id='state', ctx=Load()),
                            attr='world',
                            ctx=Load()),
                        attr=child.id,
                        ctx=Load())
                elif child.id in escaped_items:
                    child = Str(escaped_items[child.id])
                else:
                    child = Str(child.id.replace('_', ' '))
            new_args.append(child)

        if isinstance(node.func, Name):
            return Call(
                func=Attribute(
                    value=Name(id='state', ctx=Load()),
                    attr=node.func.id,
                    ctx=Load()),
                args=new_args,
                keywords=node.keywords)
        else:
            return node


    def visit_Subscript(self, node):
        if isinstance(node.value, Name):
            return Subscript(
                value=Attribute(
                    value=Attribute(
                        value=Name(id='state', ctx=Load()),
                        attr='world',
                        ctx=Load()),
                    attr=node.value.id,
                    ctx=Load()),
                slice=Index(value=Str(node.slice.value.id)),
                ctx=node.ctx)
        else:
            return node


def parse_rule_string(rule, world):
    if rule is None:
        return lambda state: True
    else:
        rule = 'lambda state: ' + rule
    rule = rule.split('#')[0]

    rule_ast = parse(rule, mode='eval')
    rule_ast = fix_missing_locations(Rule_AST_Transformer(world).visit(rule_ast))
    rule_lambda = eval(compile(rule_ast, '<string>', 'eval'))
    return rule_lambda
