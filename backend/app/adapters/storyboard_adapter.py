import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class StoryboardAdapter:
    """
    Directorial Storyboard Adapter.
    Generates structured, multi-scene cinematic storyboards with distinct narrative arcs,
    cinematography composition cues, acoustic design, and bespoke voiceover scripts.
    Operates via a deterministic, context-aware directorial heuristic engine labeled honestly.
    """

    # Domain keywords for context classification
    THEME_CUES = {
        "sci-fi": ["space", "alien", "rover", "planet", "laser", "galaxy", "cyber", "robot", "ship", "crystalline", "future", "star", "hologram", "cavern", "deep-sea", "trench", "submarine", "submersible"],
        "nature": ["forest", "ocean", "wildlife", "mountain", "mountains", "falcon", "bird", "alpine", "crags", "river", "animal", "animals", "jungle", "arctic", "tree", "trees", "desert", "weather", "earth", "storm", "volcano"],
        "commercial": ["product", "brand", "app", "service", "customer", "startup", "platform", "business", "launch", "solution", "innovative", "software", "market", "wearable", "biometric"],
        "documentary": ["history", "culture", "investigation", "century", "tradition", "real-life", "community", "heritage", "legacy", "historical", "archive", "archival"],
        "thriller": ["dark", "mystery", "chase", "shadow", "secret", "detective", "escape", "agent", "conspiracy", "danger", "heist", "tension", "night"],
        "fantasy": ["dragon", "magic", "sword", "kingdom", "wizard", "spell", "castle", "myth", "realm", "legend", "portal", "sorcery"]
    }

    def _detect_theme(self, text: str, style: str) -> str:
        text_lower = text.lower()
        scores: Dict[str, int] = {}
        for theme, keywords in self.THEME_CUES.items():
            count = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'(?:s|es)?\b', text_lower))
            if count > 0:
                scores[theme] = count
        if scores:
            return max(scores, key=scores.get)

        style_lower = style.lower()
        if "sci-fi" in style_lower or "cyberpunk" in style_lower:
            return "sci-fi"
        if "documentary" in style_lower:
            return "documentary"
        if "commercial" in style_lower or "3d" in style_lower:
            return "commercial"
        if "fantasy" in style_lower:
            return "fantasy"
        return "cinematic_general"

    def _get_cinematic_composition(self, scene_role: str, theme: str, style: str) -> str:
        compositions = {
            "hook": {
                "sci-fi": f"Extreme wide establishing shot, anamorphic 35mm lens, volumetric atmospheric haze, cyan and tungsten rim lighting, slow low-angle crane tracking in {style}.",
                "nature": f"Sweeping aerial drone shot, 24mm wide angle, golden hour directional sunlight, slow sweeping tilt revealing panoramic terrain in {style}.",
                "commercial": f"Pristine macro hero framing, 85mm f/1.4 lens, soft diffused studio key light with specular highlights, smooth motorized slider glide in {style}.",
                "documentary": f"Eye-level observational wide shot, 35mm prime lens, natural ambient environmental lighting, slow tripod pan in {style}.",
                "thriller": f"Dutch angle medium-wide shot, 28mm lens, chiaroscuro harsh side lighting with deep obscuring shadows, slow handheld creeping move in {style}.",
                "fantasy": f"Epic panoramic vista, ultra-wide 20mm lens, mystical crepuscular rays piercing cloud cover, steady bird's eye descent in {style}.",
                "cinematic_general": f"Wide atmospheric establishing shot, 35mm cinema lens, soft rim key lighting, steady forward dolly tracking in {style}."
            },
            "exploration": {
                "sci-fi": f"Over-the-shoulder tracking shot, 50mm anamorphic, neon reflections off reflective alloy surfaces, smooth motorized gimbal following navigation in {style}.",
                "nature": f"Medium close-up at subject eye level, 70mm lens, dappled forest canopy light, slow parallax horizontal tracking in {style}.",
                "commercial": f"Dynamic angled cut-in, 50mm prime, high-speed shutter with crisp motion clarity, subtle 45-degree rotational push-in in {style}.",
                "documentary": f"Medium intimate handheld framing, 50mm prime lens, documentary grain texture, responsive organic camera adjustments in {style}.",
                "thriller": f"Tight tracking shot behind subject, 40mm lens, flickering practical light sources, rapid low-profile lateral slide in {style}.",
                "fantasy": f"Low-angle medium tracker, 35mm lens, ambient magical particulate glow, rising jib arm movement in {style}.",
                "cinematic_general": f"Medium tracking profile shot, 50mm cinema prime, warm natural backlight, fluid lateral dolly tracking in {style}."
            },
            "climax": {
                "sci-fi": f"Intense tight close-up, 85mm portrait cinema lens, pulsating energy flare illumination, rapid vertigo zoom-in (dolly counter-zoom) in {style}.",
                "nature": f"High-speed 120fps slow-motion close-up, 100mm macro lens, sharp crystalline rim lighting capturing peak action freeze in {style}.",
                "commercial": f"360-degree rotational hero orbit, 50mm lens, dynamic edge backlighting, instantaneous visual transformation snapshot in {style}.",
                "documentary": f"Direct straight-on candid close-up, 85mm prime, high-contrast natural light capturing emotional peak revelation in {style}.",
                "thriller": f"Extreme tight close-up on eyes and hands, 100mm macro, sudden strobe light flash, rapid whip-pan accentuating crisis in {style}.",
                "fantasy": f"Dynamic low-angle hero framing, 28mm wide, blinding ethereal luminescence erupting from focal source in {style}.",
                "cinematic_general": f"Dramatic high-contrast close-up, 85mm lens, intense directional spotlight, dynamic push-in in {style}."
            },
            "resolution": {
                "sci-fi": f"High-angle pull-away shot, 35mm anamorphic, deep twilight space palette with subtle lens flares, slow continuous crane ascending in {style}.",
                "nature": f"Wide environmental tableau, 35mm lens, sunset dusk palette settling over still landscape, lock-off master shot in {style}.",
                "commercial": f"Centered clean brand master composition, 50mm prime, bright balanced neutral lighting, smooth settled lock-off with negative space in {style}.",
                "documentary": f"Environmental medium wide shot, 35mm prime, soft contemplative twilight lighting, steady lingering hold in {style}.",
                "thriller": f"Medium shot receding into shadow, 50mm lens, lone streetlamp casting long silhouettes, slow reverse tracking into darkness in {style}.",
                "fantasy": f"Elevated horizon vista, 24mm wide, triumphant atmospheric sky glow, gentle crane lift toward expanding horizon in {style}.",
                "cinematic_general": f"Wide closing tableau, 35mm lens, warm lingering sunset tones, smooth slow reverse dolly out in {style}."
            }
        }
        theme_key = theme if theme in compositions["hook"] else "cinematic_general"
        role_key = scene_role if scene_role in compositions else "hook"
        return compositions[role_key].get(theme_key, compositions[role_key]["cinematic_general"])

    def _get_audio_design(self, scene_role: str, theme: str) -> str:
        audio_designs = {
            "hook": {
                "sci-fi": "Sub-bass harmonic drone, low-frequency atmospheric rumble, rhythmic telemetry pings echoing into vast stillness.",
                "nature": "Natural environmental acoustic bed, soft wind gusting through vegetation, distant wildlife calls fading in.",
                "commercial": "Crisp modern electronic rise, clean acoustic plucks, subtle percussive heartbeat building momentum.",
                "documentary": "Subtle contemplative cello sustained note, room tone, quiet archival tape hiss establishing era.",
                "thriller": "Eerie metallic bowed cymbal, dissonant low cello drone, sudden muted heartbeat thump.",
                "fantasy": "Ethereal choir vowel pads, wind chimes, distant brass French horn melody swelling softly.",
                "cinematic_general": "Lush atmospheric orchestral swell, soft piano baseline, ambient stereo field wash."
            },
            "exploration": {
                "sci-fi": "Ascending synthesizer arpeggio, hydraulic servo hiss, energetic mechanical propulsion frequencies.",
                "nature": "Textured foley footsteps on gravel, rushing water cascades, rhythmic insect chatter expanding.",
                "commercial": "Driving uptempo electronic percussion, warm bassline synth, bright polyphonic melody entry.",
                "documentary": "Acoustic fingerpicked guitar and viola melody, realistic footsteps, clear location ambience.",
                "thriller": "Accelerating ticking tempo, sharp breathless foley, sudden industrial scrape in background.",
                "fantasy": "Galloping percussion, acoustic hand drums, soaring Celtic flute phrase weaving through.",
                "cinematic_general": "Rhythmic string staccato pattern, steady dynamic percussion layer, warm evolving pads."
            },
            "climax": {
                "sci-fi": "Thunderous cinematic sub-drop, full orchestral brass crescendo, high-energy electro-acoustic sonic boom.",
                "nature": "Sudden dynamic crash, roaring elemental wind, triumphant brass and percussion blast at full volume.",
                "commercial": "Resonant sub-bass swell, crystalline shimmer FX, dramatic musical drop-out with clean impact.",
                "documentary": "Soaring full string section crescendo, poignant solo violin peak, resonant acoustic room acoustic.",
                "thriller": "Piercing high-frequency screech, sudden heavy percussive impact, breathless silence following shock.",
                "fantasy": "Grand orchestral battle theme, roaring timpani rolls, triumphant choir singing at full velocity.",
                "cinematic_general": "Powerful full-orchestra thematic climax, pounding percussion, dramatic brass chords."
            },
            "resolution": {
                "sci-fi": "Gentle sustained ambient synth fade, soothing harmonic resonance, low telemetry signals settling.",
                "nature": "Calm twilight breeze, gentle nocturnal crickets, distant river trickle fading into serene dusk.",
                "commercial": "Pristine acoustic chime resolution, signature melodic audio logo brand sting, confident silence.",
                "documentary": "Warm solo acoustic piano progression resolving softly, subtle wind whisper lingering.",
                "thriller": "Low haunting contrabass note sustaining, solitary echoing footstep, sudden definitive cut to black.",
                "fantasy": "Warm harp arpeggios, soft French horn motif fading into peaceful ambient choir hum.",
                "cinematic_general": "Warm resolved orchestral cadence, gentle piano motif, peaceful lingering silence."
            }
        }
        theme_key = theme if theme in audio_designs["hook"] else "cinematic_general"
        role_key = scene_role if scene_role in audio_designs else "hook"
        return audio_designs[role_key].get(theme_key, audio_designs[role_key]["cinematic_general"])

    def generate_storyboard(self, concept: str, style: str = "Cinematic", target_duration_sec: int = 60) -> Dict[str, Any]:
        """
        Synthesizes an input-specific, varied multi-scene storyboard.
        Enforces duration arithmetic integrity: sum(scene.duration) == target_duration_sec.
        """
        if not concept or not concept.strip():
            raise ValueError("Concept / brief cannot be empty. Please provide a description of your scene or narrative.")

        concept_clean = concept.strip()
        words = concept_clean.split()
        if len(words) < 3 or len(concept_clean) < 12:
            raise ValueError(
                "Concept is too brief or vague. Please provide at least 3 descriptive words "
                "(min 12 characters) detailing the subject, setting, or core narrative."
            )

        # Enforce reasonable duration bounds (15s to 600s)
        duration_clamped = max(15, min(600, int(target_duration_sec)))

        # Determine optimal scene count based on duration
        if duration_clamped <= 30:
            scene_count = 3
        elif duration_clamped <= 60:
            scene_count = 4
        elif duration_clamped <= 120:
            scene_count = 5
        else:
            scene_count = 6

        theme = self._detect_theme(concept_clean, style)

        # Calculate exact duration allocation so sum(durations) == duration_clamped
        base_duration = duration_clamped // scene_count
        remainder = duration_clamped % scene_count
        durations = [base_duration + (1 if i < remainder else 0) for i in range(scene_count)]

        # Scene narrative archetypes based on scene count
        archetypes = [
            ("hook", "Act I: The Inciting Hook", "Establish the environment and introduce the core subject under atmospheric tension."),
            ("exploration", "Act II: The Journey & Progression", "The subject navigates through the core space, engaging dynamic challenges."),
            ("exploration", "Act III: The Rising Complication", "Unforeseen complexities or environmental dynamics escalate the narrative stakes."),
            ("climax", "Act IV: The Pivotal Transformation", "The climactic breakthrough or confrontation reaches peak emotional and visual intensity."),
            ("resolution", "Act V: The Aftermath & Discovery", "The transformative outcome resonates, showcasing the lasting impact of the event."),
            ("resolution", "Act VI: Epilogue & Forward Horizon", "Lingering wide contemplation framing the final takeaway and memorable parting image.")
        ]
        selected_archetypes = archetypes[:scene_count]
        # Ensure the last scene is always marked resolution and second to last has climax
        if scene_count >= 3:
            selected_archetypes[-1] = ("resolution", selected_archetypes[-1][1], selected_archetypes[-1][2])
            selected_archetypes[-2] = ("climax", selected_archetypes[-2][1], selected_archetypes[-2][2])

        # Craft scene-specific bespoke content derived from input concept
        scenes: List[Dict[str, Any]] = []
        for i, (role, act_title, narrative_purpose) in enumerate(selected_archetypes):
            scene_dur = durations[i]
            comp = self._get_cinematic_composition(role, theme, style)
            audio = self._get_audio_design(role, theme)

            if role == "hook":
                visual_action = (
                    f"Camera opens on the world of '{concept_clean[:80]}'. "
                    f"The subject emerges into the focal frame as atmospheric elements establish scale and presence."
                )
                voiceover = (
                    f"\"In the beginning, every boundary is an invitation. We enter the realm of {concept_clean[:50]}—"
                    f"where the first step defines everything to come.\""
                )
            elif role == "exploration" and i == 1:
                visual_action = (
                    f"Tracking movement follows the unfolding progression: '{concept_clean[:100]}'. "
                    f"Subtle micro-actions reveal operational details, environmental textures, and increasing velocity."
                )
                voiceover = (
                    f"\"Moving deeper into the journey, momentum gathers. Every detail of {concept_clean[:45]} "
                    f"tests endurance and sharpens purpose.\""
                )
            elif role == "exploration":
                visual_action = (
                    f"Deeper investigation into {concept_clean[:70]}. "
                    f"Dynamic subject movement interacts with intricate environmental obstacles, shifting narrative direction."
                )
                voiceover = (
                    f"\"Complexity rises where certainty ends. In this crucible, the true nature of our endeavor is revealed.\""
                )
            elif role == "climax":
                visual_action = (
                    f"Peak visual climax of {concept_clean[:90]}. "
                    f"High-energy transformation occurs at center frame with dramatic kinetic motion and intense illumination."
                )
                voiceover = (
                    f"\"This is the turning point: the moment {concept_clean[:40]} transcends anticipation into reality.\""
                )
            else:
                visual_action = (
                    f"Settling wide visual aftermath of {concept_clean[:80]}. "
                    f"Residual kinetic energy dissipates into steady, iconic resolution against the horizon."
                )
                voiceover = (
                    f"\"What began as an idea now stands realized. The impact echoes across the horizon, enduring and complete.\""
                )

            scenes.append({
                "scene_number": i + 1,
                "title": f"Scene {i+1} — {act_title}",
                "narrative_purpose": narrative_purpose,
                "duration_seconds": scene_dur,
                "visual_prompt": f"[{style}] {visual_action} Composition: {comp}",
                "composition": comp,
                "visual_action": visual_action,
                "audio_cue": audio,
                "voiceover_script": voiceover,
                "camera_notes": f"Shot {i+1}: {comp.split(',')[0].strip()} with synchronized audio cue."
            })

        actual_total = sum(s["duration_seconds"] for s in scenes)

        return {
            "title": f"Directorial Storyboard: {concept_clean[:45]}",
            "concept_summary": concept_clean,
            "style": style,
            "detected_theme": theme,
            "target_duration_seconds": duration_clamped,
            "actual_total_duration": actual_total,
            "scene_count": len(scenes),
            "scenes": scenes,
            "model_engine": "MultimediaToolKit Contextual Directorial Engine (Heuristic Directorial Model v2)"
        }


storyboard_adapter = StoryboardAdapter()
