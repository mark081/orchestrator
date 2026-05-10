import anthropic
from research_agent import run_research
from writer_agent import run_writer


def run_pipeline(client: anthropic.Anthropic, topic: str) -> str:
    print(f"[Orchestrator] Starting pipeline for topic: {topic!r}")

    print("[Orchestrator] Calling research agent...")
    research_notes = run_research(client, topic)

    print("[Orchestrator] Calling writer agent...")
    final_report = run_writer(client, topic, research_notes)

    print("[Orchestrator] Pipeline complete.")
    return final_report
