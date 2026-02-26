#!/usr/bin/env python3
"""Long-press element by index number (faster than text search)."""

import argparse
import sys

from droidutils import (
    run_adb,
    query_tree_with_retry,
    find_element_by_index,
    get_tap_point,
    short_class_name,
    ensure_screen_awake,
)


def main():
    parser = argparse.ArgumentParser(description="Long-press UI element by index number")
    parser.add_argument("index", type=int, help="Element index to long-press (from droid-observe output)")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--duration", type=int, default=1500, help="Long-press duration in ms (default: 1500)")
    parser.add_argument("--ensure-awake", action="store_true", help="Wake screen before action")
    parser.add_argument("--full", action="store_true", help="Use full a11y tree (match droid-observe --full indices)")
    args = parser.parse_args()

    if args.ensure_awake:
        ensure_screen_awake(serial=args.serial)

    tree = query_tree_with_retry(serial=args.serial, max_retries=1, delay=0, full=args.full)
    if not tree:
        print("Error: failed to query a11y tree", file=sys.stderr)
        sys.exit(1)

    element = find_element_by_index(tree, args.index)
    if not element:
        print(f"Error: no element found with index {args.index}", file=sys.stderr)
        sys.exit(1)

    tap_point = get_tap_point(element)
    if not tap_point:
        print(f"Error: element has no bounds: {element}", file=sys.stderr)
        sys.exit(1)

    cx, cy = tap_point
    text = element.get("text", "") or element.get("contentDescription", "")
    class_name = short_class_name(element.get("className", ""))

    # Long-press = swipe with same start/end coordinates
    run_adb(
        ["shell", "input", "swipe", str(cx), str(cy), str(cx), str(cy), str(args.duration)],
        serial=args.serial,
    )

    display_text = f'"{text}"' if text else f"index {args.index}"
    print(f"Long-pressed {display_text} ({class_name}) at ({cx}, {cy}) for {args.duration}ms")


if __name__ == "__main__":
    main()
