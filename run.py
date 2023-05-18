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
D4J_DIR=f"{ROOTDIR}/d4j"
FULL_CLASS_PATH = ""

def execute(cmd: str, dir: str) -> int:
  print(f"Executing: {cmd} @ {dir}")
  proc = subprocess.run(cmd, shell=True, cwd=dir)
  print(f"Exit code: {proc.returncode}")
  return proc.returncode

def get_package_prefix(bugid: str) -> Tuple[str, str]:
  proj, bid = bugid.split("-")
  prefix = ".*"
  test_regex = ""
  if proj == "Chart":
    prefix = "org.jfree."
    test_regex = ".*Tests$"
  elif proj == "Closure":
    prefix = "com.google."
    test_regex = ".*(Test|TestCase)$"
  elif proj == "Lang":
    prefix = "org.apache.commons.lang3."
    test_regex = ".*Test$"
  elif proj == "Math":
    prefix = "org.apache.commons.math3."
    test_regex = ".*Test$"
  elif proj == "Mockito":
    prefix = "org.mockito."
    test_regex = ".*Test$"
  elif proj == "Time":
    prefix = "org.joda.time."
    test_regex = "^Test.*"
  return prefix, test_regex

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

def init(bugid: str, workdir: str, is_fixed: bool):
  os.makedirs(workdir, exist_ok=True)
  proj, bid = bugid.split("-")
  # workdir = f"{buggy_dir}/{proj}-{bid}"
  version = bid
  if is_fixed:
    version = f"{bid}f"
  else:
    version = f"{bid}b"
  savedir = f"{D4J_DIR}/{bugid}"
  os.makedirs(savedir, exist_ok=True)
  execute(f"defects4j checkout -p {proj} -v {version} -w {workdir}", ROOTDIR)
  execute(f"defects4j compile", workdir)
  execute(f"defects4j test", workdir)
  if is_fixed:
    execute(f"defects4j export -p dir.bin.classes -o {savedir}/builddir.txt", workdir)
    execute(f"defects4j export -p dir.bin.tests -o {savedir}/testbuilddir.txt", workdir)
    execute(f"defects4j export -p cp.test -o {savedir}/cp.txt", workdir)
    execute(f"defects4j export -p dir.src.classes -o {savedir}/srcdir.txt", workdir)
    execute(f"defects4j export -p tests.trigger -o {savedir}/tests.txt", workdir)
    execute(f"defects4j export -p classes.modified -o {savedir}/modified.txt", workdir)

def gentrace(bugid: str, work_dir: str):
  print("################## Generating traces...")
  init(bugid, work_dir, True)
  proj, bid = bugid.split("-")
  full_class_path = f"{OK_LIB}"
  savedir = f"{D4J_DIR}/{bugid}"
  with open(os.path.join(savedir, "builddir.txt"), "r") as f:
    content = f.read().strip()
    full_class_path = f"{full_class_path}:{work_dir}/{content}"
  with open(os.path.join(savedir, "testbuilddir.txt"), "r") as f:
    content = f.read().strip()
    full_class_path = f"{full_class_path}:{work_dir}/{content}"
  global FULL_CLASS_PATH
  FULL_CLASS_PATH = full_class_path
  test_dict = dict()
  tests = list()
  test_all = list()
  test_class = ""
  test_method = ""
  with open(os.path.join(savedir, "tests.txt"), "r") as f:
    for line in f.readlines():
      test_all.append(line.strip())
      test = line.strip().split("::")[0]
      if test not in test_dict:
        test_class = test
        test_method = line.strip().split("::")[1]
        break
        test_dict[test] = list()
        tests.append(test)
      test_dict[test].append(line.strip().split("::")[1])
  # gentrace_test 
  diff_file_list = ""
  test_trace_prefix = f"{bugid}"
  with open(os.path.join(savedir, "modified.txt"), "r") as f:
    for line in f.readlines():
      classname = line.strip()
      if '$' in classname:
        classname = classname[:classname.index('$')]
      filename = f"{classname.replace('.', '/')}.java"
      diff_file_list += f" {filename}"
  conf_file_path = os.path.join(savedir, "ok.properties")
  conf = read_conf(os.path.join(ROOTDIR, "conf", "samples", "d4j-sample.properties"))
  conf[SYSTEM_DIR_PATH_KEY] = work_dir
  prefix, test_regex = get_package_prefix(bugid)
  conf[SYSTEM_PACKAGE_PREFIX_KEY] = prefix
  conf[TEST_CLASS_NAME_REGEX_KEY] = test_regex
  # conf[TEST_CLASS_NAME_REGEX_KEY] = f"[{'|'.join(tests)}]"
  write_conf(conf, conf_file_path)
  patchstate = "patched"
  cmd = f"timeout 60m java -cp {FULL_CLASS_PATH} -Xmx8g -Dok.testname={test_class} -Dok.testmethod={test_method} -Dok.invmode=dump " \
        f"-Dlog4j.configuration={LOG4J_CONF} -Dok.patchstate={patchstate} " \
        f"-Dok.conf={conf_file_path} -Dok.filediff=\"{diff_file_list}\" " \
        f"-Dok.ok_root_abs_path={ROOTDIR} -Dok.target_system_abs_path={work_dir} -Dok.test_trace_prefix={test_trace_prefix} " \
        f"-Dok.ticket_id={bugid} oathkeeper.engine.tester.TestEngine"
  execute(cmd, ROOTDIR)
  # git reset --hard
  init(bugid, work_dir, False)
  patchstate = "unpatched"
  cmd = f"timeout 60m java -cp {FULL_CLASS_PATH} -Xmx8g -Dok.testname={test_class} -Dok.testmethod={test_method} -Dok.invmode=dump " \
        f"-Dlog4j.configuration={LOG4J_CONF} -Dok.patchstate={patchstate} " \
        f"-Dok.conf={conf_file_path} -Dok.filediff=\"{diff_file_list}\" " \
        f"-Dok.ok_root_abs_path={ROOTDIR} -Dok.target_system_abs_path={work_dir} -Dok.test_trace_prefix={test_trace_prefix} " \
        f"-Dok.ticket_id={bugid} oathkeeper.engine.tester.TestEngine"
  execute(cmd, ROOTDIR)

def infer(bugid: str, work_dir: str):
  print("################ Infer")
  savedir = f"{D4J_DIR}/{bugid}"
  test_class = ""
  test_method = ""
  with open(os.path.join(savedir, "tests.txt"), "r") as f:
    for line in f.readlines():
      test = line.strip().split("::")[0]
      test_class = test
      test_method = line.strip().split("::")[1]

  test_trace_prefix = f"{bugid}"
  conf_file_path = os.path.join(savedir, "ok.properties")
  cmd = f"timeout 60m java -cp {FULL_CLASS_PATH} -Dok.conf={conf_file_path} -Dok.ok_root_abs_path={ROOTDIR} " \
        f"-Dok.target_system_abs_path={work_dir} -Dok.ticket_id={bugid} " \
        f"-Dok.template_version= " \
        f"oathkeeper.engine.InferEngine {test_class}"
  execute(cmd, ROOTDIR)

def verify(bugid: str, work_dir: str):
  print("########################## Verify")
  savedir = f"{D4J_DIR}/{bugid}"
  test_class = ""
  test_method = ""
  test_dict = dict()
  tests = list()
  test_all = list()
  with open(os.path.join(savedir, "tests.txt"), "r") as f:
    for line in f.readlines():
      test_all.append(line.strip())
      test = line.strip().split("::")[0]
      if test not in test_dict:
        test_class = test
        test_method = line.strip().split("::")[1]
        break
  test_trace_prefix = f"{bugid}"
  conf_file_path = os.path.join(savedir, "ok.properties")
  cmd = f"timeout 60m java -cp {FULL_CLASS_PATH} -Dlog4j.configuration={LOG4J_CONF} " \
        f"-Dok.conf={conf_file_path} -Dok.ok_root_abs_path={ROOTDIR} -Dok.patchstate=patched " \
        f"-Dok.invfile={test_class} -Dok.invmode=verify -Dok.testmethod={test_method} -Dok.target_system_abs_path={work_dir} " \
        f"-Dok.ticket_id={bugid} -Dok.verify_test_package= " \
        f"oathkeeper.engine.tester.TestEngine {test_class}"
  execute(cmd, ROOTDIR)

def main(args: List[str]):
  print(f"Start {args}")
  bugid = args[1]
  # init
  buggy_dir = os.path.join(ROOTDIR, "buggy")
  # gentrace
  work_dir = os.path.join(buggy_dir, bugid)
  gentrace(bugid, work_dir)
  # infer
  infer(bugid, work_dir)
  # verify
  verify(bugid, work_dir)


if __name__ == "__main__":
  main(sys.argv)