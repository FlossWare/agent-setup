"""Contract-level tests for the canonical Setup TUI document."""

from curses_tui import SCHEMA_VERSION, validate

from flossware_setup.tui.contract import build_document


def test_setup_tui_document_uses_canonical_schema() -> None:
    document = build_document(
        "redhat-cost-conscious",
        {
            "provider": "Anthropic",
            "budget.monthly": 300,
            "optimization.strategy": "balanced",
            "policy.allow_personal_accounts": False,
            "policy.allow_provider_fallback": False,
        },
        ["default", "redhat-cost-conscious"],
    )

    assert document["schema"] == SCHEMA_VERSION
    assert document["id"] == "agent-setup"
    assert document["windows"]
    assert document["menus"]
    assert validate(document) is document


def test_setup_tui_document_has_unique_ids() -> None:
    document = build_document("default", {}, ["default"])
    ids: list[str] = []

    def collect_widget(widget: dict) -> None:
        ids.append(widget["id"])
        if widget["type"] == "group":
            for child in widget["children"]:
                collect_widget(child)

    for menu in document["menus"]:
        ids.append(menu["id"])
        ids.extend(item["id"] for item in menu["items"])
    for window in document["windows"]:
        ids.append(window["id"])
        for widget in window["content"]:
            collect_widget(widget)

    assert len(ids) == len(set(ids))
