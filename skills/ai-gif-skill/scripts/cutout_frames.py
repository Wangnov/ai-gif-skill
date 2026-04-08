#!/usr/bin/env python3

from __future__ import annotations

import sys

from ai_gif_skill.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["cutout-frames", *sys.argv[1:]]))
