"""Image→Text (OCR) and Image→Audio (read text aloud) pipelines."""
import json

from app.engines.base import ConversionError, JobContext, stem_of
from app.engines.pipelines.common import ocr_image_file, speak_text


def _ocr(ctx: JobContext, start: float):
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    ctx.progress(start, "Reading text from image")
    try:
        result = ocr_image_file(ctx, path)
    except ValueError as e:
        raise ConversionError(str(e))
    if not result.text.strip():
        raise ConversionError("No readable text was found in this image.", code="NO_TEXT_FOUND")
    return source, result


def image_to_text(ctx: JobContext) -> None:
    source, result = _ocr(ctx, 15)
    stem = stem_of(source.filename, "image")
    ctx.progress(85, "Saving extracted text")
    meta = {
        "engine": "Tesseract OCR",
        "ocr_language": result.language,
        "layout": result.layout,
        "word_count": result.word_count,
        "mean_confidence": result.mean_confidence,
        "preview_text": result.text[:2000],
        "source_asset_id": source.id,
    }
    ctx.add_text_output(result.text + "\n", f"{stem}_text.txt", "ocr_txt", meta)
    ctx.add_text_output(json.dumps({**meta, "text": result.text}, indent=2, ensure_ascii=False),
                        f"{stem}_ocr.json", "ocr_json", {"engine": "Tesseract OCR"})


def image_to_audio(ctx: JobContext) -> None:
    """Mode read_aloud: OCR the image, then speak the text with local TTS."""
    source, result = _ocr(ctx, 10)
    stem = stem_of(source.filename, "image")
    ctx.add_text_output(result.text + "\n", f"{stem}_read_text.txt", "ocr_txt", {
        "engine": "Tesseract OCR", "preview_text": result.text[:2000], "word_count": result.word_count,
    })
    speak_text(ctx, result.text, f"{stem}_read_aloud", 35, 98, {
        "pipeline": "Tesseract OCR → text-to-speech", "source_asset_id": source.id,
    })
