#!/usr/bin/env python3
"""Coverage-guided fuzzer for CS 182 Phase 2."""

import argparse
import os
import random
import sys
import traceback
from pathlib import Path

try:
    import coverage
except ImportError:
    sys.exit("pip install coverage")

ALPHANUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
BOUNDS = [0, 1, -1, 2, 10, 100, 1000, -1000]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("program")
    p.add_argument("corpus")
    p.add_argument("--budget", type=int, default=15000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--random", action="store_true")
    return p.parse_args()


def input_type(path):
    with open(path) as f:
        line = f.readline().strip()
    return line.split(": ", 1)[1] if line.startswith("# input: ") else "str"


def parse(raw, typ):
    raw = raw.strip()
    if typ == "int":
        return int(raw) if raw else 0
    if typ == "ints":
        return [int(x) for x in raw.split()] if raw else []
    return raw


def fmt(val, typ):
    return " ".join(map(str, val)) if typ == "ints" else str(val)


def mut_int(v, rng):
    op = rng.choice("add neg bound digit rand".split())
    if op == "add":
        d = rng.choice([i for i in range(-16, 17) if i])
        return v + d
    if op == "neg":
        return -v
    if op == "bound":
        return rng.choice(BOUNDS)
    if op == "digit":
        s = str(v)
        if not s or s[0] == "-":
            return v
        i = rng.randrange(len(s))
        return int(s[:i] + str(rng.randint(0, 9)) + s[i + 1:])
    return rng.randint(-10000, 10000)


def mut_str(s, rng):
    op = rng.choice("rep ins del".split())
    if not s and op == "del":
        op = "ins"
    if op == "rep" and s:
        i = rng.randrange(len(s))
        return s[:i] + rng.choice(ALPHANUM) + s[i + 1:]
    if op == "ins":
        i = rng.randrange(len(s) + 1)
        return s[:i] + rng.choice(ALPHANUM) + s[i:]
    if s:
        i = rng.randrange(len(s))
        return s[:i] + s[i + 1:]
    return s


def mut_ints(lst, rng):
    if not lst:
        return [rng.randint(-100, 100)]
    op = rng.choice("elem ins del swap".split())
    lst = lst[:]
    if op == "elem":
        i = rng.randrange(len(lst))
        lst[i] = mut_int(lst[i], rng)
    elif op == "ins":
        lst.insert(rng.randrange(len(lst) + 1), rng.randint(-1000, 1000))
    elif op == "del":
        del lst[rng.randrange(len(lst))]
    elif len(lst) >= 2:
        i, j = rng.sample(range(len(lst)), 2)
        lst[i], lst[j] = lst[j], lst[i]
    return lst


def mutate(val, typ, rng):
    for _ in range(rng.randint(1, 3)):
        val = {"int": mut_int, "str": mut_str, "ints": mut_ints}[typ](val, rng)
    return val


def gen_random(typ, rng):
    if typ == "int":
        return rng.randint(-10000, 10000)
    if typ == "str":
        return "".join(rng.choice(ALPHANUM) for _ in range(rng.randint(1, 10)))
    return [rng.randint(-1000, 1000) for _ in range(rng.randint(1, 10))]


def run(prog, inp):
    prog = os.path.abspath(prog)
    cov = coverage.Coverage(source=[os.path.dirname(prog)], branch=False, data_file=None)
    cov.start()
    exc = None
    lines = set()
    try:
        tokens = inp.split() if inp else []
        old = sys.argv[:]
        sys.argv = [os.path.basename(prog)] + tokens
        with open(prog) as f:
            exec(compile(f.read(), prog, "exec"), {"__name__": "__main__", "__file__": prog})
    except SystemExit:
        pass
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        ln = next((fr.lineno for fr in reversed(tb) if os.path.abspath(fr.filename) == prog), 0)
        exc = f"{type(e).__name__} at line {ln}"
    finally:
        sys.argv = old
        cov.stop()
        cov.save()
    data = cov.get_data()
    if prog in data.measured_files():
        lines = set(data.lines(prog) or [])
    return lines, exc


def main():
    args = parse_args()
    rng = random.Random(args.seed)
    typ = input_type(args.program)

    seeds = [parse(Path(f).read_text().strip(), typ)
             for f in sorted(Path(args.corpus).glob("*.txt"))]

    covered, corpus, exceptions, n = set(), [], set(), 0

    def process(val):
        nonlocal n, covered
        n += 1
        s = fmt(val, typ)
        lines, exc = run(args.program, s)
        if exc:
            if exc not in exceptions:
                exceptions.add(exc)
                print(f"Execution {n}: EXCEPTION {exc} input={s}")
            covered |= lines
            return
        if lines - covered:
            covered |= lines
            corpus.append(val)
            print(f"Execution {n}: NEW #lines={len(covered)} input={s}")

    for seed in seeds:
        process(seed)

    for _ in range(args.budget):
        if args.random or not corpus:
            process(gen_random(typ, rng))
        else:
            process(mutate(rng.choice(corpus), typ, rng))

    print(f"DONE #executions={n} #corpus_inputs={len(corpus)} "
          f"#lines={len(covered)} #exceptions={len(exceptions)}")


if __name__ == "__main__":
    main()
