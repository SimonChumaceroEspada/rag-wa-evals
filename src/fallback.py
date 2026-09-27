"""Fallback primario -> FreeLLMAPI con registro de quién sirvió.

Uso: respuestas del chat, juez y rerank (lo propenso a 429).
Los evals leen el campo `served_by` para no mezclar modelos en el baseline.
"""


def call_with_fallback(primary_fn, fallback_fn, label: str = "call"):
    """Intenta primary_fn; ante excepción usa fallback_fn. Devuelve (valor, quién)."""
    try:
        return primary_fn(), "primary"
    except Exception as e:
        print(f"{label}: primario falló ({e.__class__.__name__}), fallback router")
        return fallback_fn(), "fallback"
