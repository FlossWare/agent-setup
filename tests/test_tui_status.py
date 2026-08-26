from flossware_setup.tui.status import item_status


def test_item_status_uses_catalog_description() -> None:
    assert item_status("Crush", "Shared project context") == "STATUS: Crush | Shared project context"


def test_item_status_never_needs_secret_values() -> None:
    text = item_status("Provider Credentials", "View detected credential sources (names only)")
    assert "secret" in text.lower()
    assert "key=" not in text.lower()


def test_item_status_control_center_actions() -> None:
    assert item_status("Review Current Configuration", "Inspect persisted project configuration").startswith("STATUS: Review")
    assert item_status("Exit", "Leave Setup") == "STATUS: Exit | leave Setup Control Center"
