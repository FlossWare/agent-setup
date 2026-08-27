  mv "$EXTRACTED" "$SETUP_DIR"
fi
for required in scripts/setup.py scripts/profile.sh flossware_setup/tui/app.py scripts/flossware-ai scripts/router_mcp.py scripts/discovery.py scripts/mcp.py scripts/tui.py scripts/agent_setup.py scripts/runtime.py scripts/dogfood.py; do [[ -f "$SETUP_DIR/$required" ]] || fail "missing $required"; done
[[ "$PROFILE" == "default" || -f "$SETUP_DIR/profiles/$PROFILE.toml" ]] || fail "profile '$PROFILE' is not defined; refusing to substitute the neutral default profile"
python -m compileall -q "$SETUP_DIR/scripts/setup.py" "$SETUP_DIR/scripts/tui.py" "$SETUP_DIR/scripts/agent_setup.py" "$SETUP_DIR/scripts/router_mcp.py" "$SETUP_DIR/scripts/discovery.py" "$SETUP_DIR/scripts/mcp.py" "$SETUP_DIR/scripts/runtime.py" "$SETUP_DIR/scripts/dogfood.py"
"$VENV/bin/python" -m pip install -e "$SETUP_DIR" --quiet || fail "failed to install coding-agent-setup package into managed venv"
PROFILE_DIR="$INSTALL_ROOT/config/profiles/$PROFILE"; mkdir -p "$PROFILE_DIR" "$INSTALL_ROOT/bin" "$INSTALL_ROOT/state" "$INSTALL_ROOT/cache" "$INSTALL_ROOT/mcp"
cp "$SETUP_DIR/scripts/profile.sh" "$PROFILE_DIR/profile.sh"
cp "$SETUP_DIR/profiles/$PROFILE.toml" "$PROFILE_DIR/profile.toml"
cp "$SETUP_DIR/scripts/flossware-ai" "$INSTALL_ROOT/bin/flossware-ai"; cp "$SETUP_DIR/scripts/tui.py" "$INSTALL_ROOT/tui.py"; cp "$SETUP_DIR/scripts/agent_setup.py" "$INSTALL_ROOT/agent_setup.py"; cp "$SETUP_DIR/scripts/setup.py" "$INSTALL_ROOT/setup.py"; cp "$SETUP_DIR/scripts/router_mcp.py" "$INSTALL_ROOT/router_mcp.py"; cp "$SETUP_DIR/scripts/discovery.py" "$INSTALL_ROOT/discovery.py"; cp "$SETUP_DIR/scripts/mcp.py" "$INSTALL_ROOT/mcp.py"; cp "$SETUP_DIR/scripts/runtime.py" "$INSTALL_ROOT/runtime.py"; cp "$SETUP_DIR/scripts/dogfood.py" "$INSTALL_ROOT/dogfood.py"
chmod 700 "$PROFILE_DIR/profile.sh" "$INSTALL_ROOT/bin/flossware-ai" "$INSTALL_ROOT"/*.py; printf '%s\n' "$PROFILE" > "$INSTALL_ROOT/state/active-profile"; chmod 600 "$INSTALL_ROOT/state/active-profile"
printf '{\n  "profile": "%s",\n  "credential_values_written": false,\n  "credential_source": "native-agent-store-or-environment"\n}\n' "$PROFILE" > "$PROFILE_DIR/profile.json"; chmod 600 "$PROFILE_DIR/profile.json"
PATH_SHIM="$HOME/.local/bin/flossware-ai"; mkdir -p "$(dirname "$PATH_SHIM")"; cat > "$PATH_SHIM" <<EOF
#!/usr/bin/env bash
exec "$INSTALL_ROOT/bin/flossware-ai" "\$@"
EOF
# Invoke this helper explicitly with bash because GitHub's Contents API cannot preserve
# the executable bit on newly-created text files. This keeps fresh installs portable.
bash "$SETUP_DIR/scripts/write-install-metadata.sh" "$INSTALL_ROOT" "$RELEASE_REF" "$USE_SOURCE" "$PLATFORM" "$PROFILE"
chmod 700 "$PATH_SHIM"
log "Installation complete: $INSTALL_ROOT"; printf '%s\n' "Profile: $PROFILE" "Platform: $PLATFORM" "Source mode: $USE_SOURCE" "Run: flossware-ai tui" "Run: flossware-ai doctor" "Run: flossware-ai dogfood --strict"