import unittest
from types import SimpleNamespace

from calculator import CalculationError, evaluate
from main import CalculatorApp


class DisplayStub:
    def __init__(self):
        self.text = ""

    def configure(self, **values):
        self.text = values.get("text", self.text)


def make_app_without_window():
    app = CalculatorApp.__new__(CalculatorApp)
    app.expression = ""
    app.last_result = 0.0
    app.just_evaluated = False
    app.error_message = ""
    app.expression_label = DisplayStub()
    app.value_label = DisplayStub()
    app.status_label = DisplayStub()
    return app


class CalculatorTests(unittest.TestCase):
    def test_basic_arithmetic_and_precedence(self):
        self.assertEqual(evaluate("2 + 3 * 4"), 14)
        self.assertEqual(evaluate("(2 + 3) * 4"), 20)
        self.assertEqual(evaluate("-2.5 + 5"), 2.5)

    def test_percentage_semantics(self):
        self.assertEqual(evaluate("50%"), 0.5)
        self.assertEqual(evaluate("200 + 10%"), 220)
        self.assertEqual(evaluate("200 - 10%"), 180)
        self.assertEqual(evaluate("500 * 10%"), 50)

    def test_square_root(self):
        self.assertEqual(evaluate("sqrt(25)"), 5)
        self.assertEqual(evaluate("sqrt(144)"), 12)
        with self.assertRaisesRegex(CalculationError, "negative"):
            evaluate("sqrt(-1)")

    def test_invalid_and_unsafe_expressions_are_rejected(self):
        for expression in ("", "2+", "1//2", "__import__('os')", "2 ** 8"):
            with self.subTest(expression=expression):
                with self.assertRaises(CalculationError):
                    evaluate(expression)

    def test_division_by_zero_and_overflow(self):
        with self.assertRaisesRegex(CalculationError, "divide by zero"):
            evaluate("1 / 0")
        with self.assertRaisesRegex(CalculationError, "too large"):
            evaluate("1e308 * 1e308")

    def test_operator_replacement_and_unary_negative(self):
        app = make_app_without_window()
        for action in ("5", "+", "*", "2", "="):
            app.handle_action(action)
        self.assertEqual(app.last_result, 10)

        app.clear()
        for action in ("5", "+", "-", "2", "="):
            app.handle_action(action)
        self.assertEqual(app.last_result, 3)

    def test_unary_functions_operate_on_current_operand(self):
        app = make_app_without_window()
        for action in ("5", "+", "2", "5", "√", "="):
            app.handle_action(action)
        self.assertEqual(app.last_result, 10)

        app.clear()
        for action in ("2", "5", "+/-", "+/-", "="):
            app.handle_action(action)
        self.assertEqual(app.last_result, 25)

    def test_error_recovery_and_keyboard_routing(self):
        app = make_app_without_window()
        for action in ("1", "/", "0", "="):
            app.handle_action(action)
        self.assertEqual(app.status_label.text, "Cannot divide by zero")

        app.handle_action("7")
        self.assertEqual(app.error_message, "")
        self.assertEqual(app.expression, "7")

        app.clear()
        for key, character in (("", "2"), ("", "+"), ("", "3"), ("Return", "\r")):
            app._on_key(SimpleNamespace(keysym=key, char=character))
        self.assertEqual(app.last_result, 5)

        app._on_key(SimpleNamespace(keysym="F1", char=""))
        self.assertEqual(app.last_result, 5)


if __name__ == "__main__":
    unittest.main()