#!/usr/bin/env python3
"""Find a UI element by text and tap it."""

import argparse
import json
import subprocess
import sys


def run_adb(args, serial=None):
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    cmd += args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except FileNotFoundError:
        print("Error: adb not found. Is Android SDK installed and on PATH?", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Error: adb command timed out", file=sys.stderr)
        sys.exit(1)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "no devices" in stderr or "not found" in stderr:
            print("Error: no Android device connected", file=sys.stderr)
        else:
            print(f"Error: adb failed: {stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def parse_content_provider(output):
    line = output.strip()
    prefix = "Row: 0 result="
    if not line.startswith(prefix):
        print(f"Error: unexpected response format: {line[:80]}", file=sys.stderr)
        sys.exit(1)
    json_str = line[len(prefix):]
    outer = json.loads(json_str)
    if outer.get("status") != "success":
        print(f"Error: query failed: {outer}", file=sys.stderr)
        sys.exit(1)
    return json.loads(outer["result"])


def parse_bounds(bounds_str):
    parts = [int(x.strip()) for x in bounds_str.split(",")]
    return parts[0], parts[1], parts[2], parts[3]


def center_of(bounds_str):
    l, t, r, b = parse_bounds(bounds_str)
    return (l + r) // 2, (t + b) // 2


def find_element(nodes, search_text, exact=False):
    """Recursively search tree for first element matching text."""
    for node in nodes:
        text = node.get("text", "")
        if text:
            if exact:
                if text == search_text:
                    return node
            else:
                if search_text.lower() in text.lower():
                    return node
        children = node.get("children", [])
        if children:
            found = find_element(children, search_text, exact=exact)
            if found:
                return found
    return None


def main():
    parser = argparse.ArgumentParser(description="Find UI element by text and tap it")
    parser.add_argument("text", help="Text to search for in UI elements")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--exact", action="store_true", help="Require exact text match")
    args = parser.parse_args()

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

    bounds = element.get("bounds", "")
    if not bounds:
        print(f"Error: element has no bounds: {element}", file=sys.stderr)
        sys.exit(1)

    cx, cy = center_of(bounds)
    text = element.get("text", "")
    class_name = element.get("className", "").rsplit(".", 1)[-1]

    run_adb(["shell", "input", "tap", str(cx), str(cy)], serial=args.serial)
    print(f"Tapped \"{text}\" ({class_name}) at ({cx}, {cy})")


if __name__ == "__main__":
    main()
