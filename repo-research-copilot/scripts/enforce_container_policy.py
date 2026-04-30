from __future__ import annotations

import json
import re
import sys
from pathlib import Path


FROM_PATTERN = re.compile(
    r"^\s*FROM\s+(?:--platform=\S+\s+)?(?P<image>\S+)(?:\s+AS\s+(?P<alias>\S+))?\s*$",
    re.IGNORECASE,
)
ARG_PATTERN = re.compile(r"^\s*ARG\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>.+)\s*$")


def load_policy(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_dockerfile(path: Path) -> tuple[list[tuple[str, str | None]], dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    from_entries: list[tuple[str, str | None]] = []
    args: dict[str, str] = {}

    for line in lines:
        arg_match = ARG_PATTERN.match(line)
        if arg_match:
            args[arg_match.group("name")] = arg_match.group("value").strip()
            continue

        from_match = FROM_PATTERN.match(line)
        if from_match:
            image = from_match.group("image")
            alias = from_match.group("alias")
            from_entries.append((image, alias))

    return from_entries, args


def resolve_image(image: str, args: dict[str, str]) -> str:
    if image.startswith("${") and image.endswith("}"):
        key = image[2:-1]
        return args.get(key, image)
    return image


def image_repository(image: str) -> str:
    without_digest = image.split("@", 1)[0]
    if ":" in without_digest:
        return without_digest.rsplit(":", 1)[0]
    return without_digest


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    dockerfile_path = root / "Dockerfile"
    policy_path = root / "security" / "base-image-policy.json"

    policy = load_policy(policy_path)
    from_entries, args = parse_dockerfile(dockerfile_path)

    require_digest_pin = bool(policy.get("require_digest_pin", True))
    approved_images = set(policy.get("approved_images", []))
    required_stages: dict[str, str] = dict(policy.get("required_stages", {}))

    violations: list[str] = []
    stage_aliases: set[str] = set()

    for raw_image, alias in from_entries:
        image = resolve_image(raw_image, args)

        # Internal stage references are allowed and skipped from external image checks.
        if image in stage_aliases:
            if alias:
                stage_aliases.add(alias)
            continue

        if require_digest_pin and "@sha256:" not in image:
            violations.append(f"image '{image}' is missing digest pin")

        repo = image_repository(image)
        if repo not in approved_images:
            violations.append(f"image repo '{repo}' is not in approved_images")

        if alias and alias in required_stages:
            expected = required_stages[alias]
            if image != expected:
                violations.append(
                    f"stage '{alias}' image mismatch: expected '{expected}' got '{image}'"
                )

        if alias:
            stage_aliases.add(alias)

    for required_alias in required_stages:
        if required_alias not in stage_aliases:
            violations.append(f"required stage '{required_alias}' not found in Dockerfile")

    if violations:
        print("Container policy violations found:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("Container policy check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
