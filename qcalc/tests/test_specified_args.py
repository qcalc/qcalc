import unittest

from qutil import specified_args, unspecified_args


def sample(
    arg1,
    arg2,
    arg3,
    arg4,
    arg5,
    arg6,
    arg7,
    arg8,
    arg9,
    arg10,
):
    pass


class TestSpecifiedArgs(unittest.TestCase):

    def test_func_or_args_types(self):
        # 1. Function / Callable object
        self.assertEqual(
            specified_args(sample, ["1-3"]),
            ["arg1", "arg2", "arg3"],
        )

        # 2. List of argument names
        self.assertEqual(
            specified_args(["a", "b", "c", "d"], ["1-2"]),
            ["a", "b"],
        )

        # 3. Tuple of argument names
        self.assertEqual(
            specified_args(("a", "b", "c", "d"), ["2-4"]),
            ["b", "c", "d"],
        )

        # 4. Comma-separated string of argument names
        self.assertEqual(
            specified_args("a, b, c, d", ["1-2"]),
            ["a", "b"],
        )
        self.assertEqual(
            specified_args("x, y, z", ["y-z"]),
            ["y", "z"],
        )

    def test_string_func_or_args(self):
        self.assertEqual(
            specified_args("arg1, arg2, arg3, arg4", ["1-2"]),
            ["arg1", "arg2"],
        )
        self.assertEqual(
            specified_args("arg1, arg2, arg3, arg4", ["arg2-arg4"]),
            ["arg2", "arg3", "arg4"],
        )

    def test_none(self):
        self.assertEqual(
            specified_args(sample, None),
            [
                "arg1", "arg2", "arg3", "arg4", "arg5",
                "arg6", "arg7", "arg8", "arg9", "arg10",
            ],
        )

    def test_wildcard_spec(self):
        sample_all = [
            "arg1", "arg2", "arg3", "arg4", "arg5",
            "arg6", "arg7", "arg8", "arg9", "arg10",
        ]
        self.assertEqual(
            specified_args(sample, "*"),
            sample_all,
        )
        self.assertEqual(
            specified_args(sample, ["*"]),
            sample_all,
        )
        self.assertEqual(
            specified_args(sample, ("*",)),
            sample_all,
        )
        self.assertEqual(
            specified_args(sample, ["1", "*"]),
            sample_all,
        )

    def test_partial_wildcard_pattern(self):
        # e.g., agr*nt matches argument/arg1, *cost* matches all cost columns
        args = ["cost_chart__r", "total_cost", "unit_price", "agr1nt"]
        self.assertEqual(
            specified_args(args, ["*cost*"]),
            ["cost_chart__r", "total_cost"],
        )
        self.assertEqual(
            specified_args(args, ["*cost"]),
            ["total_cost"],
        )
        self.assertEqual(
            specified_args(args, ["cost*"]),
            ["cost_chart__r"],
        )
        self.assertEqual(
            specified_args(args, ["agr*nt"]),
            ["agr1nt"],
        )
        self.assertEqual(
            specified_args(sample, ["arg1*"]),
            ["arg1", "arg10"],
        )

    def test_single_position(self):
        self.assertEqual(
            specified_args(sample, ["1"]),
            ["arg1"],
        )

        self.assertEqual(
            specified_args(sample, ["7"]),
            ["arg7"],
        )

    def test_position_range(self):
        self.assertEqual(
            specified_args(sample, ["1-2"]),
            ["arg1", "arg2"],
        )

        self.assertEqual(
            specified_args(sample, ["3-5"]),
            ["arg3", "arg4", "arg5"],
        )

    def test_argument_name_range(self):
        self.assertEqual(
            specified_args(sample, ["arg2-arg5"]),
            ["arg2", "arg3", "arg4", "arg5"],
        )

        self.assertEqual(
            specified_args(sample, ["arg2-5"]),
            ["arg2", "arg3", "arg4", "arg5"],
        )

        self.assertEqual(
            specified_args(sample, ["2-arg5"]),
            ["arg2", "arg3", "arg4", "arg5"],
        )

        self.assertEqual(
            specified_args(sample, ["arg5-arg2"]),
            ["arg5", "arg4", "arg3", "arg2"],
        )

        # String spec with comma separation
        self.assertEqual(
            specified_args(sample, "arg2-arg4, ~arg3"),
            ["arg2", "arg4"],
        )

    def test_hyphenated_arg_names(self):
        func_list = ["foo-bar", "baz", "qux"]
        # Exact match should take precedence over splitting as range
        self.assertEqual(
            specified_args(func_list, ["foo-bar"]),
            ["foo-bar"],
        )
        self.assertEqual(
            specified_args(func_list, ["foo-bar-qux"]),
            ["foo-bar", "baz", "qux"],
        )

    def test_case_insensitive_matching(self):
        # Single names in different cases
        self.assertEqual(
            specified_args(sample, ["ARG1", "Arg2"]),
            ["arg1", "arg2"],
        )
        # Name range in different cases
        self.assertEqual(
            specified_args(sample, ["ARG2-ARG5"]),
            ["arg2", "arg3", "arg4", "arg5"],
        )
        # Mixed start/end case ranges
        self.assertEqual(
            specified_args(sample, ["aRg2-ArG5"]),
            ["arg2", "arg3", "arg4", "arg5"],
        )
        self.assertEqual(
            specified_args(sample, ["aRg2-5"]),
            ["arg2", "arg3", "arg4", "arg5"],
        )
        self.assertEqual(
            specified_args(sample, ["2-ArG5"]),
            ["arg2", "arg3", "arg4", "arg5"],
        )
        # Negated range with case variation
        self.assertEqual(
            specified_args(sample, ["~ARg3-arG5"]),
            ["arg1", "arg2", "arg6", "arg7", "arg8", "arg9", "arg10"],
        )
        # Exclusions with case variation
        self.assertEqual(
            specified_args(sample, ["1-5", "~ARG3"]),
            ["arg1", "arg2", "arg4", "arg5"],
        )
        # Uppercase original arg names matched by lowercase spec
        self.assertEqual(
            specified_args(["FOO", "BAR", "BAZ"], ["foo-bar"]),
            ["FOO", "BAR"],
        )
        # String spec with mixed case
        self.assertEqual(
            specified_args("ArgOne, ArgTwo, ArgThree", ["ARGONE-ARGTWO"]),
            ["ArgOne", "ArgTwo"],
        )
        self.assertEqual(
            specified_args("ArgOne, ArgTwo, ArgThree", "argone-argtwo, ~argone"),
            ["ArgTwo"],
        )

    def test_title_and_suffix_matching(self):
        args_list = ["cost_chart__r", "total_price__rf", "user_count__ri", "gold__rq"]

        # Match 'cost_chart__r' using base variable name without suffix '__r'
        self.assertEqual(
            specified_args(args_list, ["cost_chart"]),
            ["cost_chart__r"],
        )

        # Match 'cost_chart__r' using title case 'Cost Chart'
        self.assertEqual(
            specified_args(args_list, ["Cost Chart"]),
            ["cost_chart__r"],
        )

        # Match range 'cost_chart' to 'total_price'
        self.assertEqual(
            specified_args(args_list, ["cost_chart-total_price"]),
            ["cost_chart__r", "total_price__rf"],
        )

        # Match range using Title Case 'Cost Chart' to 'User Count'
        self.assertEqual(
            specified_args(args_list, ["Cost Chart-User Count"]),
            ["cost_chart__r", "total_price__rf", "user_count__ri"],
        )

        # Match vice versa: spec has suffix 'cost_chart__r', list has base variable 'cost_chart'
        self.assertEqual(
            specified_args(["cost_chart", "total_price"], ["cost_chart__r"]),
            ["cost_chart"],
        )

    def test_unspecified_args(self):
        # 1. Spec is None -> none specified, so all are unspecified (returns empty if spec is None, per specified_args returning ["*"])
        self.assertEqual(
            unspecified_args(sample, None),
            [],
        )

        # 2. Spec is '*' or ['*'] -> all specified, so none unspecified
        self.assertEqual(
            unspecified_args(sample, "*"),
            [],
        )
        self.assertEqual(
            unspecified_args(sample, ["*"]),
            [],
        )

        # 3. Specify positional range 1-3 -> remaining arg4 to arg10 are unspecified
        self.assertEqual(
            unspecified_args(sample, ["1-3"]),
            ["arg4", "arg5", "arg6", "arg7", "arg8", "arg9", "arg10"],
        )

        # 4. Specify names with case and title variations
        args_list = ["cost_chart__r", "total_price__rf", "user_count__ri", "gold__rq"]
        self.assertEqual(
            unspecified_args(args_list, ["Cost Chart"]),
            ["total_price__rf", "user_count__ri", "gold__rq"],
        )

        # 5. Specify with exclusions/ranges
        self.assertEqual(
            unspecified_args("a, b, c, d, e", ["a-c", "~b"]),
            ["b", "d", "e"],
        )

    def test_argument_names(self):
        self.assertEqual(
            specified_args(sample, ["arg1", "arg2"]),
            ["arg1", "arg2"],
        )

        self.assertEqual(
            specified_args(sample, ["arg4", "arg7"]),
            ["arg4", "arg7"],
        )

    def test_mixed_specification(self):
        self.assertEqual(
            specified_args(sample, ["1-2", "7", "arg4"]),
            ["arg1", "arg2", "arg7", "arg4"],
        )

    def test_fraction(self):
        self.assertEqual(
            specified_args(sample, 0.6),
            ["arg1", "arg2", "arg3", "arg4", "arg5", "arg6"],
        )

        self.assertEqual(
            specified_args(sample, 0.3),
            ["arg1", "arg2", "arg3"],
        )

    def test_exclusions(self):
        self.assertEqual(
            specified_args(sample, ["~arg3", "~arg7"]),
            [
                "arg1", "arg2", "arg4", "arg5",
                "arg6", "arg8", "arg9", "arg10",
            ],
        )

        self.assertEqual(
            specified_args(sample, ["~3-5"]),
            ["arg1", "arg2", "arg6", "arg7", "arg8", "arg9", "arg10"],
        )

        self.assertEqual(
            specified_args(sample, ["~arg3-arg5"]),
            ["arg1", "arg2", "arg6", "arg7", "arg8", "arg9", "arg10"],
        )

    def test_mixed_exclusions(self):
        self.assertEqual(
            specified_args(sample, ["1-8", "~arg3", "~arg7"]),
            ["arg1", "arg2", "arg4", "arg5", "arg6", "arg8"],
        )

        self.assertEqual(
            specified_args(sample, ["1-10", "~3-5"]),
            ["arg1", "arg2", "arg6", "arg7", "arg8", "arg9", "arg10"],
        )

    def test_duplicates_are_removed(self):
        self.assertEqual(
            specified_args(sample, ["1", "1", "arg1", "1-2"]),
            ["arg1", "arg2"],
        )

    def test_order_is_preserved(self):
        self.assertEqual(
            specified_args(sample, ["7", "2", "5"]),
            ["arg7", "arg2", "arg5"],
        )

    def test_invalid_fraction(self):
        with self.assertRaises(ValueError):
            specified_args(sample, 1.0)

        with self.assertRaises(ValueError):
            specified_args(sample, 1.5)

        with self.assertRaises(ValueError):
            specified_args(sample, 0)

    def test_invalid_argument(self):
        with self.assertRaises(ValueError):
            specified_args(sample, ["unknown"])

    def test_out_of_range_position(self):
        # Current implementation silently ignores out-of-range positions.
        self.assertEqual(
            specified_args(sample, ["99"]),
            [],
        )


if __name__ == "__main__":
    unittest.main()
