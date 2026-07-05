from __future__ import annotations

import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "submission" / "real-flow-screenshots"
OUT = ROOT / "submission" / "video"
FRAMES = OUT / "frames"
WIDTH = 1280
HEIGHT = 720


NARRATION = """This is a real walkthrough of Caregiver Handoff Memory running locally with the FastAPI backend connected to Cognee Cloud and Gemini.
The public page introduces the product: every shift should start with the right context, not a lost chat thread.
The app starts with role-based sign in. Demo sign-in issues a JWT, and the backend decides which patients and actions each user can access.
Rosa signs in as the supervisor. She sees the assignment dashboard, where Nia is assigned to the night shift and Omar is assigned to the morning shift for Avery.
Nia signs in as the night caregiver. She only sees her night-shift workspace, so she saves the important overnight note: Avery woke twice after 3 AM, asked for water, and settled when the room stayed quiet.
That note is remembered through the backend memory layer. The worker does not need to know Cognee exists. She just saves the thing the next shift must not miss.
Omar signs in as the morning lead. Before generating the handoff, the screen has no pasted context from Nia.
When Omar clicks generate handoff, the backend recalls Avery's case memory from Cognee, Gemini writes a structured handoff from the recalled sources, and the UI shows the source-backed brief.
Omar then asks a follow-up: what changed after 3 AM? The app answers from saved memory and cites the remembered note.
Rosa returns as supervisor. She can review the memory that will keep shaping future handoffs.
When she marks a note important, that feedback is sent as an improve signal so future handoffs prioritize it.
Finally, proof mode shows the technical evidence: Cognee Cloud is active, Gemini is active, and the memory lifecycle includes remember, recall, improve, and forget traces with API keys redacted.
The submission also declares AI usage: Codex helped build the product, Gemini is the runtime reasoning layer, and Cognee is the runtime memory layer."""


CAPTIONS = [
    ("01_public_landing.png", "Public landing page", "The product story before entering the app."),
    ("02_login_roles.png", "Role-based sign in", "Each demo user receives a JWT-backed workspace."),
    ("03_supervisor_assignments.png", "Supervisor assigns shifts", "Assignments decide which patients each worker can access."),
    ("04_night_note_empty.png", "Night caregiver workspace", "Nia sees note capture, not supervisor controls."),
    ("05_night_note_remembered.png", "Remember", "A 3 AM note is saved for the next shift."),
    ("06_morning_before_handoff.png", "Morning lead workspace", "Omar starts without pasted context from Nia."),
    ("07_morning_handoff_with_sources.png", "Recall", "Cognee-backed memory becomes a source-backed handoff."),
    ("08_morning_followup_answer.png", "Ask from memory", "A follow-up answer cites the remembered note."),
    ("09_supervisor_review_memory.png", "Supervisor review", "Rosa decides what should keep shaping handoffs."),
    ("10_supervisor_improve_memory.png", "Improve", "Important memory is promoted for future handoffs."),
    ("11_judge_proof_top.png", "Proof mode", "Reviewers can see Cognee Cloud and Gemini are active."),
    ("12_judge_proof_trace.png", "Backend-to-memory trace", "Memory calls are visible with secrets redacted."),
]


def font(name: str, size: int):
    for candidate in (f"C:/Windows/Fonts/{name}.ttf", "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


TITLE = font("seguisb", 25)
BODY = font("segoeui", 18)


def wav_duration(path: Path) -> float:
    if not path.exists():
        return 130.0
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / float(wav.getframerate())


def overlay_caption(image: Image.Image, title: str, body: str) -> Image.Image:
    image = image.convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((32, 595, 780, 688), radius=18, fill=(14, 28, 24, 222))
    draw.text((58, 614), title, font=TITLE, fill=(255, 255, 255, 255))
    draw.text((58, 650), body, font=BODY, fill=(221, 238, 232, 255))
    return Image.alpha_composite(image, overlay).convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    (OUT / "narration.txt").write_text(NARRATION, encoding="utf-8")

    frame_paths: list[Path] = []
    for index, (filename, title, body) in enumerate(CAPTIONS, start=1):
        source = SHOTS / filename
        if not source.exists():
            raise FileNotFoundError(source)
        img = Image.open(source).convert("RGB").resize((WIDTH, HEIGHT))
        frame = overlay_caption(img, title, body)
        frame_path = FRAMES / f"real_flow_{index:02d}.png"
        frame.save(frame_path)
        frame_paths.append(frame_path)

    audio_seconds = wav_duration(OUT / "voiceover.wav")
    per_frame = max(6.0, min(12.0, audio_seconds / len(frame_paths)))
    lines = []
    for frame in frame_paths:
        lines.append(f"file '{frame.as_posix()}'")
        lines.append(f"duration {per_frame:.3f}")
    lines.append(f"file '{frame_paths[-1].as_posix()}'")
    (OUT / "slides.ffconcat").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"real_flow_frames={len(frame_paths)}")
    print(f"audio_seconds={audio_seconds:.2f}")
    print(f"slide_seconds={per_frame:.2f}")


if __name__ == "__main__":
    main()
