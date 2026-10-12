"""Public repository eligibility without exposing recipes or credentials."""
from backend.execution import load_recipes
from backend.models import PipelineError


def eligibility(repository, allowed, recipes):
    # None means GitHub App authorization was checked by the caller.
    # Operator callers may still supply the explicit deployment allowlist.
    if allowed is not None and repository.lower() not in allowed:
        return {'run_supported': False, 'run_reason': 'Repository is not enabled for this Torque deployment.'}
    if recipes is None:
        return {'run_supported': False, 'run_reason': 'Test recipe configuration is unavailable.'}
    if repository.lower() not in recipes:
        return {'run_supported': False, 'run_reason': 'No reviewed test recipe for this repository.'}
    return {'run_supported': True, 'run_reason': None}


def reviewed_recipes():
    try:
        return load_recipes()
    except PipelineError:
        return None
