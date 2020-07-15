#!/usr/bin/env python
# coding=UTF-8

from collections import OrderedDict
from pickle import FALSE

from prettytable import PrettyTable
from prettytable import RuleStyle, TableStyle
from prettytable import from_db_cursor
from prettytable.prettytable import DEFAULT, PrettyTableException, RANDOM

try:
    import sqlite3
    _have_sqlite = True
except ImportError:
    _have_sqlite = False

from io import StringIO
import math
import textwrap
import unittest


class BuildEquivelanceTest(unittest.TestCase):
    """Make sure that building a table row-by-row and column-by-column yield the same results"""

    def setUp(self):
        # Row by row...
        self.row = PrettyTable()
        self.row.field_names = ["City name", "Area", "Population", "Annual Rainfall"]
        self.row.add_row(["Adelaide", 1295, 1158259, 600.5])
        self.row.add_row(["Brisbane", 5905, 1857594, 1146.4])
        self.row.add_row(["Darwin", 112, 120900, 1714.7])
        self.row.add_row(["Hobart", 1357, 205556, 619.5])
        self.row.add_row(["Sydney", 2058, 4336374, 1214.8])
        self.row.add_row(["Melbourne", 1566, 3806092, 646.9])
        self.row.add_row(["Perth", 5386, 1554769, 869.4])

        # Column by column...
        self.col = PrettyTable()
        self.col.add_column("City name", ["Adelaide", "Brisbane", "Darwin", "Hobart", "Sydney", "Melbourne", "Perth"])
        self.col.add_column("Area", [1295, 5905, 112, 1357, 2058, 1566, 5386])
        self.col.add_column("Population", [1158259, 1857594, 120900, 205556, 4336374, 3806092, 1554769])
        self.col.add_column("Annual Rainfall", [600.5, 1146.4, 1714.7, 619.5, 1214.8, 646.9, 869.4])

        # A mix of both!
        self.mix = PrettyTable()
        self.mix.field_names = ["City name", "Area"]
        self.mix.add_row(["Adelaide", 1295])
        self.mix.add_row(["Brisbane", 5905])
        self.mix.add_row(["Darwin", 112])
        self.mix.add_row(["Hobart", 1357])
        self.mix.add_row(["Sydney", 2058])
        self.mix.add_row(["Melbourne", 1566])
        self.mix.add_row(["Perth", 5386])
        self.mix.add_column("Population", [1158259, 1857594, 120900, 205556, 4336374, 3806092, 1554769])
        self.mix.add_column("Annual Rainfall", [600.5, 1146.4, 1714.7, 619.5, 1214.8, 646.9, 869.4])

    def testRowColEquivalenceASCII(self):
        self.assertEqual(self.row.get_string(), self.col.get_string())

    def testRowMixEquivalenceASCII(self):
        self.assertEqual(self.row.get_string(), self.mix.get_string())

    def testRowColEquivalenceHTML(self):
        self.assertEqual(self.row.get_html_string(), self.col.get_html_string())

    def testRowMixEquivalenceHTML(self):
        self.assertEqual(self.row.get_html_string(), self.mix.get_html_string())


class FieldsTest(unittest.TestCase):

    def testDefault(self):
        t = PrettyTable(field_names=("a", "b"))
        self.assertEqual(t.fields, None)

    def testUnknownFields(self):
        try:
            PrettyTable(field_names=("a", "b"), fields=("a", "b", "c"))
            assert False
        except PrettyTableException:
            assert True

    def testConstructor(self):
        t = PrettyTable(field_names=("a", "b"), fields=("a",))
        t.add_row([1, 2])
        result = t.get_string()
        self.assertEqual(t.fields, ("a", ))
        self.assertEqual(textwrap.dedent("""\
            +---+
            | a |
            +---+
            | 1 |
            +---+
            """).strip(), result)

    def testAssign(self):
        t = PrettyTable(field_names=("a", "b"))
        t.add_row([1, 2])
        result = t.get_string()
        self.assertEqual(t.fields, None)
        self.assertEqual(textwrap.dedent("""\
            +---+---+
            | a | b |
            +---+---+
            | 1 | 2 |
            +---+---+
            """).strip(), result)
        t.fields = ("a",)
        self.assertEqual(t.fields, ("a", ))
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +---+
            | a |
            +---+
            | 1 |
            +---+
            """).strip(), result)

    def testAllFieldsPresent(self):
        t = PrettyTable(field_names=("a", "b"), fields=("a", "b"))
        t.add_row([1, 2])
        result = t.get_string()
        self.assertEqual(t.fields, ("a", "b",))
        self.assertEqual(textwrap.dedent("""\
            +---+---+
            | a | b |
            +---+---+
            | 1 | 2 |
            +---+---+
            """).strip(), result)

    def testBadType(self):
        try:
            PrettyTable(field_names=("a", "b"), fields=9)
            assert False
        except PrettyTableException:
            assert True

# class FieldnamelessTableTest(unittest.TestCase):
#
#    """Make sure that building and stringing a table with no fieldnames works fine"""
#
#    def setUp(self):
#        self.x = PrettyTable()
#        self.x.add_row(["Adelaide",1295, 1158259, 600.5])
#        self.x.add_row(["Brisbane",5905, 1857594, 1146.4])
#        self.x.add_row(["Darwin", 112, 120900, 1714.7])
#        self.x.add_row(["Hobart", 1357, 205556, 619.5])
#        self.x.add_row(["Sydney", 2058, 4336374, 1214.8])
#        self.x.add_row(["Melbourne", 1566, 3806092, 646.9])
#        self.x.add_row(["Perth", 5386, 1554769, 869.4])
#
#    def testCanStringASCII(self):
#        self.x.get_string()
#
#    def testCanStringHTML(self):
#        self.x.get_html_string()
#
#    def testAddFieldnamesLater(self):
#        self.x.field_names = ["City name", "Area", "Population", "Annual Rainfall"]
#        self.x.get_string()

class CityDataTest(unittest.TestCase):
    """Just build the Australian capital city data example table."""

    def setUp(self):
        self.x = PrettyTable(["City name", "Area", "Population", "Annual Rainfall"])
        self.x.add_row(["Adelaide", 1295, 1158259, 600.5])
        self.x.add_row(["Brisbane", 5905, 1857594, 1146.4])
        self.x.add_row(["Darwin", 112, 120900, 1714.7])
        self.x.add_row(["Hobart", 1357, 205556, 619.5])
        self.x.add_row(["Sydney", 2058, 4336374, 1214.8])
        self.x.add_row(["Melbourne", 1566, 3806092, 646.9])
        self.x.add_row(["Perth", 5386, 1554769, 869.4])

class HeaderTests(unittest.TestCase):

    def testDefault(self):
        t = PrettyTable()
        self.assertEquals(True, t.header)

    def testHeaderTrue(self):
        t = PrettyTable(field_names=("C1", "C2"), header=True)
        self.assertEquals(t.header, True)
        t.add_row(["a1", "b1"])
        t.add_row(["c1", "d1"])
        self.assertEquals(textwrap.dedent("""\
            +----+----+
            | C1 | C2 |
            +----+----+
            | a1 | b1 |
            | c1 | d1 |
            +----+----+""").strip(), t.get_string())

    def testHeaderFalse(self):
        t = PrettyTable(field_names=("C1", "C2"), header=False)
        self.assertEquals(t.header, False)
        t.add_row(["a1", "b1"])
        t.add_row(["c1", "d1"])
        self.assertEquals(textwrap.dedent("""\
            +----+----+
            | a1 | b1 |
            | c1 | d1 |
            +----+----+""").strip(), t.get_string())

    def testInvalidType(self):
        try:
            PrettyTable(field_names=("C1", "C2"), header="yes")
            assert False
        except PrettyTableException:
            assert True


class IntFormatTests(unittest.TestCase):

    def getTable(self, **kwargs):
        t = PrettyTable(field_names=(1, 2), **kwargs)
        t.add_row([3,4])
        t.add_row([5,-6])
        return t

    def testDefault(self):
        t = self.getTable()
        self.assertEquals(textwrap.dedent("""\
            +---+----+
            | 1 | 2  |
            +---+----+
            | 3 | 4  |
            | 5 | -6 |
            +---+----+
            """).strip(), t.get_string())

    def testEmptyFormat(self):
        t = self.getTable(int_format="")
        self.assertEquals(textwrap.dedent("""\
            +---+----+
            | 1 | 2  |
            +---+----+
            | 3 | 4  |
            | 5 | -6 |
            +---+----+
            """).strip(), t.get_string())

    def testChangeDefault(self):
        t = PrettyTable(field_names=("F",),int_format="04")
        self.assertEquals({"F": "04"}, t.int_format)
        t.int_format = ""
        self.assertEquals({"F": ""}, t.int_format)

    def testReset(self):
        t = self.getTable()
        t.int_format = {"1": "03", "2": "+05"}
        self.assertEquals(textwrap.dedent("""\
            +-----+-------+
            |  1  |   2   |
            +-----+-------+
            | 003 | +0004 |
            | 005 | -0006 |
            +-----+-------+
            """).strip(), t.get_string())
        t.int_format = ""
        self.assertEquals(textwrap.dedent("""\
            +---+----+
            | 1 | 2  |
            +---+----+
            | 3 | 4  |
            | 5 | -6 |
            +---+----+
            """).strip(), t.get_string())

    def testMultiple(self):
        t = self.getTable()
        t.int_format = {"1": "03", "2": "+05"}
        self.assertEquals(textwrap.dedent("""\
            +-----+-------+
            |  1  |   2   |
            +-----+-------+
            | 003 | +0004 |
            | 005 | -0006 |
            +-----+-------+
            """).strip(), t.get_string())

    def testInvalid(self):
        t = self.getTable()
        try:
            t.int_format = "x"
            assert False
        except PrettyTableException:
            assert True


class FloatFormatTests(unittest.TestCase):

    def getTable(self, **kwargs):
        t = PrettyTable(field_names=(1, 2), **kwargs)
        t.add_row([3.14159, 2.7182])
        t.add_row([5., -6.])
        t.add_row([math.inf, 0])
        return t

    def testDefault(self):
        t = self.getTable()
        self.assertEquals(textwrap.dedent("""\
            +---------+--------+
            |    1    |   2    |
            +---------+--------+
            | 3.14159 | 2.7182 |
            |   5.0   |  -6.0  |
            |   inf   |   0    |
            +---------+--------+
            """).strip(), t.get_string())

    def testEmptyFormat(self):
        t = self.getTable(float_format="")
        self.assertEquals(textwrap.dedent("""\
            +----------+-----------+
            |    1     |     2     |
            +----------+-----------+
            | 3.141590 |  2.718200 |
            | 5.000000 | -6.000000 |
            |   inf    |     0     |
            +----------+-----------+
            """).strip(), t.get_string())

    def testChangeDefault(self):
        t = PrettyTable(field_names=("F",),int_format="04")
        self.assertEquals({"F": "04"}, t.int_format)
        t.int_format = ""
        self.assertEquals({"F": ""}, t.int_format)

    def testReset(self):
        t = self.getTable()
        t.float_format = {"1": "1.02", "2": "+1.04"}
        self.assertEquals(textwrap.dedent("""\
            +------+---------+
            |  1   |    2    |
            +------+---------+
            | 3.14 | +2.7182 |
            | 5.00 | -6.0000 |
            | inf  |    0    |
            +------+---------+
            """).strip(), t.get_string())
        t.float_format = ""
        self.assertEquals(textwrap.dedent("""\
            +----------+-----------+
            |    1     |     2     |
            +----------+-----------+
            | 3.141590 |  2.718200 |
            | 5.000000 | -6.000000 |
            |   inf    |     0     |
            +----------+-----------+
            """).strip(), t.get_string())

    def testMultiple(self):
        t = self.getTable()
        t.float_format = {"1": "1.02", "2": "+1.04"}
        self.assertEquals(textwrap.dedent("""\
            +------+---------+
            |  1   |    2    |
            +------+---------+
            | 3.14 | +2.7182 |
            | 5.00 | -6.0000 |
            | inf  |    0    |
            +------+---------+
            """).strip(), t.get_string())

    def testInvalid_x(self):
        t = self.getTable()
        try:
            t.float_format = "x"
            assert False
        except PrettyTableException:
            assert True

    def testInvalid_f(self):
        t = self.getTable()
        try:
            t.float_format = "f"
            assert False
        except PrettyTableException:
            assert True


class MaxTableWidthTests(unittest.TestCase):
    def testEmptyDefault(self):
        t = PrettyTable()
        self.assertEquals(t.max_table_width, None)
        self.assertEquals(textwrap.dedent("""\
            ++
            ||
            ++
            ++""").strip(), t.get_string())

    def testEmptyConstructor(self):
        t = PrettyTable(max_table_width=5)
        self.assertEquals(t.max_table_width, 5)
        self.assertEquals(textwrap.dedent("""\
            ++
            ||
            ++
            ++""").strip(), t.get_string())

    def testEmptyColumn(self):
        t = PrettyTable([""], max_table_width=3, title="")
        t.add_row([""])
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +--+
            |  |
            +--+
            |  |
            +--+
            |  |
            +--+
            """).strip(), result)

    def testDefault(self):
        t = PrettyTable(header=False)
        t.add_row([1, 2])
        t.add_row([3, 4])
        self.assertEquals(t.max_table_width, None)
        self.assertEquals(textwrap.dedent("""\
            +---+---+
            | 1 | 2 |
            | 3 | 4 |
            +---+---+""").strip(), t.get_string())

    def testConstructor(self):
        t = PrettyTable(header=False, max_table_width=10, hrules=RuleStyle.ALL)
        t.add_row(["a b c d e f", "g h i j k l"])
        t.add_row(["m n o p q r", "s t u v w x"])
        self.assertEquals(t.max_table_width, 10)
        self.assertEquals(textwrap.dedent("""\
            +---+---+
            | a | g |
            | b | h |
            | c | i |
            | d | j |
            | e | k |
            | f | l |
            +---+---+
            | m | s |
            | n | t |
            | o | u |
            | p | v |
            | q | w |
            | r | x |
            +---+---+
            """).strip(), t.get_string())

    def testConstructorLongLine(self):
        t = PrettyTable(header=False, max_table_width=10, hrules=RuleStyle.ALL)
        t.add_row(["abcdef", "ghijkl"])
        t.add_row(["mnopqr", "stuvwx"])
        self.assertEquals(t.max_table_width, 10)
        self.assertEquals(textwrap.dedent("""\
            +---+---+
            | a | g |
            | b | h |
            | c | i |
            | d | j |
            | e | k |
            | f | l |
            +---+---+
            | m | s |
            | n | t |
            | o | u |
            | p | v |
            | q | w |
            | r | x |
            +---+---+
            """).strip(), t.get_string())

    def testConstructorWidthTooSmall(self):
        t = PrettyTable(header=False, max_table_width=5, hrules=RuleStyle.ALL)
        t.add_row(["abcdef", "ghijkl"])
        t.add_row(["mnopqr", "stuvwx"])
        self.assertEqual(5, t.max_table_width)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +---+---+
            | a | g |
            | b | h |
            | c | i |
            | d | j |
            | e | k |
            | f | l |
            +---+---+
            | m | s |
            | n | t |
            | o | u |
            | p | v |
            | q | w |
            | r | x |
            +---+---+
            """).strip(), result)

    def testInvalid(self):
        try:
            PrettyTable(max_table_width=-1)
            assert False
        except PrettyTableException:
            assert True

    def testNone(self):
        t = PrettyTable()
        t.max_table_width = None

    def testMaxTableWidthIsTheLaw(self):
        max_width = 127
        t = PrettyTable(max_table_width=max_width)
        t.field_names = ['tag', 'versions']

        versions = (
            'python/django-appconf:1.0.1',
            'python/django-braces:1.8.1',
            'python/django-compressor:2.0',
            'python/django-debug-toolbar:1.4',
            'python/django-extensions:1.6.1',
        )
        t.add_row(['allmychanges.com', ', '.join(versions)])
        result = t.get_string(hrules=RuleStyle.ALL)
        lines = result.strip().split('\n')

        for line in lines:
            line_length = len(line)
            self.assertLessEqual(line_length, max_width)

    def testMaxTableWidthIsTheLawWhenMinColumnWidthSetForSomeColumns(self):
        max_width = 40
        t = PrettyTable(max_table_width=max_width)
        t.field_names = ['tag', 'versions']
        versions = [
            'python/django-appconf:1.0.1',
            'python/django-braces:1.8.1',
            'python/django-compressor:2.0',
            'python/django-debug-toolbar:1.4',
            'python/django-extensions:1.6.1',
        ]
        t.add_row(['allmychanges.com', ', '.join(versions)])

        # Now, we'll set min width for first column
        # to not wrap it's content
        t._min_width['tag'] = len('allmychanges.com')

        result = t.get_string(hrules=RuleStyle.ALL)
        lines = result.strip().split('\n')

        for line in lines:
            line_length = len(line)
            self.assertLessEqual(line_length, max_width)


class MinTableWidthTests(unittest.TestCase):
    def testEmptyDefault(self):
        t = PrettyTable()
        self.assertEquals(t.min_table_width, None)
        self.assertEquals(textwrap.dedent("""\
            ++
            ||
            ++
            ++""").strip(), t.get_string())

    def testEmptyConstructor(self):
        t = PrettyTable(min_table_width=5)
        self.assertEquals(t.min_table_width, 5)
        self.assertEquals(textwrap.dedent("""\
            ++
            ||
            ++
            ++""").strip(), t.get_string())

    def testDefault(self):
        t = PrettyTable(header=False)
        t.add_row([1, 2])
        t.add_row([3, 4])
        self.assertEquals(t.min_table_width, None)
        self.assertEquals(textwrap.dedent("""\
            +---+---+
            | 1 | 2 |
            | 3 | 4 |
            +---+---+""").strip(), t.get_string())

    def testConstructor(self):
        t = PrettyTable(header=False, min_table_width=17)
        t.add_row([1, 2])
        t.add_row([3, 4])
        self.assertEquals(t.min_table_width, 17)
        self.assertEquals(textwrap.dedent("""\
            +-------+-------+
            |   1   |   2   |
            |   3   |   4   |
            +-------+-------+""").strip(), t.get_string())

    def testInvalid(self):
        try:
            PrettyTable(min_table_width=-1)
            assert False
        except PrettyTableException:
            assert True

    def testNone(self):
        t = PrettyTable()
        t.min_table_width = None


class OptionOverrideTests(CityDataTest):
    """Make sure all options are properly overwritten by get_string."""

    def testBorder(self):
        default = self.x.get_string()
        override = self.x.get_string(border=False)
        self.assertTrue(default != override)
    def testHrulesAll(self):
        default = self.x.get_string()
        override = self.x.get_string(hrules=RuleStyle.ALL)
        self.assertTrue(default != override)

    def testHrulesNone(self):
        default = self.x.get_string()
        override = self.x.get_string(hrules=RuleStyle.NONE)
        self.assertTrue(default != override)

    def testRemoveRow(self):
        rc = self.x.rowcount
        self.x.del_row(0)
        assert self.x.rowcount + 1 == rc


class OptionAttributeTests(CityDataTest):
    """Make sure all options which have an attribute interface work as they should.
    Also make sure option settings are copied correctly when a table is cloned by
    slicing."""

    def testSetForAllColumns(self):
        self.x.field_names = sorted(self.x.field_names)
        self.x.align = "l"
        self.x.max_width = 10
        self.x.start = 2
        self.x.end = 4
        self.x.sortby = "Area"
        self.x.sort_key = lambda x: x
        self.x.reversesort = True
        self.x.header = True
        self.x.border = False
        self.x.hrule = True
        self.x.int_format = "4"
        self.x.float_format = "2.2"
        self.x.padding_width = 2
        self.x.left_padding_width = 2
        self.x.right_padding_width = 2
        self.x.vertical_char = "!"
        self.x.horizontal_char = "~"
        self.x.junction_char = "*"
        self.x.format = True
        self.x.attributes = {"class": "prettytable"}
        assert self.x.get_string() == self.x[:].get_string()

    def testSetForOneColumn(self):
        self.x.align["Rainfall"] = "l"
        self.x.max_width["Name"] = 10
        self.x.int_format["Population"] = "4"
        self.x.float_format["Area"] = "2.2"
        assert self.x.get_string() == self.x[:].get_string()


class BasicTests(CityDataTest):
    """Some very basic tests."""

    def testNoBlankLines(self):
        """No table should ever have blank lines in it."""

        string = self.x.get_string()
        lines = string.split("\n")
        self.assertTrue("\n" not in lines)

    def testAllLengthsEqual(self):
        """All lines in a table should be of the same length."""

        string = self.x.get_string()
        lines = string.split("\n")
        lengths = [len(line) for line in lines]
        lengths = set(lengths)
        self.assertEqual(len(lengths), 1)

    def testAddWrongSizedColumn(self):
        try:
            self.x.add_column("nb", list(range(self.x.rowcount-1)))
            assert False
        except PrettyTableException:
            assert True

    def testClearRows(self):
        self.x.clear_rows()
        assert self.x.rowcount == 0
        assert self.x.colcount > 0
        assert len(self.x.field_names) > 0

    def testClear(self):
        self.x.clear()
        assert self.x.rowcount == 0
        assert self.x.colcount == 0
        assert len(self.x.field_names) == 0

    def testCopy(self):
        str_x = self.x.get_string()
        y = self.x.copy()
        assert y.get_string() == str_x
        y.clear()
        assert self.x.get_string() == str_x
        assert y.get_string() != str_x

    def testSubTable(self):
        x3 = self.x[3]
        assert isinstance(x3, PrettyTable)
        assert x3.field_names == self.x.field_names
        assert x3.colcount == self.x.colcount
        assert x3.rowcount == 1

    def testWrongItem(self):
        try:
            x3 = self.x["3"]
            assert False
        except PrettyTableException:
            assert True


class TitleBasicTests(BasicTests):
    """Run the basic tests with a title"""

    def setUp(self):
        BasicTests.setUp(self)
        self.x.title = "My table"


class NoBorderBasicTests(BasicTests):
    """Run the basic tests with border = False"""

    def setUp(self):
        BasicTests.setUp(self)
        self.x.border = False


class NoHeaderBasicTests(BasicTests):
    """Run the basic tests with header = False"""

    def setUp(self):
        BasicTests.setUp(self)
        self.x.header = False


class HrulesNoneBasicTests(BasicTests):
    """Run the basic tests with hrules = NONE"""

    def setUp(self):
        BasicTests.setUp(self)
        self.x.hrules = RuleStyle.NONE


class HrulesAllBasicTests(BasicTests):
    """Run the basic tests with hrules = ALL"""

    def setUp(self):
        BasicTests.setUp(self)
        self.x.hrules = RuleStyle.ALL


class HrulesHeaderBasicTests(BasicTests):
    """Run the basic tests with hrules = ALL"""

    def setUp(self):
        BasicTests.setUp(self)
        self.x.hrules = RuleStyle.HEADER


class EmptyTableTests(BasicTests):
    """Make sure the print_empty option works"""

    def setUp(self):
        BasicTests.setUp(self)
        self.y = PrettyTable()

    def testRemoveRow(self):
        try:
            self.y.del_row(0)
            assert False
        except PrettyTableException:
            assert True

    def testDimensions(self):
        self.assertEquals(0, self.y.rowcount)
        self.assertEquals(0, self.y.colcount)

    def testPrintEmptyTrue(self):
        self.assertNotEquals("", self.y.get_string(print_empty=True))
        self.assertNotEquals(self.x.get_string(print_empty=True), self.y.get_string(print_empty=True))

    def testPrintEmptyFalse(self):
        self.assertEquals("", self.y.get_string(print_empty=False))
        self.assertNotEquals(self.y.get_string(print_empty=False), self.x.get_string(print_empty=False))

    def testInteractionWithBorder(self):
        self.assertEquals("", self.y.get_string(border=False, print_empty=True))

    def testPrintEmptyFalseConstructor(self):
        t = PrettyTable(print_empty=False)
        self.assertFalse(t.print_empty)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            """).strip(), result)

    def testPrintEmptyPropertySetter(self):
        t = PrettyTable(print_empty=False)
        self.assertFalse(t.print_empty)
        t.print_empty = True
        self.assertTrue(t.print_empty)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            ++
            ||
            ++
            ++
            """).strip(), result)

    def testPrintEmptyTrueConstructorNoheader(self):
        t = PrettyTable(header=False, print_empty=True)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            ++
            ++
            """).strip(), result)

    def testPrintEmptyTrueConstructorHeader(self):
        t = PrettyTable(header=True, print_empty=True)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            ++
            ||
            ++
            ++
            """).strip(), result)

    def testPrintEmptyNoVrule(self):
        t = PrettyTable(header=True, print_empty=True, vrules=RuleStyle.NONE)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            --
            """) + "  " + textwrap.dedent("""
            --
            --
            """).rstrip(), result)


class TableSortTest(unittest.TestCase):
    def createTable(self, **kwargs):
        t = PrettyTable(field_names=("c1", "c2"), header=False, sortby="c2", **kwargs)
        t.add_row([1, 9])
        t.add_row([2, 8])
        t.add_row([3, 7])
        t.add_row([4, 6])
        t.add_row([5, 5])
        return t

    def testSort(self):
        t = self.createTable()
        result = t.get_string(padding_width=0)
        self.assertEqual(result, textwrap.dedent("""\
            +-+-+
            |5|5|
            |4|6|
            |3|7|
            |2|8|
            |1|9|
            +-+-+
            """).strip())

    def testOldsortsliceConstructorFalse(self):
        t = self.createTable(start=1, end=3, oldsortslice=False)
        self.assertEqual(False, t.oldsortslice)
        result = t.get_string(padding_width=0)
        self.assertEqual(result, textwrap.dedent("""\
            +-+-+
            |4|6|
            |3|7|
            +-+-+
            """).strip())

    def testOldsortsliceConstructorTrue(self):
        t = self.createTable(start=1, end=3, oldsortslice=True)
        self.assertEqual(True, t.oldsortslice)
        result = t.get_string(padding_width=0)
        self.assertEqual(result, textwrap.dedent("""\
            +-+-+
            |3|7|
            |2|8|
            +-+-+
            """).strip())

    def testOldsortsliceSetAttrFalse(self):
        t = self.createTable(start=1, end=3)
        self.assertEqual(False, t.oldsortslice)
        t.oldsortslice = False
        self.assertEqual(False, t.oldsortslice)
        result = t.get_string(padding_width=0)
        self.assertEqual(result, textwrap.dedent("""\
            +-+-+
            |4|6|
            |3|7|
            +-+-+
            """).strip())

    def testOldsortsliceSetAttrTrue(self):
        t = self.createTable(start=1, end=3)
        self.assertEqual(False, t.oldsortslice)
        t.oldsortslice = True
        self.assertEqual(True, t.oldsortslice)
        result = t.get_string(padding_width=0)
        self.assertEqual(result, textwrap.dedent("""\
            +-+-+
            |3|7|
            |2|8|
            +-+-+
            """).strip())


class RangePrint(unittest.TestCase):
    def getTable(self, **kwargs):
        t = PrettyTable(("F",), **kwargs)
        for i in range(5):
            t.add_row([i])
        return t

    def testDefault(self):
        t = self.getTable()
        self.assertEqual(0, t.start)
        self.assertEqual(None, t.end)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +---+
            | F |
            +---+
            | 0 |
            | 1 |
            | 2 |
            | 3 |
            | 4 |
            +---+
            """).strip(), result)

    def testConstructorStart(self):
        t = self.getTable(start=2)
        self.assertEqual(2, t.start)
        self.assertEqual(None, t.end)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +---+
            | F |
            +---+
            | 2 |
            | 3 |
            | 4 |
            +---+
            """).strip(), result)

    def testConstructorEnd(self):
        t = self.getTable(end=2)
        self.assertEqual(0, t.start)
        self.assertEqual(2, t.end)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +---+
            | F |
            +---+
            | 0 |
            | 1 |
            +---+
            """).strip(), result)

    def testConstructorStartEnd(self):
        t = self.getTable(start=2, end=4)
        self.assertEqual(2, t.start)
        self.assertEqual(4, t.end)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +---+
            | F |
            +---+
            | 2 |
            | 3 |
            +---+
            """).strip(), result)

class EmptyTableTestsFieldNames(CityDataTest):
    """Make sure the print_empty option works"""

    def setUp(self):
        CityDataTest.setUp(self)
        self.y = PrettyTable()
        self.y.field_names = ["City name", "Area", "Population", "Annual Rainfall"]

    def testPrintEmptyTrue(self):
        assert self.y.get_string(print_empty=True) != ""
        assert self.x.get_string(print_empty=True) != self.y.get_string(print_empty=True)

    def testPrintEmptyFalse(self):
        assert self.y.get_string(print_empty=False) == ""
        assert self.y.get_string(print_empty=False) != self.x.get_string(print_empty=False)

    def testInteractionWithBorder(self):
        assert self.y.get_string(border=False, print_empty=True) == ""


class EmptyRowTests(unittest.TestCase):
    def setUp(self):
        self.y = PrettyTable()
        self.y.add_row([])

    def testSize(self):
        assert self.y.rowcount == 1
        assert self.y.colcount == 0


class FieldNamesTests(unittest.TestCase):

    def testDefault(self):
        t = PrettyTable()
        t.add_row([])
        self.assertEquals([], t.field_names)

    def testNewFieldNamesEmptyTable(self):
        t = PrettyTable(field_names=("1", "2", "3"))
        t.field_names = ("1", "2", "3", "4")
        self.assertListEqual(["1", "2", "3", "4"], t.field_names)

    def testExactFieldNames(self):
        t = PrettyTable(field_names=("a", "b"))
        t.add_row([1,2])
        result = t.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            +---+---+
            | a | b |
            +---+---+
            | 1 | 2 |
            +---+---+
            """).strip())

    def testConstructorTupleInt(self):
        t = PrettyTable(field_names=(1,2,3))
        t.add_row([4,5,6])
        result = t.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            +---+---+---+
            | 1 | 2 | 3 |
            +---+---+---+
            | 4 | 5 | 6 |
            +---+---+---+
            """).strip())

    def testTypeAttrTupleInt(self):
        t = PrettyTable(field_names=("x", "y", "z"))
        t.add_row([4,5,6])
        t.field_names = (1,2,3)
        result = t.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            +---+---+---+
            | 1 | 2 | 3 |
            +---+---+---+
            | 4 | 5 | 6 |
            +---+---+---+
            """).strip())

    def testBadTypeConstructorInt(self):
        try:
            PrettyTable(field_names=9)
            assert False
        except PrettyTableException:
            assert True

    def testBadTypeConstructorStr(self):
        try:
            PrettyTable(field_names="abc")
            assert False
        except PrettyTableException:
            assert True

    def testBadTypeAttrInt(self):
        try:
            t = PrettyTable(field_names=1)
            t.field_names = 4
            assert False
        except PrettyTableException:
            assert True

    def testBadTypeAttrStr(self):
        try:
            t = PrettyTable(field_names="abc")
            t.field_names = 4
            assert False
        except PrettyTableException:
            assert True

    def testTooFewFieldNamesConstructor(self):
        t = PrettyTable(field_names=("a",))
        try:
            t.add_row([1,2])
            assert False
        except PrettyTableException:
            assert True

    def testTooManyFieldNames(self):
        t = PrettyTable(field_names=("a", "b", "c"))
        try:
            t.add_row([1,2])
            assert False
        except PrettyTableException:
            assert True

    def testTooFewFieldNamesProperty(self):
        t = PrettyTable()
        t.add_row(["a1", "a2"])
        try:
            t.field_names = ["F1"]
            assert False
        except PrettyTableException:
            assert True

    def testTooManyFieldNamesProperty(self):
        t = PrettyTable()
        t.add_row(["a1", "a2"])
        try:
            t.field_names = ["F1"]
            assert False
        except PrettyTableException:
            assert True

    def testTooManyFieldNamesProperty2(self):
        t = PrettyTable()
        t.add_row([])
        try:
            t.field_names = ["F1"]
            assert False
        except PrettyTableException:
            assert True

    def testFieldNamesNotUnique(self):
        t = PrettyTable()
        t.add_row(["a1", "b1"])
        try:
            t.field_names = ["F", "F"]
            assert False
        except PrettyTableException:
            assert True


class BasicTestsStyle_MSWORD_FRIENDLY(BasicTests):
    """Run the basic tests after using set_style"""
    def setUp(self):
        BasicTests.setUp(self)
        self.x.set_style(TableStyle.MSWORD_FRIENDLY)


class BasicTestsStyle_PLAIN_COLUMNS(BasicTests):
    """Run the basic tests after using set_style"""
    def setUp(self):
        BasicTests.setUp(self)
        self.x.set_style(TableStyle.PLAIN_COLUMNS)


class LeftPaddingWidth(unittest.TestCase):
    def getTable(self, **kwargs):
        t = PrettyTable(("F",), **kwargs)
        t.add_row(["1"])
        return t

    def testDefault(self):
        t = self.getTable()
        self.assertEqual(None, t.left_padding_width)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +---+
            | F |
            +---+
            | 1 |
            +---+
            """).strip(), result)

    def testConstructor(self):
        t = self.getTable(left_padding_width=3)
        self.assertEqual(3, t.left_padding_width)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +-----+
            |   F |
            +-----+
            |   1 |
            +-----+
            """).strip(), result)

    def testSetAttr(self):
        t = self.getTable()
        self.assertEqual(None, t.left_padding_width)
        t.left_padding_width = 3
        self.assertEqual(3, t.left_padding_width)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +-----+
            |   F |
            +-----+
            |   1 |
            +-----+
            """).strip(), result)

    def testReset(self):
        t = self.getTable(left_padding_width=3)
        self.assertEqual(3, t.left_padding_width)
        t.left_padding_width = None
        self.assertEqual(None, t.left_padding_width)

    def testInvalid(self):
        t = self.getTable()
        try:
            t.left_padding_width = -1
            self.assertTrue(False)
        except PrettyTableException:
            self.assertTrue(True)


class RightPaddingWidth(unittest.TestCase):
    def getTable(self, **kwargs):
        t = PrettyTable(("F",), **kwargs)
        t.add_row(["1"])
        return t

    def testDefault(self):
        t = self.getTable()
        self.assertEqual(None, t.right_padding_width)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +---+
            | F |
            +---+
            | 1 |
            +---+
            """).strip(), result)

    def testConstructor(self):
        t = self.getTable(right_padding_width=3)
        self.assertEqual(3, t.right_padding_width)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +-----+
            | F   |
            +-----+
            | 1   |
            +-----+
            """).strip(), result)

    def testSetAttr(self):
        t = self.getTable()
        self.assertEqual(None, t.right_padding_width)
        t.right_padding_width = 3
        self.assertEqual(3, t.right_padding_width)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +-----+
            | F   |
            +-----+
            | 1   |
            +-----+
            """).strip(), result)

    def testReset(self):
        t = self.getTable(right_padding_width=3)
        self.assertEqual(3, t.right_padding_width)
        t.right_padding_width = None
        self.assertEqual(None, t.right_padding_width)

    def testInvalid(self):
        t = self.getTable()
        try:
            t.right_padding_width = -1
            self.assertTrue(False)
        except PrettyTableException:
            self.assertTrue(True)


class TestLeftRightPadding(unittest.TestCase):
    def testBoth(self):
        t = PrettyTable(("F",), left_padding_width=3, right_padding_width=7)
        t.add_row([1])
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +-----------+
            |   F       |
            +-----------+
            |   1       |
            +-----------+
            """).strip(), result)


class RandomStyleTests(BasicTests):
    """Run the basic tests after using set_style"""

    def setUp(self):
        BasicTests.setUp(self)
        self.x.set_style(RANDOM)


class InvalidStyleTest(unittest.TestCase):
    def testInvalidStyle(self):
        t = PrettyTable()
        try:
            t.set_style(1337)
            assert False
        except PrettyTableException:
            assert True


class DefaultStyleTests(BasicTests):
    """Run the basic tests after using set_style"""

    def setUp(self):
        BasicTests.setUp(self)
        self.x.set_style(DEFAULT)


class SortTests(unittest.TestCase):
    def getTable(self, **kwargs):
        t = PrettyTable(["F1"], **kwargs)
        t.add_row([3])
        t.add_row([2])
        t.add_row([0])
        return t

    def getFunc(self):
        return lambda x: abs(x[0] - 2)

    def testDefault(self):
        t = self.getTable()
        self.assertIsNotNone(t.sort_key)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +----+
            | F1 |
            +----+
            | 3  |
            | 2  |
            | 0  |
            +----+
            """).strip(), result)

    def testDefaultSort(self):
        t = self.getTable(sortby="F1")
        self.assertIsNotNone(t.sort_key)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +----+
            | F1 |
            +----+
            | 0  |
            | 2  |
            | 3  |
            +----+
            """).strip(), result)

    def testConstructor(self):
        f = self.getFunc()
        t = self.getTable(sort_key=f, sortby="F1")
        self.assertEqual(f, t.sort_key)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +----+
            | F1 |
            +----+
            | 2  |
            | 3  |
            | 0  |
            +----+
            """).strip(), result)

    def testSetAttr(self):
        f = self.getFunc()
        t = self.getTable()
        self.assertIsNone(t.sortby)
        t.sort_key = f
        t.sortby = "F1"
        self.assertEqual(f, t.sort_key)
        self.assertEqual("F1", t.sortby)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +----+
            | F1 |
            +----+
            | 2  |
            | 3  |
            | 0  |
            +----+
            """).strip(), result)

    def testGetString(self):
        f = self.getFunc()
        t = self.getTable()
        self.assertIsNone(t.sortby)
        result = t.get_string(sort_key=f, sortby="F1")
        self.assertIsNone(t.sortby)
        self.assertNotEqual(f, t.sort_key)
        self.assertEqual(textwrap.dedent("""\
            +----+
            | F1 |
            +----+
            | 2  |
            | 3  |
            | 0  |
            +----+
            """).strip(), result)

    def testReverseDefault(self):
        f = self.getFunc()
        t = self.getTable(sort_key=f, sortby="F1")
        self.assertEqual(False, t.reversesort)
        t.reversesort = True
        self.assertEqual(True, t.reversesort)
        result = t.get_string()
        self.assertEqual(textwrap.dedent("""\
            +----+
            | F1 |
            +----+
            | 0  |
            | 3  |
            | 2  |
            +----+
            """).strip(), result)

    def testInvalidSortFunc(self):
        try:
            self.getTable(sort_key=None)
            self.assertTrue(False)
        except PrettyTableException:
            self.assertTrue(True)


class SlicingTests(CityDataTest):
    def setUp(self):
        CityDataTest.setUp(self)

    def testSliceAll(self):
        y = self.x[:]
        assert self.x.get_string() == y.get_string()

    def testSliceFirstTwoRows(self):
        y = self.x[0:2]
        string = y.get_string()
        assert len(string.split("\n")) == 6
        assert "Adelaide" in string
        assert "Brisbane" in string
        assert "Melbourne" not in string
        assert "Perth" not in string

    def testSliceLastTwoRows(self):
        y = self.x[-2:]
        string = y.get_string()
        assert len(string.split("\n")) == 6
        assert "Adelaide" not in string
        assert "Brisbane" not in string
        assert "Melbourne" in string
        assert "Perth" in string


class SortingTests(CityDataTest):
    def setUp(self):
        CityDataTest.setUp(self)

    def testSortBy(self):
        self.x.sortby = self.x.field_names[0]
        old = self.x.get_string()
        for field in self.x.field_names[1:]:
            self.x.sortby = field
            new = self.x.get_string()
            assert new != old

    def testReverseSort(self):
        for field in self.x.field_names:
            self.x.sortby = field
            self.x.reversesort = False
            forward = self.x.get_string()
            self.x.reversesort = True
            backward = self.x.get_string()
            forward_lines = forward.split("\n")[2:]  # Discard header lines
            backward_lines = backward.split("\n")[2:]
            backward_lines.reverse()
            assert forward_lines == backward_lines

    def testSortKey(self):
        # Test sorting by length of city name
        def key(vals):
            vals[0] = len(vals[0])
            return vals

        self.x.sortby = "City name"
        self.x.sort_key = key
        assert self.x.get_string().strip() == textwrap.dedent("""\
            +-----------+------+------------+-----------------+
            | City name | Area | Population | Annual Rainfall |
            +-----------+------+------------+-----------------+
            |   Perth   | 5386 |  1554769   |      869.4      |
            |   Darwin  | 112  |   120900   |      1714.7     |
            |   Hobart  | 1357 |   205556   |      619.5      |
            |   Sydney  | 2058 |  4336374   |      1214.8     |
            |  Adelaide | 1295 |  1158259   |      600.5      |
            |  Brisbane | 5905 |  1857594   |      1146.4     |
            | Melbourne | 1566 |  3806092   |      646.9      |
            +-----------+------+------------+-----------------+
            """).strip()

    def testSortSlice(self):
        """Make sure sorting and slicing interact in the expected way"""
        x = PrettyTable(["Foo"])
        for i in range(20, 0, -1):
            x.add_row([i])
        newstyle = x.get_string(sortby="Foo", end=10)
        assert "10" in newstyle
        assert "20" not in newstyle
        oldstyle = x.get_string(sortby="Foo", end=10, oldsortslice=True)
        assert "10" not in oldstyle
        assert "20" in oldstyle


class IntegerFormatBasicTests(BasicTests):
    """Run the basic tests after setting an integer format string"""

    def setUp(self):
        BasicTests.setUp(self)
        self.x.int_format = "04"


class BreakLineTests(unittest.TestCase):
    def testAsciiBreakLine(self):
        t = PrettyTable(['Field 1', 'Field 2'])
        t.add_row(['value 1', 'value2\nsecond line'])
        t.add_row(['value 3', 'value4'])
        result = t.get_string(hrules=RuleStyle.ALL)
        assert result.strip() == textwrap.dedent("""\
            +---------+-------------+
            | Field 1 |   Field 2   |
            +---------+-------------+
            | value 1 |    value2   |
            |         | second line |
            +---------+-------------+
            | value 3 |    value4   |
            +---------+-------------+
            """).strip()

        t = PrettyTable(['Field 1', 'Field 2'])
        t.add_row(['value 1', 'value2\nsecond line'])
        t.add_row(['value 3\n\nother line', 'value4\n\n\nvalue5'])
        result = t.get_string(hrules=RuleStyle.ALL)
        assert result.strip() == textwrap.dedent("""\
            +------------+-------------+
            |  Field 1   |   Field 2   |
            +------------+-------------+
            |  value 1   |    value2   |
            |            | second line |
            +------------+-------------+
            |  value 3   |    value4   |
            |            |             |
            | other line |             |
            |            |    value5   |
            +------------+-------------+
            """).strip()

        t = PrettyTable(['Field 1', 'Field 2'])
        t.add_row(['value 1', 'value2\nsecond line'])
        t.add_row(['value 3\n\nother line', 'value4\n\n\nvalue5'])
        result = t.get_string()
        assert result.strip() == textwrap.dedent("""\
            +------------+-------------+
            |  Field 1   |   Field 2   |
            +------------+-------------+
            |  value 1   |    value2   |
            |            | second line |
            |  value 3   |    value4   |
            |            |             |
            | other line |             |
            |            |    value5   |
            +------------+-------------+
            """).strip()

    def testHtmlBreakLine(self):
        t = PrettyTable(['Field 1', 'Field 2'])
        t.add_row(['value 1', 'value2\nsecond line'])
        t.add_row(['value 3', 'value4'])
        result = t.get_html_string(hrules=RuleStyle.ALL)
        self.assertEquals(textwrap.dedent("""\
            <table>
                <thead>
                    <tr>
                        <th>Field 1</th>
                        <th>Field 2</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>value 1</td>
                        <td>value2<br>second line</td>
                    </tr>
                    <tr>
                        <td>value 3</td>
                        <td>value4</td>
                    </tr>
                </tbody>
            </table>
            """).strip(), result.strip())

    def testXHtml(self):
        t = PrettyTable(['Field 1', 'Field 2'], xhtml=True)
        t.add_row(['value 1', 'value2\nsecond line'])
        t.add_row(['value 3', 'value4'])
        result = t.get_html_string(hrules=RuleStyle.ALL)
        self.assertEqual(result.strip(), textwrap.dedent("""\
            <table>
                <thead>
                    <tr>
                        <th>Field 1</th>
                        <th>Field 2</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>value 1</td>
                        <td>value2<br/>second line</td>
                    </tr>
                    <tr>
                        <td>value 3</td>
                        <td>value4</td>
                    </tr>
                </tbody>
            </table>
            """).strip())


class HtmlOutputTests(unittest.TestCase):
    def testHtmlOutput(self):
        t = PrettyTable(['Field 1', 'Field 2', 'Field 3'])
        t.add_row(['value 1', 'value2', 'value3'])
        t.add_row(['value 4', 'value5', 'value6'])
        t.add_row(['value 7', 'value8', 'value9'])
        result = t.get_html_string()
        assert result.strip() == textwrap.dedent("""\
            <table>
                <thead>
                    <tr>
                        <th>Field 1</th>
                        <th>Field 2</th>
                        <th>Field 3</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>value 1</td>
                        <td>value2</td>
                        <td>value3</td>
                    </tr>
                    <tr>
                        <td>value 4</td>
                        <td>value5</td>
                        <td>value6</td>
                    </tr>
                    <tr>
                        <td>value 7</td>
                        <td>value8</td>
                        <td>value9</td>
                    </tr>
                </tbody>
            </table>
            """).strip()

    def testFields(self):
        t = PrettyTable(['Field 1', 'Field 2', 'Field 3'])
        t.add_row(['value 1', 'value2', 'value3'])
        t.add_row(['value 4', 'value5', 'value6'])
        t.add_row(['value 7', 'value8', 'value9'])
        result = t.get_html_string(fields=("Field 1", "Field 2"))
        self.assertEqual(textwrap.dedent("""\
            <table>
                <thead>
                    <tr>
                        <th>Field 1</th>
                        <th>Field 2</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>value 1</td>
                        <td>value2</td>
                    </tr>
                    <tr>
                        <td>value 4</td>
                        <td>value5</td>
                    </tr>
                    <tr>
                        <td>value 7</td>
                        <td>value8</td>
                    </tr>
                </tbody>
            </table>
            """).strip(), result.strip())

    def testHtmlOutputFormated(self):
        t = PrettyTable(['Field 1', 'Field 2', 'Field 3'])
        t.add_row(['value 1', 'value2', 'value3'])
        t.add_row(['value 4', 'value5\nvalue5b', 'value6'])
        t.add_row(['value 7', 'value8', 'value9'])
        result = t.get_html_string(format=True)
        self.assertEqual(textwrap.dedent("""\
            <table frame="box" rules="cols">
                <thead>
                    <tr>
                        <th style="padding-left: 1em; padding-right: 1em; text-align: center">Field 1</th>
                        <th style="padding-left: 1em; padding-right: 1em; text-align: center">Field 2</th>
                        <th style="padding-left: 1em; padding-right: 1em; text-align: center">Field 3</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value 1</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value2</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value3</td>
                    </tr>
                    <tr>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value 4</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value5<br>value5b</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value6</td>
                    </tr>
                    <tr>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value 7</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value8</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value9</td>
                    </tr>
                </tbody>
            </table>
            """).strip(), result.strip())

    def testHtmlOutputFormatedXhtml(self):
        t = PrettyTable(['Field 1', 'Field 2', 'Field 3'], xhtml=True)
        t.add_row(['value 1', 'value2', 'value3'])
        t.add_row(['value 4', 'value5\nvalue5b', 'value6'])
        t.add_row(['value 7', 'value8', 'value9'])
        result = t.get_html_string(format=True)
        assert result.strip() == textwrap.dedent("""\
            <table frame="box" rules="cols">
                <thead>
                    <tr>
                        <th style="padding-left: 1em; padding-right: 1em; text-align: center">Field 1</th>
                        <th style="padding-left: 1em; padding-right: 1em; text-align: center">Field 2</th>
                        <th style="padding-left: 1em; padding-right: 1em; text-align: center">Field 3</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value 1</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value2</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value3</td>
                    </tr>
                    <tr>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value 4</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value5<br/>value5b</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value6</td>
                    </tr>
                    <tr>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value 7</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value8</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value9</td>
                    </tr>
                </tbody>
            </table>
            """).strip()

    def testFormatedFieldsConstructor(self):
        t = PrettyTable(['Field 1', 'Field 2', 'Field 3'], format=True)
        self.assertEqual(True, t.format)

    def testFormatedFields(self):
        t = PrettyTable(['Field 1', 'Field 2', 'Field 3'], xhtml=True)
        t.add_row(['value 1', 'value2', 'value3'])
        t.add_row(['value 4', 'value5\nvalue5b', 'value6'])
        t.add_row(['value 7', 'value8', 'value9'])
        result = t.get_html_string(format=True, fields=("Field 2", "Field 3"))
        assert result.strip() == textwrap.dedent("""\
            <table frame="box" rules="cols">
                <thead>
                    <tr>
                        <th style="padding-left: 1em; padding-right: 1em; text-align: center">Field 2</th>
                        <th style="padding-left: 1em; padding-right: 1em; text-align: center">Field 3</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value2</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value3</td>
                    </tr>
                    <tr>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value5<br/>value5b</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value6</td>
                    </tr>
                    <tr>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value8</td>
                        <td style="padding-left: 1em; padding-right: 1em; text-align: center; vertical-align: top">value9</td>
                    </tr>
                </tbody>
            </table>
            """).strip()

    def testTitle(self):
        t = PrettyTable(['Field 1', 'Field 2'], title="Important data")
        t.add_row(['value 1', 'value2'])
        t.add_row(['value 3', 'value4'])
        result = t.get_html_string()
        self.assertEqual(result.strip(), textwrap.dedent("""\
            <table>
                <tr>
                    <td colspan=2>Important data</td>
                </tr>
                <thead>
                    <tr>
                        <th>Field 1</th>
                        <th>Field 2</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>value 1</td>
                        <td>value2</td>
                    </tr>
                    <tr>
                        <td>value 3</td>
                        <td>value4</td>
                    </tr>
                </tbody>
            </table>
            """).strip())

    def testAttributes(self):
        attrs = OrderedDict()
        attrs["title"] = "testdata"
        attrs["lang"] = "en"
        t = PrettyTable(['Field 1', 'Field 2'], attributes=attrs)
        t.add_row(['value 1', 'value2'])
        t.add_row(['value 3', 'value4'])
        self.assertDictEqual({"title":"testdata", "lang": "en"}, t.attributes)
        result = t.get_html_string()
        self.assertEqual(result.strip(), textwrap.dedent("""\
            <table title="testdata" lang="en">
                <thead>
                    <tr>
                        <th>Field 1</th>
                        <th>Field 2</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>value 1</td>
                        <td>value2</td>
                    </tr>
                    <tr>
                        <td>value 3</td>
                        <td>value4</td>
                    </tr>
                </tbody>
            </table>
            """).strip())

    def testAttributesInvalid(self):
        t = PrettyTable()
        try:
            t.attributes = "a=b"
            assert False
        except PrettyTableException:
            assert True

    def testTag(self):
        t = PrettyTable(['Field 1', 'Field 2'], title="Important data")
        t.add_row(['value 1', 'value2'])
        t.add_row(['value 3', 'value4'])
        result = t.get_html_string()
        self.assertEqual(result.strip(), textwrap.dedent("""\
            <table>
                <tr>
                    <td colspan=2>Important data</td>
                </tr>
                <thead>
                    <tr>
                        <th>Field 1</th>
                        <th>Field 2</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>value 1</td>
                        <td>value2</td>
                    </tr>
                    <tr>
                        <td>value 3</td>
                        <td>value4</td>
                    </tr>
                </tbody>
            </table>
            """).strip())


class HAlignTests(unittest.TestCase):
    def setUp(self):
        t = PrettyTable(header=False, field_names=("c1", "c2", "c3"))
        t.add_row(["aaaaa", "a",     "a"])
        t.add_row(["aaaa", "aaa",   "aa"])
        t.add_row(["aaa", "aaaaa", "aaa"])
        t.add_row(["aa",   "aaa", "aaaa"])
        t.add_row(["a",    "a" , "aaaaa"])
        t.align["c1"] = "l"
        t.align["c2"] = "c"
        t.align["c3"] = "r"
        self.x = t

    def testString(self):
        result = self.x.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            +-------+-------+-------+
            | aaaaa |   a   |     a |
            | aaaa  |  aaa  |    aa |
            | aaa   | aaaaa |   aaa |
            | aa    |  aaa  |  aaaa |
            | a     |   a   | aaaaa |
            +-------+-------+-------+""").strip())

    def testInvalidHalignKey(self):
        table = PrettyTable(field_names=("f1", "f2"))
        try:
            table.align = "XX"
            assert False
        except PrettyTableException:
            assert True


class ValignTests(unittest.TestCase):
    def testDefault(self):
        table = PrettyTable(field_names=("f1", "f2"))
        self.assertDictEqual({"f1": "t", "f2": "t"}, table.valign)
        table.add_row(("a1\n"
                       "a2\n"
                       "a3", "b1"))
        table.add_row(("c1", "d1\nd2\nd3"))
        self.assertEqual(textwrap.dedent("""\
            +----+----+
            | f1 | f2 |
            +----+----+
            | a1 | b1 |
            | a2 |    |
            | a3 |    |
            | c1 | d1 |
            |    | d2 |
            |    | d3 |
            +----+----+
            """).strip(), table.get_string())

    def testVAlignMid(self):
        table = PrettyTable(field_names=("f1", "f2"), valign="m")
        table.add_row(("a1\n"
                       "a2\n"
                       "a3", "b1"))
        self.assertEquals(table.valign, {"f1": "m", "f2": "m"})
        table.add_row(("c1", "d1\nd2\nd3"))
        self.assertEqual(textwrap.dedent("""\
            +----+----+
            | f1 | f2 |
            +----+----+
            | a1 |    |
            | a2 | b1 |
            | a3 |    |
            |    | d1 |
            | c1 | d2 |
            |    | d3 |
            +----+----+
            """).strip(), table.get_string())

    def testVAlignBottom(self):
        table = PrettyTable(field_names=("f1", "f2"), valign="b")
        table.add_row(("a1\n"
                       "a2\n"
                       "a3", "b1"))
        self.assertEquals(table.valign, {"f1": "b", "f2": "b"})
        table.add_row(("c1", "d1\nd2\nd3"))
        self.assertEqual(textwrap.dedent("""\
            +----+----+
            | f1 | f2 |
            +----+----+
            | a1 |    |
            | a2 |    |
            | a3 | b1 |
            |    | d1 |
            |    | d2 |
            | c1 | d3 |
            +----+----+
            """).strip(), table.get_string())

    def testVAlignMixed(self):
        table = PrettyTable(field_names=("f1", "f2"))
        table.add_row(("a1\n"
                       "a2\n"
                       "a3", "b1"))
        table.add_row(("c1", "d1\nd2\nd3"))
        table.valign = {"f1": "t", "f2": "b"}
        self.assertEquals(table.valign, {"f1": "t", "f2": "b"})
        self.assertEqual(textwrap.dedent("""\
            +----+----+
            | f1 | f2 |
            +----+----+
            | a1 |    |
            | a2 |    |
            | a3 | b1 |
            | c1 | d1 |
            |    | d2 |
            |    | d3 |
            +----+----+
            """).strip(), table.get_string())
        table.valign = {"f1": "m", "f2": "t"}
        self.assertEquals(table.valign, {"f1": "m", "f2": "t"})
        self.assertEqual(textwrap.dedent("""\
            +----+----+
            | f1 | f2 |
            +----+----+
            | a1 | b1 |
            | a2 |    |
            | a3 |    |
            |    | d1 |
            | c1 | d2 |
            |    | d3 |
            +----+----+
            """).strip(), table.get_string())

    def testInvalidValignKeys(self):
        table = PrettyTable(field_names=("f1", "f2"))
        table.valign = {}
        try:
            table.valign = {"f1": "t"}
            assert False
        except PrettyTableException:
            assert True
        try:
            table.valign = {"f1": "t", "f2": "t", "f3": "t"}
            assert False
        except PrettyTableException:
            assert True
        table.valign = {"f1": "t", "f2": "t"}

    def testInvalidValignKey(self):
        table = PrettyTable(field_names=("f1", "f2"))
        try:
            table.valign = "XX"
            assert False
        except PrettyTableException:
            assert True

    def testVAlignAfterFieldNamesChange(self):
        table = PrettyTable(field_names=("f1", "f2"), valign="b")
        self.assertEquals(table.valign, {"f1": "b", "f2": "b"})
        table.field_names = ("F1", "F2")
        self.assertEqual({"F1": "b", "F2": "b"}, table.valign)


class HrulesTest(unittest.TestCase):
    def testVrulesDefault(self):
        table = PrettyTable(field_names=("f1", "f2"))
        self.assertEqual(table.hrules, RuleStyle.FRAME)

    def testHrulesALL(self):
        table = PrettyTable(field_names=("f1", "f2"), hrules=RuleStyle.ALL)
        table.add_row(["a1", "b1"])
        table.add_row(["c1", "d1"])
        self.assertEqual(table.hrules, RuleStyle.ALL)
        self.assertEqual(textwrap.dedent("""\
            +----+----+
            | f1 | f2 |
            +----+----+
            | a1 | b1 |
            +----+----+
            | c1 | d1 |
            +----+----+            
        """).strip(), table.get_string())

    def testHrulesHEADER(self):
        table = PrettyTable(field_names=("f1", "f2"), hrules=RuleStyle.HEADER)
        table.add_row(["a1", "b1"])
        table.add_row(["c1", "d1"])
        self.assertEquals(table.hrules, RuleStyle.HEADER)
        self.assertEqual(textwrap.dedent("""\
            | f1 | f2 |
            +----+----+
            | a1 | b1 |
            | c1 | d1 |            
        """).strip(), table.get_string())

    def testHrulesFRAME(self):
        table = PrettyTable(field_names=("f1", "f2"), hrules=RuleStyle.FRAME)
        table.add_row(["a1", "b1"])
        table.add_row(["c1", "d1"])
        self.assertEquals(table.hrules, RuleStyle.FRAME)
        self.assertEqual(textwrap.dedent("""\
            +----+----+
            | f1 | f2 |
            +----+----+
            | a1 | b1 |
            | c1 | d1 |
            +----+----+            
        """).strip(), table.get_string())

    def testHrulesNONE(self):
        table = PrettyTable(field_names=("f1", "f2"), hrules=RuleStyle.NONE)
        table.add_row(["a1", "b1"])
        table.add_row(["c1", "d1"])
        self.assertEquals(table.hrules, RuleStyle.NONE)
        self.assertEqual(textwrap.dedent("""\
            | f1 | f2 |
            | a1 | b1 |
            | c1 | d1 |   
        """).strip(), table.get_string())

    def testInvalid(self):
        t = PrettyTable()
        try:
            t.hrules = 0x1337
            assert False
        except PrettyTableException:
            assert True


class TableCharTests(unittest.TestCase):

    def getTable(self):
        t = PrettyTable(field_names=("H1", "H2"))
        t.add_row(["a1", "b1"])
        t.add_row(["c1", "d1"])
        return t

    def getText(self, vchar="|", hchar="-", jchar="+"):
        trans = str.maketrans("|-+", "{}{}{}".format(vchar, hchar, jchar))
        return textwrap.dedent("""\
            +----+----+
            | H1 | H2 |
            +----+----+
            | a1 | b1 |
            | c1 | d1 |
            +----+----+
            """).strip().translate(trans)

    def testDefault(self):
        t = self.getTable()
        self.assertEquals(self.getText(), t.get_string())

    def testVchar(self):
        t = self.getTable()
        t.vertical_char = "!"
        self.assertEqual("!", t.vertical_char)
        self.assertEquals(self.getText(vchar="!"), t.get_string())

    def testHchar(self):
        t = self.getTable()
        t.horizontal_char = "_"
        self.assertEqual("_", t.horizontal_char)
        self.assertEquals(self.getText(hchar="_"), t.get_string())

    def testJchar(self):
        t = self.getTable()
        t.junction_char = "#"
        self.assertEqual("#", t.junction_char)
        self.assertEquals(self.getText(jchar="#"), t.get_string())

    def testAll(self):
        t = PrettyTable(field_names=("F", "G"))
        t.add_row(["a", "b"])
        t.add_row(["c", "d"])
        t.vertical_char = "!"
        t.horizontal_char = "_"
        t.junction_char= "%"
        self.assertEquals(textwrap.dedent("""\
            %___%___%
            ! F ! G !
            %___%___%
            ! a ! b !
            ! c ! d !
            %___%___%
             """).strip(), t.get_string())

    def testIllegalChar(self):
        t = PrettyTable()
        try:
            t.junction_char = "PP"
            assert False
        except PrettyTableException:
            assert True


class VrulesTest(unittest.TestCase):
    def testVrulesDefault(self):
        table = PrettyTable(field_names=("f1", "f2"))
        self.assertEqual(table.vrules, RuleStyle.ALL)

    def testVrulesSetAttr(self):
        table = PrettyTable(field_names=("f1", "f2"))
        self.assertEqual(table.vrules, RuleStyle.ALL)
        table.vrules = RuleStyle.FRAME
        self.assertEqual(table.vrules, RuleStyle.FRAME)

    def testVrulesALL(self):
        table = PrettyTable(field_names=("f1", "f2"), vrules=RuleStyle.ALL)
        table.add_row(["a1", "b1"])
        table.add_row(["c1", "d1"])
        self.assertEqual(table.vrules, RuleStyle.ALL)
        self.assertEqual(textwrap.dedent("""\
            +----+----+
            | f1 | f2 |
            +----+----+
            | a1 | b1 |
            | c1 | d1 |
            +----+----+            
        """).strip(), table.get_string())

    def testVrulesHEADER(self):
        try:
            PrettyTable(field_names=("f1", "f2"), vrules=RuleStyle.HEADER)
            assert False
        except PrettyTableException:
            assert True

    def testVrulesFRAME(self):
        table = PrettyTable(field_names=("f1", "f2"), vrules=RuleStyle.FRAME)
        table.add_row(["a1", "b1"])
        table.add_row(["c1", "d1"])
        self.assertEquals(table.vrules, RuleStyle.FRAME)
        self.assertEqual(textwrap.dedent("""\
            +---------+
            | f1   f2 |
            +---------+
            | a1   b1 |
            | c1   d1 |
            +---------+            
        """).strip(), table.get_string())

    def testVrulesNONE(self):
        table = PrettyTable(field_names=("f1", "f2"), vrules=RuleStyle.NONE)
        self.assertEquals(RuleStyle.NONE, table.vrules)
        table.add_row(["a1", "b1"])
        table.add_row(["c1", "d1"])
        self.assertEquals(table.vrules, RuleStyle.NONE)
        self.assertEqual(textwrap.dedent("""\
            -----------
              f1   f2  
            -----------
              a1   b1  
              c1   d1  
            -----------            
        """).strip(), table.get_string())

    def testVrulesIllegal(self):
        table = PrettyTable()
        try:
            table.vrules = 1337
            self.assertTrue(False)
        except PrettyTableException:
            self.assertTrue(True)



class PaginateTests(unittest.TestCase):
    def getTable(self):
        t = PrettyTable(("F1", "F2"))
        t.add_row(["a1", "b1"])
        t.add_row(["a2", "b2"])
        t.add_row(["a3", "b3"])
        t.add_row(["a4", "b4"])
        t.add_row(["a5", "b5"])
        t.add_row(["a6", "b6"])
        return t

    def testPaginate(self):
        self.assertEquals("\f".join((textwrap.dedent("""\
            +----+----+
            | F1 | F2 |
            +----+----+
            | a1 | b1 |
            | a2 | b2 |
            | a3 | b3 |
            +----+----+
            """).strip(), textwrap.dedent("""\
            +----+----+
            | F1 | F2 |
            +----+----+
            | a4 | b4 |
            | a5 | b5 |
            | a6 | b6 |
            +----+----+
            """).strip())), self.getTable().paginate(3))

    def testPaginate2(self):
        self.assertEquals("\f".join((textwrap.dedent("""\
            +----+----+
            | F1 | F2 |
            +----+----+
            | a1 | b1 |
            | a2 | b2 |
            +----+----+
            """).strip(), textwrap.dedent("""\
            +----+----+
            | F1 | F2 |
            +----+----+
            | a3 | b3 |
            | a4 | b4 |
            +----+----+
            """).strip(), textwrap.dedent("""\
            +----+----+
            | F1 | F2 |
            +----+----+
            | a5 | b5 |
            | a6 | b6 |
            +----+----+
            """).strip())), self.getTable().paginate(2))


if _have_sqlite:
    class DatabaseConstructorTest(BasicTests):
        def setUp(self):
            self.conn = sqlite3.connect(":memory:")
            self.cur = self.conn.cursor()
            self.cur.execute("CREATE TABLE cities (name TEXT, area INTEGER, population INTEGER, rainfall REAL)")
            self.cur.execute("INSERT INTO cities VALUES (\"Adelaide\", 1295, 1158259, 600.5)")
            self.cur.execute("INSERT INTO cities VALUES (\"Brisbane\", 5905, 1857594, 1146.4)")
            self.cur.execute("INSERT INTO cities VALUES (\"Darwin\", 112, 120900, 1714.7)")
            self.cur.execute("INSERT INTO cities VALUES (\"Hobart\", 1357, 205556, 619.5)")
            self.cur.execute("INSERT INTO cities VALUES (\"Sydney\", 2058, 4336374, 1214.8)")
            self.cur.execute("INSERT INTO cities VALUES (\"Melbourne\", 1566, 3806092, 646.9)")
            self.cur.execute("INSERT INTO cities VALUES (\"Perth\", 5386, 1554769, 869.4)")
            self.cur.execute("SELECT * FROM cities")
            self.x = from_db_cursor(self.cur)

        def testNonSelectCurosr(self):
            self.cur.execute("INSERT INTO cities VALUES (\"Adelaide\", 1295, 1158259, 600.5)")
            assert from_db_cursor(self.cur) is None


class JunctionCharTest(unittest.TestCase):
    def get_table(self, **kwargs):
        t = PrettyTable(header=False, **kwargs)
        t.add_row("ab")
        t.add_row("cd")
        return t

    def testDefaultJunction(self):
        t = self.get_table()
        result = t.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            +---+---+
            | a | b |
            | c | d |
            +---+---+""").strip())
        self.assertEqual(t.junction_char, "+")

    def testCustomJuction_char(self):
        t = self.get_table(junction_char="#")
        result = t.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            #---#---#
            | a | b |
            | c | d |
            #---#---#""").strip())
        self.assertEqual(t.junction_char, "#")


class PrintEnglishTest(CityDataTest):
    def setUp(self):
        x = PrettyTable(["City name", "Area", "Population", "Annual Rainfall"])
        x.title = "Australian capital cities"
        x.sortby = "Population"
        x.reversesort = True
        x.int_format["Area"] = "04"
        x.float_format = "6.1"
        x.align["City name"] = "l"  # Left align city names
        x.add_row(["Adelaide", 1295, 1158259, 600.5])
        x.add_row(["Brisbane", 5905, 1857594, 1146.4])
        x.add_row(["Darwin", 112, 120900, 1714.7])
        x.add_row(["Hobart", 1357, 205556, 619.5])
        x.add_row(["Sydney", 2058, 4336374, 1214.8])
        x.add_row(["Melbourne", 1566, 3806092, 646.9])
        x.add_row(["Perth", 5386, 1554769, 869.4])
        self.x = x

        y = PrettyTable(["City name", "Area", "Population", "Annual Rainfall"],
                        title="Australian capital cities",
                        sortby="Population",
                        reversesort=True,
                        int_format="04",
                        float_format="6.1",
                        max_width=12,
                        min_width=4,
                        align="c",
                        valign="t")
        y.align["City name"] = "l"  # Left align city names
        y.add_row(["Adelaide", 1295, 1158259, 600.5])
        y.add_row(["Brisbane", 5905, 1857594, 1146.4])
        y.add_row(["Darwin", 112, 120900, 1714.7])
        y.add_row(["Hobart", 1357, 205556, 619.5])
        y.add_row(["Sydney", 2058, 4336374, 1214.8])
        y.add_row(["Melbourne", 1566, 3806092, 646.9])
        y.add_row(["Perth", 5386, 1554769, 869.4])
        self.y = y

    def test_h_print(self):
        stdout = StringIO()
        print(file=stdout)
        print("Generated using setters:", file=stdout)
        print(self.x, file=stdout)
        self.assertEquals(textwrap.dedent("""\
            
            Generated using setters:
            +-------------------------------------------------+
            |            Australian capital cities            |
            +-----------+------+------------+-----------------+
            | City name | Area | Population | Annual Rainfall |
            +-----------+------+------------+-----------------+
            | Sydney    | 2058 |  4336374   |      1214.8     |
            | Melbourne | 1566 |  3806092   |       646.9     |
            | Brisbane  | 5905 |  1857594   |      1146.4     |
            | Perth     | 5386 |  1554769   |       869.4     |
            | Adelaide  | 1295 |  1158259   |       600.5     |
            | Hobart    | 1357 |   205556   |       619.5     |
            | Darwin    | 0112 |   120900   |      1714.7     |
            +-----------+------+------------+-----------------+
            """), stdout.getvalue())

    def test_v_print(self):
        stdout = StringIO()
        print(file=stdout)
        print("Generated using constructor arguments:", file=stdout)
        print(self.y, file=stdout)
        self.assertEquals(textwrap.dedent("""\
            
            Generated using constructor arguments:
            +-------------------------------------------------+
            |            Australian capital cities            |
            +-----------+------+------------+-----------------+
            | City name | Area | Population | Annual Rainfall |
            +-----------+------+------------+-----------------+
            | Sydney    | 2058 |  4336374   |      1214.8     |
            | Melbourne | 1566 |  3806092   |       646.9     |
            | Brisbane  | 5905 |  1857594   |      1146.4     |
            | Perth     | 5386 |  1554769   |       869.4     |
            | Adelaide  | 1295 |  1158259   |       600.5     |
            | Hobart    | 1357 |   205556   |       619.5     |
            | Darwin    | 0112 |   120900   |      1714.7     |
            +-----------+------+------------+-----------------+
            """), stdout.getvalue())


class HeaderStyleTest(unittest.TestCase):
    def get_table(self, **kwargs):
        t = PrettyTable(field_names=("colUMn oNe", "cOlumn twO"), **kwargs)
        return t

    def testNoHeaderStyle(self):
        t = self.get_table()
        result = t.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            +------------+------------+
            | colUMn oNe | cOlumn twO |
            +------------+------------+
            +------------+------------+""").strip())
        self.assertEqual(t.header_style, None)

    def testSetHeaderStyle(self):
        t = self.get_table()
        result = t.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            +------------+------------+
            | colUMn oNe | cOlumn twO |
            +------------+------------+
            +------------+------------+""").strip())
        self.assertEqual(t.header_style, None)
        t.header_style = "title"
        result = t.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            +------------+------------+
            | Column One | Column Two |
            +------------+------------+
            +------------+------------+""").strip())
        self.assertEqual(t.header_style, "title")

    def testHeaderStyleCap(self):
        t = self.get_table(header_style="cap")
        result = t.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            +------------+------------+
            | Column one | Column two |
            +------------+------------+
            +------------+------------+""").strip())
        self.assertEqual(t.header_style, "cap")

    def testHeaderStyleTitle(self):
        t = self.get_table(header_style="title")
        result = t.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            +------------+------------+
            | Column One | Column Two |
            +------------+------------+
            +------------+------------+""").strip())
        self.assertEqual(t.header_style, "title")

    def testHeaderStyleLower(self):
        t = self.get_table(header_style="lower")
        result = t.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            +------------+------------+
            | column one | column two |
            +------------+------------+
            +------------+------------+""").strip())
        self.assertEqual(t.header_style, "lower")

    def testHeaderStyleUpper(self):
        t = self.get_table(header_style="upper")
        result = t.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            +------------+------------+
            | COLUMN ONE | COLUMN TWO |
            +------------+------------+
            +------------+------------+""").strip())
        self.assertEqual(t.header_style, "upper")

    def testHeaderStyleInvalid(self):
        try:
            self.get_table(header_style="XXXX")
            assert False
        except PrettyTableException:
            assert True


class TitleTests(unittest.TestCase):
    def getTable(self, **kwargs):
        t = PrettyTable(("F1", "F2"), **kwargs)
        t.add_row(["a1", "b1"])
        t.add_row(["a2", "b2"])
        return t

    def testConstructor(self):
        t = self.getTable(title="mytitle")
        self.assertEqual("mytitle", t.title)
        self.assertEqual(textwrap.dedent("""
            +---------+
            | mytitle |
            +----+----+
            | F1 | F2 |
            +----+----+
            | a1 | b1 |
            | a2 | b2 |
            +----+----+
            """).strip(), t.get_string())

    def testAssignAttr(self):
        t = self.getTable()
        t.title = "mytitle"
        self.assertEqual("mytitle", t.title)
        self.assertEqual(textwrap.dedent("""
            +---------+
            | mytitle |
            +----+----+
            | F1 | F2 |
            +----+----+
            | a1 | b1 |
            | a2 | b2 |
            +----+----+
            """).strip(), t.get_string())

    def testGetString(self):
        t = self.getTable()
        result = t.get_string(title="mytitle")
        self.assertIsNone(t.title)
        self.assertEqual(textwrap.dedent("""
            +---------+
            | mytitle |
            +----+----+
            | F1 | F2 |
            +----+----+
            | a1 | b1 |
            | a2 | b2 |
            +----+----+
            """).strip(), result)

    def testHrulesNONE(self):
        t = self.getTable(hrules=RuleStyle.NONE)
        result = t.get_string(title="mytitle")
        self.assertIsNone(t.title)
        self.assertEqual(textwrap.dedent("""
            | mytitle |
            | F1 | F2 |
            | a1 | b1 |
            | a2 | b2 |
            """).strip(), result)

    def testHrulesALL(self):
        t = self.getTable(hrules=RuleStyle.ALL)
        result = t.get_string(title="mytitle")
        self.assertIsNone(t.title)
        self.assertEqual(textwrap.dedent("""
            +---------+
            | mytitle |
            +----+----+
            | F1 | F2 |
            +----+----+
            | a1 | b1 |
            +----+----+
            | a2 | b2 |
            +----+----+
            """).strip(), result)

    def testHrulesFRAME(self):
        t = self.getTable(hrules=RuleStyle.FRAME)
        result = t.get_string(title="mytitle")
        self.assertIsNone(t.title)
        self.assertEqual(textwrap.dedent("""
            +---------+
            | mytitle |
            +----+----+
            | F1 | F2 |
            +----+----+
            | a1 | b1 |
            | a2 | b2 |
            +----+----+
            """).strip(), result)

    def testVrulesNONE(self):
        t = self.getTable(vrules=RuleStyle.NONE)
        result = t.get_string(title="mytitle")
        self.assertIsNone(t.title)
        self.assertEqual(textwrap.dedent("""
            -----------
              mytitle  
            -----------
              F1   F2  
            -----------
              a1   b1  
              a2   b2  
            -----------
            """).strip(), result)

    def testVrulesFRAME(self):
        t = self.getTable(vrules=RuleStyle.FRAME)
        result = t.get_string(title="mytitle")
        self.assertIsNone(t.title)
        self.assertEqual(textwrap.dedent("""
            +---------+
            | mytitle |
            +---------+
            | F1   F2 |
            +---------+
            | a1   b1 |
            | a2   b2 |
            +---------+
            """).strip(), result)

    def testVrulesALL(self):
        t = self.getTable(vrules=RuleStyle.ALL)
        result = t.get_string(title="mytitle")
        self.assertIsNone(t.title)
        self.assertEqual(textwrap.dedent("""
            +---------+
            | mytitle |
            +----+----+
            | F1 | F2 |
            +----+----+
            | a1 | b1 |
            | a2 | b2 |
            +----+----+
            """).strip(), result)


class PrintJapaneseTest(unittest.TestCase):
    def setUp(self):
        self.x = PrettyTable(["Kanji", "Hiragana", "English"])
        self.x.add_row(["神戸", "こうべ", "Kobe"])
        self.x.add_row(["京都", "きょうと", "Kyoto"])
        self.x.add_row(["長崎", "ながさき", "Nagasaki"])
        self.x.add_row(["名古屋", "なごや", "Nagoya"])
        self.x.add_row(["大阪", "おおさか", "Osaka"])
        self.x.add_row(["札幌", "さっぽろ", "Sapporo"])
        self.x.add_row(["東京", "とうきょう", "Tokyo"])
        self.x.add_row(["横浜", "よこはま", "Yokohama"])

    def testPrint(self):
        stdout = StringIO()
        print(file=stdout)
        print(self.x, file=stdout)
        self.assertEquals(textwrap.dedent("""\
            
            +--------+------------+----------+
            | Kanji  |  Hiragana  | English  |
            +--------+------------+----------+
            |  神戸  |   こうべ   |   Kobe   |
            |  京都  |  きょうと  |  Kyoto   |
            |  長崎  |  ながさき  | Nagasaki |
            | 名古屋 |   なごや   |  Nagoya  |
            |  大阪  |  おおさか  |  Osaka   |
            |  札幌  |  さっぽろ  | Sapporo  |
            |  東京  | とうきょう |  Tokyo   |
            |  横浜  |  よこはま  | Yokohama |
            +--------+------------+----------+
            """), stdout.getvalue())



class UnpaddedTableTest(unittest.TestCase):
    def create_table(self, *args, **kwargs):
        res = PrettyTable(*args, header=False, padding_width=0, **kwargs)
        res.add_row("abc")
        res.add_row("def")
        res.add_row("g..")
        return res

    def setUp(self):
        self.x = self.create_table()

    def testUnbordered(self):
        self.x.border = False
        self.assertEqual(False, self.x.border)
        result = self.x.get_string()
        self.assertEqual(result.strip(), textwrap.dedent("""\
            abc
            def
            g..
            """).strip())

    def testBordered(self):
        self.x.border = True
        self.assertEqual(True, self.x.border)
        result = self.x.get_string()
        self.assertEqual(result.strip(), textwrap.dedent("""\
            +-+-+-+
            |a|b|c|
            |d|e|f|
            |g|.|.|
            +-+-+-+
            """).strip())

    def testBorderConstructor(self):
        p = self.create_table(border=False)
        result = p.get_string()
        self.assertEqual(result, textwrap.dedent("""\
            abc
            def
            g..
            """).strip())


class PrintMarkdownAndRstTest(unittest.TestCase):
    def setUp(self):
        self.x = PrettyTable(["A", "B", "C"])
        self.x.add_row(["a", "b", "c"])
        self.x.add_row(["aa", "bb", "cc"])

    def testMarkdownOutput(self):
        result = self.x.get_md_string()
        stdout = StringIO()
        self.assertEqual(textwrap.dedent("""\
            | A  | B  | C  |
            |----|----|----|
            | a  | b  | c  |
            | aa | bb | cc |
            """).strip(), result)

    def testRstOutput(self):
        result = self.x.get_rst_string()
        self.assertEqual(result.strip(), textwrap.dedent("""\
            +----+----+----+
            | A  | B  | C  |
            +====+====+====+
            | a  | b  | c  |
            +----+----+----+
            | aa | bb | cc |
            +----+----+----+
            """).strip())


class BackwardCompatibilityTest(unittest.TestCase):
    def testRuleStyleMainModule(self):
        from prettytable import ALL, HEADER, NONE
        assert isinstance(ALL.value, int)
        assert isinstance(HEADER.value, int)
        assert isinstance(NONE.value, int)

    def testRuleStyleSubModule(self):
        from prettytable.prettytable import ALL, FRAME, NONE, HEADER
        assert isinstance(ALL.value, int)
        assert isinstance(FRAME.value, int)
        assert isinstance(NONE.value, int)
        assert isinstance(HEADER.value, int)

    def testTableStyleMainModule(self):
        from prettytable import MSWORD_FRIENDLY, PLAIN_COLUMNS
        assert isinstance(MSWORD_FRIENDLY.value, int)
        assert isinstance(PLAIN_COLUMNS.value, int)

    def testTableStyleSubModule(self):
        from prettytable.prettytable import DEFAULT, MSWORD_FRIENDLY, PLAIN_COLUMNS, RANDOM
        assert isinstance(DEFAULT.value, int)
        assert isinstance(MSWORD_FRIENDLY.value, int)
        assert isinstance(PLAIN_COLUMNS.value, int)
        assert isinstance(RANDOM.value, int)


if __name__ == "__main__":
    unittest.main()
