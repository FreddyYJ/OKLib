#! /usr/bin/env python3
import os
import sys
import json
import subprocess
from typing import List, Dict, Set, Tuple

ROOTDIR = os.path.abspath(os.path.dirname(__file__))
OK_LIB=f"{ROOTDIR}/target/OathKeeper-1.0-SNAPSHOT-jar-with-dependencies.jar"
LOG4J_CONF=f"{ROOTDIR}/conf/log4j.properties"
INV_OUT=f"{ROOTDIR}/inv_infer_output"
TRACE_OUT=f"{ROOTDIR}/trace_output"
CHECK_OUT=f"{ROOTDIR}/inv_checktrace_output"

def execute(cmd: str, dir: str) -> int:
  print(f"Executing: {cmd} @ {dir}")
  proc = subprocess.run(cmd, shell=True, cwd=dir)
  print(f"Exit code: {proc.returncode}")
  return proc.returncode

def init(ticket_file: str, buggy_dir: str):
  os.makedirs(buggy_dir, exist_ok=True)
  proj, bid = ticket_file.split("-")
  workdir = f"{buggy_dir}/{proj}-{bid}"
  execute(f"defects4j checkout -p {proj} -v {bid}b -w {workdir}", ROOTDIR)
  execute(f"defects4j export -p dir.bin.classes -o {workdir}/builddir.txt", workdir)
  execute(f"defects4j export -p cp.test -o {workdir}/cp.txt", workdir)
  execute(f"defects4j export -p dir.src.classes -o {workdir}/srcdir.txt", workdir)

def gentrace(ticket_file: str, work_dir: str):
  full_class_path = f"{OK_LIB}"
  with open(os.path.join(work_dir, "builddir.txt"), "r") as f:
    content = f.read().strip()
    full_class_path = f"{full_class_path}:{content}"
  
  

def main(args: List[str]):
  print(f"Start {args}")
  conf_file = args[1]
  ticket_file = args[2]
  # init
  buggy_dir = os.path.join(ROOTDIR, "buggy")
  init(ticket_file, buggy_dir)
  # gentrace
  work_dir = os.path.join(buggy_dir, ticket_file)
  # infer
  # verify

if __name__ == "__main__":
  main(sys.argv)