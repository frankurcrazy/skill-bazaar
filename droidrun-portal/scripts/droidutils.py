"""Shared utilities for droidrun-portal scripts.

Improvements from droidrun library:
- Index-based O(1) element lookup
- Minimum size filtering
- Visibility threshold filtering
- Keyboard element filtering
- Retry logic with configurable attempts
- Clear point detection for overlapping elements
"""

import json
import subprocess
import sys
import time
from typing import Optional

# =============================================================================
# Constants
# =============================================================================

MIN_ELEMENT_SIZE = 5  # Minimum element size in pixels
VISIBILITY_THRESHOLD = 0.1  # 10% of element must be visible
MAX_RETRIES = 3
RETRY_DELAY = 0.5

# Node classes that are just layout containers (no meaningful content)
NOISE_CLASSES = {
    "View", "FrameLayout", "LinearLayout", "RelativeLayout",
    "ConstraintLayout", "CoordinatorLayout", "ViewGroup",
    "RecyclerView", "ScrollView", "HorizontalScrollView",
    "NestedScrollView", "ViewPager", "ViewPager2",
    "ComposeView", "AndroidComposeView",
}

# Keyboard element prefixes to filter out
KEYBOARD_PREFIXES = [
    "com.google.android.inputmethod",
    "com.android.inputmethod",
    "com.samsung.android.honeyboard",
]


# =============================================================================
# ADB Utilities
# =============================================================================

def ensure_screen_awake(serial=None):
    """Wake screen if it's off.

    Args:
        serial: Device serial number for adb -s
    """
    run_adb(["shell", "input", "keyevent", "KEYCODE_WAKEUP"], serial=serial, check=False)
    time.sleep(0.3)


def run_adb(args, serial=None, timeout=10, check=True):
    """Run an adb command and return stdout.

    Args:
        args: List of arguments to pass to adb
        serial: Device serial number for adb -s
        timeout: Command timeout in seconds
        check: If True, exit on error; if False, return None on error

    Returns:
        Command stdout, or None if check=False and command failed
    """
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    cmd += args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        if check:
            print("Error: adb not found. Is Android SDK installed and on PATH?", file=sys.stderr)
            sys.exit(1)
        return None
    except subprocess.TimeoutExpired:
        if check:
            print("Error: adb command timed out", file=sys.stderr)
            sys.exit(1)
        return None
    if result.returncode != 0:
        if check:
            stderr = result.stderr.strip()
            if "no devices" in stderr or "not found" in stderr:
                print("Error: no Android device connected", file=sys.stderr)
            else:
                print(f"Error: adb failed: {stderr}", file=sys.stderr)
            sys.exit(1)
        return None
    return result.stdout


def parse_content_provider(output, check=True):
    """Parse ContentProvider response: Row: 0 result=<JSON with status+result>

    Args:
        output: Raw adb output string
        check: If True, exit on error; if False, return None on error

    Returns:
        Parsed JSON result, or None if check=False and parsing failed
    """
    if not output:
        if check:
            print("Error: empty response from ContentProvider", file=sys.stderr)
            sys.exit(1)
        return None

    line = output.strip()
    prefix = "Row: 0 result="
    if not line.startswith(prefix):
        if check:
            print(f"Error: unexpected response format: {line[:80]}", file=sys.stderr)
            sys.exit(1)
        return None

    json_str = line[len(prefix):]
    try:
        outer = json.loads(json_str)
        if outer.get("status") != "success":
            if check:
                print(f"Error: query failed: {outer}", file=sys.stderr)
                sys.exit(1)
            return None
        return json.loads(outer["result"])
    except (json.JSONDecodeError, KeyError) as e:
        if check:
            print(f"Error: JSON parse failed: {e}", file=sys.stderr)
            sys.exit(1)
        return None


def query_tree_with_retry(serial=None, max_retries=MAX_RETRIES, delay=RETRY_DELAY, full=False):
    """Query a11y_tree with retry logic.

    Args:
        serial: Device serial number
        max_retries: Maximum number of attempts
        delay: Delay between retries in seconds
        full: If True, use a11y_tree_full with state properties

    Returns:
        Parsed tree (list), or None if all retries failed
    """
    uri = "content://com.droidrun.portal/a11y_tree_full" if full else "content://com.droidrun.portal/a11y_tree"

    for attempt in range(max_retries):
        output = run_adb(
            ["shell", "content", "query", "--uri", uri],
            serial=serial,
            check=False,
        )
        tree_data = parse_content_provider(output, check=False)
        if tree_data:
            # a11y_tree_full returns a single root dict, wrap and assign indices
            if full and isinstance(tree_data, dict):
                tree = [tree_data]
                counter = [1]
                def assign_indices(nodes):
                    for node in nodes:
                        node["index"] = counter[0]
                        counter[0] += 1
                        assign_indices(node.get("children", []))
                assign_indices(tree)
                return tree
            return tree_data
        if attempt < max_retries - 1:
            time.sleep(delay)
    return None


# =============================================================================
# Bounds Utilities
# =============================================================================

def parse_bounds(bounds):
    """Parse bounds into (l, t, r, b).

    Args:
        bounds: Either a string 'left, top, right, bottom' or
                a dict {'left': l, 'top': t, 'right': r, 'bottom': b}

    Returns:
        Tuple (left, top, right, bottom)
    """
    if isinstance(bounds, dict):
        return bounds["left"], bounds["top"], bounds["right"], bounds["bottom"]
    # String format: "left, top, right, bottom"
    parts = [int(x.strip()) for x in bounds.split(",")]
    return parts[0], parts[1], parts[2], parts[3]


def get_bounds(node):
    """Get bounds from node, handling both a11y_tree and a11y_tree_full formats.

    Returns:
        Bounds in consistent format, or empty string if not found
    """
    # a11y_tree format: "bounds" as string
    bounds = node.get("bounds", "")
    if bounds:
        return bounds
    # a11y_tree_full format: "boundsInScreen" as dict
    bounds_obj = node.get("boundsInScreen")
    if bounds_obj:
        return f"{bounds_obj['left']}, {bounds_obj['top']}, {bounds_obj['right']}, {bounds_obj['bottom']}"
    return ""


def center_of(bounds_str):
    """Get center point of bounds."""
    l, t, r, b = parse_bounds(bounds_str)
    return (l + r) // 2, (t + b) // 2


def get_element_size(bounds):
    """Get width and height of bounds."""
    l, t, r, b = parse_bounds(bounds)
    return r - l, b - t


# =============================================================================
# Filtering
# =============================================================================

def is_too_small(node, min_size=MIN_ELEMENT_SIZE):
    """Check if element is smaller than minimum size."""
    bounds = get_bounds(node)
    if not bounds:
        return False
    w, h = get_element_size(bounds)
    return w < min_size or h < min_size


def is_keyboard_element(node):
    """Check if element belongs to a keyboard."""
    resource_id = node.get("resourceId", "")
    return any(resource_id.startswith(p) for p in KEYBOARD_PREFIXES)


def is_visible(node, screen_width, screen_height, threshold=VISIBILITY_THRESHOLD):
    """Check if at least threshold% of element is visible on screen.

    Args:
        node: Element node with bounds
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        threshold: Minimum visible percentage (0.0 to 1.0)

    Returns:
        True if element is sufficiently visible
    """
    bounds = get_bounds(node)
    if not bounds:
        return True  # No bounds = assume visible

    l, t, r, b = parse_bounds(bounds)

    # Clip to screen
    vl = max(l, 0)
    vt = max(t, 0)
    vr = min(r, screen_width)
    vb = min(b, screen_height)

    if vr <= vl or vb <= vt:
        return False  # Completely off-screen

    visible_area = (vr - vl) * (vb - vt)
    total_area = (r - l) * (b - t)

    if total_area == 0:
        return False

    return (visible_area / total_area) >= threshold


def is_noise(node):
    """Return True if this node is a layout container with no meaningful text."""
    class_name = node.get("className", "")
    short_class = class_name.rsplit(".", 1)[-1] if "." in class_name else class_name
    if short_class not in NOISE_CLASSES:
        return False
    text = node.get("text", "")
    if not text or text == short_class or text == class_name:
        return True
    if "resource_name_obfuscated" in text or "0_resource" in text:
        return True
    return False


def should_filter(node, screen_width=None, screen_height=None,
                  filter_noise=True, filter_small=True,
                  filter_keyboard=True, filter_invisible=True):
    """Check if node should be filtered out.

    Args:
        node: Element node to check
        screen_width: Screen width (required for visibility check)
        screen_height: Screen height (required for visibility check)
        filter_noise: Filter layout containers
        filter_small: Filter tiny elements
        filter_keyboard: Filter keyboard elements
        filter_invisible: Filter off-screen elements

    Returns:
        True if node should be filtered out
    """
    if filter_noise and is_noise(node):
        return True
    if filter_small and is_too_small(node):
        return True
    if filter_keyboard and is_keyboard_element(node):
        return True
    if filter_invisible and screen_width and screen_height:
        if not is_visible(node, screen_width, screen_height):
            return True
    return False


# =============================================================================
# Tree Traversal
# =============================================================================

def walk_tree(nodes, results, **filter_kwargs):
    """Recursively walk tree, collecting elements that pass filters.

    Args:
        nodes: List of tree nodes
        results: List to append matching elements to
        **filter_kwargs: Arguments passed to should_filter()
    """
    for node in nodes:
        if not should_filter(node, **filter_kwargs):
            results.append(node)
        children = node.get("children", [])
        if children:
            walk_tree(children, results, **filter_kwargs)


def build_index(tree):
    """Build index->element dict for O(1) lookup.

    Args:
        tree: List of tree nodes

    Returns:
        Dict mapping index (int) to element node
    """
    index_map = {}

    def walk(nodes):
        for node in nodes:
            idx = node.get("index")
            if idx is not None:
                index_map[idx] = node
            walk(node.get("children", []))

    walk(tree)
    return index_map


def find_element(nodes, search_text, exact=False):
    """Recursively search tree for first element matching text.

    Args:
        nodes: List of tree nodes
        search_text: Text to search for
        exact: If True, require exact match; if False, substring match

    Returns:
        Matching node, or None if not found
    """
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


def find_element_by_index(tree, index):
    """Find element by index using O(1) lookup.

    Args:
        tree: List of tree nodes (will build index if needed)
        index: Element index to find

    Returns:
        Matching node, or None if not found
    """
    index_map = build_index(tree)
    return index_map.get(index)


# =============================================================================
# Clear Point Detection (from droidrun)
# =============================================================================

def find_clear_point(bounds, blockers, depth=0, max_depth=4):
    """Find unblocked tap point using quadrant subdivision.

    When an element is overlapped by other elements, this finds a point
    within the element's bounds that isn't blocked.

    Args:
        bounds: Tuple (l, t, r, b) of target element bounds
        blockers: List of (l, t, r, b) tuples for overlapping elements
        depth: Current recursion depth
        max_depth: Maximum recursion depth

    Returns:
        (x, y) tuple of clear point, or None if no clear point found
    """
    l, t, r, b = bounds
    cx, cy = (l + r) // 2, (t + b) // 2

    def is_blocked(x, y):
        for bl, bt, br, bb in blockers:
            if bl <= x <= br and bt <= y <= bb:
                return True
        return False

    # Check center point
    if not is_blocked(cx, cy):
        return (cx, cy)

    # Stop if too deep or area too small
    area = (r - l) * (b - t)
    if depth >= max_depth or area < 100:
        return None

    # Try quadrants
    quadrants = [
        (l, t, cx, cy),      # top-left
        (cx, t, r, cy),      # top-right
        (l, cy, cx, b),      # bottom-left
        (cx, cy, r, b),      # bottom-right
    ]

    for q in quadrants:
        point = find_clear_point(q, blockers, depth + 1, max_depth)
        if point:
            return point

    return None


def get_tap_point(element, tree=None):
    """Get the best tap point for an element, avoiding overlaps if possible.

    Args:
        element: Target element node
        tree: Full tree (optional, for finding overlapping elements)

    Returns:
        (x, y) tuple of tap point
    """
    bounds = get_bounds(element)
    if not bounds:
        return None

    l, t, r, b = parse_bounds(bounds)
    cx, cy = (l + r) // 2, (t + b) // 2

    # If no tree provided, just return center
    if not tree:
        return (cx, cy)

    # Find overlapping elements (elements that overlap but aren't ancestors/descendants)
    target_idx = element.get("index")
    blockers = []

    def find_overlaps(nodes):
        for node in nodes:
            idx = node.get("index")
            if idx == target_idx:
                continue

            node_bounds = node.get("bounds", "")
            if not node_bounds:
                continue

            nl, nt, nr, nb = parse_bounds(node_bounds)

            # Check if this element overlaps and is "above" (higher index = rendered later)
            if idx and target_idx and idx > target_idx:
                # Check for overlap
                if not (nr <= l or nl >= r or nb <= t or nt >= b):
                    blockers.append((nl, nt, nr, nb))

            find_overlaps(node.get("children", []))

    find_overlaps(tree)

    if not blockers:
        return (cx, cy)

    # Try to find a clear point
    clear = find_clear_point((l, t, r, b), blockers)
    return clear if clear else (cx, cy)


# =============================================================================
# Formatting
# =============================================================================

def short_class_name(class_name):
    """Get short class name without package prefix."""
    return class_name.rsplit(".", 1)[-1] if "." in class_name else class_name


def short_resource_id(resource_id):
    """Get short resource ID without package prefix."""
    if not resource_id or "obfuscated" in resource_id:
        return ""
    return resource_id.rsplit("/", 1)[-1] if "/" in resource_id else resource_id


def format_element(node, include_state=True):
    """Format element for display.

    Args:
        node: Element node dict
        include_state: If True, include checked/enabled/selected state
    """
    idx = node.get("index", "?")
    # Handle both text and contentDescription for a11y_tree_full
    text = node.get("text", "") or node.get("contentDescription", "")
    bounds = get_bounds(node)
    class_name = short_class_name(node.get("className", ""))
    resource_id = short_resource_id(node.get("resourceId", ""))

    parts = [f"[{idx}]"]
    if text:
        parts.append(f'"{text}"')
    if bounds:
        cx, cy = center_of(bounds)
        l, t, r, b = parse_bounds(bounds)
        parts.append(f"center=({cx},{cy})")
        parts.append(f"bounds=({l},{t},{r},{b})")
    parts.append(f"class={class_name}")
    if resource_id:
        parts.append(f"id={resource_id}")

    # Add state properties for interactive elements
    if include_state:
        states = []
        # Check for checked state (switches, checkboxes, radio buttons)
        # Handle both isChecked (full tree) and checked
        is_checkable = node.get("isCheckable")
        checked = node.get("isChecked")
        if checked is None:
            checked = node.get("checked")
        if is_checkable or checked is not None:
            if checked is not None:
                states.append(f"checked={str(checked).lower()}")
        # Check for enabled state
        enabled = node.get("isEnabled")
        if enabled is None:
            enabled = node.get("enabled")
        if enabled is False:
            states.append("enabled=false")
        # Check for selected state
        selected = node.get("isSelected") or node.get("selected")
        if selected:
            states.append("selected=true")
        # Check for focused state
        focused = node.get("isFocused") or node.get("focused")
        if focused:
            states.append("focused=true")
        if states:
            parts.append(f"[{', '.join(states)}]")

    return " ".join(parts)


def format_element_json(node):
    """Format element as JSON-serializable dict.

    Args:
        node: Element node dict

    Returns:
        Dict with standardized element properties
    """
    bounds = get_bounds(node)
    center = None
    if bounds:
        cx, cy = center_of(bounds)
        center = [cx, cy]

    # Handle both text and contentDescription
    text = node.get("text", "") or node.get("contentDescription", "")

    return {
        "index": node.get("index"),
        "text": text,
        "className": short_class_name(node.get("className", "")),
        "bounds": bounds,
        "center": center,
        "resourceId": short_resource_id(node.get("resourceId", "")),
        "checked": node.get("isChecked") if node.get("isChecked") is not None else node.get("checked"),
        "enabled": node.get("isEnabled") if node.get("isEnabled") is not None else node.get("enabled"),
        "selected": node.get("isSelected") or node.get("selected"),
        "focused": node.get("isFocused") or node.get("focused"),
        "clickable": node.get("isClickable") or node.get("clickable"),
    }


# =============================================================================
# Phone State
# =============================================================================

def get_phone_state(serial=None):
    """Query phone state (current app, keyboard, focused element)."""
    output = run_adb(
        ["shell", "content", "query", "--uri",
         "content://com.droidrun.portal/phone_state"],
        serial=serial,
    )
    return parse_content_provider(output)


def get_screen_size(serial=None):
    """Get screen dimensions from device.

    Returns:
        (width, height) tuple, or (1080, 1920) as default
    """
    output = run_adb(
        ["shell", "wm", "size"],
        serial=serial,
        check=False,
    )
    if output:
        # Output format: "Physical size: 1080x1920"
        for line in output.strip().split("\n"):
            if "size:" in line.lower():
                size_part = line.split(":")[-1].strip()
                if "x" in size_part:
                    w, h = size_part.split("x")
                    return int(w), int(h)
    return 1080, 1920  # Default fallback
