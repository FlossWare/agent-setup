"""Static, provider-neutral setup catalogs.

Domain data only: agent adapters, capabilities, budget policies, and providers.
No I/O, no credentials, no UI.
"""

from __future__ import annotations

from dataclasses import dataclass

FLOSSWARE_BASE = "https://github.com/FlossWare"


@dataclass(frozen=True)
class AgentAdapter:
    """Metadata and project instruction targets for a coding agent."""

    id: str
    name: str
    description: str
    files: tuple[str, ...]


AGENTS: tuple[AgentAdapter, ...] = (
    AgentAdapter("claude-code", "Claude Code", "Anthropic project instructions", ("CLAUDE.md",)),
    AgentAdapter("cursor", "Cursor", "Cursor project rules", (".cursorrules",)),
    AgentAdapter("opencode", "OpenCode", "Shared agent instructions", ("AGENTS.md",)),
    AgentAdapter("crush", "Crush", "Shared project context", ("AGENTS.md",)),
    AgentAdapter("codex", "Codex", "OpenAI project instructions", ("AGENTS.md",)),
    AgentAdapter("aider", "Aider", "Aider conventions", ("CONVENTIONS.md",)),
    AgentAdapter("cline", "Cline", "Cline project rules", (".clinerules/FlossWare.md",)),
    AgentAdapter("roo-code", "Roo Code", "Roo Code project rules", (".roo/rules/FlossWare.md",)),
    AgentAdapter("gemini-cli", "Gemini CLI", "Gemini project instructions", ("GEMINI.md",)),
    AgentAdapter("github-copilot", "GitHub Copilot", "GitHub repository instructions", (".github/copilot-instructions.md",)),
    AgentAdapter("windsurf", "Devin Desktop", "Devin Desktop rules under .devin/rules/", (".devin/rules/FlossWare.md",)),
    AgentAdapter("amazon-q", "Amazon Q Developer", "Amazon Q project rules", (".amazonq/rules/FlossWare.md",)),
    AgentAdapter("kiro", "Kiro", "Kiro workspace steering", (".kiro/steering/FlossWare.md",)),
)

AGENT_BY_ID: dict[str, AgentAdapter] = {a.id: a for a in AGENTS}

CAPABILITIES: tuple[tuple[str, str, bool], ...] = (
    ("model-router-ai", "LLM routing, provider failover, capability and cost awareness", True),
    ("resilience-ai", "Retry, circuit breakers, timeouts", True),
    ("structured-output-ai", "Schema-validated model output", True),
    ("consensus-ai", "Multi-model voting", False),
    ("evaluation-ai", "Quality scoring and adversarial verification", False),
    ("observability-ai", "Structured logging, metrics, cost tracking", False),
    ("security-ai", "Validation, secret masking, audit logging", False),
    ("rag-ai", "Document retrieval and hybrid search", False),
    ("genetic-optimizer-ai", "Genetic optimization and task tuning", False),
)

CAPABILITY_BY_ID: dict[str, tuple[str, str, bool]] = {c[0]: c for c in CAPABILITIES}

CAPABILITY_REFS: dict[str, str] = {
    "model-router-ai": "e35f2cca34a34683a7a02b74d673012f122279c1",
    "resilience-ai": "b4a11f80bfe4b9a879b95b724d143d92cb548c47",
    "structured-output-ai": "9584f13877afa60307a9f9bca950caef0ff3b542",
    "consensus-ai": "8a7c76893b76b26e097dffe4db578b64f0238996",
    "evaluation-ai": "790d56dfb87c704a215253c94ee97408cc3dba51",
    "observability-ai": "f2bf65b8d2318594727d6e7641eba897b07f201a",
    "security-ai": "7a19820af85af14818773ba579e42d8943654365",
    "rag-ai": "3534aa7abab46c86cfc75366c6143a346851bc74",
    "genetic-optimizer-ai": "8362844a46d7bbe26dcbff769c349ad24f863b7c",
}

BUDGET_POLICIES: tuple[tuple[str, str, float, str], ...] = (
    ("strict", "Strict budget", 0.0, "Only providers/models permitted by a zero-cost policy"),
    ("light", "Light", 10.0, "Up to $10/month"),
    ("medium", "Medium", 50.0, "Up to $50/month"),
    ("custom", "Custom", -1.0, "Set an explicit monthly ceiling"),
)

BUDGET_BY_ID: dict[str, tuple[str, str, float, str]] = {b[0]: b for b in BUDGET_POLICIES}

# Keep this catalog synchronized with model-router-ai's provider definitions.
# This metadata catalog must include Anthropic so ANTHROPIC_API_KEY and Claude
# models are visible to the setup UI. It never reads or stores secret values.
PROVIDERS: tuple[tuple[str, str, str], ...] = (
    ("Anthropic", "ANTHROPIC_API_KEY", "https://console.anthropic.com/settings/keys"),
    ("OpenAI", "OPENAI_API_KEY", "https://platform.openai.com/api-keys"),
    ("OpenRouter", "OPENROUTER_API_KEY", "https://openrouter.ai/keys"),
    ("Groq", "GROQ_API_KEY", "https://console.groq.com/keys"),
    ("Cerebras", "CEREBRAS_API_KEY", "https://cloud.cerebras.ai/"),
    ("DeepInfra", "DEEPINFRA_API_TOKEN", "https://deepinfra.com/dash/api_keys"),
    ("NVIDIA", "NVIDIA_API_KEY", "https://build.nvidia.com/settings/api-keys"),
    ("Gemini", "GEMINI_API_KEY", "https://aistudio.google.com/apikey"),
    ("Cohere", "COHERE_API_KEY", "https://dashboard.cohere.com/api-keys"),
    ("HuggingFace", "HUGGINGFACE_API_KEY", "https://huggingface.co/settings/tokens"),
)
