#!/usr/bin/env python
"""Build a wheel for pyblish-qml.

Usage:
    python scripts/build_wheel.py
    python scripts/build_wheel.py --outdir dist
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> None:
    print("[build-wheel]", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True)


def find_uv() -> str | None:
    # Prefer uv next to the current interpreter for studio portability.
    exe_dir = Path(sys.executable).resolve().parent
    candidates = [exe_dir / "uv.exe", exe_dir / "uv"]

    which_uv = shutil.which("uv")
    if which_uv:
        candidates.append(Path(which_uv))

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def build_with_uv(uv_exe: str, repo_root: Path, outdir: Path) -> None:
    cmd = [uv_exe, "build", str(repo_root), "--wheel", "--out-dir", str(outdir)]
    cache = os.environ.get("UV_CACHE_DIR")
    if cache:
        cmd.extend(["--cache-dir", cache])
    run(cmd, repo_root)


def build_with_python_build(repo_root: Path, outdir: Path) -> None:
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "build", "setuptools", "wheel"], repo_root)
    run([sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir)], repo_root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build pyblish-qml wheel")
    parser.add_argument("--outdir", default="dist", help="Output directory for wheels")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    outdir = Path(args.outdir)
    abs_outdir = repo_root / outdir
    abs_outdir.mkdir(parents=True, exist_ok=True)

    # Avoid stale wheels in CI artifacts/releases.
    for stale in abs_outdir.glob("*.whl"):
        stale.unlink()

    uv_exe = find_uv()
    if uv_exe:
        build_with_uv(uv_exe, repo_root, outdir)
    else:
        build_with_python_build(repo_root, outdir)

    wheels = sorted(abs_outdir.glob("*.whl"))
    if not wheels:
        raise RuntimeError("No wheel file was produced")

    print("[build-wheel] Built wheel(s):")
    for wheel in wheels:
        print(f"  - {wheel}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
