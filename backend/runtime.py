"""Build per-run clients/budgets while owning telemetry once per worker process."""
import math
import os
import shutil
from backend.config import ROOT
from backend.execution import Limits, load_recipes, workspace_root
from backend.integrations.github import GitHub
from backend.integrations.gemini import Gemini
from backend.integrations.litellm import LiteLLM
from backend.integrations.neatlogs import Telemetry
from backend.integrations.providers import Budget, StructuredProvider
from backend.models import PipelineError, parse_issue
from backend.pipeline import Pipeline
from backend.tools.repository import snapshot
from backend.tools.sandbox import DockerRunner

SECRET_NAMES = ("NEATLOGS_API_KEY","LITELLM_API_KEY","GEMINI_API_KEY","GITHUB_TOKEN","TORQUE_OPERATOR_TOKEN","NEATLOGS_TOKEN","TORQUE_ACTIONS_TOKEN")

def rates(prefix):
    try:
        values = tuple(float(os.getenv(prefix+"_"+side+"_USD_PER_MILLION","")) for side in ("INPUT","OUTPUT"))
    except ValueError:
        raise PipelineError("Model cost rates must be numeric") from None
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise PipelineError("Configure nonnegative conservative input/output cost rates for both models")
    return values

def readiness():
    reasons = []
    for name in ("LITELLM_API_KEY","LITELLM_BASE_URL","LITELLM_MODEL","GEMINI_API_KEY","GEMINI_MODEL","NEATLOGS_API_KEY"):
        if not os.getenv(name):
            reasons.append(name+" missing")
    for prefix in ("LITELLM","GEMINI"):
        try:
            rates(prefix)
        except PipelineError:
            reasons.append(prefix+" conservative cost rates missing/invalid")
    try:
        Limits.load()
        load_recipes()
    except (PipelineError,ValueError):
        reasons.append("Execution limits or test recipes missing/invalid")
    runner_kind = os.getenv("TORQUE_RUNNER","docker")
    if runner_kind == "github-actions" and not os.getenv("TORQUE_ACTIONS_TOKEN"):
        reasons.append("TORQUE_ACTIONS_TOKEN missing")
    elif runner_kind not in {"docker","github-actions"}:
        reasons.append("Unsupported TORQUE_RUNNER")
    elif runner_kind == "docker" and not shutil.which("docker"):
        reasons.append("Docker unavailable")
    return {"configured":not reasons,"missing":reasons,"live_integrations_verified":False}

class AgentProcessor:
    def __init__(self):
        self.secrets = tuple(os.getenv(name,"") for name in SECRET_NAMES)
        self.telemetry = Telemetry(os.getenv("NEATLOGS_API_KEY",""),self.secrets)

    def __call__(self,store,run_id,owner,checkpoint):
        if not os.getenv("NEATLOGS_API_KEY"):
            raise PipelineError("Neatlogs project key is required for agent execution")
        source_owner,repo,_ = parse_issue(store.get(run_id)["issue_url"])
        recipe = load_recipes().get(f"{source_owner}/{repo}".lower())
        if recipe is None:
            raise PipelineError("No reviewed acceptance recipe for this repository")
        if os.getenv("TORQUE_RUNNER","docker") == "github-actions":
            from backend.tools.actions_runner import ActionsRunner
            runner = ActionsRunner(recipe)
        elif os.getenv("TORQUE_RUNNER","docker") == "docker":
            runner = DockerRunner(recipe)
        else:
            raise PipelineError("Unsupported TORQUE_RUNNER")
        runner.preflight()  # Fail before constructing providers or spending credits.
        limits = Limits.load()
        model_rates = rates("GEMINI"),rates("LITELLM")
        clients = []
        try:
            github = GitHub(os.getenv("GITHUB_TOKEN",""))
            clients.append(github)
            gemini = Gemini(os.getenv("GEMINI_API_KEY",""),os.getenv("GEMINI_MODEL",""),self.telemetry.wrap)
            clients.append(gemini)
            claude = LiteLLM(os.getenv("LITELLM_API_KEY",""),os.getenv("LITELLM_BASE_URL",""),
                             os.getenv("LITELLM_MODEL",""),self.telemetry.wrap)
            clients.append(claude)
            budget = Budget(limits)
            providers = [StructuredProvider(adapter,budget,*costs,checkpoint,limits.transport_retries)
                         for adapter,costs in zip((gemini,claude),model_rates)]
            Pipeline(github=github,prepare=snapshot,runner=runner,
                     investigator_provider=providers[0],implementer_provider=providers[1],
                     budget=budget,recipe=recipe,workspaces=workspace_root(),
                     artifacts=ROOT/"var"/"artifacts",telemetry=self.telemetry,
                     secrets=self.secrets)(store,run_id,owner,checkpoint)
        finally:
            for client in reversed(clients):
                client.close()
            if hasattr(runner,"close"):
                runner.close()

    def close(self):
        self.telemetry.close()
