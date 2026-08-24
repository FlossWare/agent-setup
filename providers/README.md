# Provider registry

Provider definitions describe public metadata only. They never contain API keys,
OAuth tokens, cookies, or account secrets.

Credential presence is discovered by `model-router-ai` from the process
environment. Models are discovered from provider APIs when credentials are
available.

Profiles decide which discovered providers/models are permitted to reach an
agent. Discovery and authorization are intentionally separate.
