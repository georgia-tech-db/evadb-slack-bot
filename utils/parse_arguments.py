import ast

def parse_args(args):
    args = 'f ({})'.format(args)
    tree = ast.parse(args)
    funccall = tree.body.value
    args = [ast.literal_eval(arg) for arg in funccall.args]
    kwargs = {arg.arg: ast.literal_eval(arg.value) for arg in funccall.keywords}
    return args, kwargs

args, kwargs = parse_args('mystring --foo 1')
print(args, kwargs)