"""Publish exactly the files delivered by the COMTracer signing workflow."""

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

REPOSITORY = "qchen9999/COMTracer-Downloads"
DIRECTORY = Path("payload")


def gh(*args, missing_ok=False):
    result = subprocess.run(["gh", "release", *args, "--repo", REPOSITORY],
                            capture_output=True, text=True)
    if result.returncode:
        if missing_ok and result.stderr.strip() in {"release not found", "no releases found"}:
            return None
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def read_release(tag):
    data = gh("view", tag, "--json", "isDraft,isPrerelease,assets,url", missing_ok=True)
    return json.loads(data) if data is not None else None


def signed_files(version):
    prefix = f"COMTracer-{version}-x64"
    names = {prefix + ".msi", prefix + ".zip", "binary-signatures.json",
             "installer-signature.json", "build-info.json", "SHA256SUMS.txt"}
    if {p.name for p in DIRECTORY.iterdir()} != names:
        raise ValueError("Unexpected or missing release files")
    digests = {}
    for name in sorted(names):
        path = DIRECTORY / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Invalid payload file: {name}")
        digests[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    sums = {}
    for line in (DIRECTORY / "SHA256SUMS.txt").read_text(encoding="utf-8-sig").splitlines():
        match = re.fullmatch(r"([a-f0-9]{64})  ([\w.\-]+)", line)
        if not match or match[2] in sums:
            raise ValueError("Invalid SHA256SUMS.txt")
        sums[match[2]] = match[1]
    if sums != {name: digest for name, digest in digests.items() if name != "SHA256SUMS.txt"}:
        raise ValueError("Package checksums disagree with the signing workflow")
    info = json.loads((DIRECTORY / "build-info.json").read_text(encoding="utf-8-sig"))
    if info["version"] != version or info["publisher"] != "BBSOFT LLC":
        raise ValueError("Signed build version or publisher mismatch")
    receipt = json.loads((DIRECTORY / "installer-signature.json").read_text(encoding="utf-8-sig"))
    if receipt["file"] != prefix + ".msi" or receipt["sha256"] != digests[prefix + ".msi"]:
        raise ValueError("Installer signing receipt mismatch")
    return digests


def pending(release, digests):
    if release["isPrerelease"]:
        raise ValueError("The release tag belongs to a prerelease")
    assets = {a["name"]: a for a in release["assets"]}
    missing = []
    for name, digest in digests.items():
        asset = assets.get(name)
        if asset and asset.get("digest") == "sha256:" + digest:
            continue
        if release["isDraft"] and (asset is None or asset.get("state") == "starter"):
            missing.append(str(DIRECTORY / name))
        else:
            raise ValueError(f"Release asset conflicts with the signed build: {name}")
    return missing


def main():
    match = re.fullmatch(r"signed/(v(\d+\.\d+\.\d+))", os.environ["GITHUB_REF_NAME"])
    if not match:
        raise ValueError("Expected a signed version branch")
    tag, version = match.groups()
    digests = signed_files(version)
    release = read_release(tag)
    if release is None:
        # Point the tag at the public documentation commit, before the temporary payload.
        target = subprocess.check_output(["git", "rev-parse", "HEAD^"], text=True).strip()
        gh("create", tag, "--draft", "--target", target, "--title", f"COMTracer {version}",
           "--notes", "Windows x64 installer and portable ZIP. The MSI and packaged executables "
           "are signed by BBSOFT LLC. SHA-256 checksums and signing receipts are included.")
        release = read_release(tag)
    missing = pending(release, digests)
    if missing:
        gh("upload", tag, *missing, "--clobber")
    if pending(read_release(tag), digests):
        raise ValueError("Upload verification failed")
    if release["isDraft"]:
        latest = gh("view", "--json", "tagName", "--jq", ".tagName", missing_ok=True)
        make_latest = True
        if latest and re.fullmatch(r"v\d+\.\d+\.\d+", latest.strip()):
            make_latest = tuple(map(int, version.split("."))) >= tuple(map(int, latest.strip()[1:].split(".")))
        gh("edit", tag, "--draft=false", "--latest=" + str(make_latest).lower())
    published = read_release(tag)
    if published["isDraft"] or pending(published, digests):
        raise ValueError("Public release verification failed")
    print(published["url"])


if __name__ == "__main__":
    main()
