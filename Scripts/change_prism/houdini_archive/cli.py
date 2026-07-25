from __future__ import unicode_literals

import argparse
import os
import sys

from change_prism.houdini_archive.service import (
    ArchiveError,
    PackageCancelled,
    build_package_plan,
    execute_package,
    format_bytes,
)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Package a Houdini scene and supported dependencies."
    )
    parser.add_argument("source_hip")
    parser.add_argument("--archive-root", required=True)
    parser.add_argument("--hython")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Create the Archive without asking for confirmation.",
    )
    return parser


def main(argv=None, input_func=input, output=None):
    output = output or sys.stdout
    args = build_parser().parse_args(argv)
    try:
        plan = build_package_plan(
            args.source_hip,
            args.archive_root,
            hython_executable=args.hython,
        )
        _print_plan(plan, output)
        if not args.yes:
            answer = input_func("Create this Houdini Archive? [y/N] ")
            if str(answer).strip().lower() not in ("y", "yes"):
                output.write("Cancelled.\n")
                return 2
        result = execute_package(plan)
    except PackageCancelled:
        output.write("Cancelled.\n")
        return 2
    except ArchiveError as exc:
        output.write("Error: %s\n" % exc)
        return 1

    output.write(
        "Created %s: %s\n"
        % (result["version"], result["version_path"])
    )
    return 0


def _print_plan(plan, output):
    summary = plan["summary"]
    output.write("Source: %s\n" % plan["source_hip"])
    output.write(
        "Houdini: %s via %s\n"
        % (plan["houdini_version"], plan["hython_executable"])
    )
    if plan.get("version_warning"):
        output.write("Warning: %s\n" % plan["version_warning"])
    output.write(
        "Target: %s\n"
        % os.path.join(
            plan.get("version_root", plan["archive_root"]),
            plan["proposed_version"],
        )
    )
    output.write(
        "References: %d, packaged: %d, skipped cache: %d, "
        "skipped missing: %d, skipped unsupported: %d\n"
        % (
            summary["reference_count"],
            summary["package_input_count"],
            summary["skipped_cache_count"],
            summary.get("skipped_missing_count", 0),
            summary["skipped_unsupported_count"],
        )
    )
    skipped_missing = summary.get("skipped_missing_count", 0)
    if skipped_missing:
        output.write(
            "Warning: %d unavailable /mnt/nas reference(s) will be "
            "skipped and keep their original paths.\n"
            % skipped_missing
        )
    output.write(
        "Payload: %s across %d files\n"
        % (
            format_bytes(plan["estimated_total_bytes"]),
            plan["estimated_file_count"],
        )
    )


if __name__ == "__main__":
    sys.exit(main())
