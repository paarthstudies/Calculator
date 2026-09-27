"""Safe arithmetic expression evaluation for the desktop calculator."""

import math
import re


class CalculationError(ValueError):
    """Raised when an expression is invalid or cannot be calculated."""


class ExpressionParser:
    """Evaluate arithmetic expressions without executing Python code."""

    _number_pattern = r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?"
    _token_pattern = re.compile(rf"sqrt|{_number_pattern}|[+\-*/()%]", re.IGNORECASE)

    def evaluate(self, expression: str) -> float:
        self.tokens = self._tokenize(expression)
        self.position = 0
        if not self.tokens:
            raise CalculationError("Invalid expression")

        syntax_tree = self._parse_expression()
        if self.position != len(self.tokens):
            raise CalculationError("Invalid expression")

        return self._evaluate_node(syntax_tree)

    def _tokenize(self, expression: str) -> list[str]:
        tokens = []
        position = 0
        while position < len(expression):
            if expression[position].isspace():
                position += 1
                continue

            match = self._token_pattern.match(expression, position)
            if match is None:
                raise CalculationError("Invalid expression")
            tokens.append(match.group(0))
            position = match.end()
        return tokens

    def _peek(self) -> str | None:
        if self.position == len(self.tokens):
            return None
        return self.tokens[self.position]

    def _take(self) -> str:
        token = self._peek()
        if token is None:
            raise CalculationError("Invalid expression")
        self.position += 1
        return token

    def _parse_expression(self) -> tuple:
        node = self._parse_term()
        while self._peek() in ("+", "-"):
            operator = self._take()
            node = ("binary", operator, node, self._parse_term())
        return node

    def _parse_term(self) -> tuple:
        node = self._parse_unary()
        while self._peek() in ("*", "/"):
            operator = self._take()
            node = ("binary", operator, node, self._parse_unary())
        return node

    def _parse_unary(self) -> tuple:
        if self._peek() in ("+", "-"):
            return ("unary", self._take(), self._parse_unary())

        node = self._parse_primary()
        while self._peek() == "%":
            self._take()
            node = ("percent", node)
        return node

    def _parse_primary(self) -> tuple:
        token = self._take()
        if re.fullmatch(self._number_pattern, token):
            return ("number", float(token))
        if token.lower() == "sqrt":
            if self._take() != "(":
                raise CalculationError("Invalid expression")
            node = self._parse_expression()
            if self._take() != ")":
                raise CalculationError("Invalid expression")
            return ("sqrt", node)
        if token == "(":
            node = self._parse_expression()
            if self._take() != ")":
                raise CalculationError("Invalid expression")
            return node
        raise CalculationError("Invalid expression")

    def _evaluate_node(self, node: tuple) -> float:
        kind = node[0]
        if kind == "number":
            return self._checked(node[1])
        if kind == "unary":
            value = self._evaluate_node(node[2])
            return self._checked(-value if node[1] == "-" else value)
        if kind == "percent":
            return self._checked(self._evaluate_node(node[1]) / 100)
        if kind == "sqrt":
            value = self._evaluate_node(node[1])
            if value < 0:
                raise CalculationError("Cannot calculate square root of a negative number")
            return self._checked(math.sqrt(value))

        operator, left_node, right_node = node[1:]
        left = self._evaluate_node(left_node)
        right = self._evaluate_node(right_node)
        if operator in ("+", "-") and right_node[0] == "percent":
            right = self._checked(left * right)

        if operator == "+":
            result = left + right
        elif operator == "-":
            result = left - right
        elif operator == "*":
            result = left * right
        else:
            if right == 0:
                raise CalculationError("Cannot divide by zero")
            result = left / right
        return self._checked(result)

    @staticmethod
    def _checked(value: float) -> float:
        if not math.isfinite(value):
            raise CalculationError("Result is too large")
        return value


def evaluate(expression: str) -> float:
    """Evaluate a calculator expression and return its numeric result."""
    return ExpressionParser().evaluate(expression)