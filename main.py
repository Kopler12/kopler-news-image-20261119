#!/usr/bin/env python3
"""make.fun entry runner: copy entry.png into the output directory.

Standard library only. The destination directory comes from the
MAKEFUN_OUTPUT_DIR environment variable (default: /output); the file is
copied byte-for-byte as entry.png, creating the directory if needed.
"""
import os
import shutil


def main():
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    dest_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copyfile(src, os.path.join(dest_dir, "entry.png"))


if __name__ == "__main__":
    main()
