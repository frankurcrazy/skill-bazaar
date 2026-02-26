#!/usr/bin/env python3
"""Tap on a window by name (for system overlays like bubbles, PiP).

Uses dumpsys window windows to find touchable regions, since these
overlays are not visible in the accessibility tree.
"""

import argparse
import re
import sys

from droidutils import run_adb, ensure_screen_awake


def parse_region(region_str):
    """Parse SkRegion string into bounds tuple."""
    match = re.search(r'\((-?\d+),(-?\d+),(-?\d+),(-?\d+)\)', region_str)
    if match:
        return tuple(int(x) for x in match.groups())
    return None


def find_window(dumpsys_output, name_filter):
    """Find a window by name and return its touchable region center."""
    # Parse each window entry directly in the output
    # Format: ", hash name, frame=[Rect(x1, y1 - x2, y2)], touchableRegion=SkRegion((...)), ..."
    window_pattern = re.compile(
        r'(?:[\[,]\s*)([a-f0-9]+)\s+([^,]+),\s*'
        r'frame=\[Rect\((\d+),\s*(\d+)\s*-\s*(\d+),\s*(\d+)\)\],\s*'
        r'touchableRegion=(SkRegion\(\([^)]+\)\))'
    )

    for match in window_pattern.finditer(dumpsys_output):
        window_name = match.group(2).strip()

        if name_filter.lower() in window_name.lower():
            region_str = match.group(7)
            region = parse_region(region_str)

            if region:
                center = ((region[0] + region[2]) // 2, (region[1] + region[3]) // 2)
                return {
                    'name': window_name,
                    'region': region,
                    'center': center,
                }

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Tap on a window by name (for bubbles, PiP, system overlays)"
    )
    parser.add_argument("name", help="Window name to search for (case-insensitive)")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--ensure-awake", action="store_true", help="Wake screen before action")
    parser.add_argument("--long-press", action="store_true", help="Long-press instead of tap")
    parser.add_argument("--duration", type=int, default=1500, help="Long-press duration in ms")
    args = parser.parse_args()

    if args.ensure_awake:
        ensure_screen_awake(serial=args.serial)

    output = run_adb(
        ["shell", "dumpsys", "window", "windows"],
        serial=args.serial,
        timeout=30,
    )

    window = find_window(output, args.name)

    if not window:
        print(f"Error: no window found matching \"{args.name}\"", file=sys.stderr)
        print("Use droid-windows.py --all to see available windows", file=sys.stderr)
        sys.exit(1)

    cx, cy = window['center']

    if args.long_press:
        run_adb(
            ["shell", "input", "swipe", str(cx), str(cy), str(cx), str(cy), str(args.duration)],
            serial=args.serial,
        )
        print(f"Long-pressed \"{window['name']}\" at ({cx}, {cy}) for {args.duration}ms")
    else:
        run_adb(["shell", "input", "tap", str(cx), str(cy)], serial=args.serial)
        print(f"Tapped \"{window['name']}\" at ({cx}, {cy})")


if __name__ == "__main__":
    main()
