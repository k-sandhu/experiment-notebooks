"""Small file utilities shared by the harness, never by submitted programs."""

import csv
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from bench import config as C


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    write_text(temporary, json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_csv(path):
    if not Path(path).exists():
        return []
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def append_csv(path, row, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow(row)
        stream.flush()


def remove_tree(path, root):
    """Refuse a recursive deletion outside the explicitly named work subtree."""
    path, root = Path(path).resolve(), Path(root).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError(f"Unsafe deletion: {path} (root {root})")
    if path.exists():
        shutil.rmtree(path)


def vendor_config(project):
    # TOML literal strings allow Windows paths without backslash escaping.
    write_text(Path(project) / ".cargo/config.toml", '[source.crates-io]\nreplace-with = "vendored-sources"\n\n'
               f"[source.vendored-sources]\ndirectory = '{C.VENDOR.as_posix()}'\n")


def manifest():
    return read_json(C.DATA / "inputs_manifest.json")["inputs"]


def shim_command(command):
    """Quote .cmd shims without letting Popen backslash-escape cmd.exe's outer quotes."""
    if os.name == "nt" and Path(command[0]).suffix.lower() in (".cmd", ".bat"):
        prefix = subprocess.list2cmdline([os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c"])
        return prefix + ' "' + subprocess.list2cmdline(command) + '"'
    return command
