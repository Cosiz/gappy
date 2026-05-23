import litellm
from app.core.config import get_settings

settings = get_settings()

litellm.set_verbose = False

async def acompletion(prompt: str, model: str | None = None) -> str:
    """Simple async completion using LiteLLM"""
    model = model or settings.LITELLM_MODEL
    
    response = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return response.choices[0].message.content or ""