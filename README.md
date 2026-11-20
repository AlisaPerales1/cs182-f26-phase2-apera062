# CS 182 Project Phase 2 – Coverage-Guided Fuzzer

Coverage-guided mutation-based fuzzer for Fall 2026 Phase 2.

## Repository Structure

```
.
├── src/
│   └── fuzz.py          # Main fuzzer implementation
├── README.md
└── .github/
    └── workflows/       # (add your GitHub Actions workflow here)
```

Place the provided files (`programs/`, `fixed_inputs/`, `fixed_expected/`, `campaign_seeds/`, `campaign_expected/`) at the repository root (or adjust paths in the workflow).

## Requirements

- Python 3.10+
- `coverage` library  
  ```bash
  pip install coverage
  ```

## Usage

```bash
python3 src/fuzz.py <program.py> <corpus_dir> [--budget N] [--seed S] [--random]
```

| Argument       | Description                                      | Default   |
|----------------|--------------------------------------------------|-----------|
| `program`      | Target Python program (reads input from `sys.argv`) | —     |
| `corpus`       | Directory of seed `.txt` files                   | —         |
| `--budget N`   | Number of new inputs after seeds                 | 15000     |
| `--seed S`     | Random seed for all fuzzer decisions             | 0         |
| `--random`     | Pure random testing (no mutations / corpus)      | off       |

### Examples

Seed corpus only (deterministic):
```bash
python3 src/fuzz.py programs/program_03.py fixed_inputs/program_03/set_1 --budget 0
```

Full coverage-guided campaign:
```bash
python3 src/fuzz.py programs/program_03.py campaign_seeds/program_03 --budget 15000 --seed 0
```

Random testing baseline:
```bash
python3 src/fuzz.py programs/program_03.py campaign_seeds/program_03 --budget 15000 --seed 0 --random
```

## Implementation Notes

- **Input types** are detected from the first line of the target (`# input: int|str|ints`).
- **Seeds** are executed in lexicographic order of filenames.
- **Coverage** is statement coverage collected via the `coverage` library. An input is added to the corpus only when it covers at least one previously unseen line and does not raise a new exception.
- **Mutations** follow the required operators (1–3 applied per input). All randomness is controlled by `random.Random(seed)`.
- **Exceptions** are reported only the first time a given signature (`ExceptionType at line N`) is observed. Lines covered by crashing runs still count toward total coverage.
- Output format matches the specification exactly (`Execution N: NEW ...`, `Execution N: EXCEPTION ...`, final `DONE` line).

## Testing / GitHub Actions

The workflow should:

1. Run every fixed-input set with `--budget 0` and compare output line-by-line against `fixed_expected/`.
2. Run three coverage-guided campaigns (`--seed 0,1,2`, budget 15000) per program and verify every expected exception signature appears in at least 2 of the 3 runs.
3. Run one random campaign per program as a baseline.
4. Print commands prefixed with `$`, `[PASS]`/`[FAIL]` results, and summary counts; exit non-zero on failure.

## Author

CS 182 Phase 2 submission.
