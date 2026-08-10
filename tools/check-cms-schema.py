"""Fail if the CMS schema has drifted from the data files it edits.

Sveltia rewrites a file from the fields declared in static/admin/config.yml.
Any key that is not declared is silently dropped the first time a board member
presses Publish — so a field added to data/organization.yaml and forgotten here
becomes data loss that nobody notices until the phone number disappears.

This walks every `file:` collection that points at a data/*.yaml, and compares
the real key tree against the declared field tree.

    python3 tools/check-cms-schema.py

Exits non-zero on drift. Run it in CI.
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "static/admin/config.yml"


def declared(fields):
    """The key tree the CMS knows how to write, as nested dicts."""
    out = {}
    for f in fields or []:
        name = f.get("name")
        if not name:
            continue
        widget = f.get("widget", "string")
        if widget == "object":
            out[name] = declared(f.get("fields"))
        elif widget == "list":
            if f.get("fields"):
                # A list of objects: describe one item.
                out[name] = {"[]": declared(f["fields"])}
            else:
                # A list of scalars, or a `field:` shorthand.
                out[name] = {"[]": {}}
        elif f.get("multiple"):
            # select/relation with multiple:true also stores a list.
            out[name] = {"[]": {}}
        else:
            out[name] = {}
    return out


def actual(value):
    """The key tree a YAML file actually contains."""
    if isinstance(value, dict):
        return {k: actual(v) for k, v in value.items()}
    if isinstance(value, list):
        merged = {}
        for item in value:
            if isinstance(item, dict):
                for k, v in item.items():
                    merged.setdefault(k, actual(v))
        return {"[]": merged}
    return {}


def compare(have, know, path, missing):
    """Every key in `have` must appear in `know`."""
    for key, sub in have.items():
        if key not in know:
            missing.append(f"{path}.{key}".lstrip("."))
            continue
        compare(sub, know[key], f"{path}.{key}".lstrip("."), missing)


def main():
    config = yaml.safe_load(CONFIG.read_text())
    missing = []
    checked = 0

    for collection in config["collections"]:
        for entry in collection.get("files", []):
            rel = entry.get("file", "")
            if not rel.startswith("data/"):
                continue
            data_file = ROOT / rel
            if not data_file.exists():
                missing.append(f"{rel}: declared in the CMS but missing on disk")
                continue

            data = yaml.safe_load(data_file.read_text()) or {}
            know = declared(entry.get("fields"))
            have = actual(data)

            before = len(missing)
            compare(have, know, "", missing)
            for i in range(before, len(missing)):
                missing[i] = f"{rel}: {missing[i]}"
            checked += 1

    if missing:
        print(f"CMS SCHEMA DRIFT — {len(missing)} key(s) would be destroyed on save:\n")
        for m in missing:
            print(f"  {m}")
        print("\nAdd the matching field(s) to static/admin/config.yml.")
        return 1

    print(f"CMS schema matches all {checked} edited data files. "
          "No key would be lost on save.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
