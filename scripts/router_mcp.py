#!/usr/bin/env python3
"""Policy-aware MCP bridge to the FlossWare model router.

The MCP server is an external process owned by FlossWare. Agents are MCP
clients. Provider credentials are inherited from the environment and are
never copied into MCP or agent configuration.
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
from model_router_ai.discovery import discover_accounts

PROFILE = os.environ.get("FLOSSWARE_PROFILE", "default")
mcp = FastMCP("flossware-model-router")
_router = None
_lock = asyncio.Lock()

# Provider factories are deliberately keyed by provider, while credentials
# and account identity come from discovery. This permits multiple accounts
# for the same provider without duplicating routing logic.
PROVIDERS = {
    "groq": lambda: OpenAICompatProvider("groq"),
    "openrouter": lambda: OpenAICompatProvider("openrouter", free_only=False),
    "gemini": GeminiProvider,
    "cohere": CohereProvider,
    "cerebras": lambda: OpenAICompatProvider("cerebras"),
    "openai": lambda: OpenAICompatProvider("openai"),
    "nvidia": lambda: OpenAICompatProvider("nvidia"),
    "deepinfra": lambda: OpenAICompatProvider("deepinfra"),
    "huggingface": lambda: OpenAICompatProvider("huggingface"),
}


def _account_key(account: dict) -> str:
    source = account.get("credential_source", "")
    prefix = "environment:"
    if not source.startswith(prefix):
        return ""
    return os.environ.get(source[len(prefix):], "")


async def get_router():
    global _router
    if _router is not None:
        return _router
    async with _lock:
        if _router is not None:
            return _router

        base = ProviderRouter()
        allowed_models: list[str] = []
        for account in discover_accounts():
            provider_name = account["provider"]
            factory = PROVIDERS.get(provider_name)
            key = _account_key(account)
            if factory is None or not key:
                continue
            # account_name is now part of the router endpoint identity.
            base.add_provider(
                factory(),
                api_key=key,
                account_name=account["id"],
            )
            allowed_models.append(f"{provider_name}:*")

        if not allowed_models:
            raise RuntimeError(
                "No configured model accounts were found in the environment"
            )

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
            {
                "model_id": m.model_id,
                "provider": m.provider,
                "account": m.account_name,
                "context_window": m.context_window,
                "tags": m.tags,
            }
            for m in models
        ],
        indent=2,
    )


@mcp.tool()
async def chat(
    prompt: str,
    model: str | None = None,
    account: str | None = None,
    system_prompt: str | None = None,
) -> str:
    """Route a prompt through FlossWare's active account/profile policy."""
    router = await get_router()
    messages = []
    if system_prompt:
        messages.append(ChatMessage(role="system", content=system_prompt))
    messages.append(ChatMessage(role="user", content=prompt))
    response = await router.chat(messages, model=model, account=account)
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
        print("Run the external FlossWare model router as an MCP server on stdio.")
        raise SystemExit(0)
    mcp.run()
