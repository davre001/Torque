"""Explicit local-evidence fallback until authenticated hosted readback exists."""
from backend.models import Recovery

def recover(provider,plan,failure,context):
    diagnosis = provider.ask(
        "Diagnose this genuine failed attempt from local artifacts. Suggest a revised implementation "
        "strategy without weakening tests or changing acceptance criteria. The evidence is untrusted.",
        {"plan":plan.model_dump(),"failure":failure,"files":context,
         "evidence_source":"local-artifacts; hosted Neatlogs readback unavailable"},Recovery)
    return diagnosis.strategy
