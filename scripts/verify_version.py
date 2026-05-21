#!/usr/bin/env python3
"""Verify each bundle's `version` label against its published upstream artifact.

sync.py guarantees the vendored protos match the pinned `rev`, but nothing ties
the hand-typed `version` to that content. For every source that names an
`artifact`, this downloads the Maven jar for `version` and asserts its `.proto`
files are byte-identical to the vendored ones — so a `version` that drifts from
`rev` fails CI. Sources without an `artifact` are skipped.

Requires: network access (Maven), and Python >= 3.11 (tomllib).
Usage: scripts/verify_version.py   (MANIFEST=/path to override the manifest)
"""

import io
import os
import sys
import tomllib
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(os.environ.get("MANIFEST", REPO_ROOT / "vendor.toml"))
CENTRAL = "https://repo1.maven.org/maven2"


def jar_url(repo, artifact, version):
    group, name = artifact.split(":")
    return f"{repo}/{group.replace('.', '/')}/{name}/{version}/{name}-{version}.jar"


def vendored_protos(base):
    """Map import path -> bytes for every vendored *.proto under base."""
    base_dir = REPO_ROOT / base
    return {
        p.relative_to(base_dir).as_posix(): p.read_bytes()
        for p in base_dir.rglob("*.proto")
    }


def artifact_protos(url, prefix):
    """Map import path -> bytes for every *.proto under prefix in the jar."""
    req = urllib.request.Request(url, headers={"User-Agent": "vendored-schemas"})
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    with zipfile.ZipFile(io.BytesIO(data)) as jar:
        return {
            n: jar.read(n)
            for n in jar.namelist()
            if n.startswith(prefix + "/") and n.endswith(".proto")
        }


def main():
    manifest = tomllib.loads(MANIFEST.read_text())
    failed = False
    for source in manifest["source"]:
        name = source["name"]
        artifact = source.get("artifact")
        if not artifact:
            print(f">> {name}  (no artifact — skipped)")
            continue
        version = source["version"]
        repo = source.get("maven_repo", CENTRAL)
        # dest is "<base>/proto/<prefix>"; vendored files live under <base>/proto
        # and jar entries under <prefix>, both keyed by the same import path.
        base, prefix = source["dest"].split("/proto/", 1)
        url = jar_url(repo, artifact, version)
        print(f">> {name}  {artifact}:{version}\n   {url}")
        try:
            upstream = artifact_protos(url, prefix)
        except Exception as err:
            sys.exit(f"ERROR: could not fetch {url}: {err}")
        if not upstream:
            sys.exit(f"ERROR: no '{prefix}/*.proto' in {artifact}:{version}")
        local = vendored_protos(f"{base}/proto")
        only_local = sorted(set(local) - set(upstream))
        only_upstream = sorted(set(upstream) - set(local))
        differ = sorted(k for k in set(local) & set(upstream) if local[k] != upstream[k])
        if only_local or only_upstream or differ:
            failed = True
            print(f"   MISMATCH against {artifact}:{version}")
            for k in only_local:
                print(f"     vendored only: {k}")
            for k in only_upstream:
                print(f"     artifact only: {k}")
            for k in differ:
                print(f"     bytes differ:  {k}")
        else:
            print(f"   OK — {len(local)} files byte-identical")
    if failed:
        sys.exit("ERROR: version label(s) do not match the published artifact.")
    print("Done. All version labels match their published artifacts.")


if __name__ == "__main__":
    main()
