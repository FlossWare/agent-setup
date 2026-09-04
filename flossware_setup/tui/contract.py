"""Build the Setup TUI's canonical FlossWare TUI Schema 1.0 document."""

from __future__ import annotations


def build_document(profile: str, config: dict[str, object], profiles: list[str]) -> dict:
    """Build the declarative Setup TUI document from application state."""
    profile_items = [
        {
            "id": f"profile-{name}",
            "label": name.replace("-", " ").title(),
            "value": name,
            "enabled": True,
        }
        for name in profiles
    ]
    return {
        "schema": "flossware.tui/1.0",
        "id": "agent-setup",
        "title": "FlossWare AI Setup",
        "theme": {"name": "default"},
        "menus": [
            {
                "id": "file",
                "label": "File",
                "items": [
                    {"id": "file-exit", "label": "Exit", "action": "app.exit"}
                ],
            },
            {
                "id": "edit",
                "label": "Edit",
                "items": [
                    {
                        "id": "edit-reorder",
                        "label": "Reorder menus",
                        "action": "config.reorder",
                    }
                ],
            },
            {
                "id": "view",
                "label": "View",
                "items": [
                    {"id": "view-profiles", "label": "Profiles", "action": "profile.select"},
                    {"id": "view-bindings", "label": "Directory Bindings", "action": "bindings.view"},
                    {"id": "view-config", "label": "Configuration", "action": "config.view"},
                    {"id": "view-theme", "label": "Theme", "action": "theme.select"},
                ],
            },
            {
                "id": "config",
                "label": "Config",
                "items": [
                    {"id": "config-profiles", "label": "Profiles", "action": "profile.select"},
                    {"id": "config-create-profile", "label": "Create Profile", "action": "profile.create"},
                    {"id": "config-bindings", "label": "Directory Bindings", "action": "bindings.edit"},
                    {"id": "config-validate", "label": "Validate", "action": "config.validate"},
                ],
            },
            {
                "id": "models",
                "label": "Models",
                "items": [
                    {"id": "models-select", "label": "Select Model", "action": "model.select"}
                ],
            },
            {
                "id": "agents",
                "label": "Agents",
                "items": [
                    {"id": "agents-select", "label": "Select Agent", "action": "agent.select"}
                ],
            },
            {
                "id": "optimize",
                "label": "Optimize",
                "items": [
                    {"id": "optimize-settings", "label": "Settings", "action": "optimizer.settings"}
                ],
            },
            {
                "id": "help",
                "label": "Help",
                "items": [
                    {"id": "help-about", "label": "About", "action": "help.about"}
                ],
            },
        ],
        "windows": [
            {
                "id": "profiles",
                "kind": "panel",
                "title": "Profiles",
                "layout": {"x": 1, "y": 2, "width": 27, "height": 15, "anchor": "top-left"},
                "content": [
                    {
                        "id": "profile-list",
                        "type": "list",
                        "label": "Profiles",
                        "items": profile_items,
                        "action": "profile.select",
                    }
                ],
                "initialFocus": "profile-list",
            },
            {
                "id": "configuration",
                "kind": "window",
                "title": "Configuration",
                "layout": {"x": 30, "y": 2, "width": 48, "height": 15, "anchor": "top-left"},
                "content": [
                    {"id": "provider", "type": "label", "label": f"Provider: {config.get('provider', 'unknown')}"},
                    {"id": "budget", "type": "label", "label": f"Budget: ${float(config.get('budget.monthly', 0)):.2f} / month"},
                    {"id": "optimizer", "type": "label", "label": f"Optimizer: {config.get('optimization.strategy', 'unknown')}"},
                    {"id": "personal-accounts", "type": "label", "label": f"Personal accounts: {'allowed' if config.get('policy.allow_personal_accounts') else 'blocked'}"},
                    {"id": "provider-fallback", "type": "label", "label": f"Provider fallback: {'allowed' if config.get('policy.allow_provider_fallback') else 'blocked'}"},
                    {"id": "status-separator", "type": "separator"},
                    {"id": "active-profile", "type": "label", "label": f"Active profile: {profile}"},
                ],
            },
        ],
    }


__all__ = ["build_document"]
