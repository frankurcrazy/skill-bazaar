#!/usr/bin/env python3
"""Find a UI element by text and long-press it."""

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
    parser = argparse.ArgumentParser(description="Long-press UI element by text")
    parser.add_argument("text", nargs="?", help="Text to search for in UI elements")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--exact", action="store_true", help="Require exact text match")
    parser.add_argument("--duration", type=int, default=1500, help="Long-press duration in ms (default: 1500)")
    parser.add_argument("--coords", nargs=2, type=int, metavar=("X", "Y"), help="Direct coordinates instead of text search")
    parser.add_argument("--ensure-awake", action="store_true", help="Wake screen before action")
    args = parser.parse_args()

    if not args.text and not args.coords:
        parser.error("Either text or --coords is required")

    if args.ensure_awake:
        ensure_screen_awake(serial=args.serial)

    if args.coords:
        cx, cy = args.coords
        display_text = f"coordinates ({cx}, {cy})"
    else:
        output = run_adb(
            ["shell", "content", "query", "--uri",
             "content://com.droidrun.portal/a11y_tree"],
            serial=args.serial,
        )
        tree = parse_content_provider(output)

        element = find_element(tree, args.text, exact=args.exact)
        if not element:
            print(f"Error: no element found matching \"{args.text}\"", file=sys.stderr)
            sys.exit(1)

        tap_point = get_tap_point(element)
        if not tap_point:
            print(f"Error: element has no bounds: {element}", file=sys.stderr)
            sys.exit(1)

        cx, cy = tap_point
        text = element.get("text", "")
        class_name = short_class_name(element.get("className", ""))
        display_text = f'"{text}" ({class_name})'

    # Long-press = swipe with same start/end coordinates
    run_adb(
        ["shell", "input", "swipe", str(cx), str(cy), str(cx), str(cy), str(args.duration)],
        serial=args.serial,
    )

    print(f"Long-pressed {display_text} at ({cx}, {cy}) for {args.duration}ms")


if __name__ == "__main__":
    main()
