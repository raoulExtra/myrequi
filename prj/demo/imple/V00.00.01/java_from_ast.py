from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from javalang import tree
except ModuleNotFoundError:  # pragma: no cover
    tree = None


class JavaGraphError(ValueError):
    pass


def _render_name(node: dict[str, Any], default: str | None = None) -> str:
    return str(node.get("name") or node.get("member") or node.get("text") or node.get("label") or default or node.get("id"))


def _render_modifiers(value: Any) -> set[str]:
    if not value:
        return set()
    if isinstance(value, str):
        return {part for part in value.replace(",", " ").split() if part}
    return {str(item) for item in value}


def _render_literal(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)
    text = str(value)
    if not text:
        return '""'
    if text in {"null", "true", "false"}:
        return text
    if text[0] in '"\'' and text[-1] == text[0]:
        return text
    try:
        float(text)
        return text
    except ValueError:
        return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


class JavaAstBuilder:
    def __init__(self, graph_data: dict[str, Any]):
        if tree is None:
            raise JavaGraphError("javalang module is unavailable")
        if not isinstance(graph_data, dict):
            raise JavaGraphError("graph data must be an object")
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise JavaGraphError("graph data must contain nodes and edges arrays")
        self.nodes = nodes
        self.node_map = {str(n.get("id")): n for n in nodes if isinstance(n, dict) and "id" in n}
        self.children: dict[str, list[tuple[str, int, int, str]]] = {}
        self.targets: set[str] = set()
        for edge_index, edge in enumerate(edges):
            if not isinstance(edge, dict) or "from" not in edge or "to" not in edge:
                raise JavaGraphError("each edge must contain from and to")
            order = edge.get("order", edge_index)
            if isinstance(order, bool) or not isinstance(order, (int, float)):
                raise JavaGraphError("each edge order must be numeric when present")
            src = str(edge["from"])
            dst = str(edge["to"])
            self.children.setdefault(src, []).append((str(edge.get("label") or ""), int(order), edge_index, dst))
            self.targets.add(dst)

    def build(self) -> Any:
        return self._convert(self._find_root())

    def _find_root(self) -> str:
        for node in self.nodes:
            if isinstance(node, dict) and "id" in node and str(node["id"]) not in self.targets:
                return str(node["id"])
        if self.nodes and isinstance(self.nodes[0], dict) and "id" in self.nodes[0]:
            return str(self.nodes[0]["id"])
        raise JavaGraphError("graph has no nodes")

    def _grouped(self, node_id: str) -> dict[str, list[str]]:
        grouped: dict[str, list[tuple[int, int, str]]] = {}
        for label, order, edge_index, dst in self.children.get(node_id, []):
            grouped.setdefault(label, []).append((order, edge_index, dst))
        return {label: [dst for _, _, dst in sorted(items, key=lambda x: (x[0], x[1]))] for label, items in grouped.items()}

    def _single(self, grouped: dict[str, list[str]], label: str) -> Any | None:
        items = grouped.get(label, [])
        if not items:
            return None
        if len(items) != 1:
            raise JavaGraphError(f"field {label} expects one child")
        return self._convert(items[0])

    def _many(self, grouped: dict[str, list[str]], label: str) -> list[Any]:
        return [self._convert(item) for item in grouped.get(label, [])]

    def _convert(self, node_id: str) -> Any:
        if node_id not in self.node_map:
            raise JavaGraphError(f"missing node {node_id}")
        node = self.node_map[node_id]
        kind = str(node.get("type") or node.get("label") or node.get("text") or "")
        grouped = self._grouped(node_id)

        if kind == "CompilationUnit":
            return tree.CompilationUnit(package=self._single(grouped, "package"), imports=self._many(grouped, "imports"), types=self._many(grouped, "types"))
        if kind == "PackageDeclaration":
            return tree.PackageDeclaration(modifiers=_render_modifiers(node.get("modifiers")), annotations=self._many(grouped, "annotations"), documentation=node.get("documentation"), name=_render_name(node))
        if kind == "Import":
            return tree.Import(path=_render_name(node), static=bool(node.get("static", False)), wildcard=bool(node.get("wildcard", False)))
        if kind == "ClassDeclaration":
            return tree.ClassDeclaration(modifiers=_render_modifiers(node.get("modifiers")), annotations=self._many(grouped, "annotations"), documentation=node.get("documentation"), name=_render_name(node), body=self._many(grouped, "body"), type_parameters=self._many(grouped, "type_parameters"), extends=self._single(grouped, "extends"), implements=self._many(grouped, "implements"))
        if kind == "FieldDeclaration":
            return tree.FieldDeclaration(documentation=node.get("documentation"), modifiers=_render_modifiers(node.get("modifiers")), annotations=self._many(grouped, "annotations"), type=self._single(grouped, "type"), declarators=self._many(grouped, "declarators"))
        if kind == "VariableDeclarator":
            return tree.VariableDeclarator(name=_render_name(node), dimensions=node.get("dimensions") or [], initializer=self._single(grouped, "initializer"))
        if kind == "MethodDeclaration":
            return tree.MethodDeclaration(documentation=node.get("documentation"), modifiers=_render_modifiers(node.get("modifiers")), annotations=self._many(grouped, "annotations"), type_parameters=self._many(grouped, "type_parameters"), return_type=self._single(grouped, "return_type"), name=_render_name(node), parameters=self._many(grouped, "parameters"), throws=self._many(grouped, "throws"), body=self._many(grouped, "body"))
        if kind == "ConstructorDeclaration":
            return tree.ConstructorDeclaration(modifiers=_render_modifiers(node.get("modifiers")), annotations=self._many(grouped, "annotations"), documentation=node.get("documentation"), type_parameters=self._many(grouped, "type_parameters"), name=_render_name(node), parameters=self._many(grouped, "parameters"), throws=self._many(grouped, "throws"), body=self._many(grouped, "body"))
        if kind == "FormalParameter":
            return tree.FormalParameter(modifiers=_render_modifiers(node.get("modifiers")), annotations=self._many(grouped, "annotations"), type=self._single(grouped, "type"), name=_render_name(node), varargs=bool(node.get("varargs", False)))
        if kind == "LocalVariableDeclaration":
            return tree.LocalVariableDeclaration(modifiers=_render_modifiers(node.get("modifiers")), annotations=self._many(grouped, "annotations"), type=self._single(grouped, "type"), declarators=self._many(grouped, "declarators"))
        if kind == "Literal":
            return tree.Literal(prefix_operators=[], postfix_operators=[], qualifier=node.get("qualifier"), selectors=[], value=node.get("value") if node.get("value") is not None else node.get("text"))
        if kind == "MemberReference":
            return tree.MemberReference(prefix_operators=[], postfix_operators=[], qualifier=node.get("qualifier"), selectors=[], member=_render_name(node))
        if kind == "MethodInvocation":
            return tree.MethodInvocation(prefix_operators=[], postfix_operators=[], qualifier=node.get("qualifier"), selectors=[], type_arguments=self._many(grouped, "type_arguments"), arguments=self._many(grouped, "arguments"), member=_render_name(node))
        if kind == "BinaryOperation":
            return tree.BinaryOperation(operator=str(node.get("operator") or _render_name(node)), operandl=self._single(grouped, "operandl") or self._single(grouped, "left"), operandr=self._single(grouped, "operandr") or self._single(grouped, "right"))
        if kind == "Assignment":
            return tree.Assignment(expressionl=self._single(grouped, "expressionl") or self._single(grouped, "left"), value=self._single(grouped, "value") or self._single(grouped, "right"), type=str(node.get("type") or "="))
        if kind == "StatementExpression":
            return tree.StatementExpression(label=node.get("label"), expression=self._single(grouped, "expression"))
        if kind == "ReturnStatement":
            return tree.ReturnStatement(label=node.get("label"), expression=self._single(grouped, "expression"))
        if kind == "IfStatement":
            return tree.IfStatement(label=node.get("label"), condition=self._single(grouped, "condition") or self._single(grouped, "test"), then_statement=self._single(grouped, "then_statement") or self._single(grouped, "body"), else_statement=self._single(grouped, "else_statement") or self._single(grouped, "orelse"))
        if kind == "WhileStatement":
            return tree.WhileStatement(label=node.get("label"), condition=self._single(grouped, "condition") or self._single(grouped, "test"), body=self._single(grouped, "body"))
        if kind == "ForStatement":
            return tree.ForStatement(label=node.get("label"), control=self._single(grouped, "control"), body=self._single(grouped, "body"))
        if kind == "BlockStatement":
            return tree.BlockStatement(label=node.get("label"), statements=self._many(grouped, "statements"))
        if kind == "This":
            return tree.This(prefix_operators=[], postfix_operators=[], qualifier=node.get("qualifier"), selectors=[])
        if kind == "TryStatement":
            return tree.TryStatement(label=node.get("label"), resources=self._many(grouped, "resources"), block=self._many(grouped, "block"), catches=self._many(grouped, "catches"), finally_block=self._many(grouped, "finally_block"))
        if kind == "CatchClause":
            return tree.CatchClause(label=node.get("label"), parameter=self._single(grouped, "parameter"), block=self._many(grouped, "block"))
        if kind == "CatchClauseParameter":
            return tree.CatchClauseParameter(modifiers=_render_modifiers(node.get("modifiers")), annotations=self._many(grouped, "annotations"), types=self._many(grouped, "types"), name=_render_name(node))
        if kind == "ThrowStatement":
            return tree.ThrowStatement(label=node.get("label"), expression=self._single(grouped, "expression"))
        if kind == "ArrayInitializer":
            return tree.ArrayInitializer(initializers=self._many(grouped, "initializers"))
        if kind == "ArrayCreator":
            return tree.ArrayCreator(prefix_operators=[], postfix_operators=[], qualifier=node.get("qualifier"), selectors=[], type=self._single(grouped, "type"), dimensions=self._many(grouped, "dimensions"), initializer=self._single(grouped, "initializer"))
        if kind == "Annotation":
            return tree.Annotation(name=_render_name(node), element=self._single(grouped, "element"))
        if kind in {"BasicType", "ReferenceType", "ClassReference"}:
            if kind == "BasicType":
                return tree.BasicType(name=_render_name(node), dimensions=node.get("dimensions") or [])
            if kind == "ReferenceType":
                return tree.ReferenceType(name=_render_name(node), dimensions=node.get("dimensions") or [], arguments=self._many(grouped, "arguments") or None, sub_type=self._single(grouped, "sub_type"))
            return tree.ClassReference(prefix_operators=[], postfix_operators=[], qualifier=node.get("qualifier"), selectors=[], type=self._single(grouped, "type") or tree.ReferenceType(name=_render_name(node), dimensions=[], arguments=None, sub_type=None))

        raise JavaGraphError(f"unsupported Java AST node type: {kind}")


def graph_to_ast(graph_data: dict[str, Any]) -> Any:
    return JavaAstBuilder(graph_data).build()


def _flatten_block(items: Any) -> list[Any]:
    if items is None:
        return []
    if isinstance(items, list) and len(items) == 1 and type(items[0]).__name__ == "BlockStatement":
        return list(items[0].statements or [])
    return list(items) if isinstance(items, list) else [items]


def _render_expr(node: Any) -> str:
    if node is None:
        return ""
    kind = type(node).__name__
    if kind == "Literal":
        return _render_literal(node.value)
    if kind == "MemberReference":
        return f"{node.qualifier}.{node.member}" if getattr(node, "qualifier", None) else node.member
    if kind == "MethodInvocation":
        prefix = f"{node.qualifier}." if getattr(node, "qualifier", None) else ""
        return f"{prefix}{node.member}({', '.join(_render_expr(a) for a in (node.arguments or []))})"
    if kind == "BinaryOperation":
        return f"{_render_expr(node.operandl)} {node.operator} {_render_expr(node.operandr)}"
    if kind == "Assignment":
        return f"{_render_expr(node.expressionl)} {node.type} {_render_expr(node.value)}"
    if kind == "This":
        return "this"
    if kind == "Annotation":
        return _render_annotation(node)
    return str(node)


def _render_type(node: Any) -> str:
    if node is None:
        return ""
    kind = type(node).__name__
    if kind == "BasicType":
        return node.name + "[]" * len(getattr(node, "dimensions", []) or [])
    if kind == "ReferenceType":
        return node.name + ("[]" * len(getattr(node, "dimensions", []) or []))
    if kind == "ClassReference":
        return f"{_render_type(node.type)}.class"
    if kind == "Annotation":
        return _render_annotation(node)
    return _render_expr(node)


def _render_annotation(node: Any) -> str:
    text = f"@{node.name}"
    if getattr(node, "element", None) is not None:
        text += f"({_render_expr(node.element)})"
    return text


def _render_statement(node: Any, indent: int) -> str:
    pad = "    " * indent
    kind = type(node).__name__
    if kind == "StatementExpression":
        return f"{pad}{_render_expr(node.expression)};"
    if kind == "ReturnStatement":
        expr = _render_expr(node.expression)
        return f"{pad}return{(' ' + expr) if expr else ''};"
    if kind == "LocalVariableDeclaration":
        decls = ", ".join(_render_variable_decl(d) for d in (node.declarators or []))
        mods = sorted(node.modifiers) if getattr(node, "modifiers", None) else []
        prefix = (" ".join(mods) + " ") if mods else ""
        return f"{pad}{prefix}{_render_type(node.type)} {decls};"
    if kind == "IfStatement":
        then_text = _render_blockish(node.then_statement, indent)
        out = f"{pad}if ({_render_expr(node.condition)}) {then_text}"
        if getattr(node, "else_statement", None) is not None:
            out += f" else {_render_blockish(node.else_statement, indent)}"
        return out
    if kind == "WhileStatement":
        return f"{pad}while ({_render_expr(node.condition)}) {_render_blockish(node.body, indent)}"
    if kind == "ForStatement":
        return f"{pad}for (...) {_render_blockish(node.body, indent)}"
    if kind == "ThrowStatement":
        return f"{pad}throw {_render_expr(node.expression)};"
    if kind == "TryStatement":
        catches = " ".join(_render_catch(c, indent) for c in (node.catches or []))
        finally_block = f" finally {_render_blockish(node.finally_block, indent)}" if getattr(node, "finally_block", None) else ""
        return f"{pad}try {_render_blockish(node.block, indent)}{(' ' + catches) if catches else ''}{finally_block}"
    if kind == "BlockStatement":
        return _render_block(node.statements or [], indent)
    return f"{pad}{_render_expr(node)};"


def _render_block(items: Any, indent: int) -> str:
    stmts = _flatten_block(items)
    if not stmts:
        return "{}"
    inner = "\n".join(_render_statement(stmt, indent + 1) for stmt in stmts)
    return "{\n" + inner + "\n" + ("    " * indent) + "}"


def _render_blockish(node: Any, indent: int) -> str:
    if node is None:
        return "{}"
    if type(node).__name__ == "BlockStatement":
        return _render_block(node.statements or [], indent)
    if isinstance(node, list):
        return _render_block(node, indent)
    return _render_block([node], indent)


def _render_variable_decl(node: Any) -> str:
    text = str(node.name)
    if getattr(node, "initializer", None) is not None:
        text += f" = {_render_expr(node.initializer)}"
    return text


def _render_catch(node: Any, indent: int) -> str:
    param = node.parameter
    if param is None:
        return f"catch (Exception exc) {_render_block(node.block or [], indent)}"
    types = " | ".join(_render_type(item) for item in (param.types or [])) or "Exception"
    return f"catch ({types} {param.name}) {_render_block(node.block or [], indent)}"


def _render_member(node: Any, indent: int) -> str:
    pad = "    " * indent
    kind = type(node).__name__
    if kind == "FieldDeclaration":
        mods = sorted(node.modifiers) if getattr(node, "modifiers", None) else []
        prefix = (" ".join(mods) + " ") if mods else ""
        return f"{pad}{prefix}{_render_type(node.type)} {', '.join(_render_variable_decl(d) for d in (node.declarators or []))};"
    if kind == "MethodDeclaration":
        mods = sorted(node.modifiers) if getattr(node, "modifiers", None) else []
        prefix = (" ".join(mods) + " ") if mods else ""
        ret = _render_type(node.return_type) if getattr(node, "return_type", None) is not None else "void"
        params = ", ".join(_render_param(p) for p in (node.parameters or []))
        throws = ""
        if getattr(node, "throws", None):
            throws = " throws " + ", ".join(_render_type(t) for t in node.throws)
        return f"{pad}{prefix}{ret} {node.name}({params}){throws} {_render_block(node.body or [], indent)}"
    if kind == "ConstructorDeclaration":
        mods = sorted(node.modifiers) if getattr(node, "modifiers", None) else []
        prefix = (" ".join(mods) + " ") if mods else ""
        params = ", ".join(_render_param(p) for p in (node.parameters or []))
        throws = ""
        if getattr(node, "throws", None):
            throws = " throws " + ", ".join(_render_type(t) for t in node.throws)
        return f"{pad}{prefix}{node.name}({params}){throws} {_render_block(node.body or [], indent)}"
    if kind == "ClassDeclaration":
        mods = sorted(node.modifiers) if getattr(node, "modifiers", None) else []
        prefix = (" ".join(mods) + " ") if mods else ""
        extends = f" extends {_render_type(node.extends)}" if getattr(node, "extends", None) is not None else ""
        implements = ""
        if getattr(node, "implements", None):
            implements = " implements " + ", ".join(_render_type(item) for item in node.implements)
        body = "{}" if not (node.body or []) else "{\n" + "\n".join(_render_member(item, indent + 1) for item in node.body) + "\n" + pad + "}"
        return f"{pad}{prefix}class {node.name}{extends}{implements} {body}"
    return f"{pad}{kind}()"


def _render_param(node: Any) -> str:
    mods = sorted(node.modifiers) if getattr(node, "modifiers", None) else []
    prefix = (" ".join(mods) + " ") if mods else ""
    varargs = "..." if getattr(node, "varargs", False) else ""
    return f"{prefix}{_render_type(node.type)} {varargs}{node.name}".replace("  ", " ").strip()


def _render_import(node: Any) -> str:
    text = "import " + ("static " if getattr(node, "static", False) else "") + node.path
    if getattr(node, "wildcard", False):
        text += ".*"
    return text + ";"


def to_source(value: Any) -> str:
    if isinstance(value, dict):
        value = graph_to_ast(value)
    if value is None:
        return ""
    if type(value).__name__ == "CompilationUnit":
        parts: list[str] = []
        if getattr(value, "package", None) is not None:
            parts.append(f"package {value.package.name};")
        if getattr(value, "imports", None):
            if parts:
                parts.append("")
            parts.extend(_render_import(item) for item in value.imports)
        if getattr(value, "types", None):
            if parts:
                parts.append("")
            parts.extend(_render_member(item, 0) for item in value.types)
        return "\n".join(parts).rstrip() + ("\n" if parts else "")
    return _render_expr(value)


def to_dump(value: Any) -> str:
    return repr(graph_to_ast(value) if isinstance(value, dict) else value)


def from_json_file(path: str | Path) -> Any:
    return graph_to_ast(json.loads(Path(path).read_text(encoding="utf-8")))
