"""
********************************
reslib.automate.code_scanner
********************************

This module contains the basic functionality to scan a code-base and extract dependencies from comments.

Assumes files look something like this:


    |                    ┌────────────────────────┐
    | INPUT FILES -----> │   This file runs and   │ --> This file (file path)
    |                    │   creates some output  │
    |                    │   or writes data to    │
    | INPUT DATASETS --> │   disk.                │ --> OUTPUT DATASETS
    |                    └────────────────────────┘

Parses comments that look like "# INPUT_FILE:" or "# INPUT_DATASET:" or "# OUTPUT_DATASET:" and calculate
the dependency graph from this.
This stemmed from ``doit graph``, but I wanted more flexibility.
Parsing Python modules to programatically add functions to the graph is the next TODO.

:copyright: (c) 2019 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""
# STDlib imports
import os
import re
import logging

# import datetime as dt

# 3rd party package imports
# import numpy as np
# import pandas as pd

# project imports
# from reslib.config import Config


# Local logger
logger = logging.getLogger(__name__)


def _clnpth(path_to_clean, re_pathsep=re.compile(r"[\\]+"), re_dotstart=re.compile(r"^./|/$")):
    """Clean a path by replacing ``\\\\`` with ``/``, and removing beginning ``./`` and trailing ``/``"""
    if path_to_clean is None:
        return None
    return re_dotstart.sub("", re_pathsep.sub("/", str(path_to_clean)))


def _pthjoin(*paths):
    """Join, normalize, and clean a list of paths, allowing for ``None``s (filtered out)"""
    return _clnpth(os.path.normpath(os.path.join(*filter(None, paths))))


class DependencyScanner:
    """Scan a code-base for dependencies.

    Attributes:
        parser_list: List of parser objects, which subclass ``CodeParser`` below.
        ignore_folders: Set of folders (thus also sub-folders) to ignore.
        project_root (str, path): Absolute path to project root. Will call ``os.path.abspath()`` if input is not already so.
        code_path_prefix (str, path, None): Prefix string to add to any code, used to resolve the absolute path via:
            ```os.path.join(project_root, code_path_prefix, relative_code_path_from_comment)```.
        data_path_prefix (str, path, None): Prefix string to add to any data, used to resolve the absolute path via:
            ```os.path.join(project_root, data_path_prefix, relative_data_path_from_comment)```.

    Example usage::

        from reslib.automate.code_scanner import DependencyScanner, SAS, Stata

        # Just scan for SAS and Stata code, located in the code directory.
        ds = DependencyScanner(SAS, Stata, project_root='~/projects/project1/', code_path_prefix='code', )
        list_of_dependency_dicts = ds.scan()

        print(list_of_dependency_dicts[0])
    """

    # List of Parsers to check against cost. Defaults to [SAS, Stata, Notebook, Python]
    parser_list = None
    ignore_folders = {".git", ".ipynb_checkpoints", "__pycache__"}

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
            self.ignore_folders = set(ignore_folders)

    def scan(self):
        """
        Scan through the directory starting from ``self.project_root`` (or ``override_path`` if provided),
        calling analyze(file) for each file that matches ``*.extension``.

        The dir that is passed to parser.analyze is always based on what was passed in.
        If project_root is absolute, the parser will get absolute paths.
        If it is relative, it will get relatives paths.
        """
        self.results = []

        start_dir = self.project_root
        if self.code_path_prefix is not None:
            start_dir = _pthjoin(start_dir, self.code_path_prefix)

        for _dir, _, _files in os.walk(start_dir):
            # Ignore if the ignore_folders are anywhere in the path
            if len(set(_dir.split(os.path.sep)) & self.ignore_folders):
                continue
            for _file in _files:
                path = _clnpth(_pthjoin(_dir, _file))
                for parser in self.parser_list:
                    if not parser.matches(path):
                        continue

                    res = parser(
                        abs_path=path,
                        project_root=self.project_root,
                        code_path_prefix=self.code_path_prefix,
                        data_path_prefix=self.data_path_prefix,
                    )

                    if res.is_parsed:
                        self.results.append(res)

                    break  # break out of parser_list, we found our match

        return self.results


class CodeParserMetaclass(type):
    """
    Compile a CodeParser class to include the regex and parsing functionality.

    This allows for ``SAS.matches`` instead of ``SAS().matches``
    """

    def __new__(cls, name, bases, attrs):
        if name.startswith("None"):
            return None

        new_class = super().__new__(cls, name, bases, attrs)

        def lastattr(attr_name, use_dict=None, first_non_empty=False):
            if use_dict is not None:
                return use_dict.get(attr_name, None)
            # Otherwise return the last attribute from the the stack of class inheretence
            a = list(getattr(bc, attr_name, {}) for bc in bases + (new_class,))
            if first_non_empty:
                for x in reversed(a):
                    if x is not None:
                        return x
            return a[-1]

        # SET FILE SEARCH REGEX - Do not inheret, recalculate every time.
        f_regex = lastattr("file_match_regex", attrs)

        if isinstance(f_regex, str):
            try:
                f_regex = re.compile(f_regex)
            except (TypeError, re.error) as e:
                f_regex = None

        # Otherwise just use the extension to match
        # (a failure to compile re above defaults to this too)
        if f_regex is None:
            try:
                f_regex = re.compile("\.{}$".format(re.escape(lastattr("extension"))), re.I)
            except (TypeError, re.error) as e:
                # Accept anything with an extension
                f_regex = re.compile("\.[^.]*$")

        new_class.file_match_regex = f_regex

        # SET CODE SEARCH REGEXES
        def recomp(re_flags=re.MULTILINE, **kwargs):
            # If start/end is in kwargs, skip the following.
            # If comment_*_regex is true, don't add to kwargs until after re.escape
            for c in "start end".split():
                if c not in kwargs and not lastattr(f"comment_{c}_regex"):
                    kwargs[c] = lastattr(f"comment_{c}")

            kwargs = {k: re.escape(v) for k, v in kwargs.items()}

            for c in "start end".split():
                if c not in kwargs:
                    kwargs[c] = lastattr(f"comment_{c}")

            return re.compile("^\s*{start}\s*{text}:\s*(.+)\s*{end}\s*$".format(**kwargs), flags=re_flags)

        new_class.input_dataset_comment_regex = recomp(text=lastattr("input_dataset_comment_text"))
        new_class.input_file_comment_regex = recomp(text=lastattr("input_file_comment_text"))
        new_class.output_dataset_comment_regex = recomp(text=lastattr("output_dataset_comment_text"))

        return new_class


class CodeParser(metaclass=CodeParserMetaclass):
    """CodeParser imagines a file as something that takes input, and makes output:

        |                    ┌────────────────────────┐
        | INPUT FILES -----> │   This file runs and   │ --> This file (file path)
        |                    │   creates some output  │
        |                    │   or writes data to    │
        | INPUT DATASETS --> │   disk.                │ --> OUTPUT DATASETS
        |                    └────────────────────────┘

    Attributes:
        relative_path (str, path, None): Path of the code to be analyzed, relative to
            ``os.path.join(project_root, code_path_prefix)``. Defaults to None, which means no file has been scanned.
        code_path_prefix (str, path, None): Relative path to the code directory, starting from ``project_root``.
            Defaults to ``None``, meaning all code paths are relative to ``project_root``.
        data_path_prefix (str, path, None): Relative path to the data directory, starting from ``project_root``.
            Defaults to ``None``, meaning all data paths are relative to ``project_root``.
        project_root (str, path): Root of the project. If your project has multiple roots, I can't help you friend.
        input_files (set): Set of input files scanned from comments in the code.
        input_datasets (set): Set of input datasets scanned from comments in the code.
        output_datasets (set): Set of output datasets scanned from comments in the code.
        language (str): Short name for the language of the CodeParser.
        extension (str): File extension of the code for this language.
        file_match_regex (re): Regular expression to match files to be checked by this parser. Default: ``*.extension``.
        file_encoding (str): Encoding of the file to be opened (passed to ``open(path, encoding=self.file_encoding)``)
        comment_start (str): The string to search for demarking the start of the comment.
        comment_start_regex (bool): Flag denoting the ``comment_start`` variable is a regular expression
            (pre-compiled or string to be complied).
        comment_end (str): The string to search for demarking the end of the comment.
        comment_end_regex (bool): Flag denoting the ``comment_end`` variable is a regular expression
            (pre-compiled or string to be complied).
        input_file_comment_text (str): String denoting the input file type.
        input_dataset_comment_text (str): String denoting the input dataset type.
        output_dataset_comment_text (str): String denoting the output dataset type.
        input_file_comment_regex (re): Regular expression complied from the comment start/end attribute and comment
            text. Used to find input file comments in the code.
        input_dataset_comment_regex (re): Regular expression complied from the comment start/end attribute and comment
            text. Used to find input dataset comments in the code.
        output_dataset_comment_regex (re): Regular expression complied from the comment start/end attribute and comment
            text. Used to find output dataset comments in the code.

    """

    #: Relative path of the code to be analyzed, relative to ``os.path.join(project_root, code_path_prefix)``. Defaults to None, which means no file has been scanned.
    relative_path = None
    #: Absolute path of the code to be analyzed. Defaults to None, which means no file has been scanned.
    abs_path = None
    #: Relative path to the code directory, starting from ``project_root``.
    code_path_prefix = None
    #: Relative path to the data directory, starting from ``project_root``.
    data_path_prefix = None
    #: Root of the project. If your project has multiple roots, I can't help you friend.
    project_root = None

    #: Set of input files scanned from comments in the code.
    input_files = None
    #: Set of input datasets scanned from comments in the code.
    input_datasets = None
    #: Set of output datasets scanned from comments in the code.
    output_datasets = None

    language = "text"
    extension = "txt"
    file_match_regex = None
    file_encoding = "utf-8"

    comment_start = "/*"  # TODO: implement list of start/stop pairs later
    comment_start_regex = False  # TODO: implement matching list of false/trues
    comment_end = "*/"  # TODO: implement list of start/stop pairs later
    comment_end_regex = False  # TODO: implement matching list of false/trues
    input_dataset_comment_text = "INPUT"  # TODO: Change to INPUT_DATA
    input_file_comment_text = "INPUT_TASK"  # TODO: Change to INPUT_FILE
    output_dataset_comment_text = "OUTPUT"

    #: local variable to store last parsed file
    _parsed_file = None

    def __init__(
        self,
        relative_path=None,
        abs_path=None,
        project_root=".",
        code_path_prefix=None,
        data_path_prefix=None,
        **kwargs,
    ):
        self.config = kwargs

        for k, v in kwargs.items():
            setattr(self, k, v)

        self.set_path(
            relative_path=relative_path,
            abs_path=abs_path,
            project_root=project_root,
            code_path_prefix=code_path_prefix,
            data_path_prefix=data_path_prefix,
        )

        if self.relative_path is not None:
            self.analyze()

    def __repr__(self):
        s = [self.language.capitalize()]

        try:
            s.append(f" (I:{len(self.input_files)+len(self.input_datasets)}/O:{len(self.output_datasets)})")
            s.append(f" {self.relative_path}")
        except AttributeError:
            s.append(" (unparsed)")

        return f"<{''.join(s)}>"

    def __str__(self):
        s = [f"{self.language.capitalize()}:: {str(self.relative_path)}"]

        s.append(f"\tProject Root: {self.project_root}")
        if self.code_path_prefix is not None:
            s.append(f"\tCode Prefix: {self.code_path_prefix}")
        if self.data_path_prefix is not None:
            s.append(f"\tData Prefix: {self.data_path_prefix}")

        s.append(f"\tINPUT FILES (found {len(self.input_files)}):")
        for f in sorted(self.input_files):
            s.append(f"\t\t{f}")

        s.append(f"\tINPUT DATASETS (found {len(self.input_datasets)}):")
        for f in sorted(self.input_datasets):
            s.append(f"\t\t{f}")

        s.append(f"\tOUTPUT DATASETS (found {len(self.output_datasets)}):")
        for f in sorted(self.output_datasets):
            s.append(f"\t\t{f}")

        return "\n".join(s)

    @classmethod
    def matches(cls, relative_path):
        return bool(cls.file_match_regex.search(relative_path))

    @property
    def is_parsed(self):
        return self._parsed_file is not None and self.relative_path == self._parsed_file

    def set_path(
        self, relative_path=None, abs_path=None, project_root=".", code_path_prefix=None, data_path_prefix=None
    ):
        """Set the file path of the analyzed object, and calculate its relative position to base_dir.

        Arguments:
            relative_path (str, path, None): Path of the code to be analyzed, relative to
                ``os.path.join(project_root, code_path_prefix)``. Defaults to None.
            abs_path (str, path, None): Absolute path of the code to be analyzed, from which ``relative_path`` is
                calculated. Ignored if ``relative_path`` is provided. Defaults to None.
            code_path_prefix (str, path, None): Relative path to the code directory, starting from ``project_root``.
                Defaults to ``None``, meaning all code paths are relative to ``project_root``.
            data_path_prefix (str, path, None): Relative path to the data directory, starting from ``project_root``.
                Defaults to ``None``, meaning all data paths are relative to ``project_root``.
            project_root (str, path): Root of the project. If your project has multiple roots, I can't help you friend.
        """
        # Reset dependencies when analyzing
        self._parsed_file = None
        self.input_files = set()
        self.input_datasets = set()
        self.output_datasets = set()

        if "~" in project_root:
            project_root = os.path.expanduser(project_root)
        self.project_root = _clnpth(os.path.abspath(project_root))

        self.code_path_prefix = _clnpth(code_path_prefix)
        self.data_path_prefix = _clnpth(data_path_prefix)

        # If they provided abs_path, not relative_path, derive relative_path from it, and recalculate abs_path below
        if relative_path is None and abs_path is not None:
            if os.path.isabs(abs_path):
                abs_path = os.path.relpath(abs_path, _pthjoin(self.project_root, self.code_path_prefix))
            relative_path = abs_path

        if relative_path is not None:
            self.relative_path = _clnpth(relative_path)
            # Recalculate the abs_path to the code file
            self.abs_path = _pthjoin(self.project_root, self.code_path_prefix, self.relative_path)

    def analyze(self, relative_path=None, abs_path=None):
        """
        Analyze the actual file.

        Calls self.analyze_code(file_contents) after reading the file.

        Args:
            relative_path (str): Path to the file. Defaults to None, taking the path to analyze from ``relative_path``.

        Returns:
            dict: Dictionary of the resulting code object dependencies

        Raises:
            UnicodeDecodeError: Raised if file is not encoded according to self.file_encoding (default: utf-8)
        """
        if relative_path is not None:
            self.set_path(
                relative_path=relative_path,
                abs_path=abs_path,
                project_root=self.project_root,
                code_path_prefix=self.code_path_prefix,
                data_path_prefix=self.data_path_prefix,
            )

        if self.abs_path is None:
            raise FileNotFoundError("File path must be specified in init or as first argument to analyze().")

        logger.debug("%r.analyze(): %r (from %r)", self.__class__, self.relative_path, self.project_root)

        try:
            with open(self.abs_path, encoding=self.file_encoding) as fh:
                code = fh.read()
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(f"Unicode decode error: {self.abs_path}") from e

        return self.analyze_code(code)

    def analyze_code(self, code):
        """Analyze the text of the file."""
        found_something = False

        for _regex, _set in (
            (self.input_file_comment_regex, self.input_files),
            (self.input_dataset_comment_regex, self.input_datasets),
            (self.output_dataset_comment_regex, self.output_datasets),
        ):

            for _pth in _regex.finditer(code):
                _set.add(_clnpth(_pth.group(1)))

                # We found something, this is a file worth 'keeping'
                found_something = True

        if found_something:
            self._parsed_file = self.relative_path

    def matches_output(self, file_to_check):
        """ "Are you my mother" test.
        Returns True-like if the file matches one of the 'outputs' of this code.
        Should be tested against inputs of other code to find a parent dependency.

        Checks the input file against this code's ``relative_path`` (for a file dependency) and dataset outputs
        (for a dataset dependency).

        Args:
            file_to_check (str, path): File to check against this one's 'outputs', the relative path.

        Returns:
            (str, None): The path to the file or dataset that matches, otherwise None.

        Example:
            parent = CodeParser(relative_path="a.sas")
            child = CodeParser(relative_path="b.sas")

            for f in child.input_files | child.input_datasets:
                match = parent.matches_output(f)
                if not match:
                    print(f"No relation for {f}")
                else:
                    print(f"{parent.relative_path} is the {match} we are looking for")
        """
        file_to_check = _clnpth(file_to_check)

        return (
            (file_to_check == self.relative_path)
            or (self.abs_path.endswith(file_to_check))
            or (file_to_check in self.output_datasets)
        )

    def matches_input(self, file_to_check):
        """Asks "Is this one of your inputs", for testing if this is your 'child'.

        Checks the input file against this code's name (for a file dependency) and outputs (for a dataset dependency).

        Args:
            file_to_check (str, path): File to check against this one's 'outputs'

        Returns:
            (bool): Returns ``True`` if file_to_check is in the input files or datasets.

        Example:
            parent = CodeParser(relative_path="a.sas")
            child = CodeParser(relative_path="b.sas")

            for f in parent.output_datasets:
                match = child.matches_input(f)
                if not match:
                    print(f"No relation for {f}")
                else:
                    print(f"{child.relative_path} is the {match} we are looking for")
        """
        return _clnpth(file_to_check) in self.input_files | self.input_datasets

    def check_parent_relationships(self, potential_parent):
        """Tests all outputs of provided potential parent to see if they match this object's inputs.

        Args:
            potential_parent (CodeParser): Potential parent code object to test the outputs against self's inputs.

        Returns:
            list: List of overlapping files. These will be either the ``full_path`` of ``potential_parent`` or its
                output datasets.
        """
        matching_outputs_to_inputs = []

        # First check if the file itself is one of the self.input_files
        match = self.matches_input(potential_parent.relative_path)
        if match:
            matching_outputs_to_inputs.append(match)

        # Second, check if any of the parent's output_datasets match input_datasets
        for file in potential_parent.output_datasets:
            match = self.matches_input(file)
            if match:
                matching_outputs_to_inputs.append(match)

        return matching_outputs_to_inputs


class SAS(CodeParser):
    language = "sas"
    extension = "sas"


class Stata(CodeParser):
    language = "stata"
    extension = "do"


class Notebook(CodeParser):
    language = "notebook"
    extension = "ipynb"
    comment_start = '"#'
    comment_end = '\\\\n",?'
    comment_end_regex = True


class Python(CodeParser):
    language = "python"
    extension = "py"
    comment_start = "#"
    comment_end = ""
