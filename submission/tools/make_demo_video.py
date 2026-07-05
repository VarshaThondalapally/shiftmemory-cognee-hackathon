from __future__ import annotations

import os
import textwrap
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "submission" / "video"
FRAMES = OUT / "frames"
SCREENSHOTS = ROOT / "submission" / "screenshots"
WIDTH = 1280
HEIGHT = 720

BG = "#f4f7f4"
PANEL = "#ffffff"
INK = "#14201c"
MUTED = "#65716e"
GREEN = "#006b58"
GREEN_DARK = "#004d40"
BLUE = "#245c7a"
AMBER = "#b17919"
RED = "#b2483d"
LINE = "#d7dfdc"
SOFT_GREEN = "#e3f2ed"
SOFT_BLUE = "#e3eef4"
SOFT_AMBER = "#fff4d6"
SOFT_RED = "#f8e4e1"


NARRATION = """This is Caregiver Handoff Memory, built for home-care and assisted-living teams.
The problem is simple: the most important shift details are often small. A resident woke after 3 AM, a family member needs an update, or an old preference should stop appearing.
The product is not one shared notes screen. Each person gets their own workspace. The supervisor assigns shifts, the night caregiver records what changed, the morning lead receives the handoff, and proof mode shows what the memory layer did.
First, the supervisor assigns Nia to Avery's night shift and Omar to the morning shift. Those assignments decide which care recipients each person can access after login.
During the night, Nia saves one note: Avery woke twice after 3 AM, asked for water, and settled when the room stayed quiet. The backend sends this as durable memory to Cognee.
In the morning, Omar does not paste that note. He clicks generate handoff. The backend asks Cognee for relevant case memory, Gemini turns the recalled sources into a structured handoff, and the app cites where each item came from.
Omar can also ask what changed after 3 AM. The answer is built from saved memory, not from a fresh explanation typed into the prompt.
The supervisor can mark a note important so future handoffs prioritize it, or remove stale memory so it stops appearing. That is the full lifecycle: remember, recall, improve, and forget.
For judges, proof mode shows Cognee Cloud active, Gemini active, redacted backend-to-memory communication, source IDs, and trace events.
OpenAI Codex was used during development as an AI pair engineer. Gemini is the runtime reasoning layer. Cognee is the runtime memory layer.
This is a hackathon MVP using synthetic data, not production healthcare software. The claim is focused: a note saved by one worker can be remembered, recalled with source, improved, and forgotten without the next worker pasting context again."""


def font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        f"C:/Windows/Fonts/{name}.ttf",
        f"C:/Windows/Fonts/{name}.otf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


FONT = {
    "eyebrow": font("seguisb", 20),
    "h1": font("seguisb", 58),
    "h2": font("seguisb", 38),
    "h3": font("seguisb", 27),
    "body": font("segoeui", 25),
    "small": font("segoeui", 18),
    "bold": font("seguisb", 24),
    "mono": font("consola", 18),
}


def rounded(draw: ImageDraw.ImageDraw, box, fill, outline=None, width=1, radius=18):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap(draw: ImageDraw.ImageDraw, text: str, font_obj, max_width: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        words = para.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if draw.textbbox((0, 0), test, font=font_obj)[2] <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def text(draw, xy, content, font_obj, fill=INK, max_width=None, line_gap=8):
    x, y = xy
    if max_width:
        for line in wrap(draw, content, font_obj, max_width):
            draw.text((x, y), line, font=font_obj, fill=fill)
            y += draw.textbbox((0, 0), line, font=font_obj)[3] + line_gap
        return y
    draw.text((x, y), content, font=font_obj, fill=fill)
    return y + draw.textbbox((0, 0), content, font=font_obj)[3]


def card(draw, x, y, w, h, title, body, accent=GREEN, fill=PANEL):
    rounded(draw, (x, y, x + w, y + h), fill, LINE, radius=18)
    draw.rectangle((x, y, x + 8, y + h), fill=accent)
    text(draw, (x + 28, y + 24), title, FONT["bold"], accent)
    body_font = FONT["small"] if h <= 160 or w <= 380 else FONT["body"]
    text(draw, (x + 28, y + 66), body, body_font, INK, max_width=w - 58, line_gap=7)


def base(title: str, eyebrow: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    text(draw, (58, 48), eyebrow.upper(), FONT["eyebrow"], GREEN)
    text(draw, (58, 86), title, FONT["h1"], INK, max_width=760, line_gap=10)
    if subtitle:
        text(draw, (60, 224), subtitle, FONT["body"], MUTED, max_width=720, line_gap=9)
    return img, draw


def paste_screenshot(img: Image.Image, path: Path, box: tuple[int, int, int, int]):
    if not path.exists():
        return
    shot = Image.open(path).convert("RGB")
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    shot.thumbnail((bw, bh))
    canvas = Image.new("RGB", (bw, bh), "#edf3f1")
    ox = (bw - shot.width) // 2
    oy = (bh - shot.height) // 2
    canvas.paste(shot, (ox, oy))
    img.paste(canvas, (x1, y1))
    draw = ImageDraw.Draw(img)
    rounded(draw, box, None, LINE, width=2, radius=22)


def frame_01():
    img, draw = base(
        "Caregiver Handoff Memory",
        "Cognee hackathon submission",
        "A role-based handoff app where overnight notes survive refreshes, worker changes, supervisor feedback, and stale-memory cleanup.",
    )
    rounded(draw, (830, 68, 1195, 622), PANEL, LINE, radius=26)
    paste_screenshot(img, SCREENSHOTS / "01_landing_page.png", (850, 92, 1175, 392))
    card(draw, 850, 420, 325, 150, "Core claim", "Remember, recall, improve, and forget care context with Cognee behind the workflow.", GREEN, SOFT_GREEN)
    text(draw, (60, 590), "React + FastAPI + JWT/RBAC + Cognee Cloud + Gemini", FONT["bold"], BLUE)
    return img


def frame_02():
    img, draw = base(
        "The product has real actors",
        "Role-separated workflow",
        "The first design mistake would be one screen for everyone. The final MVP gives each role only the actions they should own.",
    )
    roles = [
        ("Supervisor", "Assigns shifts, reviews memory, removes stale context.", GREEN),
        ("Night caregiver", "Saves what changed once, in normal shift language.", BLUE),
        ("Morning lead", "Generates the brief and asks follow-up questions.", AMBER),
        ("Judge mode", "Shows redacted Cognee/Gemini proof traces.", RED),
    ]
    for idx, (title, body, accent) in enumerate(roles):
        x = 60 + (idx % 2) * 590
        y = 330 + (idx // 2) * 150
        card(draw, x, y, 540, 118, title, body, accent)
    return img


def frame_03():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    text(draw, (58, 48), "JWT AND ROLE-BASED ACCESS", FONT["eyebrow"], GREEN)
    text(draw, (58, 86), "Login by role", FONT["h1"], INK, max_width=520)
    text(
        draw,
        (60, 224),
        "Demo sign-in issues a token. The backend filters patients and actions by role.",
        FONT["body"],
        MUTED,
        max_width=520,
        line_gap=9,
    )
    paste_screenshot(img, SCREENSHOTS / "02_login_roles.png", (640, 82, 1210, 570))
    card(
        draw,
        60,
        455,
        520,
        135,
        "Security boundary",
        "The browser talks to FastAPI. Cognee and Gemini keys stay server-side.",
        GREEN,
        SOFT_GREEN,
    )
    return img


def frame_04():
    img, draw = base("Supervisor assigns shifts", "Step 1", "Rosa assigns Nia to the night shift and Omar to the morning shift for Avery.")
    rounded(draw, (90, 330, 1190, 590), PANEL, LINE, radius=20)
    text(draw, (130, 365), "Avery Johnson", FONT["h2"], INK)
    text(draw, (130, 420), "Tonight 7 PM - tomorrow 7 AM", FONT["body"], MUTED)
    card(draw, 650, 355, 230, 115, "Night caregiver", "Nia Brooks", BLUE, SOFT_BLUE)
    card(draw, 910, 355, 230, 115, "Morning lead", "Omar Chen", AMBER, SOFT_AMBER)
    text(draw, (130, 520), "Assignments decide which patients appear after login.", FONT["bold"], GREEN)
    return img


def frame_05():
    img, draw = base("Night caregiver remembers", "Step 2", "Nia saves one note in plain language. This is the remember operation.")
    rounded(draw, (90, 310, 690, 605), PANEL, LINE, radius=22)
    text(draw, (128, 345), "Save the thing the morning team must not miss", FONT["h3"], INK, max_width=500)
    rounded(draw, (128, 430, 650, 535), "#f9fbfa", LINE, radius=14)
    text(draw, (150, 452), "At 3:18 AM Avery woke twice, asked for water, and settled when the room stayed quiet.", FONT["body"], INK, max_width=460)
    rounded(draw, (128, 552, 390, 590), GREEN, None, radius=18)
    text(draw, (152, 560), "Remember for morning", FONT["bold"], "#ffffff")
    card(draw, 750, 360, 390, 150, "Backend to Cognee", "The note is stored as durable case memory with a source ID.", GREEN, SOFT_GREEN)
    return img


def frame_06():
    img, draw = base("Morning lead recalls", "Step 3", "Omar generates the handoff without asking Nia to paste the night shift again.")
    headers = [("Before 9 AM", GREEN), ("Watch Today", BLUE), ("Preference", AMBER), ("Later Today", "#6d5c8f")]
    for idx, (header, accent) in enumerate(headers):
        x = 70 + idx * 300
        rounded(draw, (x, 330, x + 270, 575), PANEL, LINE, radius=18)
        text(draw, (x + 22, 355), header, FONT["bold"], accent)
        body = [
            "Call Mira before breakfast.",
            "Watch tiredness after 3 AM wakeups.",
            "Oatmeal today. Avoid orange juice.",
            "Send blue laundry bag after lunch.",
        ][idx]
        text(draw, (x + 22, 410), body, FONT["body"], INK, max_width=220)
        text(draw, (x + 22, 520), "Source: remembered note", FONT["small"], MUTED)
    text(draw, (72, 610), "Cognee recalls relevant memory. Gemini writes the structured handoff from verified sources.", FONT["bold"], GREEN)
    return img


def frame_07():
    img, draw = base("Follow-up answers use memory", "Step 4", "The morning lead asks what changed after 3 AM. The answer cites saved notes instead of relying on fresh pasted context.")
    rounded(draw, (90, 320, 550, 585), SOFT_BLUE, LINE, radius=22)
    text(draw, (125, 355), "Question", FONT["eyebrow"], BLUE)
    text(draw, (125, 395), "What changed after 3 AM?", FONT["h3"], INK, max_width=360)
    rounded(draw, (630, 320, 1160, 585), PANEL, LINE, radius=22)
    text(draw, (665, 355), "Answer from saved notes", FONT["eyebrow"], GREEN)
    text(draw, (665, 395), "Avery woke twice after 3 AM, asked for water, and settled when the room stayed quiet. Watch for tiredness before breakfast.", FONT["body"], INK, max_width=430)
    text(draw, (665, 520), "Source: night worker note", FONT["bold"], GREEN)
    return img


def frame_08():
    img, draw = base("Supervisor improves or forgets", "Step 5", "Rosa can prioritize memory that should keep shaping future handoffs, or remove stale notes.")
    card(draw, 90, 330, 500, 145, "Keep important", "Supervisor feedback tells memory this note should surface again.", GREEN, SOFT_GREEN)
    card(draw, 690, 330, 500, 145, "Remove stale", "Wrong or outdated memory is deleted so it stops appearing.", RED, SOFT_RED)
    text(draw, (90, 535), "This completes the lifecycle: remember -> recall -> improve -> forget.", FONT["h2"], INK)
    return img


def frame_09():
    img, draw = base("Proof mode is for judges", "Backend-to-memory evidence", "Normal users never need this screen. Judges can inspect redacted traces and verify that Cognee and Gemini are active.")
    card(draw, 80, 320, 330, 110, "Memory backend", "Cognee Cloud", GREEN, SOFT_GREEN)
    card(draw, 475, 320, 330, 110, "Reasoning layer", "Gemini", BLUE, SOFT_BLUE)
    card(draw, 870, 320, 330, 110, "Source policy", "Cited notes only", AMBER, SOFT_AMBER)
    rounded(draw, (80, 470, 1200, 610), "#101916", None, radius=18)
    trace = "POST /datasets/{case}/data -> 200\\nPOST /search -> recalled source mem-3am-note\\nPOST /cognify -> supervisor feedback accepted\\nDELETE /datasets/{note} -> stale memory removed"
    text(draw, (112, 498), trace, FONT["mono"], "#dceee8", max_width=1030, line_gap=6)
    return img


def frame_10():
    img, draw = base("AI usage is declared", "Submission transparency", "The submission includes a direct disclosure of which AI systems were used and what they did.")
    card(draw, 80, 325, 350, 150, "OpenAI Codex", "Development pair engineer: architecture, code, docs, testing, submission packet.", GREEN, SOFT_GREEN)
    card(draw, 465, 325, 350, 150, "Gemini", "Runtime reasoning layer: understands notes and writes handoffs from sources.", BLUE, SOFT_BLUE)
    card(draw, 850, 325, 350, 150, "Cognee", "Runtime memory layer: remember, recall, improve, forget.", AMBER, SOFT_AMBER)
    text(draw, (82, 550), "Synthetic data only. Not production healthcare software. Not medical advice.", FONT["bold"], RED)
    return img


def frame_11():
    img, draw = base("Submission package", "Final links", "The strongest submission is repo plus landing page plus a short demo video. The full backend app runs locally unless deployed separately.")
    rounded(draw, (90, 320, 1190, 590), PANEL, LINE, radius=22)
    lines = [
        "GitHub: github.com/VarshaThondalapally/shiftmemory-cognee-hackathon",
        "Landing: varshathondalapally.github.io/shiftmemory-cognee-hackathon/",
        "Docs: handover/ and submission/",
        "Video: submission/video/caregiver-handoff-memory-demo.mp4",
    ]
    y = 355
    for line in lines:
        text(draw, (130, y), line, FONT["bold"], INK, max_width=980)
        y += 52
    text(draw, (130, 545), "Claim: memory survives across shift handoff, recall, feedback, and deletion.", FONT["h3"], GREEN)
    return img


FRAME_BUILDERS = [
    frame_01,
    frame_02,
    frame_03,
    frame_04,
    frame_05,
    frame_06,
    frame_07,
    frame_08,
    frame_09,
    frame_10,
    frame_11,
]


def wav_duration(path: Path) -> float:
    if not path.exists():
        return 165.0
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / float(wav.getframerate())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    (OUT / "narration.txt").write_text(NARRATION, encoding="utf-8")

    frame_paths = []
    for idx, builder in enumerate(FRAME_BUILDERS, start=1):
        img = builder()
        path = FRAMES / f"frame_{idx:02d}.png"
        img.save(path)
        frame_paths.append(path)

    audio_seconds = wav_duration(OUT / "voiceover.wav")
    per_frame = max(8.0, min(18.0, audio_seconds / len(frame_paths)))
    concat_lines = []
    for frame in frame_paths:
        concat_lines.append(f"file '{frame.as_posix()}'")
        concat_lines.append(f"duration {per_frame:.3f}")
    concat_lines.append(f"file '{frame_paths[-1].as_posix()}'")
    (OUT / "slides.ffconcat").write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

    print(f"frames={len(frame_paths)}")
    print(f"audio_seconds={audio_seconds:.2f}")
    print(f"slide_seconds={per_frame:.2f}")
    print(f"concat={OUT / 'slides.ffconcat'}")


if __name__ == "__main__":
    main()
