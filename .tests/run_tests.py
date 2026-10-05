#!/usr/bin/env python3
"""
Test runner for ICS 3U0 labs.

Press Ctrl+Shift+B in VS Code to run this, or run it directly.
It reads tests.json, runs main.py against each case, and reports pass or fail.
With --json it prints one JSON summary instead (used by the teacher's grader).
If tests.json has a "challenges" list, each optional challenge is tested after
the lab in its own section. Challenges never change the exit code.

Uses only the Python standard library. Nothing needs to be installed.
"""

import io
import json
import os
import re
import subprocess
import sys
import textwrap
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent   # the hidden .tests folder
FOLDER = HERE.parent                     # the lesson folder the student opens
TARGET = FOLDER / "main.py"             # swapped while a challenge is tested
TESTS = HERE / "tests.json"
TEMPLATE = HERE / "template.py"         # swapped while a challenge is tested

TIMEOUT = 5
RESULTS = {"lab": {}, "challenges": []}   # filled in for --json
WIDTH = 64
WRAP_AT = 80
HEADER_FIELDS = ["Name", "Purpose", "Author", "Created", "Updated"]
MUST_CHANGE = ["Purpose", "Author", "Created", "Updated"]

PAD = "  "          # left margin
BODY = " " * 8      # detail text, aligned under the test name
CODE = " " * 10     # numbered output lines


# ----------------------------------------------------------------------------
# Colour
# ----------------------------------------------------------------------------

def _enable_windows_ansi():
    if os.name != "nt":
        return True
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        return True
    except Exception:
        return False


USE_COLOUR = (
    not os.environ.get("NO_COLOR")
    and (os.environ.get("FORCE_COLOR") or sys.stdout.isatty())
    and _enable_windows_ansi()
)

CODES = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
}


def paint(text, *styles):
    if not USE_COLOUR or not styles:
        return text
    prefix = "".join(CODES[style] for style in styles if style in CODES)
    return "{}{}{}".format(prefix, text, CODES["reset"])


# Each detail line is (style_key, text). Styles map to colours here.
STYLE = {
    "label": ("dim",),
    "hint": ("dim",),
    "problem": ("yellow",),
    "want": ("green",),
    "got": ("red",),
    "error": ("red",),
    "plain": (),
}


def emit(style, text, indent=BODY, wrap=True):
    styles = STYLE.get(style, ())
    room = WRAP_AT - len(indent)
    if wrap and len(text) > room:
        lines = textwrap.wrap(text, width=room)
    else:
        lines = [text]
    for line in lines:
        print(indent + paint(line, *styles))


# ----------------------------------------------------------------------------
# Reading the student's file
# ----------------------------------------------------------------------------

def read_source():
    return TARGET.read_text(encoding="utf-8", errors="replace")


def header_range(src):
    """Line numbers (1-based) of the first and second #--- rule lines."""
    rules = []
    for i, line in enumerate(src.split("\n"), start=1):
        if re.match(r"^\s*#-{3,}", line):
            rules.append(i)
        if len(rules) == 2:
            return rules[0], rules[1]
    return None


def header_values(src):
    """Map each header field to the text written after its colon."""
    values = {field: "" for field in HEADER_FIELDS}
    for line in src.split("\n")[:25]:
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        body = stripped.lstrip("#").strip()
        for field in HEADER_FIELDS:
            if body.lower().startswith(field.lower() + ":"):
                values[field] = body[len(field) + 1:].strip()
    return values


def comment_lines(src):
    """Line numbers of real comments outside the header, or None if unparseable."""
    block = header_range(src)
    found = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(src).readline)
        for token in tokens:
            if token.type != tokenize.COMMENT:
                continue
            line_no = token.start[0]
            if block and block[0] <= line_no <= block[1]:
                continue
            if token.string.lstrip("#").strip():
                found.append(line_no)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    return found


# ----------------------------------------------------------------------------
# Comparing output
# ----------------------------------------------------------------------------

def normalize(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def expected_lines(expect):
    if isinstance(expect, list):
        lines = [str(item).rstrip() for item in expect]
        while lines and lines[-1] == "":
            lines.pop()
        return lines
    return normalize(str(expect))


def first_difference(expected, actual):
    for i in range(max(len(expected), len(actual))):
        got = actual[i] if i < len(actual) else None
        want = expected[i] if i < len(expected) else None
        if got != want:
            return i
    return None


def show_block(label, lines, style, mark=None):
    emit("label", label + ":", wrap=False)
    if not lines:
        emit("hint", "(nothing was printed)", indent=CODE, wrap=False)
        return
    for i, line in enumerate(lines):
        arrow = ">" if mark == i else " "
        emit(style, "{} {:>2} | {}".format(arrow, i + 1, line),
             indent=CODE, wrap=False)


# ----------------------------------------------------------------------------
# Running the program
# ----------------------------------------------------------------------------

def run_program(stdin_text):
    """Return (stdout, stderr, status). Status is 'ok', 'timeout' or 'crash'."""
    try:
        proc = subprocess.run(
            [sys.executable, str(TARGET)],
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            cwd=str(FOLDER),
        )
    except subprocess.TimeoutExpired:
        return "", "", "timeout"
    status = "ok" if proc.returncode == 0 else "crash"
    return proc.stdout, proc.stderr, status


def target_name():
    """The file under test, as the student sees it (main.py, challenges/...)."""
    return TARGET.relative_to(FOLDER).as_posix()


def tidy_error(stderr):
    """Drop the runner's own frames and shorten the path to the file name."""
    text = stderr.replace(str(TARGET), target_name()).replace(str(FOLDER) + os.sep, "")
    lines = [line.rstrip() for line in text.strip().split("\n") if line.strip()]
    return lines[-5:]


# ----------------------------------------------------------------------------
# The three kinds of check
# ----------------------------------------------------------------------------

def template_values():
    """Header values as shipped, so untouched fields can be spotted."""
    if not TEMPLATE.exists():
        return {}
    return header_values(TEMPLATE.read_text(encoding="utf-8", errors="replace"))


def check_header(case, src):
    values = header_values(src)

    blank = [field for field in HEADER_FIELDS if not values[field]]
    if blank:
        emit("problem", "Still blank: {}".format(", ".join(blank)))
        emit("hint", "Fill in every field at the top of {}.".format(target_name()))
        return False

    if values["Name"].lower() in ("your name", "name"):
        emit("problem", "Name should be the name of the program, not your own name.")
        return False

    shipped = template_values()
    stale = [field for field in MUST_CHANGE
             if shipped.get(field)
             and values[field].strip().lower() == shipped[field].strip().lower()]
    if stale:
        for field in stale:
            emit("problem", "{} still says \"{}\".".format(field, values[field]))
        emit("hint", "Replace the template's information with your own.")
        return False

    return True


def check_comments(case, src):
    minimum = case.get("min", 1)
    found = comment_lines(src)
    if found is None:
        emit("problem", "Could not read {}.".format(target_name()))
        emit("hint", "Fix the errors in your code first, then run the tests again.")
        return False
    if len(found) < minimum:
        emit("problem", "Found {} comment(s) below the header, expected at least {}."
             .format(len(found), minimum))
        emit("hint", "A comment starts with # and runs to the end of the line.")
        return False
    return True


def check_output(case, src):
    stdin_text = case.get("stdin", "")
    if isinstance(stdin_text, list):
        stdin_text = "\n".join(str(item) for item in stdin_text)
    if stdin_text and not stdin_text.endswith("\n"):
        stdin_text += "\n"

    stdout, stderr, status = run_program(stdin_text)

    if status == "timeout":
        emit("problem", "Your program ran for more than {} seconds and was stopped."
             .format(TIMEOUT))
        emit("hint", "Check for a loop that never ends, or an input() with nothing to read.")
        return False

    if status == "crash":
        emit("problem", "Your program stopped with an error:")
        for line in tidy_error(stderr):
            emit("error", line, indent=CODE, wrap=False)
        return False

    expected = expected_lines(case.get("expect", ""))
    actual = normalize(stdout)

    if actual == expected:
        return True

    index = first_difference(expected, actual)
    show_block("Expected", expected, "want", mark=index)
    show_block("Your output", actual, "got", mark=index)
    if index is not None:
        emit("hint", "First difference is on line {}.".format(index + 1))
    return False


# Runs in a separate Python process: loads the student's file (hiding anything
# it prints), calls one function, and reports the result as JSON.
FUNCTION_HARNESS = r"""
import contextlib, io, json, math, os, runpy, sys, traceback
path, func, args, expect = sys.argv[1], sys.argv[2], json.loads(sys.argv[3]), sys.argv[4]
as_tuple = sys.argv[5] == "tuple"
report = {}

def same(got, wanted):
    # Equal values of the same kind. Numbers match to 9 decimal places.
    if isinstance(got, bool) or isinstance(wanted, bool):
        return type(got) is type(wanted) and got == wanted
    numbers = (int, float)
    if isinstance(got, numbers) and isinstance(wanted, numbers):
        return math.isclose(got, wanted, rel_tol=1e-9, abs_tol=1e-9)
    if isinstance(wanted, (list, tuple)):
        return (type(got) is type(wanted) and len(got) == len(wanted)
                and all(same(g, w) for g, w in zip(got, wanted)))
    if isinstance(wanted, dict):
        return (type(got) is dict and got.keys() == wanted.keys()
                and all(same(got[k], wanted[k]) for k in wanted))
    return type(got) is type(wanted) and got == wanted

def pass_only():
    pass

def describe(error):
    lines = [f.lineno for f in traceback.extract_tb(error.__traceback__)
             if os.path.abspath(f.filename) == os.path.abspath(path)]
    where = " (line {})".format(lines[-1]) if lines else ""
    return "{}: {}{}".format(type(error).__name__, error, where)

names = None
try:
    with contextlib.redirect_stdout(io.StringIO()):
        names = runpy.run_path(path, run_name="__tests__")
except BaseException as error:
    report["load_error"] = describe(error)

if names is not None:
    target = names.get(func)
    if not callable(target):
        report["missing"] = True
    else:
        report["not_started"] = target.__code__.co_code == pass_only.__code__.co_code
        if expect != "--probe":
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    result = target(*args)
                wanted = json.loads(expect)
                if as_tuple:
                    wanted = tuple(wanted)
                report["ok"] = same(result, wanted)
                report["got"] = repr(result)
                report["got_type"] = type(result).__name__
            except BaseException as error:
                report["error"] = describe(error)
print(json.dumps(report))
"""


def call_function(func, args, expect="--probe", as_tuple=False):
    """Return the harness report as a dict, or {'timeout': True}."""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", FUNCTION_HARNESS, str(TARGET), func,
             json.dumps(args), expect, "tuple" if as_tuple else ""],
            input="", capture_output=True, text=True,
            timeout=TIMEOUT, cwd=str(FOLDER),
        )
    except subprocess.TimeoutExpired:
        return {"timeout": True}
    try:
        return json.loads(proc.stdout.strip().split("\n")[-1])
    except (ValueError, IndexError):
        return {"error": (proc.stderr.strip().split("\n") or ["Unknown error"])[-1]}


TYPE_WORDS = {"str": "text", "int": "a whole number", "float": "a decimal number",
              "bool": "True/False", "NoneType": "nothing (None)",
              "list": "a list", "tuple": "a tuple", "dict": "a dictionary"}
NUMBER_TYPES = ("int", "float")


def check_function(case, src):
    func = case["function"]
    args = case.get("args", [])
    as_tuple = case.get("expect_tuple", False)
    wanted = case.get("expect")
    if as_tuple:
        wanted = tuple(wanted)
    call = "{}({})".format(func, ", ".join(repr(a) for a in args))

    report = call_function(func, args, json.dumps(wanted), as_tuple)
    if report.get("timeout"):
        emit("problem", "{} ran for more than {} seconds and was stopped."
             .format(call, TIMEOUT))
        return False
    if report.get("load_error"):
        emit("problem", "{} stopped with an error before {} could be tested:"
             .format(target_name(), func))
        emit("error", report["load_error"], indent=CODE)
        return False
    if report.get("error"):
        emit("problem", "{} stopped with an error:".format(call))
        emit("error", report["error"], indent=CODE)
        return False
    if report.get("missing"):
        emit("problem", "Could not find a function named {}.".format(func))
        emit("hint", "Do not rename the def line.")
        return False
    if report.get("ok"):
        return True

    got_type = report.get("got_type", "")
    emit("label", "Called:", wrap=False)
    emit("plain", call, indent=CODE, wrap=False)
    emit("label", "Expected it to return:", wrap=False)
    emit("want", repr(wanted), indent=CODE, wrap=False)
    emit("label", "It returned:", wrap=False)
    emit("got", report.get("got", "?"), indent=CODE, wrap=False)
    if got_type == "NoneType":
        emit("hint", "Nothing was returned. Use return, not print.")
    elif (got_type != type(wanted).__name__
          and not (got_type in NUMBER_TYPES and type(wanted).__name__ in NUMBER_TYPES)):
        emit("hint", "Right value, wrong type? Expected {}, got {}.".format(
            TYPE_WORDS.get(type(wanted).__name__, type(wanted).__name__),
            TYPE_WORDS.get(got_type, got_type)))
    return False


def check_runs(case, src):
    """The program finishes without crashing, given the sample input."""
    stdin_text = case.get("stdin", "")
    if isinstance(stdin_text, list):
        stdin_text = "\n".join(str(item) for item in stdin_text)
    if stdin_text and not stdin_text.endswith("\n"):
        stdin_text += "\n"
    stdout, stderr, status = run_program(stdin_text)
    if status == "timeout":
        emit("problem", "Your program ran for more than {} seconds and was stopped."
             .format(TIMEOUT))
        emit("hint", "Check for a loop that never ends, or an input() with nothing to read.")
        return False
    if status == "crash":
        emit("problem", "Your program stopped with an error:")
        for line in tidy_error(stderr):
            emit("error", line, indent=CODE, wrap=False)
        if case.get("stdin"):
            emit("hint", "It was given this input, one line at a time: {}".format(
                ", ".join(str(item) for item in case["stdin"])
                if isinstance(case["stdin"], list) else case["stdin"]))
        return False
    return True


def check_uses(case, src):
    """The code uses each listed Python word (keywords or names, not comments)."""
    words = case.get("words", [])
    found = set()
    try:
        for token in tokenize.generate_tokens(io.StringIO(src).readline):
            if token.type == tokenize.NAME:
                found.add(token.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        emit("problem", "Could not read {}.".format(target_name()))
        emit("hint", "Fix the errors in your code first, then run the tests again.")
        return False
    missing = [word for word in words if word not in found]
    if missing:
        emit("problem", "Your code does not use: {}".format(", ".join(missing)))
        return False
    return True


CHECKS = {
    "runs": check_runs,
    "uses": check_uses,
    "header": check_header,
    "comments": check_comments,
    "output": check_output,
    "function": check_function,
}

DEFAULT_NAMES = {
    "header": "Header is filled in",
    "comments": "Code is commented",
    "output": "Output is correct",
    "function": "Function returns the right value",
    "runs": "Runs without crashing",
    "uses": "Uses the required code",
}


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def rule():
    print(PAD + paint("-" * WIDTH, "dim"))


def run_cases(cases, src):
    """Run each case and print its verdict. Return (passed, failed_numbers)."""
    passed = 0
    failed_numbers = []
    record = []

    for number, case in enumerate(cases, start=1):
        kind = case.get("type", "output")
        check = CHECKS.get(kind)
        name = case.get("name", DEFAULT_NAMES.get(kind, kind))

        if check is None:
            print(PAD + paint("FAIL", "bold", "red") + "  " + name)
            emit("problem", "Unknown test type '{}' in tests.json.".format(kind))
            failed_numbers.append(number)
            record.append({"name": name, "passed": False})
            print()
            continue

        # Capture the detail lines so the verdict can be printed first.
        buffer = io.StringIO()
        real_stdout = sys.stdout
        sys.stdout = buffer
        try:
            result = check(case, src)
        finally:
            sys.stdout = real_stdout

        label = "{}. {}".format(number, name)
        if result:
            print(PAD + paint("PASS", "bold", "green") + "  " + paint(label, "dim"))
        else:
            print(PAD + paint("FAIL", "bold", "red") + "  " + paint(label, "bold"))
        detail = buffer.getvalue()
        if detail.strip():
            print(detail.rstrip("\n"))
        if result:
            passed += 1
        else:
            failed_numbers.append(number)
        record.append({"name": name, "passed": bool(result)})
        print()

    RESULTS["last_cases"] = record
    return passed, failed_numbers


def same_code(a, b):
    """True if two sources match, ignoring line endings and trailing spaces."""
    return normalize(a) == normalize(b)


def run_challenges(challenges):
    """Test each optional challenge. Results are reported but never fail the lab."""
    global TARGET, TEMPLATE

    print()
    print(PAD + paint("OPTIONAL CHALLENGES", "bold", "yellow"))
    print(PAD + paint("Extra practice. These do not affect your lab result.", "yellow"))
    rule()
    print()

    lab_target, lab_template = TARGET, TEMPLATE
    try:
        for challenge in challenges:
            rel = challenge.get("file", "")
            TARGET = FOLDER / rel
            TEMPLATE = HERE / challenge.get("template", rel)
            title = challenge.get("title", rel)

            print(PAD + paint(title, "bold", "cyan") + "  " + paint("(" + rel + ")", "dim"))
            print()
            entry = {"title": title, "status": "not started", "passed": 0,
                     "total": len(challenge.get("cases", []))}
            RESULTS["challenges"].append(entry)

            if not TARGET.exists():
                print(PAD + paint("SKIP", "bold", "yellow") + "  " +
                      paint("Could not find {}.".format(rel), "dim"))
                print()
                continue

            src = read_source()
            shipped = (TEMPLATE.read_text(encoding="utf-8", errors="replace")
                       if TEMPLATE.exists() else None)
            not_started = shipped is not None and same_code(src, shipped)
            func = challenge.get("function")
            if func and not not_started:
                # A function still holding only 'pass' has not been started.
                probe = call_function(func, [])
                if probe.get("load_error"):
                    print(PAD + paint("FAIL", "bold", "red") + "  " + paint(
                        "{} stopped with an error, so this challenge could not be tested:"
                        .format(rel), "bold"))
                    emit("error", probe["load_error"], indent=CODE)
                    emit("hint", "Fix that line, then run the tests again.")
                    print()
                    entry["status"] = "error"
                    continue
                not_started = probe.get("not_started", False)
            if not_started:
                if func:
                    hint = "Not started. Find def {} in {} to try it.".format(func, rel)
                else:
                    hint = "Not started. Open {} to try it.".format(rel)
                print(PAD + paint("SKIP", "bold", "yellow") + "  " + paint(hint, "dim"))
                print()
                continue

            cases = challenge.get("cases", [])
            passed, failed_numbers = run_cases(cases, src)
            total = len(cases)
            entry["passed"] = passed
            entry["status"] = "complete" if passed == total else "incomplete"
            if passed == total:
                print(PAD + paint("Challenge complete: {} of {} tests passed."
                                  .format(passed, total), "bold", "green"))
            else:
                print(PAD + paint("{} of {} tests passed. Still to fix: test {}".format(
                    passed, total, ", ".join(str(n) for n in failed_numbers)), "yellow"))
            print()
    finally:
        TARGET, TEMPLATE = lab_target, lab_template

    rule()
    print()


def main():
    if not TARGET.exists():
        print(PAD + paint("Could not find main.py next to this script.", "red"))
        return 1
    if not TESTS.exists():
        print(PAD + paint("Could not find tests.json next to this script.", "red"))
        return 1

    try:
        data = json.loads(TESTS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(PAD + paint("tests.json is not valid JSON: {}".format(error), "red"))
        return 1

    cases = data.get("cases", [])
    src = read_source()
    title = data.get("title", FOLDER.name)

    print()
    print(PAD + paint(title, "bold", "cyan"))
    rule()
    print()

    passed, failed_numbers = run_cases(cases, src)
    RESULTS["lab"] = {"title": title, "passed": passed, "total": len(cases),
                      "complete": passed == len(cases),
                      "cases": RESULTS.pop("last_cases", [])}

    rule()
    total = len(cases)
    if passed == total:
        print(PAD + paint("{} of {} tests passed.".format(passed, total), "bold", "green"))
        print(PAD + paint("All tests passed. Save your work.", "green"))
    else:
        print(PAD + paint("{} of {} tests passed.".format(passed, total), "bold", "red"))
        print(PAD + paint("Still to fix: test {}".format(
            ", ".join(str(n) for n in failed_numbers)), "dim"))
    print()

    challenges = data.get("challenges", [])
    if challenges:
        run_challenges(challenges)

    return 0 if passed == total else 1


def main_json():
    """Run everything quietly, then print one JSON summary."""
    global USE_COLOUR
    USE_COLOUR = False
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        code = main()
    finally:
        sys.stdout = real_stdout
    RESULTS.pop("last_cases", None)
    RESULTS["exit"] = code
    print(json.dumps(RESULTS))
    return code


if __name__ == "__main__":
    sys.exit(main_json() if "--json" in sys.argv[1:] else main())
