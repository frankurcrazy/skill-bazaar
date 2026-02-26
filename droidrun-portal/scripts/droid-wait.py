#!/usr/bin/env python3
"""Poll a11y_tree until an element matching text appears."""

import argparse
import sys
import time

from droidutils import (
    query_tree_with_retry,
    find_element,
    center_of,
    parse_bounds,
    short_class_name,
)


def main():
    parser = argparse.ArgumentParser(description="Wait for UI element to appear")
    parser.add_argument("text", help="Text to search for in UI elements")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout in seconds (default: 10)")
    parser.add_argument("--exact", action="store_true", help="Require exact text match")
    args = parser.parse_args()

    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed >= args.timeout:
            print(f"Timeout: \"{args.text}\" not found after {args.timeout}s", file=sys.stderr)
            sys.exit(1)

        tree = query_tree_with_retry(serial=args.serial, max_retries=1, delay=0)
        if tree:
            element = find_element(tree, args.text, exact=args.exact)
            if element:
                text = element.get("text", "")
                bounds = element.get("bounds", "")
                class_name = short_class_name(element.get("className", ""))
                parts = [f"Found \"{text}\" ({class_name})"]
                if bounds:
                    cx, cy = center_of(bounds)
                    l, t, r, b = parse_bounds(bounds)
                    parts.append(f"at center=({cx},{cy}) bounds=({l},{t},{r},{b})")
                parts.append(f"after {elapsed:.1f}s")
                print(" ".join(parts))
                return

        time.sleep(1)


if __name__ == "__main__":
    main()
