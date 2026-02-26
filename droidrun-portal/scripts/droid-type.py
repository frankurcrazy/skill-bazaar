#!/usr/bin/env python3
"""Type text on Android device via droidrun-portal ContentProvider."""

import argparse
import base64

from droidutils import run_adb, ensure_screen_awake


def main():
    parser = argparse.ArgumentParser(description="Type text on Android device via ContentProvider")
    parser.add_argument("text", help="Text to type")
    parser.add_argument("-s", "--serial", help="Device serial number for adb -s")
    parser.add_argument("--clear", action="store_true", help="Clear the field before typing")
    parser.add_argument("--ensure-awake", action="store_true", help="Wake screen before action")
    args = parser.parse_args()

    if args.ensure_awake:
        ensure_screen_awake(serial=args.serial)

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
