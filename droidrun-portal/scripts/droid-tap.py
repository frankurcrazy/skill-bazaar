#!/usr/bin/env python3
"""Find a UI element by text and tap it."""

import argparse
import sys

from droidutils import (
    run_adb,
    parse_content_provider,
    find_element,
    get_tap_point,
    short_class_name,
    ensure_screen_awake,
)


def main():
    parser = argparse.ArgumentParser(description="Find UI element by text and tap it")
    parser.add_argument("text", help="Text to search for in UI elements")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--exact", action="store_true", help="Require exact text match")
    parser.add_argument("--avoid-overlap", action="store_true", help="Find clear tap point avoiding overlaps")
    parser.add_argument("--ensure-awake", action="store_true", help="Wake screen before action")
    args = parser.parse_args()

    if args.ensure_awake:
        ensure_screen_awake(serial=args.serial)

    output = run_adb(
        ["shell", "content", "query", "--uri",
         "content://com.droidrun.portal/a11y_tree"],
        serial=args.serial,
    )
    tree = parse_content_provider(output)

    element = find_element(tree, args.text, exact=args.exact)
    if not element:
        match_type = "exactly matching" if args.exact else "containing"
        print(f"Error: no element found with text {match_type} \"{args.text}\"", file=sys.stderr)
        sys.exit(1)

    # Get tap point (with overlap avoidance if requested)
    tap_point = get_tap_point(element, tree if args.avoid_overlap else None)
    if not tap_point:
        print(f"Error: element has no bounds: {element}", file=sys.stderr)
        sys.exit(1)

    cx, cy = tap_point
    text = element.get("text", "")
    class_name = short_class_name(element.get("className", ""))

    run_adb(["shell", "input", "tap", str(cx), str(cy)], serial=args.serial)
    print(f"Tapped \"{text}\" ({class_name}) at ({cx}, {cy})")


if __name__ == "__main__":
    main()
