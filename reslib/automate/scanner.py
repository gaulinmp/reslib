"""
********************************
reslib.automate.scanner
********************************

This module contains the basic functionality to scan a code-base and extract dependencies from comments.

Assumes files look something like this:

    |                    ┌────────────────────────┐
    | INPUT FILES -----> │   This file runs and   │ --> This file (file path)
    |                    │   creates some output  │
    |                    │   or writes data to    │
    | INPUT DATASETS --> │   disk.                │ --> OUTPUT DATASETS
    |                    └────────────────────────┘

Uses reslib.automate.code_parser.CodeParser objects to extract comments from code, then calculates the dependency graph.
This stemmed from ``doit graph``, but I wanted more flexibility.

:copyright: (c) 2019 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""
# STDlib imports
import os
import re
import logging

# 3rd party package imports

# project imports
from reslib.automate import cleanpath as _clnpth
from reslib.automate import pathjoin as _pthjoin
from reslib.automate.code_parser import SAS, Stata, Notebook, Python

# Local logger
logger = logging.getLogger(__name__)


class DependencyScanner:
    """Scan a code-base for dependencies.

    Attributes:
        project_root (str, path): Absolute path to project root. Will call ``os.path.abspath()`` if input is not already so.
        code_path_prefix (str, path, None): Prefix string to add to any code, used to resolve the absolute path via:
            ```os.path.join(project_root, code_path_prefix, relative_code_path_from_comment)```.
        data_path_prefix (str, path, None): Prefix string to add to any data, used to resolve the absolute path via:
            ```os.path.join(project_root, data_path_prefix, relative_data_path_from_comment)```.
        parser_list: List of ``CodeParser`` subclass objects (not instances!).
        scanned_code: Result list of scanned ``CodeParser`` instances.

     Private Attributes:
        _ignore_folders: Set of folders (thus also sub-folders) to ignore.

    Example usage::

        from reslib.automate.code_scanner import DependencyScanner, SAS, Stata

        # Just scan for SAS and Stata code, located in the code directory.
        ds = DependencyScanner(SAS, Stata, project_root='~/projects/project1/', code_path_prefix='code', )
        list_of_dependency_dicts = ds.scan()

        print(list_of_dependency_dicts[0])
    """

    #: List of Parsers to check against cost. Defaults to [SAS, Stata, Notebook, Python]
    parser_list = None
    #: Results of scanning
    scanned_code = None

    # Private attributes
    _ignore_folders = {".git", ".ipynb_checkpoints", "__pycache__"}

    def __init__(self, *parsers, project_root=".", code_path_prefix=None, data_path_prefix=None, ignore_folders=None):
        """Initialize the Dependency Scanner"""
        self.project_root = project_root
        self.code_path_prefix = code_path_prefix
        self.data_path_prefix = data_path_prefix

        if not os.path.isabs(self.project_root):
            self.project_root = os.path.abspath(self.project_root)

        # Take override parser list if provided
        if len(parsers):
            self.parser_list = parsers

        # Check again, to allow for sub-classing defining the parser_list
        if self.parser_list is None:
            self.parser_list = [SAS, Stata, Notebook, Python]

        # Verify that ignore_folders is a set
        if ignore_folders is not None:
            self._ignore_folders = set(ignore_folders)

        self.scanned_code = None

    def scan(self):
        """
        Scan through the directory starting from ``self.project_root`` (or ``override_path`` if provided),
        calling analyze(file) for each file that matches ``*.extension``.

        The dir that is passed to parser.analyze is always based on what was passed in.
        If project_root is absolute, the parser will get absolute paths.
        If it is relative, it will get relatives paths.

        Each CodeParser object contains four important values:

            relative_path
            input_files
            input_datasets
            output_datasets
        """
        self.scanned_code = []

        start_dir = self.project_root
        if self.code_path_prefix is not None:
            start_dir = _pthjoin(start_dir, self.code_path_prefix)

        for _dir, _, _files in os.walk(start_dir):
            # Ignore if the ignore_folders are anywhere in the path
            if len(set(_dir.split(os.path.sep)) & self._ignore_folders):
                continue
            for _file in _files:
                path = _clnpth(_pthjoin(_dir, _file))
                for parser in self.parser_list:
                    if not parser.matches(path):
                        continue
                    # Create the parser object with this code path
                    res = parser(
                        path_absolute=path,
                        project_root=self.project_root,
                        code_path_prefix=self.code_path_prefix,
                        data_path_prefix=self.data_path_prefix,
                    )

                    if res.is_parsed:
                        self.scanned_code.append(res)

                    break  # break out of parser_list, we found our match

        return self.scanned_code

    def DAG(self):
        if self.scanned_code is None:
            self.scan()

        for r in self.scanned_code:
            print(r, '\n')
