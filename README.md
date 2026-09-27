# Desktop Calculator

A desktop calculator built with Python and Tkinter. It supports standard arithmetic, parentheses, percentage calculations, square roots, sign toggling, and keyboard input. Expressions are parsed by a restricted arithmetic parser; calculator input is never executed as Python.

## Requirements

- Python 3.10 or newer
- Tkinter (included with most standard Python installations)
- No external packages

## Run

From this directory, run:

```powershell
python main.py
```

## Features and shortcuts

- `+`, `-`, `*`, `/`, decimal points, parentheses, and `Enter` for equals
- `Escape` clears the calculator; `Backspace` or `Delete` removes the last character
- `%` converts a value to a percentage; for example, `200 + 10%` gives `220`
- The `√` button applies square root to the current operand; `+/−` toggles its sign
- Errors are shown in the display and can be cleared with `Escape` or `AC`

## Project files

- `main.py` contains the Tkinter interface and mouse/keyboard event handling.
- `calculator.py` contains the safe expression parser and math evaluation.
- `test_calculator.py` contains standard-library unit tests.