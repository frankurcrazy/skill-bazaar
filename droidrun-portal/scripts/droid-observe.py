#!/usr/bin/env python3
"""Query Android a11y_tree and output a clean flat list of UI elements."""

import argparse
import sys

from droidutils import (
    run_adb,
    parse_content_provider,
    walk_tree,
    format_element,
    get_phone_state,
    get_screen_size,
)


def main():
    parser = argparse.ArgumentParser(description="Query Android a11y_tree and show clean element list")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--phone-state", action="store_true", help="Also show current activity and keyboard status")
    parser.add_argument("--all", action="store_true", help="Include layout containers (noise nodes)")
    parser.add_argument("--no-filter-small", action="store_true", help="Include tiny elements (<5px)")
    parser.add_argument("--no-filter-keyboard", action="store_true", help="Include keyboard elements")
    parser.add_argument("--no-filter-invisible", action="store_true", help="Include off-screen elements")
    args = parser.parse_args()

    output = run_adb(
        ["shell", "content", "query", "--uri",
         "content://com.droidrun.portal/a11y_tree"],
        serial=args.serial,
    )
    tree = parse_content_provider(output)

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
