import settings_manager as sset

APP_NAME = sset.get("institution_name", "EduSuite")
APP_VERSION = "1.0.0"

MIN_SCORE = 0.0
MAX_SCORE = 10.0
PERIODS = ("T1", "T2", "T3")
PERIOD_LABELS = {"T1": "Primer Trimestre", "T2": "Segundo Trimestre", "T3": "Tercer Trimestre"}

COLOR_BG = sset.get("main_bg")
COLOR_SURFACE = sset.get("surface_color")
COLOR_PANEL = sset.get("panel_color")
COLOR_INPUT = sset.get("input_color")
COLOR_BORDER = sset.get("border_color")
COLOR_HOVER = sset.get("hover_color")

COLOR_ACCENT = sset.get("accent_color")
COLOR_ACCENT_HOVER = sset.get("accent_hover_color")

COLOR_TEXT = sset.get("text_color")
COLOR_TEXT_MUTED = sset.get("text_muted")
COLOR_TEXT_DIM = sset.get("text_dim")

COLOR_SUCCESS = sset.get("success_color")
COLOR_WARNING = sset.get("warning_color")
COLOR_DANGER = sset.get("danger_color")

COLOR_SIDEBAR = sset.get("sidebar_bg")
COLOR_SIDEBAR_HOVER = sset.get("sidebar_hover")
COLOR_SIDEBAR_ACTIVE = sset.get("sidebar_active")

HEADER_FONT = '"JetBrains Mono", "Fira Code", "SF Mono", "Cascadia Code", "Consolas", monospace'
BODY_FONT = '"Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif'


def score_color(score):
    if score is None:
        return COLOR_TEXT_MUTED
    if score < 5.0:
        return COLOR_DANGER
    elif score < 7.0:
        return COLOR_WARNING
    return COLOR_SUCCESS


def score_bg(score):
    if score is None:
        return "transparent"
    if score < 5.0:
        return "#1a0e0e"
    elif score < 7.0:
        return "#1a170a"
    return "#0e170e"


def lerp_color(c1, c2, t):
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


HEATMAP_COLORS = [
    ("#D32F2F", 0.0),
    ("#D32F2F", 0.49),
    ("#F9A825", 0.5),
    ("#F9A825", 0.69),
    ("#4CAF50", 0.7),
    ("#4CAF50", 1.0),
]


def heatmap_color(score):
    if score is None:
        return "transparent"
    t = max(0.0, min(1.0, score / MAX_SCORE))
    for i in range(len(HEATMAP_COLORS) - 1):
        c1, t1 = HEATMAP_COLORS[i]
        c2, t2 = HEATMAP_COLORS[i + 1]
        if t1 <= t <= t2:
            local_t = (t - t1) / (t2 - t1) if t2 != t1 else 0
            return lerp_color(c1, c2, local_t)
    return HEATMAP_COLORS[-1][0]


def heatmap_text_color(score):
    if score is None:
        return COLOR_TEXT_MUTED
    if score < 5.0:
        return "#ffffff"
    if score < 7.0:
        return "#000000"
    return "#ffffff"


SUPABASE_URL = ""
SUPABASE_KEY = ""

# ── Asignaturas por nivel (estructura ACTA DE NOTAS) ────────────────────

SUBJECTS_BY_LEVEL = {
    "ESBA_1": [
        "Lengua", "Geografía", "Matemáticas", "Ciencias Naturales",
        "Francés", "Inglés", "Religión", "Plástica", "Educación Física",
    ],
    "ESBA_2": [
        "Lengua", "Geografía", "Matemáticas", "Ciencias Naturales",
        "Francés", "Inglés", "Religión", "Plástica", "Educación Física",
    ],
    "ESBA_3": [
        "Lengua", "Historia", "Matemáticas", "Biología",
        "Física", "Química", "Tecnología", "Francés",
        "Inglés", "Religión", "Educación Plástica", "Educación Física",
    ],
    "ESBA_4": [
        "Lengua", "Hª Universal", "Matemáticas", "B/Geología",
        "Física", "Química", "Tecnología", "Francés",
        "Inglés", "Religión", "Plástica", "Educación Física",
    ],
    "BACH_1_CIENCIAS": [
        "Lengua", "Hª África", "CTM", "B/G",
        "Matemáticas", "Física", "Química", "Economía",
        "Filosofía", "Dibujo", "Francés", "Inglés",
        "Religión", "Educación Física",
    ],
    "BACH_1_LETRAS": [
        "Lengua", "Hª África", "GGE", "CTM",
        "Matemáticas", "Economía", "Filosofía", "Francés",
        "Inglés", "Religión", "Educación Física", "Latín", "Griego",
    ],
    "BACH_2_CIENCIAS": [
        "Lengua", "HMA", "CNS", "Matemáticas",
        "Electrotecnia", "Economía", "Hª Filosofía", "Francés",
        "Inglés", "Geología", "Química",
    ],
    "BACH_2_LETRAS": [
        "Lengua", "HMA", "CNS", "Matemáticas",
        "Hª Arte", "Economía", "Hª Filosofía", "Francés",
        "Inglés", "Latín", "Griego",
    ],
}

COURSE_TO_LEVEL = {
    "1º ESBA A": "ESBA_1",
    "1º ESBA B": "ESBA_1",
    "1º ESBA C": "ESBA_1",
    "2º ESBA A": "ESBA_2",
    "2º ESBA B": "ESBA_2",
    "2º ESBA C": "ESBA_2",
    "3º ESBA A": "ESBA_3",
    "3º ESBA B": "ESBA_3",
    "4º ESBA":    "ESBA_4",
    "1º BACH A":  "BACH_1_CIENCIAS",
    "1º BACH B":  "BACH_1_LETRAS",
    "2º BACH A":  "BACH_2_CIENCIAS",
    "2º BACH B":  "BACH_2_LETRAS",
}

LEVEL_LABELS = {
    "ESBA_1": "1º-2º ESBA",
    "ESBA_2": "1º-2º ESBA",
    "ESBA_3": "3º ESBA",
    "ESBA_4": "4º ESBA",
    "BACH_1_CIENCIAS": "1º BACH Ciencias",
    "BACH_1_LETRAS": "1º BACH Letras",
    "BACH_2_CIENCIAS": "2º BACH Ciencias",
    "BACH_2_LETRAS": "2º BACH Letras",
}
