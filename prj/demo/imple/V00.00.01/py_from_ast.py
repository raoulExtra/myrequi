from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

SPECIAL_CONSTANTS = {
    "None": None,
    "null": None,
    "True": True,
    "False": False,
}

SIMPLE_NODES = {
    "Load": ast.Load,
    "Store": ast.Store,
    "Del": ast.Del,
    "Param": ast.Param,
    "Add": ast.Add,
    "Sub": ast.Sub,
    "Mult": ast.Mult,
    "Div": ast.Div,
    "Mod": ast.Mod,
    "Pow": ast.Pow,
    "LShift": ast.LShift,
    "RShift": ast.RShift,
    "BitOr": ast.BitOr,
    "BitXor": ast.BitXor,
    "BitAnd": ast.BitAnd,
    "FloorDiv": ast.FloorDiv,
    "MatMult": ast.MatMult,
    "And": ast.And,
    "Or": ast.Or,
    "Eq": ast.Eq,
    "NotEq": ast.NotEq,
    "Lt": ast.Lt,
    "LtE": ast.LtE,
    "Gt": ast.Gt,
    "GtE": ast.GtE,
    "Is": ast.Is,
    "IsNot": ast.IsNot,
    "In": ast.In,
    "NotIn": ast.NotIn,
    "UAdd": ast.UAdd,
    "USub": ast.USub,
    "Not": ast.Not,
    "Invert": ast.Invert,
    "Pass": ast.Pass,
    "Break": ast.Break,
    "Continue": ast.Continue,
}

LIST_FIELDS = {
    "Module": {"body", "type_ignores"},
    "If": {"body", "orelse"},
    "Expr": set(),
    "Assign": {"targets"},
    "FunctionDef": {"body", "decorator_list"},
    "Call": {"args", "keywords"},
    "arguments": {"posonlyargs", "args", "kwonlyargs", "kw_defaults", "defaults"},
    "keyword": set(),
    "BinOp": set(),
    "Return": set(),
}


def _coerce_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if text in SPECIAL_CONSTANTS:
        return SPECIAL_CONSTANTS[text]
    if text == "":
        return value
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return value


class GraphToAstError(ValueError):
    pass


class GraphAstBuilder:
    def __init__(self, graph_data: dict[str, Any]):
        if not isinstance(graph_data, dict):
            raise GraphToAstError("graph data must be an object")
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise GraphToAstError("graph data must contain nodes and edges arrays")
        self.nodes = nodes
        self.edges = edges
        self.node_map = {str(node.get("id")): node for node in nodes if isinstance(node, dict) and "id" in node}
        self.children: dict[str, list[tuple[str, int, int, str]]] = {}
        self.targets: set[str] = set()
        for edge_index, edge in enumerate(edges):
            if not isinstance(edge, dict) or "from" not in edge or "to" not in edge:
                raise GraphToAstError("each edge must contain from and to")
            source = str(edge["from"])
            target = str(edge["to"])
            label = str(edge.get("label") or "")
            order_value = edge.get("order", edge_index)
            if isinstance(order_value, bool) or not isinstance(order_value, (int, float)):
                raise GraphToAstError("each edge order must be numeric when present")
            order = int(order_value)
            self.children.setdefault(source, []).append((label, order, edge_index, target))
            self.targets.add(target)

    def build(self) -> ast.AST:
        root_id = self._find_root_id()
        tree = self._convert_node(root_id)
        if not isinstance(tree, ast.AST):
            raise GraphToAstError("root did not convert to an AST node")
        return ast.fix_missing_locations(tree)

    def _find_root_id(self) -> str:
        for node in self.nodes:
            if not isinstance(node, dict) or "id" not in node:
                continue
            node_id = str(node["id"])
            if node_id not in self.targets:
                return node_id
        if self.nodes:
            first = self.nodes[0]
            if isinstance(first, dict) and "id" in first:
                return str(first["id"])
        raise GraphToAstError("graph has no nodes")

    def _node_type(self, node: dict[str, Any]) -> str:
        node_type = node.get("type") or node.get("label") or node.get("text")
        if not isinstance(node_type, str) or not node_type:
            raise GraphToAstError("each node must have a type, label, or text")
        return node_type

    def _children_for(self, node_id: str) -> dict[str, list[str]]:
        grouped: dict[str, list[tuple[int, int, str]]] = {}
        for label, order, edge_index, target in self.children.get(node_id, []):
            grouped.setdefault(label, []).append((order, edge_index, target))
        return {
            label: [target for _, _, target in sorted(items, key=lambda item: (item[0], item[1]))]
            for label, items in grouped.items()
        }

    def _single_child(self, grouped: dict[str, list[str]], label: str) -> ast.AST | None:
        targets = grouped.get(label, [])
        if not targets:
            return None
        if len(targets) != 1:
            raise GraphToAstError(f"field {label} expects one child")
        return self._convert_node(targets[0])

    def _child_list(self, grouped: dict[str, list[str]], label: str) -> list[Any]:
        return [self._convert_node(target) for target in grouped.get(label, [])]

    def _convert_node(self, node_id: str) -> Any:
        if node_id not in self.node_map:
            raise GraphToAstError(f"missing node {node_id}")
        node = self.node_map[node_id]
        node_type = self._node_type(node)
        grouped = self._children_for(node_id)

        if node_type in SIMPLE_NODES:
            return SIMPLE_NODES[node_type]()

        if node_type == "Module":
            return ast.Module(
                body=self._child_list(grouped, "body"),
                type_ignores=self._child_list(grouped, "type_ignores"),
            )
        if node_type == "Assign":
            return ast.Assign(
                targets=self._child_list(grouped, "targets"),
                value=self._single_child(grouped, "value"),
                type_comment=node.get("type_comment"),
            )
        if node_type == "AnnAssign":
            return ast.AnnAssign(
                target=self._single_child(grouped, "target"),
                annotation=self._single_child(grouped, "annotation"),
                value=self._single_child(grouped, "value"),
                simple=int(node.get("simple", 1) or 1),
            )
        if node_type == "Delete":
            return ast.Delete(targets=self._child_list(grouped, "targets"))
        if node_type == "Assert":
            return ast.Assert(test=self._single_child(grouped, "test"), msg=self._single_child(grouped, "msg"))
        if node_type == "Name":
            return ast.Name(
                id=str(node.get("text") or node.get("label") or node.get("id")),
                ctx=self._single_child(grouped, "ctx") or ast.Load(),
            )
        if node_type == "Constant":
            value = node.get("value", node.get("text"))
            if value is None and node.get("text") is not None:
                value = node.get("text")
            return ast.Constant(value=_coerce_value(value), kind=node.get("kind"))
        if node_type == "Expr":
            return ast.Expr(value=self._single_child(grouped, "value"))
        if node_type == "If":
            return ast.If(
                test=self._single_child(grouped, "test"),
                body=self._child_list(grouped, "body"),
                orelse=self._child_list(grouped, "orelse"),
            )
        if node_type == "AsyncFor":
            return ast.AsyncFor(
                target=self._single_child(grouped, "target"),
                iter=self._single_child(grouped, "iter"),
                body=self._child_list(grouped, "body"),
                orelse=self._child_list(grouped, "orelse"),
                type_comment=node.get("type_comment"),
            )
        if node_type == "AsyncWith":
            return ast.AsyncWith(items=self._child_list(grouped, "items"), body=self._child_list(grouped, "body"), type_comment=node.get("type_comment"))
        if node_type == "Call":
            return ast.Call(
                func=self._single_child(grouped, "func"),
                args=self._child_list(grouped, "args"),
                keywords=self._child_list(grouped, "keywords"),
            )
        if node_type == "keyword":
            return ast.keyword(arg=node.get("arg"), value=self._single_child(grouped, "value"))
        if node_type == "List":
            return ast.List(elts=self._child_list(grouped, "elts"), ctx=self._single_child(grouped, "ctx") or ast.Load())
        if node_type == "Tuple":
            return ast.Tuple(elts=self._child_list(grouped, "elts"), ctx=self._single_child(grouped, "ctx") or ast.Load())
        if node_type == "Set":
            return ast.Set(elts=self._child_list(grouped, "elts"))
        if node_type == "Dict":
            return ast.Dict(keys=self._child_list(grouped, "keys"), values=self._child_list(grouped, "values"))
        if node_type == "UnaryOp":
            return ast.UnaryOp(op=self._single_child(grouped, "op"), operand=self._single_child(grouped, "operand"))
        if node_type == "BoolOp":
            return ast.BoolOp(op=self._single_child(grouped, "op"), values=self._child_list(grouped, "values"))
        if node_type == "Subscript":
            return ast.Subscript(value=self._single_child(grouped, "value"), slice=self._single_child(grouped, "slice"), ctx=self._single_child(grouped, "ctx") or ast.Load())
        if node_type == "Return":
            return ast.Return(value=self._single_child(grouped, "value"))
        if node_type == "Await":
            return ast.Await(value=self._single_child(grouped, "value"))
        if node_type == "Yield":
            return ast.Yield(value=self._single_child(grouped, "value"))
        if node_type == "YieldFrom":
            return ast.YieldFrom(value=self._single_child(grouped, "value"))
        if node_type == "FunctionDef":
            return ast.FunctionDef(
                name=str(node.get("text") or node.get("name") or node.get("label") or node.get("id")),
                args=self._single_child(grouped, "args") or ast.arguments(
                    posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]
                ),
                body=self._child_list(grouped, "body"),
                decorator_list=self._child_list(grouped, "decorator_list"),
                returns=self._single_child(grouped, "returns"),
                type_comment=node.get("type_comment"),
            )
        if node_type == "AsyncFunctionDef":
            return ast.AsyncFunctionDef(
                name=str(node.get("text") or node.get("name") or node.get("label") or node.get("id")),
                args=self._single_child(grouped, "args") or ast.arguments(
                    posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]
                ),
                body=self._child_list(grouped, "body"),
                decorator_list=self._child_list(grouped, "decorator_list"),
                returns=self._single_child(grouped, "returns"),
                type_comment=node.get("type_comment"),
            )
        if node_type == "ClassDef":
            return ast.ClassDef(
                name=str(node.get("text") or node.get("name") or node.get("label") or node.get("id")),
                bases=self._child_list(grouped, "bases"),
                keywords=self._child_list(grouped, "keywords"),
                body=self._child_list(grouped, "body"),
                decorator_list=self._child_list(grouped, "decorator_list"),
            )
        if node_type == "arguments":
            return ast.arguments(
                posonlyargs=self._child_list(grouped, "posonlyargs"),
                args=self._child_list(grouped, "args"),
                vararg=self._single_child(grouped, "vararg"),
                kwonlyargs=self._child_list(grouped, "kwonlyargs"),
                kw_defaults=self._child_list(grouped, "kw_defaults"),
                kwarg=self._single_child(grouped, "kwarg"),
                defaults=self._child_list(grouped, "defaults"),
            )
        if node_type == "arg":
            return ast.arg(arg=str(node.get("text") or node.get("arg") or node.get("label") or node.get("id")), annotation=self._single_child(grouped, "annotation"), type_comment=node.get("type_comment"))
        if node_type == "alias":
            return ast.alias(name=str(node.get("name") or node.get("text") or node.get("label") or node.get("id")), asname=node.get("asname"))
        if node_type == "Import":
            return ast.Import(names=self._child_list(grouped, "names"))
        if node_type == "ImportFrom":
            return ast.ImportFrom(
                module=node.get("module") or node.get("text"),
                names=self._child_list(grouped, "names"),
                level=int(node.get("level", 0) or 0),
            )
        if node_type == "Try":
            return ast.Try(
                body=self._child_list(grouped, "body"),
                handlers=self._child_list(grouped, "handlers"),
                orelse=self._child_list(grouped, "orelse"),
                finalbody=self._child_list(grouped, "finalbody"),
            )
        if node_type == "ExceptHandler":
            return ast.ExceptHandler(
                type=self._single_child(grouped, "type"),
                name=node.get("name"),
                body=self._child_list(grouped, "body"),
            )
        if node_type == "Raise":
            return ast.Raise(exc=self._single_child(grouped, "exc"), cause=self._single_child(grouped, "cause"))
        if node_type == "Attribute":
            return ast.Attribute(
                value=self._single_child(grouped, "value"),
                attr=str(node.get("attr") or node.get("text") or node.get("label") or node.get("id")),
                ctx=self._single_child(grouped, "ctx") or ast.Load(),
            )
        if node_type == "Compare":
            return ast.Compare(
                left=self._single_child(grouped, "left"),
                ops=self._child_list(grouped, "ops"),
                comparators=self._child_list(grouped, "comparators"),
            )
        if node_type == "For":
            return ast.For(
                target=self._single_child(grouped, "target"),
                iter=self._single_child(grouped, "iter"),
                body=self._child_list(grouped, "body"),
                orelse=self._child_list(grouped, "orelse"),
                type_comment=node.get("type_comment"),
            )
        if node_type == "While":
            return ast.While(
                test=self._single_child(grouped, "test"),
                body=self._child_list(grouped, "body"),
                orelse=self._child_list(grouped, "orelse"),
            )
        if node_type == "withitem":
            return ast.withitem(context_expr=self._single_child(grouped, "context_expr"), optional_vars=self._single_child(grouped, "optional_vars"))
        if node_type == "With":
            return ast.With(items=self._child_list(grouped, "items"), body=self._child_list(grouped, "body"), type_comment=node.get("type_comment"))
        if node_type == "Match":
            return ast.Match(subject=self._single_child(grouped, "subject"), cases=self._child_list(grouped, "cases"))
        if node_type == "match_case":
            return ast.match_case(pattern=self._single_child(grouped, "pattern"), guard=self._single_child(grouped, "guard"), body=self._child_list(grouped, "body"))
        if node_type == "MatchValue":
            return ast.MatchValue(value=self._single_child(grouped, "value"))
        if node_type == "MatchAs":
            return ast.MatchAs(pattern=self._single_child(grouped, "pattern"), name=node.get("name"))
        if node_type == "Lambda":
            return ast.Lambda(args=self._single_child(grouped, "args") or ast.arguments(
                posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]
            ), body=self._single_child(grouped, "body"))
        if node_type == "IfExp":
            return ast.IfExp(test=self._single_child(grouped, "test"), body=self._single_child(grouped, "body"), orelse=self._single_child(grouped, "orelse"))
        if node_type == "List":
            return ast.List(elts=self._child_list(grouped, "elts"), ctx=self._single_child(grouped, "ctx") or ast.Load())
        if node_type == "Tuple":
            return ast.Tuple(elts=self._child_list(grouped, "elts"), ctx=self._single_child(grouped, "ctx") or ast.Load())
        if node_type == "Set":
            return ast.Set(elts=self._child_list(grouped, "elts"))
        if node_type == "Dict":
            return ast.Dict(keys=self._child_list(grouped, "keys"), values=self._child_list(grouped, "values"))
        if node_type == "UnaryOp":
            return ast.UnaryOp(op=self._single_child(grouped, "op"), operand=self._single_child(grouped, "operand"))
        if node_type == "BoolOp":
            return ast.BoolOp(op=self._single_child(grouped, "op"), values=self._child_list(grouped, "values"))
        if node_type == "Subscript":
            return ast.Subscript(value=self._single_child(grouped, "value"), slice=self._single_child(grouped, "slice"), ctx=self._single_child(grouped, "ctx") or ast.Load())
        if node_type == "comprehension":
            return ast.comprehension(
                target=self._single_child(grouped, "target"),
                iter=self._single_child(grouped, "iter"),
                ifs=self._child_list(grouped, "ifs"),
                is_async=int(node.get("is_async", 0) or 0),
            )
        if node_type == "ListComp":
            return ast.ListComp(elt=self._single_child(grouped, "elt"), generators=self._child_list(grouped, "generators"))
        if node_type == "SetComp":
            return ast.SetComp(elt=self._single_child(grouped, "elt"), generators=self._child_list(grouped, "generators"))
        if node_type == "GeneratorExp":
            return ast.GeneratorExp(elt=self._single_child(grouped, "elt"), generators=self._child_list(grouped, "generators"))
        if node_type == "DictComp":
            return ast.DictComp(key=self._single_child(grouped, "key"), value=self._single_child(grouped, "value"), generators=self._child_list(grouped, "generators"))
        if node_type == "BinOp":
            return ast.BinOp(
                left=self._single_child(grouped, "left"),
                op=self._single_child(grouped, "op"),
                right=self._single_child(grouped, "right"),
            )

        raise GraphToAstError(f"unsupported AST node type: {node_type}")


def graph_to_ast(graph_data: dict[str, Any]) -> ast.AST:
    return GraphAstBuilder(graph_data).build()


def to_dump(graph_data: dict[str, Any]) -> str:
    return ast.dump(graph_to_ast(graph_data), include_attributes=False)


def from_json_file(path: str | Path) -> ast.AST:
    import json

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return graph_to_ast(data)
