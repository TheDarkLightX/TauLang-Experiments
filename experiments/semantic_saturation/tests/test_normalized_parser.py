import unittest

from normalized_parser import NormalizedParseError, parse_native_output, parse_normalized


class NativeNormalizedParserTests(unittest.TestCase):
    def test_explicit_factoring_and_scope(self):
        expected = ('eq0', ('and', ('var', 'x'), ('or', ('var', 'z'), ('var', 'y'))))
        self.assertEqual(parse_normalized('x&(z|y) = 0', ('x', 'y', 'z')), expected)
        with self.assertRaises(NormalizedParseError):
            parse_normalized('x&(z|y) = 0', ('a', 'b', 'c'))

    def test_compact_product_uses_only_declared_single_letters(self):
        self.assertEqual(parse_normalized('ab = 0', ('a', 'b')),
                         ('eq0', ('and', ('var', 'a'), ('var', 'b'))))
        with self.assertRaises(NormalizedParseError):
            parse_normalized('xy = 0', ('a', 'b'))
        with self.assertRaises(NormalizedParseError):
            parse_normalized('a1 = 0', ('a',))

    def test_formula_and_term_precedence(self):
        self.assertEqual(parse_normalized("!a = 0 || b' != 0 && T", ('a', 'b')),
                         ('orF', ('notF', ('eq0', ('var', 'a'))),
                          ('andF', ('ne0', ('not', ('var', 'b'))), ('T',))))
        self.assertEqual(parse_normalized('a | b & c = 0', ('a', 'b', 'c')),
                         ('eq0', ('or', ('var', 'a'), ('and', ('var', 'b'), ('var', 'c')))))

    def test_native_xor_and_explicit_legacy_alias(self):
        expected = ('eq0', ('xor', ('var', 'a'), ('var', 'b')))
        self.assertEqual(parse_normalized('a ^ b = 0', ('a', 'b')), expected)
        with self.assertRaises(NormalizedParseError):
            parse_normalized('a + b = 0', ('a', 'b'))
        self.assertEqual(parse_normalized('a + b = 0', ('a', 'b'), allow_legacy_plus=True), expected)

    def test_rejects_scope_and_language_escape(self):
        invalid = ('ex b b != 0', 'all a a = 0', 'a : sbf = 0', '{a} = 0',
                   'a = 1', 'a = 0 & b', 'a = 0 -> T', 'a = 0. ',
                   '(a = 0) & T', "T'", 'a && b', 'a = ', 'a', '2 = 0')
        for source in invalid:
            with self.subTest(source=source), self.assertRaises(NormalizedParseError):
                parse_normalized(source, ('a', 'b'))

    def test_native_result_boundary(self):
        self.assertEqual(parse_native_output('%1: T\n\n', ()), ('T',))
        self.assertEqual(parse_native_output('%1: F\n', ()), ('F',))
        for stdout in ('%1: T\n%2: F', 'Syntax Error\n%1: T', '\n', 'T'):
            with self.subTest(stdout=stdout), self.assertRaises(NormalizedParseError):
                parse_native_output(stdout, ())

    def test_deep_printed_term_fails_before_downstream_recursion(self):
        with self.assertRaises(NormalizedParseError):
            parse_normalized('a' + "'" * 200 + ' = 0', ('a',))


if __name__ == '__main__':
    unittest.main()
