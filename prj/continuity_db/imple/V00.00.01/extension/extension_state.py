"""Universal tagged-state helpers for project extensions."""

from __future__ import annotations

from pathlib import Path

import continuity_db_helper


OBJECT_ALIASES = {
    "telegram": "messenger-adapter.telegramm",
}


def resolve_object_alias(name: str) -> str:
    """Resolve a stable local alias to its canonical artifact name."""
    return OBJECT_ALIASES.get(name.strip().lower(), name.strip())


class ExtensionStateError(RuntimeError):
    """Raised when an extension is not installed or is disabled."""

    def __init__(
        self,
        artifact_name: str,
        missing_tags: list[str],
        *,
        kind: str = "code_artifact",
    ) -> None:
        self.name = artifact_name
        self.kind = kind
        self.missing_tags = tuple(missing_tags)
        super().__init__(
            f"{kind} {artifact_name} is not ready; "
            f"missing {', '.join(missing_tags)}"
        )


def artifact_object_key(artifact_name: str) -> str:
    return f"code_artifacts:name={artifact_name}"


def extension_tags(db_path: str | Path, artifact_name: str) -> set[str]:
    """Return current tags for a code-artifact extension."""
    con = continuity_db_helper.connect(Path(db_path))
    try:
        rows = con.execute(
            """SELECT tag_key FROM object_epistemic_tags
               WHERE object_type='row' AND object_key=?""",
            (artifact_object_key(artifact_name),),
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        con.close()


def require_extension_ready(db_path: str | Path, artifact_name: str) -> set[str]:
    """Require an extension to be installed and enabled before interaction."""
    tags = extension_tags(db_path, artifact_name)
    missing = []
    if "lifecycle:installed" not in tags:
        missing.append("lifecycle:installed")
    if "activation:enabled" not in tags:
        missing.append("activation:enabled")
    if missing:
        kind_tag = next(
            (tag for tag in tags if tag.startswith("kind:") and tag.count(":") == 1),
            "kind:code_artifact",
        )
        kind = kind_tag.split(":", 1)[1] or "code_artifact"
        raise ExtensionStateError(artifact_name, missing, kind=kind)
    return tags


def disable_extension(
    db_path: str | Path,
    artifact_name: str,
) -> set[str]:
    """Disable a tagged extension and return its resulting tags."""
    artifact_name = resolve_object_alias(artifact_name)
    con = continuity_db_helper.connect(Path(db_path))
    object_key = artifact_object_key(artifact_name)
    try:
        artifact = con.execute(
            "SELECT 1 FROM code_artifacts WHERE name=? LIMIT 1", (artifact_name,)
        ).fetchone()
        if artifact is None:
            raise ExtensionStateError(artifact_name, ["code_artifact:missing"], kind="code_artifact")
        tags = {
            row[0]
            for row in con.execute(
                """SELECT tag_key FROM object_epistemic_tags
                   WHERE object_type='row' AND object_key=?""",
                (object_key,),
            )
        }
        if not {"kind:extension", "kind:code_artifact"}.intersection(tags):
            raise ExtensionStateError(
                artifact_name,
                ["kind:extension or kind:code_artifact"],
                kind="code_artifact",
            )
        installed = "lifecycle:installed" in tags
        # An absent installation is already unavailable; make that state
        # explicit by ensuring activation is disabled rather than enabled.
        if not installed:
            tags.discard("activation:enabled")
        con.execute(
            """INSERT OR IGNORE INTO epistemic_tags(tag_key,label,description)
               VALUES (?,?,?)""",
            (
                "activation:disabled",
                "Disabled",
                "Activation state: disabled and not available for use.",
            ),
        )
        continuity_db_helper._controlled_tag_assign(
            con,
            "row",
            object_key,
            "activation:disabled",
            "Disabled by explicit route request",
        )
        con.execute(
            """DELETE FROM object_epistemic_tags
               WHERE object_type='row' AND object_key=?
                 AND tag_key='activation:enabled'""",
            (object_key,),
        )
        con.commit()
        return extension_tags(db_path, artifact_name)
    finally:
        con.close()


def enable_extension(
    db_path: str | Path,
    artifact_name: str,
) -> set[str]:
    """Enable an installed, tagged extension and return its resulting tags."""
    artifact_name = resolve_object_alias(artifact_name)
    con = continuity_db_helper.connect(Path(db_path))
    object_key = artifact_object_key(artifact_name)
    try:
        artifact = con.execute(
            "SELECT 1 FROM code_artifacts WHERE name=? LIMIT 1", (artifact_name,)
        ).fetchone()
        if artifact is None:
            raise ExtensionStateError(artifact_name, ["code_artifact:missing"], kind="code_artifact")
        tags = {
            row[0]
            for row in con.execute(
                """SELECT tag_key FROM object_epistemic_tags
                   WHERE object_type='row' AND object_key=?""",
                (object_key,),
            )
        }
        if not {"kind:extension", "kind:code_artifact"}.intersection(tags):
            raise ExtensionStateError(
                artifact_name,
                ["kind:extension or kind:code_artifact"],
                kind="code_artifact",
            )
        if "lifecycle:installed" not in tags:
            raise ExtensionStateError(artifact_name, ["lifecycle:installed"], kind="extension")
        con.execute(
            """INSERT OR IGNORE INTO epistemic_tags(tag_key,label,description)
               VALUES (?,?,?)""",
            (
                "activation:enabled",
                "Enabled",
                "Activation state: enabled and available for use.",
            ),
        )
        continuity_db_helper._controlled_tag_assign(
            con,
            "row",
            object_key,
            "activation:enabled",
            "Enabled by explicit route request",
        )
        con.execute(
            """DELETE FROM object_epistemic_tags
               WHERE object_type='row' AND object_key=?
                 AND tag_key='activation:disabled'""",
            (object_key,),
        )
        con.commit()
        return extension_tags(db_path, artifact_name)
    finally:
        con.close()


def set_configuration_state(
    db_path: str | Path,
    artifact_name: str,
    configured_tag: str = "configuration:configured",
    missing_tag: str = "configuration:credential_missing",
) -> None:
    """Replace a configuration-missing tag with a configured tag."""
    con = continuity_db_helper.connect(Path(db_path))
    object_key = artifact_object_key(artifact_name)
    try:
        con.execute(
            """INSERT OR IGNORE INTO epistemic_tags(tag_key,label,description)
               VALUES (?,?,?)""",
            (
                configured_tag,
                "Configured",
                "Extension configuration state: required configuration is present.",
            ),
        )
        continuity_db_helper._controlled_tag_assign(
            con,
            "row",
            object_key,
            configured_tag,
            "Configuration supplied; secret value was not persisted",
        )
        con.execute(
            """DELETE FROM object_epistemic_tags
               WHERE object_type='row' AND object_key=? AND tag_key=?""",
            (object_key, missing_tag),
        )
        con.commit()
    finally:
        con.close()
