"""Read-only plugin introspection endpoint — mirrors `leadforge plugins`."""
from __future__ import annotations

from fastapi import APIRouter

from leadforge.plugins import default_plugins_dir, get_registry

from ..schemas import PluginOut, PluginsOut

router = APIRouter(tags=["plugins"])


@router.get("/plugins", response_model=PluginsOut)
def list_plugins() -> PluginsOut:
    registry = get_registry()
    return PluginsOut(
        plugins=[
            PluginOut(
                name=p.name,
                source=p.source,
                category_weights_added=p.category_weights_added,
                categories_excluded=p.categories_excluded,
                audit_checks_added=p.audit_checks_added,
                scoring_rules_added=p.scoring_rules_added,
            )
            for p in registry.loaded_plugins
        ],
        plugin_directory=str(default_plugins_dir()),
    )
