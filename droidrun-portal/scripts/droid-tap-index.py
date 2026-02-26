#!/usr/bin/env python3
"""Tap element by index number (faster than text search)."""

import argparse
import sys

from droidutils import (
    run_adb,
    parse_content_provider,
    find_element_by_index,
    get_tap_point,
    short_class_name,
)


def main():
    parser = argparse.ArgumentParser(description="Tap UI element by index number")
    parser.add_argument("index", type=int, help="Element index to tap (from droid-observe output)")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--avoid-overlap", action="store_true", help="Find clear tap point avoiding overlaps")
    args = parser.parse_args()

    output = run_adb(
        ["shell", "content", "query", "--uri",
         "content://com.droidrun.portal/a11y_tree"],
        serial=args.serial,
    )
    tree = parse_content_provider(output)

    element = find_element_by_index(tree, args.index)
    if not element:
        print(f"Error: no element found with index {args.index}", file=sys.stderr)
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

    display_text = f'"{text}"' if text else f"index {args.index}"
    print(f"Tapped {display_text} ({class_name}) at ({cx}, {cy})")


if __name__ == "__main__":
    main()
