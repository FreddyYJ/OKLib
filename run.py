#! /usr/bin/env python3
import os
import sys
import json
import subprocess
from typing import List, Dict, Set, Tuple

# Config
SYSTEM_DIR_PATH_KEY = "system_dir_path"
SYSTEM_PACKAGE_PREFIX_KEY = "system_package_prefix"
TEST_CLASS_NAME_REGEX_KEY = "test_class_name_regex"
SPECIFIED_TEST_CLASS_LIST_KEY = "specified_test_class_list"
EXCLUDED_TEST_METHOD_LIST_KEY = "excluded_test_method_list"
OP_INTERFACE_CLASS_LIST_KEY = "op_interface_class_list"

INSTRUMENT_STATE_FIELDS_KEY = "instrument_state_fields"
INSTRUMENT_CLASS_ALLMETHODS_KEY = "instrument_class_allmethods"
EXCLUDE_CLASS_LIST_KEY = "exclude_class_list"
EXCLUDE_METHOD_LIST_KEY = "exclude_method_list"

TIME_WINDOW_LENGTH_IN_MILLIS_KEY = "time_window_length_in_millis"
ENABLE_FULL_INSTRUMENT_MODE_KEY = "enable_full_instrument_mode"
GENTRACE_INSTRUMENT_MODE_KEY = "gentrace_instrument_mode"

VERIFY_ABORT_AFTER_THREE_TEST_KEY = "verify_abort_after_three_test"
VERIFY_SURVIVOR_MODE_KEY = "verify_survivor_mode"

FORCE_INSTRUMENT_NOTHING_KEY = "force_instrument_nothing"
FORCE_TRACK_NO_STATES_KEY = "force_track_no_states"
FORCE_DISABLE_PROD_CHECKING_KEY = "force_disable_prod_checking"
FORCE_DISABLE_ENQUEUE_EVENTS_KEY = "force_disable_enqueue_events"
DUMP_SUPPRESS_INV_LIST_WHEN_CHECKING_KEY = "dump_suppress_inv_list_when_checking"

# Default values
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

def get_package_prefix(bugid: str):
  proj, bid = bugid.split("-")
  prefix = ""
  if proj == "Chart":
    prefix = "org.jfree."
  elif proj == "Closure":
    prefix = "com.google."
  elif proj == "Lang":
    prefix = "org.apache.commons.lang3."
  elif proj == "Math":
    prefix = "org.apache.commons.math3."
  elif proj == "Mockito":
    prefix = "org.mockito."
  elif proj == "Time":
    prefix = "org.joda.time."
  return prefix

def read_conf(conf_file: str) -> Dict[str, str]:
  result = dict()
  with open(conf_file, "r") as f:
    for line in f.readlines():
      line = line.strip()
      if line.startswith("#") or len(line) == 0:
        continue
      tokens = line.split("=", maxsplit=1)
      if len(tokens) != 2:
        result[tokens[0]] = ""
      else:
        result[tokens[0]] = tokens[1]
  return result

def write_conf(conf: Dict[str, str], conf_file: str):
  with open(conf_file, "w") as f:
    for k, v in conf.items():
      f.write(f"{k}={v}\n")

def init(bugid: str, buggy_dir: str):
  os.makedirs(buggy_dir, exist_ok=True)
  proj, bid = bugid.split("-")
  workdir = f"{buggy_dir}/{proj}-{bid}"
  execute(f"defects4j checkout -p {proj} -v {bid}b -w {workdir}", ROOTDIR)
  execute(f"defects4j compile", workdir)
  execute(f"defects4j test", workdir)
  execute(f"defects4j export -p dir.bin.classes -o {workdir}/builddir.txt", workdir)
  execute(f"defects4j export -p dir.bin.tests -o {workdir}/testbuilddir.txt", workdir)
  execute(f"defects4j export -p cp.test -o {workdir}/cp.txt", workdir)
  execute(f"defects4j export -p dir.src.classes -o {workdir}/srcdir.txt", workdir)
  execute(f"defects4j export -p tests.trigger -o tests.txt", workdir)
  execute(f"defects4j export -p classes.modified -o {workdir}/modified.txt", workdir)

def gentrace(bugid: str, work_dir: str):
  full_class_path = f"{OK_LIB}"
  with open(os.path.join(work_dir, "builddir.txt"), "r") as f:
    content = f.read().strip()
    full_class_path = f"{full_class_path}:{work_dir}/{content}"
  with open(os.path.join(work_dir, "testbuilddir.txt"), "r") as f:
    content = f.read().strip()
    full_class_path = f"{full_class_path}:{work_dir}/{content}"
  test_set = set()
  tests = list()
  with open(os.path.join(work_dir, "tests.txt"), "r") as f:
    for line in f.readlines():
      test = line.strip().split("::")[0]
      if test not in test_set:
        test_set.add(test)
        tests.append(test)
  # gentrace_test 
  diff_file_list = ""
  test_trace_prefix = f"{bugid}"
  with open(os.path.join(work_dir, "modified.txt"), "r") as f:
    for line in f.readlines():
      classname = line.strip()
      if '$' in classname:
        classname = classname[:classname.index('$')]
      filename = f"{classname.replace('.', '/')}.java"
      diff_file_list += f" {filename}"
  patchstate = "unpatched"
  conf_file_path = os.path.join(work_dir, "ok.properties")
  conf = read_conf(os.path.join(ROOTDIR, "conf", "samples", "d4j-sample.properties"))
  conf[SYSTEM_DIR_PATH_KEY] = work_dir
  conf[SYSTEM_PACKAGE_PREFIX_KEY] = get_package_prefix(bugid)
  write_conf(conf, conf_file_path)
  cmd = f"timeout 10m java -cp {full_class_path} -Xmx8g -Dok.testname={tests[0]} -Dok.invmode=dump " \
        f"-Dlog4j.configuration={LOG4J_CONF} -Dok.patchstate={patchstate} " \
        f"-Dok.conf={conf_file_path} -Dok.filediff=\"{diff_file_list}\" " \
        f"-Dok.ok_root_abs_path={ROOTDIR} -Dok.target_system_abs_path={work_dir} -Dok.test_trace_prefix={test_trace_prefix} " \
        f"-Dok.ticket_id={bugid} oathkeeper.engine.tester.TestEngine"
  execute(cmd, ROOTDIR)
  
def main(args: List[str]):
  print(f"Start {args}")
  bugid = args[1]
  # init
  buggy_dir = os.path.join(ROOTDIR, "buggy")
  init(bugid, buggy_dir)
  # gentrace
  work_dir = os.path.join(buggy_dir, bugid)
  gentrace(bugid, work_dir)
  # infer
  # verify

if __name__ == "__main__":
  main(sys.argv)