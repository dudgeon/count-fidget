"""Small read-only S-expression helpers for comparing native KiCad artifacts."""
import re


def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack, root = [], None
    for token in tokens:
        if token == '(':
            item = []
            if stack:
                stack[-1].append(item)
            else:
                if root is not None:
                    raise ValueError('Multiple roots')
                root = item
            stack.append(item)
        elif token == ')':
            if not stack:
                raise ValueError('Unbalanced closing parenthesis')
            stack.pop()
        else:
            if not stack:
                raise ValueError('Token outside root')
            if token.startswith('"'):
                token = re.sub(r'\\(.)', lambda m: {'n': '\n', 'r': '\r', 't': '\t'}.get(m[1], m[1]), token[1:-1])
            stack[-1].append(token)
    if stack or root is None:
        raise ValueError('Unbalanced or empty S-expression')
    return root


def children(node, name):
    return [x for x in node[1:] if isinstance(x, list) and x and x[0] == name]


def child(node, name):
    found = children(node, name)
    if len(found) != 1:
        raise ValueError(f'Expected one {name}, found {len(found)}')
    return found[0]


def property_value(node, name):
    return next(x[2] for x in children(node, 'property') if x[1] == name)
