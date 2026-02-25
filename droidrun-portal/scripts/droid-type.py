#!/usr/bin/env python3
"""Type text on Android device via droidrun-portal ContentProvider."""

import argparse
import base64
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


def main():
    parser = argparse.ArgumentParser(description="Type text on Android device via ContentProvider")
    parser.add_argument("text", help="Text to type")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--clear", action="store_true", help="Clear the field before typing")
    args = parser.parse_args()

    encoded = base64.b64encode(args.text.encode("utf-8")).decode("ascii")
    clear_val = "true" if args.clear else "false"

    run_adb(
        ["shell", "content", "insert", "--uri",
         "content://com.droidrun.portal/keyboard/input",
         "--bind", f"base64_text:s:{encoded}",
         "--bind", f"clear:b:{clear_val}"],
        serial=args.serial,
    )
    action = "Cleared and typed" if args.clear else "Typed"
    print(f'{action}: "{args.text}"')


if __name__ == "__main__":
    main()
