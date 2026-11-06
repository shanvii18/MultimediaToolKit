"""
Central conversion registry: the single source of truth for the 20 directed conversions
(5 formats: text, image, audio, video, animation), their modes, parameters, required
engines and pipeline functions. The API validates jobs against it and the frontend renders
its workspaces from it (GET /api/v1/conversions).
"""
import os
from typing import Any, Callable, Dict, List, Optional

from app.adapters.ffmpeg_adapter import AUDIO_FORMATS
from app.adapters.ocr_adapter import OCR_LANGUAGE_NAMES, OCR_LAYOUTS
from app.adapters.tts_adapter import KOKORO_VOICES
from app.adapters.whisper_adapter import WHISPER_LANGUAGES, WHISPER_MODELS
from app.core.config import settings
from app.engines.availability import unavailable_reason
from app.engines.base import (
    ANIMATION_EXTENSIONS, AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, TEXT_EXTENSIONS, VIDEO_EXTENSIONS,
    ConversionSpec, ModeSpec, ParamSpec,
)
from app.engines.pipelines.animation import animation_to_audio, animation_to_text
from app.engines.pipelines.image import image_to_audio, image_to_text
from app.engines.pipelines.media import audio_to_text, video_to_audio, video_to_text
from app.engines.pipelines.speech import text_to_audio
from app.engines.pipelines.storyboard import idea_to_storyboard
from app.engines.pipelines.video_image import video_to_image
from app.engines.pipelines import generative as gen
from app.engines.pipelines.generative import MAX_ANIMATION_SECONDS


def by_mode(handlers: Dict[str, Callable], default: Callable) -> Callable:
    """Route a job to the pipeline for its selected mode."""
    def run(ctx):
        return handlers.get(ctx.mode, default)(ctx)
    return run


# ---------------- reusable parameter definitions ----------------
def _choices(mapping: Dict[str, str]):
    return [(k, v) for k, v in mapping.items()]


def p_whisper_model(modes=None):
    return ParamSpec("model", "Speech model", default=settings.WHISPER_DEFAULT_MODEL,
                     choices=_choices(WHISPER_MODELS), modes=modes,
                     help="Larger models are more accurate but slower on CPU.")


def p_whisper_language(modes=None):
    return ParamSpec("language", "Spoken language", default="auto", choices=_choices(WHISPER_LANGUAGES), modes=modes)


def p_voice(modes=None):
    return ParamSpec("voice", "Voice", default="af_heart", choices=_choices(KOKORO_VOICES), modes=modes)


def p_speed(modes=None):
    return ParamSpec("speed", "Speaking speed", type="number", default=1.0, min=0.5, max=2.0, step=0.1, modes=modes)


def p_audio_format(modes=None, default="mp3"):
    labels = {"mp3": "MP3", "wav": "WAV (lossless)", "m4a": "M4A (AAC)", "ogg": "OGG (Vorbis)", "flac": "FLAC (lossless)"}
    return ParamSpec("audio_format", "Audio format", default=default,
                     choices=[(k, labels[k]) for k in AUDIO_FORMATS], modes=modes)


def p_ocr_language(modes=None):
    return ParamSpec("ocr_language", "Text language", default="eng", choices=_choices(OCR_LANGUAGE_NAMES), modes=modes,
                     help="Must be installed in Tesseract on the server.")


def p_layout(modes=None):
    return ParamSpec("layout", "Text layout", default="auto",
                     choices=[(k, v[1]) for k, v in OCR_LAYOUTS.items()], modes=modes)


def p_aspect(default="landscape", modes=None):
    return ParamSpec("aspect", "Shape", default=default, modes=modes,
                     choices=[("landscape", "Landscape 16:9"), ("portrait", "Portrait 9:16"), ("square", "Square 1:1")])


def p_style(modes=None):
    return ParamSpec("style", "Colour style", default="auto", modes=modes,
                     choices=[("auto", "Automatic"), ("brand", "Ember (brand)"), ("violet", "Violet night"),
                              ("emerald", "Emerald"), ("rose", "Rose"), ("ocean", "Ocean"), ("amber", "Amber")])


def p_image_format(modes=None):
    return ParamSpec("image_format", "Image format", default="png", modes=modes,
                     choices=[("png", "PNG"), ("jpg", "JPEG"), ("webp", "WebP")])


def p_animation_format(modes=None):
    return ParamSpec("animation_format", "Animation format", default="gif", modes=modes,
                     choices=[("gif", "GIF"), ("webp", "Animated WebP")])


def p_text(label="Text", max_length=None, help=""):
    return ParamSpec("text", label, type="textarea", default="", max_length=max_length or settings.MAX_TEXT_CHARS,
                     help=help or "Type here, or upload a .txt file instead.")


MOTIONS = [("zoom_in", "Slow zoom in"), ("zoom_out", "Slow zoom out"), ("pan_left", "Pan left"), ("pan_right", "Pan right")]
VIS_STYLES = [("waves", "Waves"), ("spectrum", "Scrolling spectrum"), ("bars", "Frequency bars")]


# ---------------- validators ----------------
def _validate_text_to_audio(params: Dict[str, Any], inputs: List) -> None:
    if inputs:
        if len(inputs) > 1:
            raise ValueError("Upload a single .txt file.")
        return
    if not (params.get("text") or "").strip():
        raise ValueError("Enter some text or upload a .txt file.")


def _validate_text_or_file(params: Dict[str, Any], inputs: List) -> None:
    if not inputs and not (params.get("text") or "").strip():
        raise ValueError("Enter some text or upload a .txt file.")


def _validate_storyboard(params: Dict[str, Any], inputs: List) -> None:
    concept = (params.get("concept") or "").strip()
    if not concept:
        raise ValueError("Concept / brief cannot be empty.")
    if len(concept.split()) < 3 or len(concept) < 12:
        raise ValueError("Concept brief is too brief. Please provide at least 3 descriptive words (min 12 characters).")


# ---------------- the 20 conversions ----------------
def _coming_soon(cid: str, source: str, target: str, title: str, description: str, category="generative") -> ConversionSpec:
    return ConversionSpec(
        id=cid, source=source, target=target, title=title, description=description, category=category,
        modes=[ModeSpec("default", "Coming soon", "Not implemented yet.", coming_soon=True)],
    )


_SPECS: List[ConversionSpec] = [
    # ---------- NORMAL ----------
    ConversionSpec(
        id="text_to_audio", source="text", target="audio", category="normal",
        title="Text → Audio", description="Turn text into natural speech with a local, offline voice model.",
        run=text_to_audio, input_kind="file_or_text", accepted_extensions=TEXT_EXTENSIONS,
        modes=[ModeSpec("speak", "Speak text", "Kokoro-82M text-to-speech (CPU).", engines=("kokoro", "ffmpeg"))],
        params=[ParamSpec("text", "Text", type="textarea", default="", max_length=settings.MAX_TEXT_CHARS,
                          help=f"Up to {settings.MAX_TEXT_CHARS} characters, or upload a .txt file instead."),
                p_voice(), p_speed(), p_audio_format()],
        validator=_validate_text_to_audio,
    ),
    ConversionSpec(
        id="audio_to_text", source="audio", target="text", category="normal",
        title="Audio → Text", description="Transcribe speech to text with timestamps (TXT, SRT, VTT, JSON).",
        run=audio_to_text, accepted_extensions=AUDIO_EXTENSIONS,
        modes=[ModeSpec("transcribe", "Transcribe", "Whisper speech recognition (CPU).", engines=("whisper", "ffmpeg"))],
        params=[p_whisper_model(), p_whisper_language()],
    ),
    ConversionSpec(
        id="video_to_text", source="video", target="text", category="normal",
        title="Video → Text", description="Transcribe the speech in a video (TXT, SRT, VTT, JSON).",
        run=video_to_text, accepted_extensions=VIDEO_EXTENSIONS,
        modes=[ModeSpec("transcribe", "Transcribe speech", "FFmpeg audio extraction + Whisper.",
                        engines=("whisper", "ffmpeg"))],
        params=[p_whisper_model(), p_whisper_language()],
    ),
    ConversionSpec(
        id="video_to_audio", source="video", target="audio", category="normal",
        title="Video → Audio", description="Extract the soundtrack of a video as MP3, WAV, M4A, OGG or FLAC.",
        run=video_to_audio, accepted_extensions=VIDEO_EXTENSIONS,
        modes=[ModeSpec("extract", "Extract audio", "FFmpeg re-encodes the first audio track.", engines=("ffmpeg",))],
        params=[p_audio_format()],
    ),
    ConversionSpec(
        id="animation_to_text", source="animation", target="text", category="normal",
        title="Animation → Text",
        description="Read on-screen text and transcribe any speech in a GIF, WebP or short clip.",
        run=by_mode({"describe": lambda ctx: gen.describe_animation(ctx, speak=False)}, animation_to_text),
        accepted_extensions=ANIMATION_EXTENSIONS,
        modes=[ModeSpec("extract", "Text & speech", "Frame OCR (Tesseract) + speech recognition (Whisper). "
                        "Visual description of silent animations is coming soon.", engines=("ffmpeg", "pillow")),
               ModeSpec("describe", "Describe visuals (AI)", "AI describes 3 key frames.",
                        engines=("ai_caption", "ffmpeg", "pillow"))],
        params=[p_ocr_language(modes=("extract",)), p_whisper_model(modes=("extract",)),
                p_whisper_language(modes=("extract",))],
    ),
    ConversionSpec(
        id="animation_to_audio", source="animation", target="audio", category="normal",
        title="Animation → Audio",
        description="Extract a clip's soundtrack, or read its on-screen text aloud.",
        run=by_mode({"narrate": lambda ctx: gen.describe_animation(ctx, speak=True)}, animation_to_audio),
        accepted_extensions=ANIMATION_EXTENSIONS,
        modes=[ModeSpec("soundtrack", "Extract soundtrack", "For clips with audio (MP4/WebM/MOV).", engines=("ffmpeg",)),
               ModeSpec("read_text", "Read on-screen text aloud", "Frame OCR → local TTS.",
                        engines=("ffmpeg", "pillow", "tesseract", "kokoro")),
               ModeSpec("narrate", "Narrate visuals (AI)", "AI frame descriptions spoken by Kokoro.",
                        engines=("ai_caption", "ffmpeg", "pillow", "kokoro"))],
        params=[p_ocr_language(modes=("read_text",)), p_voice(modes=("read_text", "narrate")),
                p_speed(modes=("read_text", "narrate")),
                p_audio_format()],
    ),
    # ---------- GENERATIVE / SPECIAL ----------
    ConversionSpec(
        id="text_to_image", source="text", target="image", category="generative",
        title="Text → Image", description="Generate an image from a prompt with AI, or design a typography poster.",
        run=gen.text_to_image, input_kind="file_or_text", accepted_extensions=TEXT_EXTENSIONS,
        modes=[ModeSpec("ai", "AI image (FLUX.1-schnell)", "Hosted AI provider generates the image.",
                        engines=("ai_image", "pillow")),
               ModeSpec("poster", "Typography poster", "Pillow renders your text as a designed poster (CPU).",
                        engines=("pillow",))],
        params=[p_text("Prompt / text", 2000), p_aspect("square"), p_style(modes=("poster",)), p_image_format()],
        validator=_validate_text_or_file,
    ),
    ConversionSpec(
        id="text_to_video", source="text", target="video", category="generative",
        title="Text → Video", description="Turn a script into a narrated scene video with captions.",
        run=gen.text_to_video, input_kind="file_or_text", accepted_extensions=TEXT_EXTENSIONS,
        modes=[ModeSpec("slides", "Narrated typography scenes", "Scene cards + Kokoro narration + camera motion (CPU).",
                        engines=("pillow", "ffmpeg", "kokoro")),
               ModeSpec("ai_scenes", "AI-illustrated scenes", "AI image per scene + narration + camera motion.",
                        engines=("ai_image", "pillow", "ffmpeg", "kokoro"))],
        params=[p_text("Script", 1800, "Each sentence becomes a scene (max 10 scenes)."), p_aspect("landscape"),
                p_style(), ParamSpec("narrate", "Narrate scenes", type="boolean", default=True), p_voice(), p_speed()],
        validator=_validate_text_or_file,
    ),
    ConversionSpec(
        id="text_to_animation", source="text", target="animation", category="generative",
        title="Text → Animation", description="Kinetic typography, or an AI image brought to life as a loop.",
        run=gen.text_to_animation, input_kind="file_or_text", accepted_extensions=TEXT_EXTENSIONS,
        modes=[ModeSpec("kinetic", "Kinetic typography", "Words animate in one by one (CPU).", engines=("pillow",)),
               ModeSpec("ai_loop", "AI image loop", "AI image + seamless camera loop.",
                        engines=("ai_image", "pillow", "ffmpeg"))],
        params=[p_text("Text / prompt", 600), p_aspect("square"), p_style(modes=("kinetic",)), p_animation_format()],
        validator=_validate_text_or_file,
    ),
    ConversionSpec(
        id="audio_to_image", source="audio", target="image", category="generative",
        title="Audio → Image", description="Waveform art, a spectrogram, or AI cover art inspired by the sound.",
        run=gen.audio_to_image, accepted_extensions=AUDIO_EXTENSIONS,
        modes=[ModeSpec("waveform", "Waveform art", "Real waveform on a mood-matched design (CPU).",
                        engines=("ffmpeg", "pillow")),
               ModeSpec("spectrogram", "Spectrogram", "Frequency map of the whole recording (CPU).",
                        engines=("ffmpeg", "pillow")),
               ModeSpec("ai_cover", "AI cover art", "Speech + mood → prompt → AI image.",
                        engines=("ai_image", "ffmpeg", "pillow"))],
        params=[p_aspect("landscape"),
                ParamSpec("title", "Title", type="text", default="", max_length=120, modes=("waveform",)),
                ParamSpec("palette", "Spectrogram colours", default="magma", modes=("spectrogram",),
                          choices=[("magma", "Magma"), ("viridis", "Viridis"), ("plasma", "Plasma"), ("fire", "Fire"),
                                   ("cool", "Cool"), ("rainbow", "Rainbow")]),
                ParamSpec("prompt_hint", "Describe what you want (optional)", type="text", default="",
                          max_length=300, modes=("ai_cover",)),
                p_whisper_model(modes=("ai_cover",)), p_image_format()],
    ),
    ConversionSpec(
        id="audio_to_video", source="audio", target="video", category="generative",
        title="Audio → Video", description="An audio-reactive visualiser video, with optional speech captions.",
        run=gen.audio_to_video, accepted_extensions=AUDIO_EXTENSIONS,
        modes=[ModeSpec("visualizer", "Visualiser", "Waves / spectrum / bars over a designed background (CPU).",
                        engines=("ffmpeg", "pillow")),
               ModeSpec("ai_visualizer", "Visualiser on AI art", "AI background generated from the audio.",
                        engines=("ai_image", "ffmpeg", "pillow"))],
        params=[ParamSpec("visual_style", "Visual style", default="waves", choices=VIS_STYLES),
                p_aspect("landscape"), ParamSpec("title", "Title", type="text", default="", max_length=120),
                ParamSpec("captions", "Add speech captions (Whisper)", type="boolean", default=False),
                p_whisper_model()],
    ),
    ConversionSpec(
        id="audio_to_animation", source="audio", target="animation", category="generative",
        title="Audio → Animation", description="A short animation that moves with the sound.",
        run=gen.audio_to_animation, accepted_extensions=AUDIO_EXTENSIONS,
        modes=[ModeSpec("waveform", "Waveform loop", "Animated visualiser (CPU).", engines=("ffmpeg", "pillow")),
               ModeSpec("pulse", "Beat pulse", "Title card pulsing with loudness (CPU).", engines=("ffmpeg", "pillow")),
               ModeSpec("ai_pulse", "AI art pulse", "AI artwork pulsing with loudness.",
                        engines=("ai_image", "ffmpeg", "pillow"))],
        params=[ParamSpec("start", "Start (seconds)", type="number", default=0, min=0, max=3600, step=0.5),
                ParamSpec("seconds", "Length (seconds)", type="number", default=6, min=1, max=MAX_ANIMATION_SECONDS,
                          step=1),
                ParamSpec("visual_style", "Visual style", default="waves", modes=("waveform",), choices=VIS_STYLES),
                ParamSpec("title", "Title", type="text", default="", max_length=80, modes=("pulse",)),
                ParamSpec("prompt_hint", "Describe what you want (optional)", type="text", default="",
                          max_length=300, modes=("ai_pulse",)),
                p_aspect("square"), p_animation_format()],
    ),
    ConversionSpec(
        id="image_to_text", source="image", target="text", category="generative",
        title="Image → Text", description="Extract the text in an image (OCR), or describe the image with AI.",
        run=by_mode({"describe": gen.describe_image_to_text}, image_to_text), accepted_extensions=IMAGE_EXTENSIONS,
        modes=[ModeSpec("ocr", "Extract text (OCR)", "Tesseract OCR (CPU).", engines=("tesseract", "pillow")),
               ModeSpec("describe", "Describe image (AI)", "Hosted vision-language model describes the image.",
                        engines=("ai_caption", "pillow"))],
        params=[p_ocr_language(modes=("ocr",)), p_layout(modes=("ocr",))],
    ),
    ConversionSpec(
        id="image_to_audio", source="image", target="audio", category="generative",
        title="Image → Audio", description="Read the text in an image aloud, or describe the image in speech.",
        run=by_mode({"describe": gen.describe_image_to_audio}, image_to_audio), accepted_extensions=IMAGE_EXTENSIONS,
        modes=[ModeSpec("read_aloud", "Read text aloud", "Tesseract OCR → Kokoro TTS.",
                        engines=("tesseract", "pillow", "kokoro", "ffmpeg")),
               ModeSpec("describe", "Describe in speech (AI)", "AI description → Kokoro TTS.",
                        engines=("ai_caption", "pillow", "kokoro", "ffmpeg"))],
        params=[p_ocr_language(modes=("read_aloud",)), p_layout(modes=("read_aloud",)),
                p_voice(modes=("read_aloud", "describe")), p_speed(modes=("read_aloud", "describe")),
                p_audio_format(modes=("read_aloud", "describe"))],
    ),
    ConversionSpec(
        id="image_to_video", source="image", target="video", category="generative",
        title="Image → Video", description="Cinematic camera motion, or an AI-narrated video of the image.",
        run=gen.image_to_video, accepted_extensions=IMAGE_EXTENSIONS,
        modes=[ModeSpec("ken_burns", "Camera motion", "Smooth Ken Burns zoom/pan (CPU).", engines=("ffmpeg", "pillow")),
               ModeSpec("narrated", "AI-narrated", "AI describes the image; Kokoro narrates over the motion.",
                        engines=("ai_caption", "kokoro", "ffmpeg", "pillow"))],
        params=[ParamSpec("motion", "Motion", default="zoom_in", choices=MOTIONS),
                ParamSpec("seconds", "Duration (seconds)", type="number", default=6, min=2, max=30, step=1,
                          modes=("ken_burns",)),
                p_voice(modes=("narrated",)), p_aspect("landscape")],
    ),
    ConversionSpec(
        id="image_to_animation", source="image", target="animation", category="generative",
        title="Image → Animation", description="A seamless looping animation with camera motion.",
        run=gen.image_to_animation, accepted_extensions=IMAGE_EXTENSIONS,
        modes=[ModeSpec("loop", "Seamless motion loop", "Zoom/pan boomerang loop (CPU).", engines=("ffmpeg", "pillow"))],
        params=[ParamSpec("motion", "Motion", default="zoom_in", choices=MOTIONS),
                ParamSpec("seconds", "Loop half-length (seconds)", type="number", default=2, min=1, max=6, step=0.5),
                p_aspect("square"), p_animation_format()],
    ),
    ConversionSpec(
        id="video_to_image", source="video", target="image", category="generative",
        title="Video → Image", description="Extract and edit a frame, or let the app pick the sharpest frame.",
        run=by_mode({"poster": gen.video_poster, "ai_poster": gen.video_poster}, video_to_image),
        accepted_extensions=VIDEO_EXTENSIONS,
        modes=[ModeSpec("frame", "Pick a frame", "Exact frame at a timestamp + edits.", engines=("ffmpeg", "pillow")),
               ModeSpec("best_frame", "Best frame (auto)", "Samples 12 frames and keeps the sharpest.",
                        engines=("ffmpeg", "pillow")),
               ModeSpec("poster", "Poster / thumbnail", "Strongest frame + title band (CPU).",
                        engines=("ffmpeg", "pillow")),
               ModeSpec("ai_poster", "AI poster", "AI describes the video's best frame and paints a poster.",
                        engines=("ai_caption", "ai_image", "ffmpeg", "pillow"))],
        params=[
            ParamSpec("timestamp", "Timestamp (seconds)", type="number", default=0.0, min=0, max=86400, step=0.04,
                      modes=("frame",), help="Use the preview player to find the moment you want."),
            ParamSpec("title", "Poster title", type="text", default="", max_length=120, modes=("poster", "ai_poster")),
            ParamSpec("rotate", "Rotate", default="0",
                      choices=[("0", "None"), ("90", "90° right"), ("180", "180°"), ("270", "90° left")]),
            ParamSpec("crop_left", "Crop left (%)", type="number", default=0, min=0, max=45, step=1),
            ParamSpec("crop_right", "Crop right (%)", type="number", default=0, min=0, max=45, step=1),
            ParamSpec("crop_top", "Crop top (%)", type="number", default=0, min=0, max=45, step=1),
            ParamSpec("crop_bottom", "Crop bottom (%)", type="number", default=0, min=0, max=45, step=1),
            ParamSpec("brightness", "Brightness", type="number", default=1.0, min=0.2, max=3.0, step=0.1),
            ParamSpec("contrast", "Contrast", type="number", default=1.0, min=0.2, max=3.0, step=0.1),
            ParamSpec("grayscale", "Black & white", type="boolean", default=False),
            ParamSpec("max_width", "Max width (px, 0 = original)", type="number", default=0, min=0, max=7680, step=1),
            ParamSpec("image_format", "Image format", default="png",
                      choices=[("png", "PNG"), ("jpg", "JPEG"), ("webp", "WebP")]),
        ],
    ),
    ConversionSpec(
        id="video_to_animation", source="video", target="animation", category="generative",
        title="Video → Animation", description="Turn a moment of a video into an optimised GIF or animated WebP.",
        run=gen.video_to_animation, accepted_extensions=VIDEO_EXTENSIONS,
        modes=[ModeSpec("clip", "Clip to animation", "Palette-optimised GIF / WebP with effects (CPU).",
                        engines=("ffmpeg",))],
        params=[ParamSpec("start", "Start (seconds)", type="number", default=0, min=0, max=86400, step=0.1,
                          help="Use the preview player to find the moment."),
                ParamSpec("duration", "Length (seconds)", type="number", default=4, min=0.5, max=MAX_ANIMATION_SECONDS,
                          step=0.5),
                ParamSpec("fps", "Frames per second", type="number", default=12, min=5, max=25, step=1),
                ParamSpec("width", "Width (px)", type="number", default=480, min=120, max=1080, step=10),
                ParamSpec("effect", "Effect", default="none",
                          choices=[("none", "None"), ("cartoon", "Cartoon edges"), ("grayscale", "Black & white"),
                                   ("vintage", "Vintage")]),
                ParamSpec("boomerang", "Boomerang (forward then back)", type="boolean", default=False),
                p_animation_format()],
    ),
    ConversionSpec(
        id="animation_to_image", source="animation", target="image", category="generative",
        title="Animation → Image", description="The sharpest frame, a titled poster, or a contact sheet.",
        run=gen.animation_to_image, accepted_extensions=ANIMATION_EXTENSIONS,
        modes=[ModeSpec("best_frame", "Best frame", "Sharpest frame picked automatically (CPU).",
                        engines=("ffmpeg", "pillow")),
               ModeSpec("poster", "Poster", "Best frame with a title band (CPU).", engines=("ffmpeg", "pillow")),
               ModeSpec("contact_sheet", "Contact sheet", "Grid of evenly sampled frames (CPU).",
                        engines=("ffmpeg", "pillow"))],
        params=[ParamSpec("title", "Title", type="text", default="", max_length=120, modes=("poster",)),
                ParamSpec("frames", "Frames", type="number", default=12, min=4, max=24, step=1,
                          modes=("contact_sheet",)),
                ParamSpec("columns", "Columns", type="number", default=4, min=2, max=6, step=1,
                          modes=("contact_sheet",)),
                p_image_format()],
    ),
    ConversionSpec(
        id="animation_to_video", source="animation", target="video", category="generative",
        title="Animation → Video", description="Convert a GIF/WebP into a shareable MP4 or WebM, looped and smoothed.",
        run=gen.animation_to_video, accepted_extensions=ANIMATION_EXTENSIONS,
        modes=[ModeSpec("convert", "Convert", "Frame-exact conversion with optional motion smoothing (CPU).",
                        engines=("ffmpeg", "pillow"))],
        params=[ParamSpec("loops", "Repeat", type="number", default=3, min=1, max=20, step=1),
                ParamSpec("width", "Width (px, 0 = original)", type="number", default=0, min=0, max=1920, step=10),
                ParamSpec("smooth", "Motion smoothing (interpolate to 30 fps)", type="boolean", default=False),
                ParamSpec("video_format", "Video format", default="mp4",
                          choices=[("mp4", "MP4 (H.264)"), ("webm", "WebM (VP9)")])],
    ),
    # ---------- legacy workflow tool (kept working) ----------
    ConversionSpec(
        id="idea_to_storyboard", source="text", target="text", category="workflow", listed=False,
        title="Idea → Storyboard", description="Deterministic multi-scene storyboard template engine.",
        run=idea_to_storyboard, input_kind="text",
        modes=[ModeSpec("template", "Template engine", "Keyword-driven templates (not AI).")],
        params=[ParamSpec("concept", "Concept", type="textarea", default="", max_length=2000),
                ParamSpec("style", "Style", type="text", default="Cinematic", max_length=100),
                ParamSpec("duration", "Duration (s)", type="number", default=60, min=10, max=600, step=1)],
        validator=_validate_storyboard,
    ),
]

REGISTRY: Dict[str, ConversionSpec] = {spec.id: spec for spec in _SPECS}
CONVERSION_IDS = [s.id for s in _SPECS if s.listed]
assert len(CONVERSION_IDS) == 20, "The product defines exactly 20 directed conversions."


def get_spec(conversion_id: str) -> Optional[ConversionSpec]:
    return REGISTRY.get((conversion_id or "").strip())


def mode_status(mode: ModeSpec) -> Dict[str, Any]:
    reason = None if mode.coming_soon else unavailable_reason(mode.engines)
    status = "coming_soon" if mode.coming_soon else ("available" if reason is None else "unavailable")
    return {"id": mode.id, "label": mode.label, "description": mode.description, "status": status,
            "reason": reason, "engines": list(mode.engines)}


def describe(spec: ConversionSpec) -> Dict[str, Any]:
    modes = [mode_status(m) for m in spec.modes]
    if not spec.implemented:
        status = "coming_soon"
    elif any(m["status"] == "available" for m in modes):
        status = "available"
    else:
        status = "unavailable"
    return {
        "id": spec.id, "source": spec.source, "target": spec.target, "title": spec.title,
        "description": spec.description, "category": spec.category, "status": status,
        "input_kind": spec.input_kind, "accepted_extensions": list(spec.accepted_extensions),
        "modes": modes, "params": [p.to_dict() for p in spec.params],
    }


def list_conversions() -> List[Dict[str, Any]]:
    return [describe(REGISTRY[cid]) for cid in CONVERSION_IDS]


def validate_job_request(spec: ConversionSpec, params: Dict[str, Any], inputs: List) -> Dict[str, Any]:
    """
    Validate a job request against the spec. Returns cleaned params.
    Raises ValueError (400), LookupError (unavailable engine, 503) or NotImplementedError (coming soon).
    """
    if not spec.implemented:
        raise NotImplementedError(f"{spec.title} is coming soon and cannot be run yet.")
    mode = spec.get_mode((params or {}).get("mode"))
    if mode.coming_soon:
        raise NotImplementedError(f"'{mode.label}' for {spec.title} is coming soon and cannot be run yet.")

    if spec.input_kind == "file":
        if not inputs:
            raise ValueError(f"No input asset specified for {spec.id}.")
        if len(inputs) > spec.max_inputs:
            raise ValueError(f"{spec.title} accepts {spec.max_inputs} input file.")
    if inputs and spec.accepted_extensions:
        for asset in inputs:
            ext = os.path.splitext(asset.storage_key or asset.filename)[1].lower()
            if ext not in spec.accepted_extensions:
                raise ValueError(f"{spec.title} does not accept '{ext}' files. "
                                 f"Accepted: {', '.join(spec.accepted_extensions)}.")

    cleaned = spec.clean_params(params, mode)
    if spec.validator:
        spec.validator(cleaned, inputs)

    reason = unavailable_reason(mode.engines)
    if reason:
        raise LookupError(reason)
    return cleaned
