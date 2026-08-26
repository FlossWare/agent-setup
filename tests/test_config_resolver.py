from flossware_setup.config.resolver import ConfigLayer, ConfigResolver


def test_layers_resolve_low_to_high_priority():
    resolver = ConfigResolver()
    resolver.add_layer(ConfigLayer("user", 200, {"x": 2}))
    resolver.add_layer(ConfigLayer("defaults", 0, {"x": 1}))
    resolver.add_layer(ConfigLayer("project", 400, {"x": 3}))
    assert resolver.resolve()["x"] == 3


def test_provenance_is_ordered():
    resolver = ConfigResolver()
    resolver.add_layer(ConfigLayer("project", 400, {"x": 3}))
    resolver.add_layer(ConfigLayer("defaults", 0, {"x": 1}))
    assert resolver.provenance("x") == [("defaults", 1), ("project", 3)]


def test_explain_shows_effective_value():
    resolver = ConfigResolver()
    resolver.add_layer(ConfigLayer("defaults", 0, {"x": 1}))
    resolver.add_layer(ConfigLayer("user", 200, {"x": 2}))
    text = resolver.explain("x")
    assert "defaults: 1" in text
    assert "user: 2" in text
    assert "effective: 2" in text
