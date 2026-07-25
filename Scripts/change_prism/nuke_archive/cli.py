from __future__ import print_function

import argparse
import sys

from change_prism.nuke_archive.service import (
    ArchiveError,
    build_package_plan,
    execute_package,
    format_bytes,
)


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Package a Nuke script and its Read dependencies."
    )
    parser.add_argument("source_nk", help="Nuke script to package")
    parser.add_argument(
        "--archive-root",
        required=True,
        help="Destination Archives directory",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Run without an interactive confirmation",
    )
    return parser


def _print_plan(plan):
    print("Source: %s" % plan["source_nk"])
    print(
        "Target: %s/%s"
        % (
            plan.get("version_root", plan["archive_root"]),
            plan["proposed_version"],
        )
    )
    print("Read nodes: %d" % len(plan["reads"]))
    print("Unique copy items: %d" % len(plan["copy_jobs"]))
    print(
        "Estimated payload: %s across %d files"
        % (
            format_bytes(plan["estimated_total_bytes"]),
            plan["estimated_file_count"],
        )
    )
    if plan["available_bytes"] is not None:
        print(
            "Available at destination: %s"
            % format_bytes(plan["available_bytes"])
        )
        if plan["estimated_total_bytes"] > plan["available_bytes"]:
            print("WARNING: The destination does not have enough free space.")
    for job in plan["copy_jobs"]:
        print("  %s <- %s" % (job["material_folder"], job["source"]))


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        plan = build_package_plan(args.source_nk, args.archive_root)
        _print_plan(plan)
        if not args.yes:
            answer = input("Create this Archive? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("Cancelled.")
                return 0

        def progress(completed, total, message):
            print("[%d/%d] %s" % (completed, total, message))

        result = execute_package(plan, progress_callback=progress)
    except ArchiveError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("Created %s: %s" % (result["version"], result["version_path"]))
    print("Nuke script: %s" % result["packaged_nk"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
