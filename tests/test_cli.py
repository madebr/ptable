#!/usr/bin/env python
# coding=UTF-8

import io
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

import prettytable.cli


CSV_INPUT = textwrap.dedent("""\
    a, b, c, d
    1, 2, 3, 4
    5, 6, 7, 8
    """)

MD_INPUT = textwrap.dedent("""\
     a | b | c | d |
    ---|---|---|---|
     1 | 2 | 3 | 4 |
     5 | 6 | 7 | 8 |
    """)


class CsvBaseCliTest(unittest.TestCase):
    def test_no_args(self):
        stdin, sys.stdin = sys.stdin, io.StringIO(CSV_INPUT)
        stdout, sys.stdout = sys.stdout, io.StringIO()
        prettytable.cli.main([])
        stdin, sys.stdin = sys.stdin, stdin
        stdout, sys.stdout = sys.stdout, stdout
        self.assertEqual(textwrap.dedent("""\
            +---+---+---+---+
            | a | b | c | d |
            +---+---+---+---+
            | 1 | 2 | 3 | 4 |
            | 5 | 6 | 7 | 8 |
            +---+---+---+---+
            """), stdout.getvalue())

    def test_from_file(self):
        itf = tempfile.NamedTemporaryFile("w")
        itf.write(CSV_INPUT)
        itf.flush()
        stdout, sys.stdout = sys.stdout, io.StringIO()
        prettytable.cli.main(["--csv", itf.name])
        stdout, sys.stdout = sys.stdout, stdout
        self.assertEqual(textwrap.dedent("""\
            +---+---+---+---+
            | a | b | c | d |
            +---+---+---+---+
            | 1 | 2 | 3 | 4 |
            | 5 | 6 | 7 | 8 |
            +---+---+---+---+
            """), stdout.getvalue())

    def test_to_file(self):
        otf = tempfile.NamedTemporaryFile("r")
        stdin, sys.stdin = sys.stdin, io.StringIO(CSV_INPUT)
        stdout, sys.stdout = sys.stdout, io.StringIO()
        prettytable.cli.main(["--csv", "-o", otf.name])
        stdin, sys.stdin = sys.stdin, stdin
        stdout, sys.stdout = sys.stdout, stdout
        self.assertEqual(textwrap.dedent("""\
            +---+---+---+---+
            | a | b | c | d |
            +---+---+---+---+
            | 1 | 2 | 3 | 4 |
            | 5 | 6 | 7 | 8 |
            +---+---+---+---+
            """), otf.read())
        self.assertEqual("", stdout.getvalue())


class MarkdownCliTest(unittest.TestCase):

    def test_from_file(self):
        itf = tempfile.NamedTemporaryFile("w")
        itf.write(MD_INPUT)
        itf.flush()
        stdout, sys.stdout = sys.stdout, io.StringIO()
        prettytable.cli.main(["--md", itf.name])
        stdout, sys.stdout = sys.stdout, stdout
        self.assertEqual(textwrap.dedent("""\
            +---+---+---+---+
            | a | b | c | d |
            +---+---+---+---+
            | 1 | 2 | 3 | 4 |
            | 5 | 6 | 7 | 8 |
            +---+---+---+---+
            """), stdout.getvalue())

    def test_to_file(self):
        otf = tempfile.NamedTemporaryFile("r")
        stdin, sys.stdin = sys.stdin, io.StringIO(MD_INPUT)
        stdout, sys.stdout = sys.stdout, io.StringIO()
        prettytable.cli.main(["--md", "-o", otf.name])
        stdin, sys.stdin = sys.stdin, stdin
        stdout, sys.stdout = sys.stdout, stdout
        self.assertEqual(textwrap.dedent("""\
            +---+---+---+---+
            | a | b | c | d |
            +---+---+---+---+
            | 1 | 2 | 3 | 4 |
            | 5 | 6 | 7 | 8 |
            +---+---+---+---+
            """), otf.read())
        self.assertEqual("", stdout.getvalue())


class RstCliTest(unittest.TestCase):
    def test_not_supported(self):
        stdin, sys.stdin = sys.stdin, io.StringIO()
        stdout, sys.stdout = sys.stdout, io.StringIO()
        stderr, sys.stderr = sys.stderr, io.StringIO()
        try:
            prettytable.cli.main(["--rst"])
            assert False
        except SystemExit:
            assert True
        stdin, sys.stdin = sys.stdin, stdin
        stdout, sys.stdout = sys.stdout, stdout
        stderr, sys.stderr = sys.stderr, stderr
        self.assertEqual("", stdout.getvalue())


class ExecutableTest(unittest.TestCase):
    def test_call(self):
        output = subprocess.check_output([sys.executable, "-m", "prettytable.cli"], input=CSV_INPUT.encode())
        self.assertEquals(textwrap.dedent("""\
            +---+---+---+---+
            | a | b | c | d |
            +---+---+---+---+
            | 1 | 2 | 3 | 4 |
            | 5 | 6 | 7 | 8 |
            +---+---+---+---+
            """), output.decode())
