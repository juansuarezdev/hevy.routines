#!/usr/bin/env python3
"""Load YAML routines, resolve exercise names to template IDs, POST each routine to Hevy."""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import ValidationError

from hevy_client import HevyAPIError, HevyClient
from models import (
    PostRoutinesRequestBody,
    PostRoutinesRequestExercise,
    PostRoutinesRequestSet,
    RoutinePayload,
    YamlRoutineDefinition,
)


class UnresolvedExerciseError(Exception):
    def __init__(self, exercise_name: str, suggestions: list[str]) -> None:
        self.exercise_name = exercise_name
        self.suggestions = suggestions
        msg = f"No exercise template with title matching exactly: {exercise_name!r}"
        if suggestions:
            msg += "\n  Similar titles in your account:\n    - " + "\n    - ".join(suggestions)
        else:
            msg += "\n  (No close matches found; check the exact title in the Hevy app.)"
        super().__init__(msg)


def load_yaml_routine(path: Path) -> YamlRoutineDefinition:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a mapping at the root")
    return YamlRoutineDefinition.model_validate(raw)


def build_title_index(templates: list) -> dict[str, str]:
    """Map exact exercise title -> template id (last wins if duplicates)."""
    out: dict[str, str] = {}
    for t in templates:
        out[t.title] = t.id
    return out


def suggest_titles(exercise_name: str, all_titles: list[str]) -> list[str]:
    """Heuristic suggestions for typos / partial matches."""
    name_lower = exercise_name.lower()
    substr = [t for t in all_titles if name_lower in t.lower() or t.lower() in name_lower]
    close = difflib.get_close_matches(exercise_name, all_titles, n=10, cutoff=0.35)
    merged: list[str] = []
    seen: set[str] = set()
    for t in substr + close:
        if t not in seen:
            seen.add(t)
            merged.append(t)
    return merged[:12]


def yaml_to_post_body(
    definition: YamlRoutineDefinition,
    title_to_id: dict[str, str],
    all_titles: list[str],
) -> PostRoutinesRequestBody:
    exercises: list[PostRoutinesRequestExercise] = []
    for ex in definition.exercises:
        tid = title_to_id.get(ex.name)
        if tid is None:
            raise UnresolvedExerciseError(ex.name, suggest_titles(ex.name, all_titles))
        sets = [PostRoutinesRequestSet.model_validate(s.model_dump()) for s in ex.sets]
        exercises.append(
            PostRoutinesRequestExercise(
                exercise_template_id=tid,
                superset_id=ex.superset_id,
                rest_seconds=ex.rest_seconds,
                notes=ex.notes,
                sets=sets,
            )
        )
    return PostRoutinesRequestBody(
        routine=RoutinePayload(
            title=definition.title,
            folder_id=definition.folder_id,
            notes=definition.notes,
            exercises=exercises,
        )
    )


def discover_yaml_files(routines_dir: Path) -> list[Path]:
    paths = sorted(list(routines_dir.glob("*.yaml")) + list(routines_dir.glob("*.yml")))
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Hevy routines from YAML files.")
    parser.add_argument(
        "--routines-dir",
        type=Path,
        default=Path("routines"),
        help="Directory containing .yaml / .yml routine definitions (default: ./routines)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve exercises and print payloads; do not POST to the API.",
    )
    args = parser.parse_args()

    load_dotenv()

    routines_dir: Path = args.routines_dir
    if not routines_dir.is_dir():
        print(f"Not a directory: {routines_dir}", file=sys.stderr)
        return 1

    files = discover_yaml_files(routines_dir)
    if not files:
        print(f"No .yaml / .yml files in {routines_dir}", file=sys.stderr)
        return 1

    try:
        with HevyClient() as client:
            print("Fetching exercise templates…")
            templates = client.fetch_all_exercise_templates()
            title_to_id = build_title_index(templates)
            all_titles = sorted(title_to_id.keys())

            results_ok: list[tuple[str, str]] = []
            results_fail: list[tuple[str, str]] = []

            for path in files:
                label = path.name
                try:
                    definition = load_yaml_routine(path)
                    body = yaml_to_post_body(definition, title_to_id, all_titles)
                except (
                    UnresolvedExerciseError,
                    ValidationError,
                    ValueError,
                ) as e:
                    results_fail.append((label, str(e)))
                    continue

                if args.dry_run:
                    print(f"\n--- {label} (dry-run) ---")
                    print(json.dumps(body.model_dump(mode="json", exclude_none=True), indent=2))
                    results_ok.append((label, "(dry-run)"))
                    continue

                try:
                    created = client.create_routine(body)
                    rid = created.id
                    results_ok.append((label, rid))
                    print(f"Created routine {label!r} → id {rid}")
                except HevyAPIError as e:
                    results_fail.append((label, str(e)))

    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except HevyAPIError as e:
        print(str(e), file=sys.stderr)
        return 1

    print("\n--- Summary ---")
    print(f"OK: {len(results_ok)}  Failed: {len(results_fail)}")
    for name, info in results_ok:
        print(f"  [ok] {name}  {info}")
    for name, err in results_fail:
        print(f"  [fail] {name}")
        for line in err.splitlines():
            print(f"         {line}")

    return 0 if not results_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
