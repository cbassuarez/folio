"""folio command-line interface."""
from __future__ import annotations
import argparse
import os
import shutil
import sys

TEMPLATES = os.path.join(os.path.dirname(__file__), "templates")


def cmd_init(args):
    dest = os.path.abspath(args.dir)
    if os.path.isdir(dest) and any(os.scandir(dest)):
        sys.exit(f"folio init: '{dest}' already exists and is not empty.")
    shutil.copytree(TEMPLATES, dest, dirs_exist_ok=True)
    print(f"Scaffolded a new packet at {dest}")
    print("Next:")
    print("  1. edit packet.yaml (identity, docs, works)")
    print("  2. put your score PDFs / audio in src/ and your prose in content/")
    print(f"  3. run:  folio build {args.dir}")


def cmd_build(args):
    from . import build as buildmod
    from .config import ConfigError
    try:
        out = buildmod.build(args.dir)
    except (ConfigError, FileNotFoundError, RuntimeError) as e:
        sys.exit(f"folio build: {e}")
    print(f"\nPacket assembled → {out}")


def main():
    p = argparse.ArgumentParser(
        prog="folio",
        description="Build a submission-ready PDF packet from a single manifest.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init", help="scaffold a new packet folder")
    pi.add_argument("dir", help="directory to create")
    pi.set_defaults(func=cmd_init)

    pb = sub.add_parser("build", help="build the packet in DIR (default: .)")
    pb.add_argument("dir", nargs="?", default=".", help="packet directory")
    pb.set_defaults(func=cmd_build)

    args = p.parse_args()
    args.func(args)
