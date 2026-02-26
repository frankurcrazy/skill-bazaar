#!/usr/bin/env python3
"""List visible windows and overlay regions from dumpsys.

Workaround for system UI elements (bubbles, PiP, etc.) not visible
in the accessibility tree.
"""

import argparse
import re
import json
import sys

from droidutils import run_adb


def parse_region(region_str):
    """Parse SkRegion string into bounds tuple.

    Examples:
        "SkRegion((-39,1439,183,1661))" -> (-39, 1439, 183, 1661)
        "SkRegion((0,0,1080,2400))" -> (0, 0, 1080, 2400)
    """
    match = re.search(r'\((-?\d+),(-?\d+),(-?\d+),(-?\d+)\)', region_str)
    if match:
        return tuple(int(x) for x in match.groups())
    return None


def parse_windows(dumpsys_output):
    """Parse dumpsys window windows output for visible touchable windows."""
    windows = []
    seen_hashes = set()

    # Find each window entry directly in the output
    # Format: ", hash name, frame=[Rect(x1, y1 - x2, y2)], touchableRegion=SkRegion((...)), ..."
    # Window entries start after [ or , in the visible windows list
    window_pattern = re.compile(
        r'(?:[\[,]\s*)([a-f0-9]+)\s+([^,]+),\s*'
        r'frame=\[Rect\((\d+),\s*(\d+)\s*-\s*(\d+),\s*(\d+)\)\],\s*'
        r'touchableRegion=(SkRegion\(\([^)]+\)\))'
    )

    for match in window_pattern.finditer(dumpsys_output):
        window_hash = match.group(1)

        # Skip duplicates (windows appear in multiple sections)
        if window_hash in seen_hashes:
            continue
        seen_hashes.add(window_hash)

        window_name = match.group(2).strip()
        frame = (int(match.group(3)), int(match.group(4)),
                 int(match.group(5)), int(match.group(6)))
        region_str = match.group(7)
        region = parse_region(region_str)

        if region:
            # Calculate center of touchable region
            center = ((region[0] + region[2]) // 2, (region[1] + region[3]) // 2)

            windows.append({
                'name': window_name,
                'hash': window_hash,
                'frame': frame,
                'touchable_region': region,
                'center': center,
            })

    return windows


def find_overlay_windows(windows):
    """Filter for likely overlay windows (bubbles, PiP, etc.)."""
    overlays = []

    # Known overlay patterns
    overlay_patterns = [
        'Bubbles',
        'PictureInPicture',
        'pip',
        'SystemUI',
        'Floating',
        'Overlay',
    ]

    # Exclude patterns (system chrome, not user-interactive overlays)
    exclude_patterns = [
        'StatusBar',
        'NavigationBar',
        'ScreenDecor',
        'InputMethod',
        'NotificationShade',
        'com.droidrun.portal',  # Our own overlay
    ]

    for window in windows:
        name = window['name']

        # Skip excluded windows
        if any(excl in name for excl in exclude_patterns):
            continue

        # Check if it's a known overlay type
        is_overlay = any(pattern.lower() in name.lower() for pattern in overlay_patterns)

        # Also consider windows with small touchable regions as potential overlays
        region = window['touchable_region']
        region_area = (region[2] - region[0]) * (region[3] - region[1])
        is_small_region = region_area < 500 * 500  # Less than 500x500 pixels

        if is_overlay or is_small_region:
            overlays.append(window)

    return overlays


def main():
    parser = argparse.ArgumentParser(
        description="List visible windows and overlay regions (for bubbles, PiP, etc.)"
    )
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--all", action="store_true", help="Show all visible windows, not just overlays")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--filter", help="Filter windows by name (case-insensitive)")
    args = parser.parse_args()

    output = run_adb(
        ["shell", "dumpsys", "window", "windows"],
        serial=args.serial,
        timeout=30,
    )

    windows = parse_windows(output)

    if not windows:
        print("No visible windows found", file=sys.stderr)
        sys.exit(1)

    # Filter windows
    if args.filter:
        windows = [w for w in windows if args.filter.lower() in w['name'].lower()]
    elif not args.all:
        windows = find_overlay_windows(windows)

    if args.json:
        print(json.dumps(windows, indent=2))
    else:
        if not windows:
            print("No overlay windows found. Use --all to see all windows.")
        else:
            for w in windows:
                region = w['touchable_region']
                center = w['center']
                print(f"[{w['name']}] center=({center[0]},{center[1]}) "
                      f"region=({region[0]},{region[1]},{region[2]},{region[3]})")


if __name__ == "__main__":
    main()
