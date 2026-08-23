## FlossWare AI Integration

This project uses [FlossWare](https://github.com/FlossWare) AI libraries
for LLM-powered development workflows.

### AI Stack
- **[model-router-ai](https://github.com/FlossWare/model-router-ai)**: Smart LLM routing with provider failover
- **[resilience-ai](https://github.com/FlossWare/resilience-ai)**: Retry, circuit breaker, timeout patterns
- **[structured-output-ai](https://github.com/FlossWare/structured-output-ai)**: Schema-validated JSON from LLMs

### Install

```bash
pip install git+https://github.com/FlossWare/model-router-ai.git
pip install git+https://github.com/FlossWare/resilience-ai.git
pip install git+https://github.com/FlossWare/structured-output-ai.git
```

### Providers

Set at least one free API key:
- Cohere (`COHERE_API_KEY`): https://dashboard.cohere.com/api-keys
- OpenRouter (`OPENROUTER_API_KEY`): https://openrouter.ai/keys
- Gemini (`GEMINI_API_KEY`): https://aistudio.google.com/apikey

### Usage

```python
from model_router_ai import create_router

router = create_router(max_monthly=0)
response = await router.complete('Explain this code')
```
