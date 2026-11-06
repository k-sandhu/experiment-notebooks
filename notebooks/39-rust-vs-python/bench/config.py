"""All experiment sizes, paths, author arguments and measurement settings."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "bench"
DATA = ROOT / "data"
WORK = Path(os.environ.get("NB39_WORK", Path.home() / "nb-work" / "39-rust-vs-python"))
INPUTS = WORK / "inputs"
SESSIONS = WORK / "sessions"
BUILD = WORK / "build"
RUNS = WORK / "runs"
VENDOR = WORK / "vendor"
PROGRAMS = DATA / "programs"
RESULTS = DATA / "results"
PYTHON = Path(r"C:\Python313\python.exe")
TASKS = ("springs", "wordpairs", "ledger", "logscan", "routes", "align", "heat", "walkers")
LANG_VARIANTS = ("cpp", "java", "csharp", "go", "js")
VARIANTS = ("rust", "plain", "fast") + LANG_VARIANTS
TOOLCHAINS = {name: Path(os.environ.get("NB39_" + name, default)) for name, default in {
    "VCVARS": r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat",
    "JAVA": r"C:\Program Files\Java\jdk-23\bin\java.exe", "JAVAC": r"C:\Program Files\Java\jdk-23\bin\javac.exe",
    "DOTNET": r"D:\projects\toolchains\dotnet8\dotnet.exe", "GO": r"D:\projects\toolchains\go1.27.3\go\bin\go.exe",
    "NODE": r"C:\Program Files\nodejs\node.exe",
}.items()}
VENDOR_LANGS = WORK.resolve() / "vendor-langs"
VENDOR_LANGS_MANIFEST = BENCH / "template/vendor_langs.json"
SESSION_KINDS = {
    "main": dict(prompt=BENCH / "AUTHOR_PROMPT.md", sessions=SESSIONS, suffix="", meta="meta.json", timeout=75 * 60),
    "langs": dict(prompt=BENCH / "AUTHOR_PROMPT_LANGS.md", sessions=WORK.resolve() / "sessions-langs", suffix=".langs", meta="meta_langs.json", timeout=100 * 60),
}
SWEEP_TASKS = ("wordpairs", "routes", "heat")
GENERATOR_VERSION = "39.2"
HARNESS_VERSION = "39.3"
SMALL_ALIGN_LENGTHS = dict(min_length=8, max_length=40)

# Editing these parameters changes future inputs; existing files are never silently replaced.
FULL = {
    "springs": dict(N=4000, S=15000, dt=0.0005),
    "wordpairs": dict(words=10_000_000, vocabulary=40_000),
    "ledger": dict(transactions=1_000_000, accounts=10_000, currencies=8, channels=8),
    "logscan": dict(lines=2_000_000, templates=220),
    "routes": dict(N=300_000, M=900_000, Q=6),
    "align": dict(P=300, min_length=100, max_length=1000, alphabet=10),
    "heat": dict(H=400, W=400, S=250),
    "walkers": dict(J=64, L=500_000, B=300),
}
SETS = {"s2": (0.001, 102), "s3": (0.05, 103), "t1": (0.002, 201), "full": (1.0, 301)}
SWEEPS = {f"sweep_{letter}": (scale, 401 + i) for i, (letter, scale) in
          enumerate(zip("abcd", (1/256, 1/64, 1/16, 1/4)))}
TINY_SCALE = 0.00001
TINY = {
    "springs": {"s1a": dict(N=1, S=3, rest_length=0.0), "s1b": dict(N=2, S=4, rest_length=0.0), "s1c": dict(N=5, S=6, rest_length=0.0)},
    "wordpairs": {"s1": dict(words=160, vocabulary=40)},
    "ledger": {"s1": dict(transactions=48, accounts=12, channels=6)},
    "logscan": {"s1": dict(lines=100, templates=15)},
    "routes": {"s1": dict(N=12, M=36)},
    "align": {"s1": dict(P=6, min_length=1, max_length=12)},
    "heat": {"s1": dict(H=7, W=9, S=4)},
    "walkers": {"s1a": dict(J=4, L=12, B=1), "s1b": dict(J=4, L=15, B=2)},
}

def claude_flags(model):
    return ["-p", "--safe-mode", "--model", model, "--effort", "high",
            "--permission-mode", "bypassPermissions", "--tools", "Bash,Read,Write,Edit,Glob,Grep",
            "--output-format", "stream-json", "--verbose"]


def claude_author(model, **route):
    return dict(cli="claude", model=model, effort="high", flags=claude_flags(model), **route)


def openrouter_author(model, provider, permaslug):
    return claude_author(model, route="openrouter", provider=provider, permaslug=permaslug, reasoning_effort="high")


def muse_author(model):
    # --yolo turns off approvals and the sandbox (like bypassPermissions); web tools are off because no other author has them.
    return dict(cli="muse", model=model, effort="high", flags=[
        "exec", "--model", model, "--reasoning-effort", "high", "--workspace", "{session}", "--yolo",
        "--disable-web-tools", "--no-foreign-personal-context", "--json", "--prompt-file", "{prompt}"])


AUTHORS = {
    "sonnet": claude_author("claude-sonnet-5-5"),
    "terra": dict(cli="codex", model="gpt-6.1-terra", effort="high", flags=[
        "exec", "-m", "gpt-6.1-terra", "-c", 'model_reasoning_effort="high"',
        # --ignore-user-config drops the user's approval policy and Windows sandbox, which commands need.
        "-c", 'approval_policy="never"', "-c", 'windows.sandbox="elevated"',
        "--ignore-user-config", "--ephemeral", "--sandbox", "workspace-write",
        "--skip-git-repo-check", "-C", "{session}", "--json", "-o", "{last}", "-"]),
    "opus55": claude_author("claude-opus-5-5"),
    "haiku": claude_author("claude-haiku-5-5"),
    "deepseek": openrouter_author("deepseek/deepseek-v4.1-flash-1017", "DeepSeek", "deepseek/deepseek-v4.1-flash-20261017"),
    "glm": openrouter_author("z-ai/glm-5.3-flash", "Z.AI", "z-ai/glm-5.3-flash-20260826"),
    "nemotron": openrouter_author("nvidia/nemotron-3.5-super-vl:free", "Nvidia", "nvidia/nemotron-3.5-super-vl-20261015"),
    "wonder": muse_author("muse-wonder-1.0"),
    "wonder-full": muse_author("muse-wonder-full-1.0"),
}
# Models Claude Code may call through the local proxy (bench/openrouter_proxy.py); anything else is rejected there.
OPENROUTER_ROUTES = {a["model"]: dict(author=name, provider=a["provider"], permaslug=a["permaslug"], reasoning_effort=a["reasoning_effort"])
                     for name, a in AUTHORS.items() if a.get("route") == "openrouter"}
OPENROUTER_PROXY_PORT = 8739
# Heat-only pilot sessions by Claude Opus 5.5 and GPT-6.1 Sol, kept under data/programs/{opus,sol}/heat.
PILOT_AUTHORS = ("opus", "sol")
SOL_PRIVATE_CARGO_HOME = False  # Sandbox feasibility requires a model call; deliberately untested.
SESSION_TIMEOUT = 75 * 60
MUSE_EXPORT_TIMEOUT = 120
SESSION_JOBS_PER_AUTHOR = 3
SESSION_JOBS = {"nemotron": 2, "wonder": 2, "wonder-full": 2}
SESSION_JOBS_TOTAL = 10  # 22 logical processors and 31 GB; sessions build and benchmark
CORRECT_TIMEOUT = 900
BUILD_TIMEOUT = 900
MEASURE_TIMEOUT = 900
OUTPUT_LIMIT_BYTES = 16 * 1024 * 1024
VERSION_TIMEOUT = 30
JOB_CLEANUP_TIMEOUT = 5
JOB_POLL_SECONDS = 0.005
LOG_MIN_MALFORMED = 39
REFERENCE_TIMEOUT = 600
CHECK_TIMEOUT = 240
BASELINE_REPEATS = 20
BUILD_REPEATS = 3
BENCH_REPEATS = 5
SLOW_REPEATS = 3
SLOW_SECONDS = 60
OTHER_REPEATS = 3
SELFTEST_REPEATS = 2
WORKER_COUNTS = (1, 2, 4, 8, 16)
CORRECT_WORKERS = 4
CORRECT_EXTRA_WORKERS = (1, 16)
ORDER_SEED = 390301
ALLOWED_CRATES = {"serde", "serde_json", "regex", "rayon"}
THREAD_ENV = {"NO_COLOR": "1", "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


def input_sets(task):
    return {**{name: (TINY_SCALE, 101) for name in TINY[task]}, **SETS,
            **(SWEEPS if task in SWEEP_TASKS else {})}


def parameters(task, scale, name=None):
    p = FULL[task].copy()
    keys = {"springs": ("N", "S"), "wordpairs": ("words",), "ledger": ("transactions",),
            "logscan": ("lines",), "routes": ("N", "M"), "align": ("P",),
            "heat": ("H", "W"), "walkers": ("L",)}[task]
    factor = scale ** 0.5 if task in ("springs", "heat") else scale
    for key in keys:
        p[key] = max(1, round(p[key] * factor))
    if scale == TINY_SCALE and name in TINY[task]:
        p.update(TINY[task][name])
    elif task == "align" and scale < .01:
        p.update(SMALL_ALIGN_LENGTHS)
    if task == "align" and name not in TINY[task]:
        p["P"] = max(6, p["P"])
    return p


def input_path(task, name):
    return (DATA / "samples" if name.startswith("s") and not name.startswith("sweep") else INPUTS) / task / f"{name}.in"


# A short, fixed PATH for author sessions and measurements. Visual Studio's vcvars64.bat fails with "The input line is
# too long" when the inherited PATH nears cmd's 8,191-character limit, which happened after a desktop-app restart on
# 2026-11-05 (the inherited PATH grew to 7,921 characters). Language sessions and builds add their toolchains in front.
BASE_PATH = os.pathsep.join([
    r"C:\Windows\system32", r"C:\Windows", r"C:\Windows\System32\Wbem", r"C:\Windows\System32\WindowsPowerShell\v1.0",
    r"C:\Windows\System32\OpenSSH", str(PYTHON.parent), str(PYTHON.parent / "Scripts"), str(Path.home() / ".cargo" / "bin"),
    r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\usr\bin", r"C:\Program Files\nodejs", r"C:\Program Files\Java\jdk-23\bin",
    r"C:\Program Files (x86)\Microsoft Visual Studio\Installer",
    str(Path.home() / ".local" / "bin"), str(Path.home() / "AppData" / "Local" / "Programs" / "muse"),
])


def environment():
    env = os.environ.copy()
    env.pop("FORCE_COLOR", None)
    env.update(THREAD_ENV, PATH=BASE_PATH)
    return env


def session_environment():
    """Environment for model sessions: none of the launching agent's Claude Code or API settings."""
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith(("CLAUDE", "ANTHROPIC_", "OPENAI_", "OPENROUTER_", "CODEX_")) and k.upper() != "FORCE_COLOR"}
    env["NO_COLOR"] = "1"
    env["PATH"] = BASE_PATH
    return env
