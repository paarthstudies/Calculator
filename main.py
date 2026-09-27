"""Tkinter desktop interface for the safe arithmetic calculator."""

import re
import tkinter as tk

from calculator import CalculationError, evaluate


class CalculatorApp:
    BACKGROUND = "#11191D"
    DISPLAY_BACKGROUND = "#1B292D"
    NUMBER_BACKGROUND = "#2A393D"
    FUNCTION_BACKGROUND = "#3B5551"
    OPERATOR_BACKGROUND = "#D87552"
    EQUALS_BACKGROUND = "#B6E3C5"
    TEXT_COLOR = "#F4F2E9"
    MUTED_COLOR = "#9AAEAA"
    ERROR_COLOR = "#F19A7B"

    _number_at_end = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?$")

    def __init__(self, root: tk.Tk):
        self.root = root
        self.expression = ""
        self.last_result = 0.0
        self.just_evaluated = False
        self.error_message = ""

        root.title("Calculator")
        root.geometry("400x620")
        root.minsize(340, 520)
        root.configure(bg=self.BACKGROUND)

        self._build_interface()
        self._refresh_display()
        root.bind_all("<Key>", self._on_key)

    def _build_interface(self):
        container = tk.Frame(self.root, bg=self.BACKGROUND, padx=14, pady=14)
        container.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=2)
        container.grid_rowconfigure(1, weight=5)

        display = tk.Frame(container, bg=self.DISPLAY_BACKGROUND, padx=18, pady=14)
        display.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        display.grid_columnconfigure(0, weight=1)
        display.grid_rowconfigure(1, weight=1)

        self.expression_label = tk.Label(
            display,
            text="",
            anchor="e",
            bg=self.DISPLAY_BACKGROUND,
            fg=self.MUTED_COLOR,
            font=("Segoe UI", 13),
        )
        self.expression_label.grid(row=0, column=0, sticky="ew")
        self.value_label = tk.Label(
            display,
            text="0",
            anchor="e",
            bg=self.DISPLAY_BACKGROUND,
            fg=self.TEXT_COLOR,
            font=("Segoe UI", 34, "bold"),
        )
        self.value_label.grid(row=1, column=0, sticky="sew", pady=(8, 2))
        self.status_label = tk.Label(
            display,
            text="",
            anchor="e",
            bg=self.DISPLAY_BACKGROUND,
            fg=self.ERROR_COLOR,
            font=("Segoe UI", 10),
        )
        self.status_label.grid(row=2, column=0, sticky="ew")

        keypad = tk.Frame(container, bg=self.BACKGROUND)
        keypad.grid(row=1, column=0, sticky="nsew")
        for column in range(4):
            keypad.grid_columnconfigure(column, weight=1, uniform="key-column")
        for row in range(6):
            keypad.grid_rowconfigure(row, weight=1, uniform="key-row")

        buttons = [
            [("AC", "AC", "function"), ("DEL", "DEL", "function"), ("(", "(", "function"), (")", ")", "function")],
            [("+/−", "+/-", "function"), ("%", "%", "function"), ("√", "√", "function"), ("÷", "/", "operator")],
            [("7", "7", "number"), ("8", "8", "number"), ("9", "9", "number"), ("×", "*", "operator")],
            [("4", "4", "number"), ("5", "5", "number"), ("6", "6", "number"), ("−", "-", "operator")],
            [("1", "1", "number"), ("2", "2", "number"), ("3", "3", "number"), ("+", "+", "operator")],
        ]
        for row_index, row_buttons in enumerate(buttons):
            for column_index, (label, action, style) in enumerate(row_buttons):
                self._add_button(keypad, label, action, style, row_index, column_index)

        self._add_button(keypad, "0", "0", "number", 5, 0, column_span=2)
        self._add_button(keypad, ".", ".", "number", 5, 2)
        self._add_button(keypad, "=", "=", "equals", 5, 3)

    def _add_button(self, parent, label, action, style, row, column, column_span=1):
        colors = {
            "number": (self.NUMBER_BACKGROUND, self.TEXT_COLOR, "#3B4D51"),
            "function": (self.FUNCTION_BACKGROUND, self.TEXT_COLOR, "#4B6863"),
            "operator": (self.OPERATOR_BACKGROUND, "#171D1D", "#E48A68"),
            "equals": (self.EQUALS_BACKGROUND, "#15231D", "#C8EDD3"),
        }
        background, foreground, active_background = colors[style]
        button = tk.Button(
            parent,
            text=label,
            command=lambda value=action: self.handle_action(value),
            bg=background,
            fg=foreground,
            activebackground=active_background,
            activeforeground=foreground,
            disabledforeground=foreground,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI", 17 if style != "number" else 19, "bold"),
            cursor="hand2",
            takefocus=False,
        )
        button.grid(
            row=row,
            column=column,
            columnspan=column_span,
            sticky="nsew",
            padx=4,
            pady=4,
        )

    def handle_action(self, action: str):
        if action == "AC":
            self.clear()
            return

        self._prepare_for_input(action)
        self.error_message = ""

        if action == "DEL":
            self._delete_last()
        elif action == "=":
            self._calculate()
        elif action == "+/-":
            self._toggle_sign()
        elif action == "√":
            self._apply_square_root()
        elif action in "0123456789.":
            self._append_digit(action)
        elif action in "+-*/":
            self._append_operator(action)
        elif action in "()":
            self._append_parenthesis(action)
        elif action == "%":
            self._append_percent()

        self._refresh_display()

    def _prepare_for_input(self, action: str):
        if self.error_message and action in "0123456789.(":
            self.expression = ""
            self.just_evaluated = False
            return

        if not self.just_evaluated:
            return

        if action in "+-*/%√+/-DEL":
            self.expression = self._format_number(self.last_result)
        else:
            self.expression = ""
        self.just_evaluated = False

    def _append_digit(self, digit: str):
        if digit == ".":
            current_number = self._current_number_fragment()
            if "." in current_number:
                return
            if not current_number:
                if self.expression.endswith((")", "%")):
                    self.expression += "*"
                self.expression += "0"
        elif self.expression.endswith((")", "%")):
            self.expression += "*"
        self.expression += digit

    def _append_operator(self, operator: str):
        if not self.expression:
            if operator == "-":
                self.expression = "-"
            return

        if self.expression.endswith("."):
            self.expression += "0"
        last_character = self.expression[-1]
        if last_character in "+-*/":
            trailing_operators = re.search(r"[+\-*/]+$", self.expression).group(0)
            if operator == "-" and trailing_operators[-1] in "+*/":
                self.expression += operator
                return

            if trailing_operators.endswith("-") and len(trailing_operators) > 1:
                self.expression = self.expression[:-len(trailing_operators)] + operator
                return

            if trailing_operators == "-":
                sign_position = len(self.expression) - 1
                if sign_position == 0 or self.expression[sign_position - 1] == "(":
                    return

            self.expression = self.expression[:-len(trailing_operators)] + operator
        elif last_character == "(":
            if operator == "-":
                self.expression += operator
        else:
            self.expression += operator

    def _append_parenthesis(self, parenthesis: str):
        if parenthesis == "(":
            if self.expression.endswith((")", "%")) or self._expression_ends_with_number():
                self.expression += "*"
            self.expression += "("
            return

        if self.expression.count("(") <= self.expression.count(")"):
            return
        if self.expression and self.expression[-1] not in "+-*/(":
            self.expression += ")"

    def _append_percent(self):
        if self.expression and self.expression[-1] not in "+-*/.(%":
            self.expression += "%"

    def _toggle_sign(self):
        span = self._current_operand_span()
        if span is None:
            return
        start, end = span
        operand = self.expression[start:end]
        if operand.startswith("-(") and operand.endswith(")"):
            replacement = operand[2:-1]
        elif self._number_at_end.fullmatch(operand) and operand.startswith("-"):
            replacement = operand[1:]
        elif self._number_at_end.fullmatch(operand):
            replacement = "-" + operand
        else:
            replacement = "-(" + operand + ")"
        self.expression = self.expression[:start] + replacement + self.expression[end:]

    def _apply_square_root(self):
        span = self._current_operand_span()
        if span is None:
            return
        start, end = span
        operand = self.expression[start:end]
        self.expression = self.expression[:start] + "sqrt(" + operand + ")" + self.expression[end:]

    def _current_operand_span(self):
        end = len(self.expression)
        if not end:
            return None

        if self.expression.endswith(")"):
            depth = 0
            opening = None
            for index in range(end - 1, -1, -1):
                if self.expression[index] == ")":
                    depth += 1
                elif self.expression[index] == "(":
                    depth -= 1
                    if depth == 0:
                        opening = index
                        break
            if opening is None:
                return None
            start = opening
            if self.expression[max(0, opening - 4):opening].lower() == "sqrt":
                start -= 4
            if start > 0 and self.expression[start - 1] == "-":
                sign_position = start - 1
                if sign_position == 0 or self.expression[sign_position - 1] in "(+-*/":
                    start = sign_position
            return start, end

        match = self._number_at_end.search(self.expression)
        if match is None:
            return None
        start = match.start()
        if start > 0 and self.expression[start - 1] == "-":
            sign_position = start - 1
            if sign_position == 0 or self.expression[sign_position - 1] in "(+-*/":
                start = sign_position
        return start, end

    def _current_number_fragment(self) -> str:
        match = self._number_at_end.search(self.expression)
        return match.group(0) if match else ""

    def _expression_ends_with_number(self) -> bool:
        return self._number_at_end.search(self.expression) is not None

    def _delete_last(self):
        if self.expression.endswith("sqrt("):
            self.expression = self.expression[:-5]
        elif self.expression:
            self.expression = self.expression[:-1]

    def _calculate(self):
        if not self.expression:
            return

        difference = self.expression.count("(") - self.expression.count(")")
        if difference < 0:
            self.error_message = "Invalid expression"
            return
        self.expression += ")" * difference

        try:
            self.last_result = evaluate(self.expression)
            self.just_evaluated = True
        except CalculationError as error:
            self.error_message = str(error)

    def clear(self):
        self.expression = ""
        self.last_result = 0.0
        self.just_evaluated = False
        self.error_message = ""
        self._refresh_display()

    def _refresh_display(self):
        self.expression_label.configure(text=self._pretty_expression(self.expression))
        self.status_label.configure(text=self.error_message)
        if self.error_message:
            value = "Error"
        elif self.just_evaluated:
            value = self._format_number(self.last_result)
        elif not self.expression:
            value = "0"
        else:
            try:
                value = self._format_number(evaluate(self.expression))
            except CalculationError:
                numbers = re.findall(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?", self.expression)
                value = numbers[-1] if numbers else self._pretty_expression(self.expression)

        self.value_label.configure(text=value)

    @staticmethod
    def _format_number(value: float) -> str:
        if value == 0:
            return "0"
        return format(value, ".12g")

    @staticmethod
    def _pretty_expression(expression: str) -> str:
        return expression.replace("sqrt", "√").replace("*", "×").replace("/", "÷")

    def _on_key(self, event):
        key_actions = {
            "Return": "=",
            "KP_Enter": "=",
            "Escape": "AC",
            "BackSpace": "DEL",
            "Delete": "DEL",
        }
        action = key_actions.get(event.keysym)
        if action is None and event.char and event.char in "0123456789.+-*/()%":
            action = event.char
        if action is None and event.char == "=":
            action = "="
        if action is None:
            return
        self.handle_action(action)
        return "break"


def main():
    root = tk.Tk()
    CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()