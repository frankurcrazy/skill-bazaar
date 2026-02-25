#!/usr/bin/env python3
"""Poll a11y_tree until an element matching text appears."""

import argparse
import json
import subprocess
import sys
import time


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
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def parse_content_provider(output):
    if not output:
        return None
    line = output.strip()
    prefix = "Row: 0 result="
    if not line.startswith(prefix):
        return None
    json_str = line[len(prefix):]
    try:
        outer = json.loads(json_str)
        if outer.get("status") != "success":
            return None
        return json.loads(outer["result"])
    except (json.JSONDecodeError, KeyError):
        return None


def parse_bounds(bounds_str):
    parts = [int(x.strip()) for x in bounds_str.split(",")]
    return parts[0], parts[1], parts[2], parts[3]


def center_of(bounds_str):
    l, t, r, b = parse_bounds(bounds_str)
    return (l + r) // 2, (t + b) // 2


def find_element(nodes, search_text, exact=False):
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
    parser = argparse.ArgumentParser(description="Wait for UI element to appear")
    parser.add_argument("text", help="Text to search for in UI elements")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout in seconds (default: 10)")
    parser.add_argument("--exact", action="store_true", help="Require exact text match")
    args = parser.parse_args()

    start = time.time()
    attempt = 0
    while True:
        elapsed = time.time() - start
        if elapsed >= args.timeout:
            print(f"Timeout: \"{args.text}\" not found after {args.timeout}s", file=sys.stderr)
            sys.exit(1)

        attempt += 1
        output = run_adb(
            ["shell", "content", "query", "--uri",
             "content://com.droidrun.portal/a11y_tree"],
            serial=args.serial,
        )
        tree = parse_content_provider(output)
        if tree:
            element = find_element(tree, args.text, exact=args.exact)
            if element:
                text = element.get("text", "")
                bounds = element.get("bounds", "")
                class_name = element.get("className", "").rsplit(".", 1)[-1]
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
