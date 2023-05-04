#! /usr/bin/env python3
import os
import sys
import json
import subprocess
import multiprocessing as mp
from typing import List, Dict, Set, Tuple

ROOTDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_bugids(filename: str) -> List[str]:
  l = list()
  if not os.path.exists(filename):
    return l
  with open(filename, "r") as f:
    for line in f.readlines():
      line = line.strip()
      if line == "" or line.startswith("#"):
        continue
      l.append(line.split(",")[0])
  return l

def execute(cmd: str, dir: str) -> int:
  print(f"Executing: {cmd} @ {dir}")
  proc = subprocess.run(cmd, shell=True, cwd=dir)
  print(f"Exit code: {proc.returncode}")
  return proc.returncode

def run(bugid: str):
  execute(f"python3 run.py {bugid}", ROOTDIR)

def main(args: List[str]):
  print(f"Start {args}")
  bug_file = os.path.join(ROOTDIR, "conf/samples/d4j-list.csv")
  bugids = get_bugids(bug_file)
  pool=mp.Pool(processes=(len(bugids)))
  for bugid in bugids:
    print(f"Start {bugid}")
    pool.apply_async(run, args=(bugid,))
  pool.close()
  pool.join()

if __name__ == "__main__":
  main(sys.argv)