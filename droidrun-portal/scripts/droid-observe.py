#!/usr/bin/env python3
"""Query Android a11y_tree and output a clean flat list of UI elements."""

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
    """Parse ContentProvider response: Row: 0 result=<JSON with status+result>"""
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
    """Parse bounds string 'left, top, right, bottom' into (l, t, r, b)."""
    parts = [int(x.strip()) for x in bounds_str.split(",")]
    return parts[0], parts[1], parts[2], parts[3]


def center_of(bounds_str):
    l, t, r, b = parse_bounds(bounds_str)
    return (l + r) // 2, (t + b) // 2


# Node classes that are just layout containers (no meaningful content on their own)
NOISE_CLASSES = {
    "View", "FrameLayout", "LinearLayout", "RelativeLayout",
    "ConstraintLayout", "CoordinatorLayout", "ViewGroup",
    "RecyclerView", "ScrollView", "HorizontalScrollView",
    "NestedScrollView", "ViewPager", "ViewPager2",
    "ComposeView", "AndroidComposeView",
}


def is_noise(node):
    """Return True if this node is a layout container with no meaningful text."""
    class_name = node.get("className", "")
    # Strip package prefix: android.widget.FrameLayout -> FrameLayout
    short_class = class_name.rsplit(".", 1)[-1] if "." in class_name else class_name
    if short_class not in NOISE_CLASSES:
        return False
    text = node.get("text", "")
    # If the text is just the class name or resourceId-like, it's noise
    if not text or text == short_class or text == class_name:
        return True
    # If text looks like an obfuscated resource ID, it's noise
    if "resource_name_obfuscated" in text or "0_resource" in text:
        return True
    return False


def walk_tree(nodes, results):
    """Recursively walk tree, collecting meaningful leaf/interactive elements."""
    for node in nodes:
        if not is_noise(node):
            results.append(node)
        children = node.get("children", [])
        if children:
            walk_tree(children, results)


def format_element(node):
    idx = node.get("index", "?")
    text = node.get("text", "")
    bounds = node.get("bounds", "")
    class_name = node.get("className", "")
    short_class = class_name.rsplit(".", 1)[-1] if "." in class_name else class_name
    resource_id = node.get("resourceId", "")

    parts = [f"[{idx}]"]
    if text:
        parts.append(f'"{text}"')
    if bounds:
        cx, cy = center_of(bounds)
        l, t, r, b = parse_bounds(bounds)
        parts.append(f"center=({cx},{cy})")
        parts.append(f"bounds=({l},{t},{r},{b})")
    parts.append(f"class={short_class}")
    if resource_id and "obfuscated" not in resource_id:
        # Show just the ID part after the last /
        short_id = resource_id.rsplit("/", 1)[-1] if "/" in resource_id else resource_id
        parts.append(f"id={short_id}")
    return " ".join(parts)


def get_phone_state(serial=None):
    output = run_adb(
        ["shell", "content", "query", "--uri",
         "content://com.droidrun.portal/phone_state"],
        serial=serial,
    )
    return parse_content_provider(output)


def main():
    parser = argparse.ArgumentParser(description="Query Android a11y_tree and show clean element list")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--phone-state", action="store_true", help="Also show current activity and keyboard status")
    parser.add_argument("--all", action="store_true", help="Include layout containers (noise nodes)")
    args = parser.parse_args()

    output = run_adb(
        ["shell", "content", "query", "--uri",
         "content://com.droidrun.portal/a11y_tree"],
        serial=args.serial,
    )
    tree = parse_content_provider(output)

    elements = []
    if args.all:
        # Flatten everything
        def walk_all(nodes):
            for node in nodes:
                elements.append(node)
                walk_all(node.get("children", []))
        walk_all(tree)
    else:
        walk_tree(tree, elements)

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
