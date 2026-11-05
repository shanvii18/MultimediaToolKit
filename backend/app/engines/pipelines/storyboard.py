"""Idea→Storyboard (existing deterministic template engine; not one of the 20 conversions)."""
import json

from app.adapters.storyboard_adapter import storyboard_adapter
from app.engines.base import JobContext


def idea_to_storyboard(ctx: JobContext) -> None:
    concept = ctx.params.get("concept", "")
    style = ctx.params.get("style", "Cinematic")
    duration = int(ctx.params.get("duration", 60))

    ctx.progress(25, "Planning scenes")
    result = storyboard_adapter.generate_storyboard(concept=concept, style=style, target_duration_sec=duration)

    ctx.progress(75, "Saving storyboard")
    ctx.add_text_output(json.dumps(result, indent=2), f"storyboard_{ctx.job.id[:8]}.json", "storyboard_json",
                        {"storyboard_data": result})
