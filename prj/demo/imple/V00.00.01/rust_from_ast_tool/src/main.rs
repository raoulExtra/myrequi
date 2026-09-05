use serde::Deserialize;
use serde_json::Value;
use std::collections::{HashMap, HashSet};
use std::env;
use std::error::Error;
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Deserialize)]
struct Graph {
    nodes: Vec<Node>,
    edges: Vec<Edge>,
}

#[derive(Debug, Deserialize, Clone)]
struct Node {
    id: Value,
    #[serde(default)]
    label: Option<String>,
    #[serde(default)]
    text: Option<String>,
    #[serde(flatten)]
    extra: HashMap<String, Value>,
}

#[derive(Debug, Deserialize)]
struct Edge {
    from: Value,
    to: Value,
    #[serde(default)]
    label: Option<String>,
    #[serde(default)]
    order: Option<Value>,
}

struct Builder {
    nodes: HashMap<String, Node>,
    children: HashMap<String, Vec<(String, i64, usize, String)>>,
    targets: HashSet<String>,
}

impl Builder {
    fn new(graph: Graph) -> Self {
        let mut nodes = HashMap::new();
        for node in graph.nodes {
            nodes.insert(key(&node.id), node);
        }

        let mut children: HashMap<String, Vec<(String, i64, usize, String)>> = HashMap::new();
        let mut targets = HashSet::new();
        for (edge_index, edge) in graph.edges.into_iter().enumerate() {
            let source = key(&edge.from);
            let target = key(&edge.to);
            let label = edge.label.unwrap_or_default();
            let order = edge.order.as_ref().and_then(value_to_i64).unwrap_or(edge_index as i64);
            children
                .entry(source)
                .or_default()
                .push((label, order, edge_index, target.clone()));
            targets.insert(target);
        }

        Self { nodes, children, targets }
    }

    fn build(&self) -> Result<String, String> {
        let root = self.find_root()?;
        let mut out = self.render_item(&root, 0)?;
        if !out.ends_with('\n') {
            out.push('\n');
        }
        Ok(out)
    }

    fn find_root(&self) -> Result<String, String> {
        for node in self.nodes.values() {
            let id = key(&node.id);
            if !self.targets.contains(&id) {
                return Ok(id);
            }
        }
        self.nodes
            .values()
            .next()
            .map(|node| key(&node.id))
            .ok_or_else(|| "graph has no nodes".to_string())
    }

    fn node(&self, id: &str) -> Result<&Node, String> {
        self.nodes.get(id).ok_or_else(|| format!("missing node {id}"))
    }

    fn kind(&self, id: &str) -> Result<String, String> {
        let node = self.node(id)?;
        Ok(node.label.clone().or_else(|| node.text.clone()).unwrap_or_else(|| id.to_string()))
    }

    fn text(&self, id: &str) -> Result<String, String> {
        let node = self.node(id)?;
        Ok(node.text.clone().or_else(|| node.label.clone()).unwrap_or_else(|| id.to_string()))
    }

    fn grouped(&self, id: &str) -> HashMap<String, Vec<String>> {
        let mut grouped: HashMap<String, Vec<(i64, usize, String)>> = HashMap::new();
        if let Some(children) = self.children.get(id) {
            for (label, order, edge_index, target) in children {
                grouped.entry(label.clone()).or_default().push((*order, *edge_index, target.clone()));
            }
        }
        grouped
            .into_iter()
            .map(|(label, mut items)| {
                items.sort_by_key(|item| (item.0, item.1));
                (label, items.into_iter().map(|item| item.2).collect())
            })
            .collect()
    }

    fn children_for(&self, grouped: &HashMap<String, Vec<String>>, label: &str) -> Vec<String> {
        grouped.get(label).cloned().unwrap_or_default()
    }

    fn single_child(&self, grouped: &HashMap<String, Vec<String>>, label: &str) -> Result<Option<String>, String> {
        let targets = self.children_for(grouped, label);
        if targets.is_empty() {
            return Ok(None);
        }
        if targets.len() != 1 {
            return Err(format!("field {label} expects one child"));
        }
        Ok(Some(targets[0].clone()))
    }

    fn render_items(&self, ids: &[String], indent: usize) -> Result<String, String> {
        let mut out = String::new();
        for id in ids {
            let rendered = self.render_item(id, indent)?;
            if !rendered.is_empty() {
                out.push_str(&rendered);
                if !rendered.ends_with('\n') {
                    out.push('\n');
                }
            }
        }
        Ok(out)
    }

    fn render_block(&self, ids: &[String], indent: usize) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let mut out = format!("{pad}{{\n");
        out.push_str(&self.render_items(ids, indent + 1)?);
        out.push_str(&format!("{pad}}}\n"));
        Ok(out)
    }

    fn render_item(&self, id: &str, indent: usize) -> Result<String, String> {
        let kind = self.kind(id)?;
        let grouped = self.grouped(id);
        let pad = "    ".repeat(indent);

        match kind.as_str() {
            "Module" | "File" => {
                let mut items = self.children_for(&grouped, "body");
                if items.is_empty() {
                    items = self.children_for(&grouped, "items");
                }
                if items.is_empty() {
                    items = self.children_for(&grouped, "statements");
                }
                self.render_items(&items, indent)
            }
            "Use" => {
                let path = self.render_use_path(id, &grouped)?;
                Ok(format!("{pad}use {path};\n"))
            }
            "Comment" | "LineComment" | "BlockComment" => self.render_comment(id, indent, false),
            "DocComment" | "Doc" => self.render_comment(id, indent, true),
            "Struct" => self.render_struct(id, indent, &grouped),
            "Enum" => self.render_enum(id, indent, &grouped),
            "Trait" => self.render_trait(id, indent, &grouped),
            "Impl" => self.render_impl(id, indent, &grouped),
            "Function" | "Fn" | "FunctionDef" | "ItemFn" => self.render_function(id, indent, &grouped),
            "Const" => self.render_const(id, indent, &grouped),
            "TypeAlias" => self.render_type_alias(id, indent, &grouped),
            "Let" | "LetStmt" => self.render_let(id, indent, &grouped),
            "Expr" | "ExpressionStatement" | "Stmt" => {
                let value = self.single_child(&grouped, "value")?.ok_or_else(|| format!("{kind} missing value"))?;
                Ok(format!("{pad}{};\n", self.render_expr(&value)?))
            }
            "Return" => {
                let value = self.single_child(&grouped, "value")?;
                let expr = match value {
                    Some(child) => self.render_expr(&child)?,
                    None => "()".to_string(),
                };
                Ok(format!("{pad}return {expr};\n"))
            }
            "If" | "IfStmt" => self.render_if_stmt(id, indent, &grouped),
            "Match" => self.render_match_stmt(id, indent, &grouped),
            "While" | "WhileStmt" => self.render_while(id, indent, &grouped),
            "Loop" => {
                let body = self.children_for(&grouped, "body");
                Ok(format!("{pad}loop {}", self.render_block(&body, indent)?))
            }
            "For" | "ForStmt" => self.render_for(id, indent, &grouped),
            "Break" => Ok(format!("{pad}break;\n")),
            "Continue" => Ok(format!("{pad}continue;\n")),
            "Block" => self.render_block(&self.children_for(&grouped, "statements"), indent),
            "Macro" => {
                let name = sanitize_ident(&self.text(id)?);
                Ok(format!("{pad}{name}!();\n"))
            }
            _ => Ok(format!("{pad}// unsupported node {kind}: {}\n", self.text(id)?)),
        }
    }

    fn render_function(&self, id: &str, indent: usize, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let name = sanitize_ident(&self.text(id)?);
        let prefix = self.visibility_prefix(id);
        let mut params = Vec::new();
        for param in self.children_for(grouped, "params") {
            params.push(self.render_param(&param)?);
        }
        if params.is_empty() {
            for param in self.children_for(grouped, "args") {
                params.push(self.render_param(&param)?);
            }
        }
        let return_type = self.render_return_type(grouped)?.unwrap_or_default();
        let generics = self.render_generics(grouped)?;
        let body = self.children_for(grouped, "body");
        let mut out = format!("{pad}{prefix}fn {name}{generics}({}){} {{\n", params.join(", "), return_type);
        out.push_str(&self.render_items(&body, indent + 1)?);
        out.push_str(&format!("{pad}}}\n"));
        Ok(out)
    }

    fn render_comment(&self, id: &str, indent: usize, doc: bool) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let text = self.text(id)?;
        let prefix = if doc { "/// " } else { "// " };
        let mut out = String::new();
        let lines: Vec<&str> = text.lines().collect();
        if lines.is_empty() {
            out.push_str(&format!("{pad}{prefix}\n"));
        } else {
            for line in lines {
                out.push_str(&format!("{pad}{prefix}{}\n", line.trim_end()));
            }
        }
        Ok(out)
    }

    fn render_struct(&self, id: &str, indent: usize, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let name = sanitize_ident(&self.text(id)?);
        let prefix = self.visibility_prefix(id);
        let generics = self.render_generics(grouped)?;
        let fields = if self.children_for(grouped, "fields").is_empty() {
            self.children_for(grouped, "body")
        } else {
            self.children_for(grouped, "fields")
        };
        if fields.is_empty() {
            return Ok(format!("{pad}{prefix}struct {name}{generics};\n"));
        }
        let mut out = format!("{pad}{prefix}struct {name}{generics} {{\n");
        for field_id in fields {
            out.push_str(&self.render_struct_field(&field_id, indent + 1)?);
        }
        out.push_str(&format!("{pad}}}\n"));
        Ok(out)
    }

    fn render_enum(&self, id: &str, indent: usize, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let name = sanitize_ident(&self.text(id)?);
        let prefix = self.visibility_prefix(id);
        let generics = self.render_generics(grouped)?;
        let variants = if self.children_for(grouped, "variants").is_empty() {
            self.children_for(grouped, "body")
        } else {
            self.children_for(grouped, "variants")
        };
        if variants.is_empty() {
            return Ok(format!("{pad}{prefix}enum {name}{generics} {{}}\n"));
        }
        let mut out = format!("{pad}{prefix}enum {name}{generics} {{\n");
        for variant_id in variants {
            out.push_str(&self.render_enum_variant(&variant_id, indent + 1)?);
        }
        out.push_str(&format!("{pad}}}\n"));
        Ok(out)
    }

    fn render_trait(&self, id: &str, indent: usize, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let name = sanitize_ident(&self.text(id)?);
        let prefix = self.visibility_prefix(id);
        let generics = self.render_generics(grouped)?;
        let items = self.children_for(grouped, "body");
        if items.is_empty() {
            return Ok(format!("{pad}{prefix}trait {name}{generics} {{}}\n"));
        }
        let mut out = format!("{pad}{prefix}trait {name}{generics} {{\n");
        out.push_str(&self.render_items(&items, indent + 1)?);
        out.push_str(&format!("{pad}}}\n"));
        Ok(out)
    }

    fn render_impl(&self, id: &str, indent: usize, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let prefix = self.visibility_prefix(id);
        let generics = self.render_generics(grouped)?;
        let trait_type = self
            .single_child(grouped, "trait")?
            .map(|t| self.render_type(&t))
            .transpose()?;
        let for_type = self
            .single_child(grouped, "for")?
            .or_else(|| self.single_child(grouped, "for_type").ok().flatten())
            .or_else(|| self.single_child(grouped, "type").ok().flatten())
            .ok_or_else(|| "Impl missing target type".to_string())?;
        let body = self.children_for(grouped, "body");
        let head = if let Some(trait_type) = trait_type {
            format!("{pad}{prefix}impl{generics} {trait_type} for {} {{\n", self.render_type(&for_type)?)
        } else {
            format!("{pad}{prefix}impl{generics} {} {{\n", self.render_type(&for_type)?)
        };
        let mut out = head;
        out.push_str(&self.render_items(&body, indent + 1)?);
        out.push_str(&format!("{pad}}}\n"));
        Ok(out)
    }

    fn render_const(&self, id: &str, indent: usize, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let name = sanitize_ident(&self.text(id)?);
        let prefix = self.visibility_prefix(id);
        let ty = self
            .single_child(grouped, "type")?
            .or_else(|| self.single_child(grouped, "ty").ok().flatten())
            .map(|node| self.render_type(&node))
            .transpose()?;
        let value = self
            .single_child(grouped, "value")?
            .ok_or_else(|| "Const missing value".to_string())?;
        let ty_text = ty.map(|t| format!(": {t}"));
        Ok(format!("{pad}{prefix}const {name}{} = {};\n", ty_text.unwrap_or_default(), self.render_expr(&value)?))
    }

    fn render_type_alias(&self, id: &str, indent: usize, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let name = sanitize_ident(&self.text(id)?);
        let prefix = self.visibility_prefix(id);
        let target = self
            .single_child(grouped, "type")?
            .or_else(|| self.single_child(grouped, "value").ok().flatten())
            .ok_or_else(|| "TypeAlias missing target type".to_string())?;
        Ok(format!("{pad}{prefix}type {name} = {};\n", self.render_type(&target)?))
    }

    fn render_let(&self, id: &str, indent: usize, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let mutable = self.truthy_extra(id, &["mutable", "mut"]);
        let pattern = self
            .single_child(grouped, "pattern")?
            .or_else(|| self.single_child(grouped, "target").ok().flatten())
            .ok_or_else(|| "Let missing target".to_string())?;
        let value = self
            .single_child(grouped, "value")?
            .ok_or_else(|| "Let missing value".to_string())?;
        let ty = self
            .single_child(grouped, "type")?
            .or_else(|| self.single_child(grouped, "ty").ok().flatten())
            .map(|node| self.render_type(&node))
            .transpose()?;
        let mut_prefix = if mutable { "mut " } else { "" };
        let ty_suffix = ty.map(|t| format!(": {t}"));
        Ok(format!("{pad}let {mut_prefix}{}{} = {};\n", self.render_pattern(&pattern)?, ty_suffix.unwrap_or_default(), self.render_expr(&value)?))
    }

    fn render_if_stmt(&self, _id: &str, indent: usize, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let test = self
            .single_child(grouped, "test")?
            .or_else(|| self.single_child(grouped, "condition").ok().flatten())
            .ok_or_else(|| "If missing condition".to_string())?;
        let body = self.children_for(grouped, "body");
        let orelse = self.children_for(grouped, "orelse");
        let mut out = format!("{pad}if {} {{\n", self.render_expr(&test)?);
        out.push_str(&self.render_items(&body, indent + 1)?);
        out.push_str(&format!("{pad}}}"));
        if !orelse.is_empty() {
            if orelse.len() == 1 && self.kind(&orelse[0])? == "If" {
                out.push_str(" else ");
                out.push_str(&self.render_item(&orelse[0], indent)?);
            } else {
                out.push_str(" else ");
                out.push_str(&self.render_block(&orelse, indent)?);
            }
        } else {
            out.push('\n');
        }
        Ok(out)
    }

    fn render_match_stmt(&self, _id: &str, indent: usize, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let expr = self
            .single_child(grouped, "subject")?
            .or_else(|| self.single_child(grouped, "value").ok().flatten())
            .or_else(|| self.single_child(grouped, "expr").ok().flatten())
            .ok_or_else(|| "Match missing subject".to_string())?;
        let arms = if self.children_for(grouped, "arms").is_empty() {
            self.children_for(grouped, "cases")
        } else {
            self.children_for(grouped, "arms")
        };
        let mut out = format!("{pad}match {} {{\n", self.render_expr(&expr)?);
        for arm_id in arms {
            out.push_str(&self.render_match_arm(&arm_id, indent + 1)?);
        }
        out.push_str(&format!("{pad}}}\n"));
        Ok(out)
    }

    fn render_while(&self, _id: &str, indent: usize, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let test = self
            .single_child(grouped, "condition")?
            .or_else(|| self.single_child(grouped, "test").ok().flatten())
            .ok_or_else(|| "While missing condition".to_string())?;
        let body = self.children_for(grouped, "body");
        let mut out = format!("{pad}while {} {{\n", self.render_expr(&test)?);
        out.push_str(&self.render_items(&body, indent + 1)?);
        out.push_str(&format!("{pad}}}\n"));
        Ok(out)
    }

    fn render_for(&self, _id: &str, indent: usize, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let pattern = self
            .single_child(grouped, "target")?
            .or_else(|| self.single_child(grouped, "pattern").ok().flatten())
            .ok_or_else(|| "For missing target".to_string())?;
        let iter = self
            .single_child(grouped, "iter")?
            .or_else(|| self.single_child(grouped, "in").ok().flatten())
            .ok_or_else(|| "For missing iterator".to_string())?;
        let body = self.children_for(grouped, "body");
        let mut out = format!("{pad}for {} in {} {{\n", self.render_pattern(&pattern)?, self.render_expr(&iter)?);
        out.push_str(&self.render_items(&body, indent + 1)?);
        out.push_str(&format!("{pad}}}\n"));
        Ok(out)
    }

    fn render_struct_field(&self, id: &str, indent: usize) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let kind = self.kind(id)?;
        let name = sanitize_ident(&self.text(id)?);
        let grouped = self.grouped(id);
        let prefix = self.visibility_prefix(id);
        let ty = self
            .single_child(&grouped, "type")?
            .or_else(|| self.single_child(&grouped, "ty").ok().flatten())
            .map(|node| self.render_type(&node))
            .transpose()?;
        if kind == "TupleField" || kind == "UnnamedField" {
            if let Some(ty) = ty {
                Ok(format!("{pad}{prefix}{ty},\n"))
            } else {
                Ok(format!("{pad}{prefix}{name},\n"))
            }
        } else {
            let ty_text = ty.unwrap_or_else(|| "()".to_string());
            Ok(format!("{pad}{prefix}{name}: {ty_text},\n"))
        }
    }

    fn render_enum_variant(&self, id: &str, indent: usize) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let kind = self.kind(id)?;
        let name = sanitize_ident(&self.text(id)?);
        let grouped = self.grouped(id);
        let fields = self.children_for(&grouped, "fields");
        let ty = self
            .single_child(&grouped, "type")?
            .or_else(|| self.single_child(&grouped, "ty").ok().flatten())
            .map(|node| self.render_type(&node))
            .transpose()?;
        if kind == "TupleVariant" {
            let inner = if fields.is_empty() { String::new() } else { fields.iter().map(|f| self.render_type(f).unwrap_or_else(|_| "()".to_string())).collect::<Vec<_>>().join(", ") };
            return Ok(format!("{pad}{name}({inner}),\n"));
        }
        if kind == "StructVariant" {
            let mut out = format!("{pad}{name} {{\n");
            for field_id in fields {
                out.push_str(&self.render_struct_field(&field_id, indent + 1)?);
            }
            out.push_str(&format!("{pad}}},\n"));
            return Ok(out);
        }
        if let Some(ty) = ty {
            Ok(format!("{pad}{name} = {ty},\n"))
        } else {
            Ok(format!("{pad}{name},\n"))
        }
    }

    fn render_match_arm(&self, id: &str, indent: usize) -> Result<String, String> {
        let pad = "    ".repeat(indent);
        let grouped = self.grouped(id);
        let pattern = self
            .single_child(&grouped, "pattern")?
            .or_else(|| self.single_child(&grouped, "pat").ok().flatten())
            .or_else(|| self.single_child(&grouped, "lhs").ok().flatten())
            .ok_or_else(|| "Match arm missing pattern".to_string())?;
        let guard = self.single_child(&grouped, "guard")?;
        let body = self.children_for(&grouped, "body");
        let value = self
            .single_child(&grouped, "value")?
            .or_else(|| self.single_child(&grouped, "expr").ok().flatten());
        let mut head = self.render_pattern(&pattern)?;
        if let Some(guard_id) = guard {
            head.push_str(&format!(" if {}", self.render_expr(&guard_id)?));
        }
        if let Some(expr_id) = value {
            Ok(format!("{pad}{head} => {},\n", self.render_expr(&expr_id)?))
        } else if !body.is_empty() {
            let mut out = format!("{pad}{head} => {{\n");
            out.push_str(&self.render_items(&body, indent + 1)?);
            out.push_str(&format!("{pad}}},\n"));
            Ok(out)
        } else {
            Ok(format!("{pad}{head} => (),\n"))
        }
    }

    fn render_use_path(&self, id: &str, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        if let Some(path) = self.single_child(grouped, "path")? {
            return self.render_path_like(&path);
        }
        if let Some(tree) = self.single_child(grouped, "tree")? {
            return self.render_path_like(&tree);
        }
        Ok(self.text(id)?)
    }

    fn render_generics(&self, grouped: &HashMap<String, Vec<String>>) -> Result<String, String> {
        let params = self.children_for(grouped, "generics");
        if params.is_empty() {
            return Ok(String::new());
        }
        let mut parts = Vec::new();
        for param in params {
            parts.push(self.render_path_like(&param)?);
        }
        Ok(format!("<{}>", parts.join(", ")))
    }

    fn render_return_type(&self, grouped: &HashMap<String, Vec<String>>) -> Result<Option<String>, String> {
        if let Some(node) = self.single_child(grouped, "return_type")? {
            return Ok(Some(format!(" -> {}", self.render_type(&node)?)));
        }
        if let Some(node) = self.single_child(grouped, "ret")? {
            return Ok(Some(format!(" -> {}", self.render_type(&node)?)));
        }
        Ok(None)
    }

    fn render_param(&self, id: &str) -> Result<String, String> {
        let kind = self.kind(id)?;
        let grouped = self.grouped(id);
        let text = self.text(id)?;
        let (name, ty) = if let Some((left, right)) = text.split_once(':') {
            (left.trim(), right.trim())
        } else {
            (text.trim(), "i32")
        };
        let mut_prefix = if self.truthy_extra(id, &["mutable", "mut"]) { "mut " } else { "" };
        let pat = self
            .single_child(&grouped, "pattern")?
            .or_else(|| self.single_child(&grouped, "target").ok().flatten())
            .map(|node| self.render_pattern(&node))
            .transpose()?
            .unwrap_or_else(|| sanitize_ident(name));
        let ty_rendered = self
            .single_child(&grouped, "type")?
            .or_else(|| self.single_child(&grouped, "ty").ok().flatten())
            .map(|node| self.render_type(&node))
            .transpose()?
            .unwrap_or_else(|| normalize_type(ty));
        match kind.as_str() {
            "SelfParam" => Ok("self".to_string()),
            "Receiver" => Ok(if self.truthy_extra(id, &["mutable", "mut"]) { "&mut self".to_string() } else { "&self".to_string() }),
            _ => Ok(format!("{mut_prefix}{pat}: {ty_rendered}")),
        }
    }

    fn render_type(&self, id: &str) -> Result<String, String> {
        let kind = self.kind(id)?;
        let grouped = self.grouped(id);
        match kind.as_str() {
            "Name" | "Ident" | "Path" | "TypePath" => self.render_path_like(id),
            "ReferenceType" | "RefType" => {
                let mutability = if self.truthy_extra(id, &["mutable", "mut"]) { "mut " } else { "" };
                let inner = self
                    .single_child(&grouped, "type")?
                    .or_else(|| self.single_child(&grouped, "inner").ok().flatten())
                    .or_else(|| self.single_child(&grouped, "value").ok().flatten())
                    .ok_or_else(|| "ReferenceType missing inner type".to_string())?;
                Ok(format!("&{mutability}{}", self.render_type(&inner)?))
            }
            "PtrType" => {
                let mutability = if self.truthy_extra(id, &["mutable", "mut"]) { "mut " } else { "const " };
                let inner = self
                    .single_child(&grouped, "type")?
                    .or_else(|| self.single_child(&grouped, "inner").ok().flatten())
                    .ok_or_else(|| "PtrType missing inner type".to_string())?;
                Ok(format!("*{mutability}{}", self.render_type(&inner)?))
            }
            "TupleType" => {
                let parts = self.children_for(&grouped, "types");
                Ok(format!("({})", self.render_list(&parts, |s| self.render_type(s), ", ")?))
            }
            "ArrayType" | "SliceType" => {
                let item = self
                    .single_child(&grouped, "type")?
                    .or_else(|| self.single_child(&grouped, "element").ok().flatten())
                    .ok_or_else(|| format!("{kind} missing inner type"))?;
                if kind == "SliceType" {
                    Ok(format!("[{}]", self.render_type(&item)?))
                } else {
                    let len = self
                        .single_child(&grouped, "len")?
                        .or_else(|| self.single_child(&grouped, "size").ok().flatten())
                        .map(|node| self.render_expr(&node))
                        .transpose()?
                        .unwrap_or_else(|| "0".to_string());
                    Ok(format!("[{}; {len}]", self.render_type(&item)?))
                }
            }
            "FnType" => {
                let params = self.children_for(&grouped, "inputs");
                let output = self.single_child(&grouped, "output")?;
                let params_text = self.render_list(&params, |s| self.render_type(s), ", ")?;
                let mut out = format!("fn({params_text})");
                if let Some(output) = output {
                    out.push_str(&format!(" -> {}", self.render_type(&output)?));
                }
                Ok(out)
            }
            "BareType" => Ok(self.text(id)?),
            _ => Ok(normalize_type(&self.text(id)?)),
        }
    }

    fn render_expr(&self, id: &str) -> Result<String, String> {
        let kind = self.kind(id)?;
        let grouped = self.grouped(id);
        match kind.as_str() {
            "Name" | "Ident" => Ok(sanitize_ident(&self.text(id)?)),
            "Path" | "TypePath" => self.render_path_like(id),
            "Literal" | "Constant" | "Lit" => Ok(render_literal(&self.text(id)?)),
            "Call" => {
                let func = self
                    .single_child(&grouped, "func")?
                    .or_else(|| self.single_child(&grouped, "callee").ok().flatten())
                    .ok_or_else(|| "Call missing func".to_string())?;
                let args = self.children_for(&grouped, "args");
                Ok(format!("{}({})", self.render_expr(&func)?, self.render_list(&args, |s| self.render_expr(s), ", ")?))
            }
            "MethodCall" => {
                let receiver = self
                    .single_child(&grouped, "receiver")?
                    .or_else(|| self.single_child(&grouped, "target").ok().flatten())
                    .ok_or_else(|| "MethodCall missing receiver".to_string())?;
                let method = sanitize_ident(&self.text(id)?);
                let args = self.children_for(&grouped, "args");
                Ok(format!("{}.{}({})", self.render_expr(&receiver)?, method, self.render_list(&args, |s| self.render_expr(s), ", ")?))
            }
            "BinaryExpr" | "BinaryOp" => {
                let left = self
                    .single_child(&grouped, "left")?
                    .or_else(|| self.single_child(&grouped, "lhs").ok().flatten())
                    .ok_or_else(|| "Binary expression missing left".to_string())?;
                let right = self
                    .single_child(&grouped, "right")?
                    .or_else(|| self.single_child(&grouped, "rhs").ok().flatten())
                    .ok_or_else(|| "Binary expression missing right".to_string())?;
                let op = self
                    .single_child(&grouped, "op")?
                    .or_else(|| self.single_child(&grouped, "operator").ok().flatten())
                    .or_else(|| self.single_child(&grouped, "value").ok().flatten())
                    .map(|node| self.render_operator(&node))
                    .transpose()?
                    .unwrap_or_else(|| self.render_operator_text(&self.kind(id).unwrap_or_else(|_| "+".to_string()), &self.text(id).unwrap_or_else(|_| "+".to_string())));
                Ok(format!("{} {} {}", self.render_expr(&left)?, op, self.render_expr(&right)?))
            }
            "UnaryExpr" => {
                let value = self
                    .single_child(&grouped, "value")?
                    .or_else(|| self.single_child(&grouped, "expr").ok().flatten())
                    .ok_or_else(|| "Unary expression missing value".to_string())?;
                let op = self.render_operator(id)?;
                Ok(format!("{}{}", op, self.render_expr(&value)?))
            }
            "FieldAccess" | "FieldExpr" => {
                let target = self
                    .single_child(&grouped, "target")?
                    .or_else(|| self.single_child(&grouped, "receiver").ok().flatten())
                    .ok_or_else(|| "Field access missing target".to_string())?;
                let field = self
                    .single_child(&grouped, "field")?
                    .or_else(|| self.single_child(&grouped, "name").ok().flatten())
                    .map(|node| self.render_path_like(&node))
                    .transpose()?
                    .unwrap_or_else(|| sanitize_ident(&self.text(id).unwrap_or_else(|_| "field".to_string())));
                Ok(format!("{}.{}", self.render_expr(&target)?, field))
            }
            "Index" => {
                let target = self
                    .single_child(&grouped, "target")?
                    .or_else(|| self.single_child(&grouped, "value").ok().flatten())
                    .ok_or_else(|| "Index missing target".to_string())?;
                let index = self
                    .single_child(&grouped, "index")?
                    .or_else(|| self.single_child(&grouped, "idx").ok().flatten())
                    .ok_or_else(|| "Index missing index".to_string())?;
                Ok(format!("{}[{}]", self.render_expr(&target)?, self.render_expr(&index)?))
            }
            "Tuple" => {
                let elts = self.children_for(&grouped, "elts");
                if elts.len() == 1 {
                    Ok(format!("({},)", self.render_expr(&elts[0])?))
                } else {
                    Ok(format!("({})", self.render_list(&elts, |s| self.render_expr(s), ", ")?))
                }
            }
            "Array" => {
                let elts = self.children_for(&grouped, "elts");
                Ok(format!("[{}]", self.render_list(&elts, |s| self.render_expr(s), ", ")?))
            }
            "StructExpr" => {
                let path = self
                    .single_child(&grouped, "path")?
                    .or_else(|| self.single_child(&grouped, "name").ok().flatten())
                    .map(|node| self.render_path_like(&node))
                    .transpose()?
                    .unwrap_or_else(|| self.text(id).unwrap_or_else(|_| "Self".to_string()));
                let fields = self.children_for(&grouped, "fields");
                if fields.is_empty() {
                    Ok(format!("{} {{}}", path))
                } else {
                    let mut parts = Vec::new();
                    for field in fields {
                        parts.push(self.render_struct_init_field(&field)?);
                    }
                    Ok(format!("{} {{ {} }}", path, parts.join(", ")))
                }
            }
            "If" | "IfExpr" => {
                let test = self
                    .single_child(&grouped, "test")?
                    .or_else(|| self.single_child(&grouped, "condition").ok().flatten())
                    .ok_or_else(|| "If expression missing condition".to_string())?;
                let body = self.children_for(&grouped, "body");
                let orelse = self.children_for(&grouped, "orelse");
                let mut out = format!("if {} {{ {} }}", self.render_expr(&test)?, self.render_inline_block(&body)?);
                if !orelse.is_empty() {
                    out.push_str(&format!(" else {{ {} }}", self.render_inline_block(&orelse)?));
                }
                Ok(out)
            }
            "Match" => {
                let expr = self
                    .single_child(&grouped, "subject")?
                    .or_else(|| self.single_child(&grouped, "value").ok().flatten())
                    .or_else(|| self.single_child(&grouped, "expr").ok().flatten())
                    .ok_or_else(|| "Match missing subject".to_string())?;
                let arms = if self.children_for(&grouped, "arms").is_empty() {
                    self.children_for(&grouped, "cases")
                } else {
                    self.children_for(&grouped, "arms")
                };
                let mut rendered = Vec::new();
                for arm in arms {
                    rendered.push(self.render_match_arm_inline(&arm)?);
                }
                Ok(format!("match {} {{ {} }}", self.render_expr(&expr)?, rendered.join(", ")))
            }
            "Block" => {
                let statements = self.children_for(&grouped, "statements");
                Ok(format!("{{ {} }}", self.render_inline_block(&statements)?))
            }
            "Reference" => {
                let inner = self
                    .single_child(&grouped, "value")?
                    .or_else(|| self.single_child(&grouped, "inner").ok().flatten())
                    .ok_or_else(|| "Reference missing value".to_string())?;
                if self.truthy_extra(id, &["mutable", "mut"]) {
                    Ok(format!("&mut {}", self.render_expr(&inner)?))
                } else {
                    Ok(format!("&{}", self.render_expr(&inner)?))
                }
            }
            "Deref" => {
                let inner = self
                    .single_child(&grouped, "value")?
                    .or_else(|| self.single_child(&grouped, "inner").ok().flatten())
                    .ok_or_else(|| "Deref missing value".to_string())?;
                Ok(format!("*{}", self.render_expr(&inner)?))
            }
            "Cast" => {
                let expr = self.single_child(&grouped, "expr")?.ok_or_else(|| "Cast missing expr".to_string())?;
                let ty = self.single_child(&grouped, "type")?.ok_or_else(|| "Cast missing type".to_string())?;
                Ok(format!("{} as {}", self.render_expr(&expr)?, self.render_type(&ty)?))
            }
            _ => Ok(sanitize_ident(&self.text(id)?)),
        }
    }

    fn render_operator(&self, id: &str) -> Result<String, String> {
        let kind = self.kind(id)?;
        let text = self.text(id)?;
        Ok(self.render_operator_text(&kind, &text))
    }

    fn render_operator_text(&self, kind: &str, text: &str) -> String {
        let kind = kind.trim();
        if matches!(kind, "Add" | "Sub" | "Mult" | "Div" | "Mod" | "Rem" | "Eq" | "Ne" | "Lt" | "Le" | "Gt" | "Ge" | "And" | "Or") {
            return normalize_op(kind);
        }
        normalize_op(text)
    }

    fn render_path_like(&self, id: &str) -> Result<String, String> {
        let grouped = self.grouped(id);
        let parts = if self.children_for(&grouped, "segments").is_empty() {
            self.children_for(&grouped, "path")
        } else {
            self.children_for(&grouped, "segments")
        };
        if !parts.is_empty() {
            let mut rendered = Vec::new();
            for part in parts {
                rendered.push(self.render_path_segment(&part)?);
            }
            return Ok(rendered.join("::"));
        }
        Ok(self.text(id)?)
    }

    fn render_path_segment(&self, id: &str) -> Result<String, String> {
        let grouped = self.grouped(id);
        if let Some(child) = self.single_child(&grouped, "path")? {
            return self.render_path_like(&child);
        }
        if let Some(child) = self.single_child(&grouped, "name")? {
            return self.render_path_like(&child);
        }
        Ok(sanitize_ident(&self.text(id)?))
    }

    fn render_struct_init_field(&self, id: &str) -> Result<String, String> {
        let kind = self.kind(id)?;
        let grouped = self.grouped(id);
        let name = sanitize_ident(&self.text(id)?);
        let value = self
            .single_child(&grouped, "value")?
            .or_else(|| self.single_child(&grouped, "expr").ok().flatten())
            .or_else(|| self.single_child(&grouped, "target").ok().flatten());
        let shorthand = self.truthy_extra(id, &["shorthand", "short"]);
        if shorthand || value.is_none() || kind == "FieldShorthand" {
            return Ok(name);
        }
        let value = value.expect("checked above");
        Ok(format!("{name}: {}", self.render_expr(&value)?))
    }

    fn render_pattern(&self, id: &str) -> Result<String, String> {
        let kind = self.kind(id)?;
        let grouped = self.grouped(id);
        match kind.as_str() {
            "Name" | "Ident" | "Pattern" => Ok(sanitize_ident(&self.text(id)?)),
            "Wildcard" | "Underscore" => Ok("_".to_string()),
            "Literal" | "Constant" | "Lit" => Ok(render_literal(&self.text(id)?)),
            "TuplePattern" | "Tuple" => {
                let elts = self.children_for(&grouped, "elts");
                Ok(format!("({})", self.render_list(&elts, |s| self.render_pattern(s), ", ")?))
            }
            "StructPattern" => {
                let path = self
                    .single_child(&grouped, "path")?
                    .or_else(|| self.single_child(&grouped, "name").ok().flatten())
                    .map(|node| self.render_path_like(&node))
                    .transpose()?
                    .unwrap_or_else(|| self.text(id).unwrap_or_else(|_| "Self".to_string()));
                let fields = self.children_for(&grouped, "fields");
                if fields.is_empty() {
                    Ok(format!("{} {{}}", path))
                } else {
                    let mut parts = Vec::new();
                    for field in fields {
                        parts.push(self.render_struct_pattern_field(&field)?);
                    }
                    Ok(format!("{} {{ {} }}", path, parts.join(", ")))
                }
            }
            "OrPattern" | "Or" => {
                let pats = self.children_for(&grouped, "patterns");
                Ok(self.render_list(&pats, |s| self.render_pattern(s), " | ")?)
            }
            "ReferencePattern" => {
                let inner = self.single_child(&grouped, "value")?.ok_or_else(|| "ReferencePattern missing value".to_string())?;
                if self.truthy_extra(id, &["mutable", "mut"]) {
                    Ok(format!("&mut {}", self.render_pattern(&inner)?))
                } else {
                    Ok(format!("&{}", self.render_pattern(&inner)?))
                }
            }
            "Path" | "TypePath" => self.render_path_like(id),
            _ => Ok(sanitize_ident(&self.text(id)?)),
        }
    }

    fn render_struct_pattern_field(&self, id: &str) -> Result<String, String> {
        let grouped = self.grouped(id);
        let name = sanitize_ident(&self.text(id)?);
        if let Some(pattern) = self.single_child(&grouped, "pattern")? {
            Ok(format!("{name}: {}", self.render_pattern(&pattern)?))
        } else {
            Ok(name)
        }
    }

    fn render_match_arm_inline(&self, id: &str) -> Result<String, String> {
        let grouped = self.grouped(id);
        let pattern = self
            .single_child(&grouped, "pattern")?
            .or_else(|| self.single_child(&grouped, "pat").ok().flatten())
            .or_else(|| self.single_child(&grouped, "lhs").ok().flatten())
            .ok_or_else(|| "Match arm missing pattern".to_string())?;
        let guard = self.single_child(&grouped, "guard")?;
        let value = self
            .single_child(&grouped, "value")?
            .or_else(|| self.single_child(&grouped, "expr").ok().flatten());
        let mut out = self.render_pattern(&pattern)?;
        if let Some(guard) = guard {
            out.push_str(&format!(" if {}", self.render_expr(&guard)?));
        }
        if let Some(value) = value {
            out.push_str(&format!(" => {}", self.render_expr(&value)?));
            return Ok(out);
        }
        let body = self.children_for(&grouped, "body");
        if !body.is_empty() {
            out.push_str(&format!(" => {{ {} }}", self.render_inline_block(&body)?));
            return Ok(out);
        }
        Ok(format!("{out} => ()"))
    }

    fn render_inline_block(&self, ids: &[String]) -> Result<String, String> {
        let mut parts = Vec::new();
        for id in ids {
            let kind = self.kind(id)?;
            let rendered = match kind.as_str() {
                "Expr" | "ExpressionStatement" | "Stmt" => {
                    let grouped = self.grouped(id);
                    let value = self.single_child(&grouped, "value")?.ok_or_else(|| format!("{kind} missing value"))?;
                    self.render_expr(&value)?
                }
                _ => self.render_item(id, 0)?.trim().to_string(),
            };
            if !rendered.is_empty() {
                parts.push(rendered.trim_end_matches('\n').to_string());
            }
        }
        Ok(parts.join(" "))
    }

    fn render_list<F>(&self, ids: &[String], mut f: F, sep: &str) -> Result<String, String>
    where
        F: FnMut(&str) -> Result<String, String>,
    {
        let mut parts = Vec::new();
        for id in ids {
            parts.push(f(id)?);
        }
        Ok(parts.join(sep))
    }

    fn visibility_prefix(&self, id: &str) -> String {
        let node = match self.node(id) {
            Ok(node) => node,
            Err(_) => return String::new(),
        };
        if self.truthy_extra(id, &["public", "pub", "visible"]) {
            return "pub ".to_string();
        }
        if let Some(value) = node.extra.get("visibility") {
            if let Some(text) = value.as_str() {
                if text.contains("pub") {
                    return "pub ".to_string();
                }
            }
        }
        if let Some(value) = node.extra.get("modifiers") {
            if let Some(text) = value.as_str() {
                if text.contains("pub") {
                    return "pub ".to_string();
                }
            }
        }
        String::new()
    }

    fn truthy_extra(&self, id: &str, keys: &[&str]) -> bool {
        let node = match self.node(id) {
            Ok(node) => node,
            Err(_) => return false,
        };
        for key in keys {
            if let Some(value) = node.extra.get(*key) {
                if truthy(value) {
                    return true;
                }
            }
        }
        false
    }
}

fn key(value: &Value) -> String {
    match value {
        Value::String(s) => s.clone(),
        Value::Number(n) => n.to_string(),
        _ => value.to_string(),
    }
}

fn value_to_i64(value: &Value) -> Option<i64> {
    match value {
        Value::Number(n) => n.as_i64().or_else(|| n.as_f64().map(|v| v as i64)),
        Value::String(s) => s.parse::<i64>().ok(),
        _ => None,
    }
}

fn truthy(value: &Value) -> bool {
    match value {
        Value::Bool(b) => *b,
        Value::Number(n) => n.as_i64().map(|v| v != 0).or_else(|| n.as_f64().map(|v| v != 0.0)).unwrap_or(false),
        Value::String(s) => matches!(s.trim().to_ascii_lowercase().as_str(), "1" | "true" | "yes" | "on"),
        _ => false,
    }
}

fn sanitize_ident(text: &str) -> String {
    let text = text.trim();
    if text.is_empty() {
        return "_".to_string();
    }
    let mut out = String::new();
    for (index, ch) in text.chars().enumerate() {
        let ok = if index == 0 {
            ch.is_ascii_alphabetic() || ch == '_'
        } else {
            ch.is_ascii_alphanumeric() || ch == '_'
        };
        out.push(if ok { ch } else { '_' });
    }
    if out.is_empty() {
        "_".to_string()
    } else {
        out
    }
}

fn normalize_type(text: &str) -> String {
    let trimmed = text.trim();
    if trimmed.is_empty() {
        "()".to_string()
    } else {
        trimmed.to_string()
    }
}

fn normalize_op(text: &str) -> String {
    match text.trim() {
        "Add" | "+" => "+".to_string(),
        "Sub" | "-" => "-".to_string(),
        "Mult" | "*" => "*".to_string(),
        "Div" | "/" => "/".to_string(),
        "Mod" | "Rem" | "%" => "%".to_string(),
        "Eq" | "==" => "==".to_string(),
        "Ne" | "!=" => "!=".to_string(),
        "Lt" | "<" => "<".to_string(),
        "Le" | "<=" => "<=".to_string(),
        "Gt" | ">" => ">".to_string(),
        "Ge" | ">=" => ">=".to_string(),
        "And" | "&&" => "&&".to_string(),
        "Or" | "||" => "||".to_string(),
        other => other.to_string(),
    }
}

fn render_literal(text: &str) -> String {
    let trimmed = text.trim();
    if trimmed == "None" || trimmed == "null" {
        return "()".to_string();
    }
    if trimmed == "True" || trimmed == "true" {
        return "true".to_string();
    }
    if trimmed == "False" || trimmed == "false" {
        return "false".to_string();
    }
    if trimmed.starts_with('"') && trimmed.ends_with('"') {
        return trimmed.to_string();
    }
    if trimmed.starts_with('\'') && trimmed.ends_with('\'') {
        return format!("\"{}\"", trimmed.trim_matches('\''));
    }
    if trimmed.parse::<i64>().is_ok() || trimmed.parse::<f64>().is_ok() {
        return trimmed.to_string();
    }
    format!("\"{}\"", trimmed.replace('\\', "\\\\").replace('"', "\\\""))
}

fn read_graph(path: &PathBuf) -> Result<Graph, Box<dyn Error>> {
    let text = fs::read_to_string(path)?;
    Ok(serde_json::from_str(&text)?)
}

fn run() -> Result<(), Box<dyn Error>> {
    let mut args = env::args().skip(1).collect::<Vec<_>>();
    if args.is_empty() || args[0] == "-h" || args[0] == "--help" {
        eprintln!("usage: rust_from_ast_tool <graph.json> [output.rs]");
        return Ok(());
    }

    let input = PathBuf::from(args.remove(0));
    let output = if let Some(path) = args.first() {
        PathBuf::from(path)
    } else {
        PathBuf::from("compare.rs")
    };

    let graph = read_graph(&input)?;
    let builder = Builder::new(graph);
    let source = builder.build().map_err(|e| format!("rust AST render failed: {e}"))?;
    if let Some(parent) = output.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&output, source)?;
    println!("wrote {}", output.display());
    Ok(())
}

fn main() {
    if let Err(err) = run() {
        eprintln!("error: {err}");
        std::process::exit(1);
    }
}
