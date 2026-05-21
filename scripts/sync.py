#!/usr/bin/env python3
"""Re-vendor the .proto files described in vendor.toml from their pinned upstream
commits.

For each source: verify the pinned rev actually modifies its `src` folder, do a
shallow/blobless/sparse fetch of `src` at that rev, mirror every *.proto under it
into `dest`, and stamp the crate version with `+g<short-sha>.v<version>`. After
running: review `git diff`.

Requires: git, and Python >= 3.11 (tomllib).
Usage: scripts/sync.py   (override the manifest with MANIFEST=/path scripts/sync.py)
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(os.environ.get("MANIFEST", REPO_ROOT / "vendor.toml"))


def git(*args, cwd=None):
    subprocess.run(["git", *args], cwd=cwd, check=True, stdout=subprocess.DEVNULL)


def require_rev_edits_path(url, rev, src):
    """Exit unless `rev` is a commit that modifies `src` (anchored at the rev).
    GitHub-only; skipped for other hosts."""
    prefix = "https://github.com/"
    if not url.startswith(prefix):
        print("   (skip rev-edits-path check: non-GitHub host)")
        return
    slug = url[len(prefix):].removesuffix(".git")
    api = f"https://api.github.com/repos/{slug}/commits?sha={rev}&path={src}&per_page=1"
    req = urllib.request.Request(api, headers={"Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
    except Exception as err:
        sys.exit(f"ERROR: could not verify rev {rev[:12]} against {slug} '{src}': {err}")
    top = data[0]["sha"] if isinstance(data, list) and data else ""
    if top != rev:
        sys.exit(
            f"ERROR: rev {rev} does not modify '{src}'.\n"
            f"       Latest commit touching that path from this rev is {top or '(none)'}.\n"
            f"       Pin a commit that actually edits {src} (see its git log)."
        )


def mirror_protos(src_dir, dest):
    """Drop existing *.proto under dest, then copy every *.proto from src_dir."""
    dest_dir = REPO_ROOT / dest
    if dest_dir.exists():
        for old in dest_dir.rglob("*.proto"):
            old.unlink()
    for proto in sorted(src_dir.rglob("*.proto")):
        rel = proto.relative_to(src_dir)
        out = dest_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(proto, out)
        print(f"   {dest}/{rel}")


def stamp_version(dest, rev, version):
    """(Re)set the crate's version build metadata from the manifest: keep the
    maintained core X.Y.Z and append +g<short-sha>.v<upstream-version>."""
    cargo = REPO_ROOT / Path(dest).parts[0] / "Cargo.toml"
    meta = f"+g{rev[:7]}.v{version}"
    new, n = re.subn(
        r'(?m)^version = "(\d+\.\d+\.\d+)(?:\+[^"]*)?"',
        lambda m: f'version = "{m.group(1)}{meta}"',
        cargo.read_text(),
    )
    if n != 1:
        sys.exit(f"ERROR: expected one version line in {cargo}, found {n}")
    cargo.write_text(new)
    print(f"   {Path(dest).parts[0]}/Cargo.toml  version {meta}")


def main():
    manifest = tomllib.loads(MANIFEST.read_text())
    for source in manifest["source"]:
        name, url, rev = source["name"], source["git"], source["rev"]
        src, dest = source["src"], source["dest"]
        print(f">> {name}  {rev[:12]}  ({url})")
        require_rev_edits_path(url, rev, src)
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            git("init", "-q", str(work))
            git("remote", "add", "origin", url, cwd=work)
            git("sparse-checkout", "set", "--no-cone", src, cwd=work)
            git("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", rev, cwd=work)
            git("checkout", "-q", "FETCH_HEAD", cwd=work)
            src_dir = work / src
            if not src_dir.is_dir():
                sys.exit(f"ERROR: src path '{src}' missing at {rev}")
            mirror_protos(src_dir, dest)
        stamp_version(dest, rev, source["version"])
    print("Done. Review 'git diff'.")


if __name__ == "__main__":
    main()
