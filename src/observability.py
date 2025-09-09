import os
from langsmith import Client
from langchain.callbacks.tracers import LangChainTracer
from langchain.callbacks.manager import collect_runs
import json
from datetime import datetime
from typing import Dict, Any
# Initialize LangSmith client
client = Client()


def setup_observability():
    """Setup LangSmith for tracing and observability"""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
    os.environ["LANGCHAIN_PROJECT"] = "travel-concierge"

    tracer = LangChainTracer()
    return tracer


def export_trace(run_id: str, filename: str):
    """Export a trace to JSON file"""
    trace = client.read_run(run_id)

    with open(f"artifacts/{filename}", "w") as f:
        json.dump(trace.dict(), f, indent=2)

    print(f"Trace exported to artifacts/{filename}")


def get_metrics(run_id: str) -> Dict[str, Any]:
    """Get metrics for a run"""
    run = client.read_run(run_id)

    metrics = {
        "total_tokens": run.usage.total_tokens if run.usage else 0,
        "prompt_tokens": run.usage.prompt_tokens if run.usage else 0,
        "completion_tokens": run.usage.completion_tokens if run.usage else 0,
        "latency_ms": run.latency.total_seconds() * 1000 if run.latency else 0,
        "error_rate": 1 if run.error else 0,
        "tools_called": len(
            [event for event in run.events if event.name == "tool_start"]
        ),
        "generated_at": datetime.now().isoformat(),
    }

    return metrics
