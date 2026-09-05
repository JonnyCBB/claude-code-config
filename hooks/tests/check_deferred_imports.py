"""Find functions that reference a name with no module-level or local import.

Written because deferring an import into one function while another still names
it produced a live NameError that 96 tests did not catch.
"""

import ast, sys


def _own_scope(node):
    """Descendants belonging to THIS function, not to a nested def or lambda.

    ast.walk descends into nested functions, so an import inside a closure was
    credited to the enclosing function and could mask a genuine dangling
    reference there - the exact defect class this checker exists to catch.
    """
    out = []
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        out.append(child)
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            stack.extend(ast.iter_child_nodes(child))
    return out


WATCH = {"Path", "PurePath", "sqlite3", "subprocess", "shutil", "tempfile", "hashlib"}
bad = []
for path in sys.argv[1:]:
    tree = ast.parse(open(path).read(), path)
    module_names = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            module_names |= {(a.asname or a.name).split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            module_names |= {(a.asname or a.name) for a in node.names}
    for fn in [
        n
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]:
        local = set()
        for node in _own_scope(fn):
            if isinstance(node, ast.Import):
                local |= {(a.asname or a.name).split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                local |= {(a.asname or a.name) for a in node.names}
        # Annotations are never evaluated under `from __future__ import
        # annotations`, so a name used only there cannot raise. Strip them.
        stripped = ast.parse(ast.unparse(fn))

        for node in ast.walk(stripped):
            if isinstance(node, (ast.arg, ast.AnnAssign)):
                node.annotation = None
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                node.returns = None
        used = {
            n.id
            for n in ast.walk(stripped)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
        }
        for name in sorted((used & WATCH) - module_names - local):
            bad.append(
                "%s:%d %s() uses %r with no import in scope"
                % (path, fn.lineno, fn.name, name)
            )
print(
    "\n".join("  " + b for b in bad) if bad else "  clean: every watched name resolves"
)
sys.exit(1 if bad else 0)
