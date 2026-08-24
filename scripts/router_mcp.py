#!/usr/bin/env python3
"""FlossWare policy-aware MCP bridge to model-router-ai.

Personal mode exposes only providers whose credentials are present in the
process environment. Red Hat mode deliberately refuses to expose this
personal-provider router; approved Anthropic access remains in the native
Red Hat agent authentication path.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

from fastmcp import FastMCP
from model_router_ai import (
    ChatMessage,
    CohereProvider,
    CostAware,
    GeminiProvider,
    LatencyOptimizer,
    OpenAICompatProvider,
    PolicyGuard,
    ProviderRouter,
    ThompsonSamplingSelector,
)

PROFILE = os.environ.get("FLOSSWARE_PROFILE", "personal")
mcp = FastMCP("flossware-model-router")
_router = None
_lock = asyncio.Lock()

# Provider definitions are intentionally limited to credentials supplied by
# the invoking environment. No credential file is read or written here.
PROVIDERS = {
    "groq": ("GROQ_API_KEY", lambda: OpenAICompatProvider("groq")),
    "openrouter": ("OPENROUTER_API_KEY", lambda: OpenAICompatProvider("openrouter", free_only=True)),
    "gemini": ("GEMINI_API_KEY", GeminiProvider),
    "cohere": ("COHERE_API_KEY", CohereProvider),
    "cerebras": ("CEREBRAS_API_KEY", lambda: OpenAICompatProvider("cerebras")),
    "openai": ("OPENAI_API_KEY", lambda: OpenAICompatProvider("openai")),
}


async def get_router():
    global _router
    if _router is not None:
        return _router
    if PROFILE == "redhat":
        raise RuntimeError(
            "FlossWare personal model router is disabled in the redhat profile; "
            "use the approved native Anthropic agent configuration."
        )
    async with _lock:
        if _router is not None:
            return _router
        base = ProviderRouter()
        allowed_models: list[str] = []
        for provider, (env_name, factory) in PROVIDERS.items():
            key = os.environ.get(env_name, "")
            if not key:
                continue
            base.add_provider(factory(), api_key=key)
            allowed_models.append(f"{provider}:*")
        if not allowed_models:
            raise RuntimeError("No configured personal model providers were found in the environment")
        routed = ThompsonSamplingSelector(base)
        routed = LatencyOptimizer(routed)
        routed = CostAware(routed, prefer_free=True)
        _router = PolicyGuard(routed, allowed=allowed_models)
        await _router.initialize()
        return _router


@mcp.tool()
async def list_models() -> str:
    """List models available under the active FlossWare profile."""
    router = await get_router()
    models = await router.list_models()
    return json.dumps(
        [
            {"model_id": m.model_id, "provider": m.provider, "context_window": m.context_window}
            for m in models
        ],
        indent=2,
    )


@mcp.tool()
async def chat(prompt: str, model: str | None = None, system_prompt: str | None = None) -> str:
    """Route a prompt through FlossWare's personal model policy."""
    router = await get_router()
    messages = []
    if system_prompt:
        messages.append(ChatMessage(role="system", content=system_prompt))
    messages.append(ChatMessage(role="user", content=prompt))
    response = await router.chat(messages, model=model)
    return json.dumps(
        {
            "content": response.content,
            "model": response.model,
            "provider": response.provider,
            "latency_ms": round(response.latency_ms, 1),
            "cost_usd": round(response.cost_usd, 6),
            "usage": response.usage,
        },
        indent=2,
    )


if __name__ == "__main__":
    if "--help" in sys.argv:
        print("Run the FlossWare model router as an MCP server on stdio.")
        raise SystemExit(0)
    mcp.run()
