"""
********************************
reslib.dag.code_parser
********************************

This module contains the basic functionality to parse dependencies from code.
Currently it uses specially formatted comments to do so, hopefully one day it will automatically extract dependencies.

Assumes files look something like this:

    |                    ┌────────────────────────┐
    | INPUT FILES -----> │   This file runs and   │ --> This file (file path)
    |                    │   creates some output  │
    |                    │   or writes data to    │
    | INPUT DATASETS --> │   disk.                │ --> OUTPUT DATASETS
    |                    └────────────────────────┘


Parses comments that look like "# INPUT_FILE:" or "# INPUT_DATASET:" or "# OUTPUT:" store them.
Files can be ignored by adding the comment: "RESLIB_IGNORE: True"

:copyright: (c) 2025 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""

# STDlib imports
import os
import re
import logging

# 3rd party package imports

# project imports
from reslib.dag import cleanpath as _clnpth
from reslib.dag import pathjoin as _pthjoin


# Local logger
logger = logging.getLogger(__name__)


class CodeParser:
    """CodeParser imagines a file as something that takes input, and makes output:

        |                    ┌────────────────────────┐
        | INPUT FILES -----> │   This file runs and   │ --> This file (file path)
        |                    │   creates some output  │
        |                    │   or writes data to    │
        | INPUT DATASETS --> │   disk.                │ --> OUTPUT DATASETS
        |                    └────────────────────────┘

    Attributes:
        path_relative (str, path, None): Path of the code to be analyzed, relative to
            ``os.path.join(project_root, code_path_prefix)``. Defaults to None, which means no file has been scanned.
        code_path_prefix (str, path, None): Relative path to the code directory, starting from ``project_root``.
            Defaults to ``None``, meaning all code paths are relative to ``project_root``.
        data_path_prefix (str, path, None): Relative path to the data directory, starting from ``project_root``.
            Defaults to ``None``, meaning all data paths are relative to ``project_root``.
        project_root (str, path): Root of the project. If your project has multiple roots, I can't help you friend.
        input_files (set): Set of input files scanned from comments in the code.
        input_datasets (set): Set of input datasets scanned from comments in the code.
        output_datasets (set): Set of output datasets scanned from comments in the code.

    Private Attributes:
        _language (str): Short name for the language of the CodeParser.
        _extension (str): File extension of the code for this language.
        _file_match_regex (re): Regular expression to match files to be checked by this parser. Default: ``*._extension``.
        _file_encoding (str): Encoding of the file to be opened (passed to ``open(path, encoding=self._file_encoding)``)
        _comment_start (str): The string to search for demarking the start of the comment.
        _comment_start_regex (bool): Flag denoting the ``_comment_start`` variable is a regular expression
            (pre-compiled or string to be complied).
        _comment_end (str): The string to search for demarking the end of the comment.
        _comment_end_regex (bool): Flag denoting the ``_comment_end`` variable is a regular expression
            (pre-compiled or string to be complied).
        _ignore_comment_text (str): String denoting the ignore comment.
        _input_file_comment_text (str): String denoting the input file type.
        _input_dataset_comment_text (str): String denoting the input dataset type.
        _output_dataset_comment_text (str): String denoting the output dataset type.
        _ignore_comment_regex (re): Regular expression complied from the comment start/end attribute and ignore comment
            text. Used to signal a particular file should be ignored.
        _input_file_comment_regex (re): Regular expression complied from the comment start/end attribute and comment
            text. Used to find input file comments in the code.
        _input_dataset_comment_regex (re): Regular expression complied from the comment start/end attribute and comment
            text. Used to find input dataset comments in the code.
        _output_dataset_comment_regex (re): Regular expression complied from the comment start/end attribute and comment
            text. Used to find output dataset comments in the code.

    """

    #: Relative path of the code to be analyzed, relative to ``os.path.join(project_root, code_path_prefix)``.
    #  Defaults to None, which means no file has been scanned.
    path_relative = None
    #: Absolute path of the code to be analyzed. Defaults to None, which means no file has been scanned.
    path_absolute = None
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

    _language = "text"
    _extension = "txt"
    _file_match_regex_pattern = None
    _file_encoding = "utf-8"
    _comment_start = "/*"  # TODO: implement list of start/stop pairs later
    _comment_start_regex = False  # TODO: implement matching list of false/trues
    _comment_end = "*/"  # TODO: implement list of start/stop pairs later
    _comment_end_regex = False  # TODO: implement matching list of false/trues
    _input_file_comment_text = "INPUT_FILE"
    _input_dataset_comment_text = "INPUT_DATASET"
    _output_dataset_comment_text = "OUTPUT"
    _ignore_comment_text = "RESLIB_IGNORE"

    #: local variable to store last parsed file
    _parsed_file = None

    def __init__(
        self,
        path_relative=None,
        path_absolute=None,
        project_root=".",
        code_path_prefix=None,
        data_path_prefix=None,
        **kwargs,
    ):
        self.config = {
            "path_relative": path_relative,
            "path_absolute": path_absolute,
            "project_root": project_root,
            "code_path_prefix": code_path_prefix,
            "data_path_prefix": data_path_prefix,
            **kwargs,
        }

        # Allow for setting attributes upon object instantiation
        for k, v in kwargs.items():
            setattr(self, k, v)

        if path_relative is not None or path_absolute is not None:
            self.set_path(
                path_relative=path_relative,
                path_absolute=path_absolute,
                project_root=project_root,
                code_path_prefix=code_path_prefix,
                data_path_prefix=data_path_prefix,
            )

            self.analyze()

    @property
    def _file_match_regex(self):
        """Compile regex pattern for matching files based on extension or custom pattern."""
        # Check if we have a custom file match regex
        try:
            return re.compile(self._file_match_regex_pattern, re.IGNORECASE)
        except (TypeError, re.error):
            pass

        # Fall back to extension-based matching
        try:
            return re.compile(r"\.{}$".format(re.escape(self._extension)), re.IGNORECASE)
        except (TypeError, re.error):
            # Accept anything with an extension
            return re.compile(r"\.[^.]*$")

    # SET CODE SEARCH REGEXES
    def _compile_comment_regex(self, text, start=None, end=None):
        # If start/end is in kwargs, skip the following.
        # If comment_*_regex is true, don't re.escape
        if start is None:
            start = getattr(self, "_comment_start", "") or ""
        if not self._comment_start_regex:
            start = re.escape(self._comment_start)

        if end is None:
            end = getattr(self, "_comment_end", "") or ""
        if not self._comment_end_regex:
            end = re.escape(self._comment_end)

        return re.compile(rf"^\s*{start}\s*{text}:\s*(.+)\s*{end}\s*$", flags=re.MULTILINE)

    @property
    def _ignore_comment_regex(self):
        """Compile regex pattern for ignore comments."""
        return self._compile_comment_regex(self._ignore_comment_text)

    @property
    def _input_file_comment_regex(self):
        """Compile regex pattern for input file comments."""
        return self._compile_comment_regex(self._input_file_comment_text)

    @property
    def _input_dataset_comment_regex(self):
        """Compile regex pattern for input dataset comments."""
        return self._compile_comment_regex(self._input_dataset_comment_text)

    @property
    def _output_dataset_comment_regex(self):
        """Compile regex pattern for output dataset comments."""
        return self._compile_comment_regex(self._output_dataset_comment_text)

    @property
    def is_parsed(self):
        return self._parsed_file is not None and self.path_relative == self._parsed_file

    def set_path(
        self,
        path_relative=None,
        path_absolute=None,
        project_root=".",
        code_path_prefix=None,
        data_path_prefix=None,
    ):
        """Set the file path of the analyzed object, and calculate its relative position to base_dir.

        Arguments:
            path_relative (str, path, None): Path of the code to be analyzed, relative to
                ``os.path.join(project_root, code_path_prefix)``. Defaults to None.
            path_absolute (str, path, None): Absolute path of the code to be analyzed, from which ``path_relative`` is
                calculated. Ignored if ``path_relative`` is provided. Defaults to None.
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

        # If they provided path_absolute, not path_relative, derive path_relative from it, and recalculate path_absolute below
        if path_relative is None and path_absolute is not None:
            if os.path.isabs(path_absolute):
                path_absolute = os.path.relpath(path_absolute, _pthjoin(self.project_root, self.code_path_prefix))
            path_relative = path_absolute

        if path_relative is not None:
            self.path_relative = _clnpth(path_relative)
            # Recalculate the path_absolute to the code file
            self.path_absolute = _pthjoin(self.project_root, self.code_path_prefix, self.path_relative)

        logger.debug(f"{self.__class__.__name__}.set_path(): {self.path_relative} (absolute: {self.path_absolute})")

    def matches(self, path_relative):
        """Check if a file path matches this parser's file pattern."""
        # Create a temporary instance to access the regex property
        return bool(self._file_match_regex.search(path_relative))

    def analyze(self, path_relative=None, path_absolute=None):
        """
        Analyze the actual file.

        Calls self.analyze_code(file_contents) after reading the file.

        Args:
            path_relative (str): Path to the file. Defaults to None, taking the path to analyze from ``path_relative``.

        Returns:
            dict: Dictionary of the resulting code object dependencies

        Raises:
            UnicodeDecodeError: Raised if file is not encoded according to self._file_encoding (default: utf-8)
        """
        if path_relative is not None or path_absolute is not None:
            self.set_path(
                path_relative=path_relative,
                path_absolute=path_absolute,
                project_root=self.project_root,
                code_path_prefix=self.code_path_prefix,
                data_path_prefix=self.data_path_prefix,
            )

        if self.path_absolute is None:
            raise FileNotFoundError("File path must be specified in init or as first argument to analyze().")

        logger.debug(
            "%r.analyze(): %r (from %r)",
            self.__class__,
            self.path_relative,
            self.project_root,
        )

        try:
            with open(self.path_absolute, encoding=self._file_encoding) as fh:
                code = fh.read()
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(f"Unicode decode error: {self.path_absolute}") from e

        return self.analyze_code(code, current_dir=os.path.dirname(self.path_absolute))

    def analyze_code(self, code, current_dir=None):
        """Analyze the text of the file.

        Args:
            code (str): Text of the file to be analyzed.

        Returns:
            bool: Returns True if the code had tags to parse.
        """
        found_something = False

        ignore = self._ignore_comment_regex.search(code)
        if ignore and ignore.group(1).strip().lower() in ("true", "yes", "1"):
            return False

        for _regex, _set in (
            (self._input_file_comment_regex, self.input_files),
            (self._input_dataset_comment_regex, self.input_datasets),
            (self._output_dataset_comment_regex, self.output_datasets),
        ):
            for _pth in _regex.finditer(code):
                _found_path = _pth.group(1).strip()

                # Check if the path is relative, if so append current dir
                _found_rel = _found_path.startswith(".\\") or _found_path.startswith("./")

                # Tack on current_dir if it's not empty
                if _found_rel and current_dir is not None:
                    _found_path = os.path.relpath(_pthjoin(current_dir, _found_path), self.project_root)

                _found_path = _clnpth(_found_path)

                # Save the corrected path to the list we're aggregating
                _set.add(_found_path)

                # We found something, this is a file worth 'keeping'
                found_something = True

        if found_something:
            self._parsed_file = self.path_relative
            logger.debug(f"{self.__class__.__name__}.analyze_code(): found in {self._parsed_file} ")
            if self.input_files:
                logger.debug(
                    f"{'':>{len(self.__class__.__name__)+16}s} INPUT_FILES: {', '.join(sorted(self.input_files))}"
                )
            if self.input_datasets:
                logger.debug(
                    f"{'':>{len(self.__class__.__name__)+16}s} INPUT_DATASETS: {', '.join(sorted(self.input_datasets))}"
                )
            if self.output_datasets:
                logger.debug(
                    f"{'':>{len(self.__class__.__name__)+16}s} OUTPUT_DATASETS: {', '.join(sorted(self.output_datasets))}"
                )
        else:
            logger.debug(f"{self.__class__.__name__}.analyze_code(): no dependencies found in {self._parsed_file}")

        return found_something

    def matches_output(self, file_to_check):
        """ "Are you my mother" test.
        Returns True-like if the file matches one of the 'outputs' of this code.
        Should be tested against inputs of other code to find a parent dependency.

        Checks the input file against this code's ``path_relative`` (for a file dependency) and dataset outputs
        (for a dataset dependency).

        Args:
            file_to_check (str, path): File to check against this one's 'outputs', the relative path.

        Returns:
            (str, None): The path to the file or dataset that matches, otherwise None.

        Example:
            parent = CodeParser(path_relative="a.sas")
            child = CodeParser(path_relative="b.sas")

            for f in child.input_files | child.input_datasets:
                match = parent.matches_output(f)
                if not match:
                    print(f"No relation for {f}")
                else:
                    print(f"{parent.path_relative} is the {match} we are looking for")
        """
        file_to_check = _clnpth(file_to_check)

        return (
            (file_to_check == self.path_relative)
            or (self.path_absolute.endswith(file_to_check))
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
            parent = CodeParser(path_relative="a.sas")
            child = CodeParser(path_relative="b.sas")

            for f in parent.output_datasets:
                match = child.matches_input(f)
                if not match:
                    print(f"No relation for {f}")
                else:
                    print(f"{child.path_relative} is the {match} we are looking for")
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
        match = self.matches_input(potential_parent.path_relative)
        if match:
            matching_outputs_to_inputs.append(match)

        # Second, check if any of the parent's output_datasets match input_datasets
        for file in potential_parent.output_datasets:
            match = self.matches_input(file)
            if match:
                matching_outputs_to_inputs.append(match)

        return matching_outputs_to_inputs

    def __repr__(self):
        s = [self._language.capitalize()]

        try:
            s.append(f" (I:{len(self.input_files)+len(self.input_datasets)}/O:{len(self.output_datasets)})")
            s.append(f" {self.path_relative}")
        except AttributeError:
            s.append(" (unparsed)")

        return f"<{''.join(s)}>"

    def __str__(self):
        s = [f"{self._language.capitalize()}:: {str(self.path_relative)}"]

        s.append(f"\tINPUT FILES (found {len(self.input_files)}):")
        for f in sorted(self.input_files):
            s.append(f"\t\t{f}")

        s.append(f"\tINPUT DATASETS (found {len(self.input_datasets)}):")
        for f in sorted(self.input_datasets):
            s.append(f"\t\t{f}")

        s.append(f"\tOUTPUT DATASETS (found {len(self.output_datasets)}):")
        for f in sorted(self.output_datasets):
            s.append(f"\t\t{f}")

        s.append(f"\tProject Root: {self.project_root}")
        if self.code_path_prefix is not None:
            s.append(f"\tCode Prefix: {self.code_path_prefix}")
        if self.data_path_prefix is not None:
            s.append(f"\tData Prefix: {self.data_path_prefix}")
        return "\n".join(s)


class SAS(CodeParser):
    _language = "sas"
    _extension = "sas"


class Stata(CodeParser):
    _language = "stata"
    _extension = "do"


class Notebook(CodeParser):
    _language = "notebook"
    _extension = "ipynb"
    _comment_start = r'"\s*#'
    _comment_end = '\\\\n",?'
    _comment_start_regex = True
    _comment_end_regex = True


class StataNotebook(CodeParser):
    _language = "statanotebook"
    _extension = "ipynb"
    _comment_start = '"/*'
    _comment_end = '[*]/\\\\n",?'
    _comment_end_regex = True


class Python(CodeParser):
    _language = "python"
    _extension = "py"
    _comment_start = "#"
    _comment_end = ""


class Latex(CodeParser):
    _language = "latex"
    _extension = "tex"
    _comment_start = "%"
    _comment_end = ""


class Manual(CodeParser):
    """Manual downloader is used to give instructions for a manual step that isn't automated in code."""

    _language = "manual"
    _extension = "txt"
    _comment_start = ""
    _comment_end = ""
