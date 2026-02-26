#!/usr/bin/env python3
"""Query Android a11y_tree and output a clean flat list of UI elements."""

import argparse
import json
import sys

from droidutils import (
    query_tree_with_retry,
    walk_tree,
    format_element,
    format_element_json,
    get_phone_state,
    get_screen_size,
    ensure_screen_awake,
)


def main():
    parser = argparse.ArgumentParser(description="Query Android a11y_tree and show clean element list")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--phone-state", action="store_true", help="Also show current activity and keyboard status")
    parser.add_argument("--all", action="store_true", help="Include layout containers (noise nodes)")
    parser.add_argument("--no-filter-small", action="store_true", help="Include tiny elements (<5px)")
    parser.add_argument("--no-filter-keyboard", action="store_true", help="Include keyboard elements")
    parser.add_argument("--no-filter-invisible", action="store_true", help="Include off-screen elements")
    parser.add_argument("--json", action="store_true", help="Output as JSON for programmatic use")
    parser.add_argument("--ensure-awake", action="store_true", help="Wake screen before querying")
    parser.add_argument("--full", action="store_true", help="Use full a11y tree with state properties (checked, enabled, etc.)")
    args = parser.parse_args()

    if args.ensure_awake:
        ensure_screen_awake(serial=args.serial)

    # Query tree (uses shared function for consistent index assignment with --full)
    tree = query_tree_with_retry(serial=args.serial, max_retries=1, delay=0, full=args.full)
    if not tree:
        print("Error: failed to query a11y tree", file=sys.stderr)
        sys.exit(1)

    # Get screen size for visibility filtering
    screen_width, screen_height = get_screen_size(serial=args.serial)

    elements = []
    if args.all:
        # Flatten everything without filtering
        def walk_all(nodes):
            for node in nodes:
                elements.append(node)
                walk_all(node.get("children", []))
        walk_all(tree)
    else:
        # Apply filters
        walk_tree(
            tree,
            elements,
            screen_width=screen_width,
            screen_height=screen_height,
            filter_noise=True,
            filter_small=not args.no_filter_small,
            filter_keyboard=not args.no_filter_keyboard,
            filter_invisible=not args.no_filter_invisible,
        )

    if args.json:
        # JSON output mode
        json_elements = [format_element_json(el) for el in elements]
        if args.phone_state:
            state = get_phone_state(serial=args.serial)
            output_data = {
                "elements": json_elements,
                "phoneState": {
                    "app": state.get("currentApp", "unknown"),
                    "activity": state.get("activityName", "unknown"),
                    "keyboardVisible": state.get("keyboardVisible", False),
                    "focusedElement": state.get("focusedElement"),
                }
            }
        else:
            output_data = json_elements
        print(json.dumps(output_data, indent=2))
    else:
        # Human-readable output
        if not elements:
            print("No meaningful UI elements found on screen.")
        else:
            for el in elements:
                print(format_element(el))

        if args.phone_state:
            state = get_phone_state(serial=args.serial)
            print()
            app = state.get("currentApp", "unknown")
            activity = state.get("activityName", "unknown")
            print(f"App: {app} ({activity})")
            print(f"Keyboard: {'shown' if state.get('keyboardVisible') else 'hidden'}")
            focused = state.get("focusedElement")
            if focused and focused.get("resourceId"):
                print(f"Focused: {focused['resourceId']}")


if __name__ == "__main__":
    main()
