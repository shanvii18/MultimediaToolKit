"""Text→Audio pipeline (local Kokoro TTS)."""
from app.engines.base import ConversionError, JobContext, stem_of
from app.engines.pipelines.common import speak_text


def _read_text_input(ctx: JobContext) -> tuple:
    """Text comes from the `text` parameter or an uploaded .txt file."""
    if ctx.job.input_asset_ids:
        asset = ctx.input_asset(0)
        path = ctx.input_path(0)
        with open(path, "rb") as f:
            raw = f.read()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ConversionError("The text file must be UTF-8 encoded.")
        return text, stem_of(asset.filename, "speech")
    return ctx.params.get("text", ""), "speech"


def text_to_audio(ctx: JobContext) -> None:
    text, stem = _read_text_input(ctx)
    ctx.progress(5, "Preparing text")
    speak_text(ctx, text, stem, 10, 98)
