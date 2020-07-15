# !/usr/bin/python
# This Python file uses the following encoding: utf-8
from io import StringIO
import unittest
from prettytable.factory import from_csv, from_html, from_html_one, from_md, split_md_row, strip_md_content
from prettytable.prettytable import PrettyTableException
import textwrap

from .test_prettytable import BasicTests, CityDataTest


md = textwrap.dedent("""\
    | name | age | 姓名 | 年龄  |   |
    |------|-----|---|---|---|
    | ke   | 1   | Kane  |  二十 |   |
    
    | wa   | 2   |  王 |   |  三十 |
    |      |     |   |   |   |
    """)


class FromMdTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.md = md

    def test_from_md(self):
        table = from_md(self.md)
        stdout = StringIO()
        print(table, file=stdout)
        self.assertEquals(textwrap.dedent("""\
            +------+-----+------+------+------+
            | name | age | 姓名 | 年龄 |      |
            +------+-----+------+------+------+
            |  ke  |  1  | Kane | 二十 |      |
            |  wa  |  2  |  王  |      | 三十 |
            |      |     |      |      |      |
            +------+-----+------+------+------+
            """), stdout.getvalue())

    def test_split_md_row(self):
        s = '| ke   | 1   | Kane  |  二十 |   |'
        splited_s = split_md_row(s)
        self.assertIn('ke', splited_s)
        self.assertIn('', splited_s)
        self.assertIn('1', splited_s)
        self.assertIn('二十', splited_s)
        self.assertNotIn(' ', splited_s)

        blank_row = '|      |     |   |   |   |'
        splited_bs = split_md_row(blank_row)
        for i in splited_bs:
            self.assertEqual('', i)

    def test_strip_md_content(self):
        s_list = ':ke', ' kane:', 'kane :', ' : kane:', '    '
        for s in s_list:
            stripped_s = strip_md_content(s)
            if stripped_s:
                self.assertNotEqual(' ', stripped_s[0])
                self.assertNotEqual(' ', stripped_s[-1])

                self.assertNotEqual(':', stripped_s[0])
                self.assertNotIn(':', stripped_s[0])


class CsvConstructorTest(object):
    def setUp(self):
        self.fp = StringIO(textwrap.dedent("""\
            City name, Area , Population , Annual Rainfall
            Sydney, 2058 ,  4336374   ,      1214.8
            Melbourne, 1566 ,  3806092   ,       646.9
            Brisbane, 5905 ,  1857594   ,      1146.4
            Perth, 5386 ,  1554769   ,       869.4
            Adelaide, 1295 ,  1158259   ,       600.5
            Hobart, 1357 ,   205556   ,       619.5
            Darwin, 0112 ,   120900   ,      1714.7
        """))


class HtmlConstructorTest(CityDataTest):
    def testHtmlAndBack(self):
        html_string = self.x.get_html_string()
        new_table = from_html(html_string)[0]
        assert new_table.get_string() == self.x.get_string()

    def testHtmlOneAndBack(self):
        html_string = self.x.get_html_string()
        new_table = from_html_one(html_string)
        assert new_table.get_string() == self.x.get_string()

    def testHtmlOneFailOnMany(self):
        html_string = self.x.get_html_string()
        html_string += self.x.get_html_string()
        self.assertRaises(Exception, from_html_one, html_string)


class HtmlTests(unittest.TestCase):
    def testNoColspan(self):
        html = textwrap.dedent("""\
            <table>
                <tr><th>Col1</th><th>Col2</th></tr>
                <tr><td>1</td><td>2</td></tr>
                <tr><td colspan="2">3&4</td></tr>
            </table>
            """)
        table = from_html_one(html)
        result = table.get_string()
        self.assertEqual(textwrap.dedent("""\
            +------+------+
            | Col1 | Col2 |
            +------+------+
            |  1   |  2   |
            | 3&4  |      |
            +------+------+
            """).strip(), result)

    def testIncompleteFirstDataRow(self):
        html = textwrap.dedent("""\
            <table>
                <tr><th>Col1</th><th>Col2</th></tr>
                <tr><td>1</td></tr>
                <tr><td>3</td><td>4</td></tr>
            </table>
            """)
        try:
            from_html_one(html)
            assert False
        except PrettyTableException:
            assert True

    def testIncompleteLastDataRow(self):
        html = textwrap.dedent("""\
            <table>
                <tr><th>Col1</th><th>Col2</th></tr>
                <tr><td>1</td><td>2</td></tr>
                <tr><td>3</td></tr>
            </table>
            """)
        try:
            from_html_one(html)
            assert False
        except PrettyTableException:
            assert True

    def testRowWithTooManyColumns(self):
        html = textwrap.dedent("""\
            <table>
                <tr><th>Col1</th><th>Col2</th></tr>
                <tr><td>1</td><td>2</td></tr>
                <tr><td>3</td><td>4</td><td>5</td></tr>
            </table>
            """)
        try:
            from_html_one(html)
            assert False
        except PrettyTableException:
            assert True

    def testTooFewHeaders(self):
        html = textwrap.dedent("""\
            <table>
                <tr><th>Col1</th><th>Col2</th></tr>
                <tr><td>1</td><td>2</td><td>3</td></tr>
                <tr><td>4</td><td>5</td><td>6</td></tr>
            </table>
            """)
        try:
            from_html_one(html)
            assert False
        except PrettyTableException:
            assert True

    def testMultipleTables(self):
        html = textwrap.dedent("""\
            <table>
                <tr><th>Col1</th><th>Col2</th></tr>
                <tr><td>1</td><td>2</td></tr>
                <tr><td>4</td><td>5</td></tr>
            </table>
            <table>
                <tr><th>Col3</th><th>Col4</th></tr>
                <tr><td>6</td><td>7</td></tr>
                <tr><td>8</td><td>9</td></tr>
            </table>
            """)
        tables = from_html(html)
        self.assertEqual(2, len(tables))
        self.assertEquals(textwrap.dedent("""\
            +------+------+
            | Col1 | Col2 |
            +------+------+
            |  1   |  2   |
            |  4   |  5   |
            +------+------+
            """).strip(), tables[0].get_string())
        self.assertEquals(textwrap.dedent("""\
            +------+------+
            | Col3 | Col4 |
            +------+------+
            |  6   |  7   |
            |  8   |  9   |
            +------+------+
            """).strip(), tables[1].get_string())

    def testMultipleTablesDifferentWidths(self):
        html = textwrap.dedent("""\
            <table>
                <tr><th>Col1</th><th>Col2</th><th>Col2b</th></tr>
                <tr><td>1</td><td>2</td><td>3</td></tr>
                <tr><td>4</td><td>5</td><td>6</td></tr>
            </table>
            <table>
                <tr><th>Col3</th><th>Col4</th></tr>
                <tr><td>6</td><td>7</td></tr>
                <tr><td>8</td><td>9</td></tr>
            </table>
            """)
        tables = from_html(html)
        self.assertEqual(2, len(tables))
        self.assertEquals(textwrap.dedent("""\
            +------+------+-------+
            | Col1 | Col2 | Col2b |
            +------+------+-------+
            |  1   |  2   |   3   |
            |  4   |  5   |   6   |
            +------+------+-------+
            """).strip(), tables[0].get_string())
        self.assertEquals(textwrap.dedent("""\
            +------+------+
            | Col3 | Col4 |
            +------+------+
            |  6   |  7   |
            |  8   |  9   |
            +------+------+
            """).strip(), tables[1].get_string())

    def testUniqueFields(self):
        html = textwrap.dedent("""\
            <table>
                <tr><th>C</th><th>C</th><th>C</th></tr>
                <tr><td>1</td><td>2</td><td>3</td></tr>
                <tr><td>4</td><td>5</td><td>6</td></tr>
            </table>
            """)
        table = from_html_one(html)
        self.assertEquals(textwrap.dedent("""\
            +---+----+-----+
            | C | C' | C'' |
            +---+----+-----+
            | 1 | 2  |  3  |
            | 4 | 5  |  6  |
            +---+----+-----+
            """).strip(), table.get_string())


class CsvConstructorTestEmpty(BasicTests, CsvConstructorTest):
    def setUp(self):
        CsvConstructorTest.setUp(self)
        self.x = from_csv(self.fp)


class CsvConstructorTest_fmtparams(BasicTests, CsvConstructorTest):
    def setUp(self):
        CsvConstructorTest.setUp(self)
        self.x = from_csv(self.fp, lineterminator="\n")


class CsvDataMissingColumnsTest(unittest.TestCase):
    def testFailingConstructor(self):
        self.fp = StringIO(textwrap.dedent("""\
            name, value, optional
            John, 10000, 50
            Sam, 12000
            Patrick, 9999, 10
        """))
        try:
            self.x = from_csv(self.fp, lineterminator="\n")
            assert False
        except PrettyTableException:
            assert True


class CsvConstructorTest_Fieldnames(BasicTests, CsvConstructorTest):
    def setUp(self):
        CsvConstructorTest.setUp(self)
        self.x = from_csv(self.fp, field_names=("City", "Area", "Population", "Annual Rainfall"))


if __name__ == '__main__':
    unittest.main()
