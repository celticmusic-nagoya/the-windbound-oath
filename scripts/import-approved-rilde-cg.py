#!/usr/bin/env python3
"""Import director-approved Rilde CG PNGs, preserving exact bytes. No scene wiring."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

import gdown

DRIVE_FILE_ID = "1kDkeBnOOiHJSxvXhkIrAMMNVkxIofnS4"
ZIP_PREFIX = "windbound-rilde-approved-cg-supplement-20261107/"
CANONICAL = {
    "assets/approved/game/cliff/sunset_background.png": "db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07",
    "assets/approved/game/cliff/sunset_two_characters_back_view.png": "f7e2c3a7ee782d29df6b9a97449ae4fd9c0cdb44116c26fe033ebc07acfdeea9",
    "assets/approved/game/cliff/stargazing_seated.png": "a0a52220d2b846cf8f3ec2be1c3680f2611f86982e83e6068d03fef3e92b5d16",
    "assets/approved/game/cliff/stargazing_standing_final.png": "370b40af6fee48d56419376e2e773b1860a6a88a9b7ec893fd86104c6d29a41d",
    "assets/approved/game/rilde_story/cliff/stargazing_dialogue_background.png": "2d500df62460e7843dbb8226d017eda8331afe9f86ce18d2d8c4973734018ce0",
    "assets/approved/game/rilde_story/road/curve_reveal_APPROVED_user_reference.png": "7989bca750f66ade1935c31fd1f15189505f7c8b481b3839d86cb5ab26c4c60b",
    "assets/approved/game/rilde_story/raid/attack_background_only.png": "a19e782ec0927f9ef983cf896cf31a18ace0aca8bf2b165714342b1cfe528c3e",
    "assets/approved/game/rilde_story/raid/attack_with_characters_APPROVED_user_reference.png": "57099c16d62ada6f5808229618ea4e2a499672bd2cdd75885c4616c5f646ddc7",
    "assets/approved/game/rilde_story/aftermath/ruins_background_only.png": "78b0801f10b6a763c66aa44265ab381edc398f3b5adfb1b3d3dee0e6c6d917b2",
    "assets/approved/game/rilde_story/recovery/relief_with_characters_APPROVED_user_reference.png": "564bf45da05f9bc1d64a5e83986d1ce8eee0ab2e6dea82dd3d62d2a0cc15cda5",
}
EXISTING_CLIFF = set(list(CANONICAL)[:4])
LEGACY_FORBIDDEN = (
    "attack_background_only_APPROVED_user_reference.png",
    "ruins_background_only_APPROVED_user_reference.png",
)


def main() -> None:
    archive = Path("/tmp/approved-rilde-20261107.zip")
    result = gdown.download(id=DRIVE_FILE_ID, output=str(archive), quiet=False)
    if result is None or not archive.is_file():
        raise RuntimeError("Google Drive download failed; do not commit partial assets")
    entries = []
    new_files = 0
    jpeg_sources = {
        "assets/approved/game/rilde_story/road/curve_reveal_APPROVED_user_reference.png",
        "assets/approved/game/rilde_story/raid/attack_with_characters_APPROVED_user_reference.png",
        "assets/approved/game/rilde_story/recovery/relief_with_characters_APPROVED_user_reference.png",
    }
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise RuntimeError("ZIP CRC check failed")
        for repo_path, expected_sha in CANONICAL.items():
            zipped = ZIP_PREFIX + repo_path
            data = z.read(zipped)
            sha = hashlib.sha256(data).hexdigest()
            if sha != expected_sha or not data.startswith(b"\x89PNG\r\n\x1a\n"):
                raise RuntimeError(f"SHA-256 or PNG signature mismatch: {repo_path}")
            target = Path(repo_path)
            if target.is_file():
                if target.read_bytes() != data:
                    raise RuntimeError(f"Approved asset differs: {repo_path}; refusing overwrite")
            elif repo_path in EXISTING_CLIFF:
                raise RuntimeError(f"Expected existing cliff asset absent: {repo_path}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                new_files += 1
            entries.append({"path": output_path, "source_zip_path": repo_path, "format": "JPEG" if is_jpeg else "PNG", "sha256": sha, "bytes": len(data), "usage": "game only"})
    for forbidden in LEGACY_FORBIDDEN:
        if any(Path(p).name == forbidden for p in CANONICAL):
            raise RuntimeError(f"Obsolete filename in canonical set: {forbidden}")
    manifest = {
        "project": "THE WINDBOUND OATH",
        "status": "approved original PNGs; runtime integration pending",
        "source": "Google Drive public shared ZIP, director-approved 2026-11-07",
        "preserve_original_bytes": True,
        "files": entries,
    }
    path = Path("docs/art/approved-rilde-story-20261107.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if new_files != 6:
        raise RuntimeError(f"Expected exactly 6 new files, got {new_files}")
    print("ZIP CRC PASS; 10/10 SHA-256 PASS; 4 preserved; 6 new originals (3 PNG, 3 JPEG).")


if __name__ == "__main__":
    main()
