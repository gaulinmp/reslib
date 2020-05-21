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

Files can be ignored by adding the comment: RESLIB_IGNORE: True

Uses reslib.automate.code_parser.CodeParser objects to extract comments from code, then calculates the dependency graph.
This stemmed from ``doit graph``, but I wanted more flexibility.

:copyright: (c) 2019 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""
# STDlib imports
import os
import re
import logging
from io import StringIO

# Local logger
logger = logging.getLogger(__name__)

# 3rd party package imports
try:
    import networkx as nx
except ModuleNotFoundError:
    logger.warning("NetworkX library not found, DAG functionality unavailable.")
try:
    from graphviz import Source
except ModuleNotFoundError:
    logger.warning("Graphviz library not found, DAG plotting unavailable.")

# project imports
from reslib.automate import cleanpath as _clnpth
from reslib.automate import pathjoin as _pthjoin
from reslib.automate.code_parser import SAS, Stata, Notebook, Python


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
        default_dot_attributes: Tuple of lines to be added to the .dot file output.

     Private Attributes:
        _scanned_code: List of scanned ``CodeParser`` instances.
        _ignore_folders: Set of folders (thus also sub-folders) to ignore.

    Examples:

        Assume the following three files exist in the ``~/projects/example folder``:

        ```code/data.sas
            /* INPUT: funda.sas7bdat */
            PROC EXPORT DATA=funda OUTFILE= "data/stata_data.dta"; RUN;
            /* OUTPUT: stata_data.dta */
        ```

        ```code/load_data.do
            /* INPUT: stata_data.dta */
            use "data/stata_data.dta"
        ```

        ```code/analysis.do
            /* INPUT_FILE: load_data.do */
            do "code/load_data.do"
        ```

        Then the following would create a graph output at pipeline.pdf::

            from reslib.automate import DependencyScanner

            # Just scan for SAS and Stata code, located in the code directory.
            ds = DependencyScanner(project_root='~/projects/example/',
                                  code_path_prefix='code', data_path_prefix='data')
            print(ds)
            ds.DAG_to_file("pipeline.pdf")

        Alternatively, a one-liner on the commandline:

            python -c "from reslib.automate import *;DependencyScanner(code_path_prefix='data', data_path_prefix='code').DAG_to_file('pipeline')"
    """

    #: List of Parsers to check against cost. Defaults to [SAS, Stata, Notebook, Python]
    parser_list = None
    #: Default attributes to add to the .dot file output.
    default_dot_attributes = {"graph": ["rankdir=LR"], "node": ["style=filled"], "edge": ["arrowsize=1.5"]}

    #: Orphaned node color
    _file_node_color = "seagreen3"
    #: Orphaned node color
    _orphan_node_color = "gold"

    #: Private esults of scanning
    _scanned_code = None

    # Private attributes
    _ignore_folders = {".git", ".ipynb_checkpoints", "__pycache__"}

    def __init__(self, *parsers, project_root=".", code_path_prefix=None, data_path_prefix=None, ignore_folders=None):
        """Initialize the Dependency Scanner"""
        self.project_root = project_root
        self.code_path_prefix = code_path_prefix
        self.data_path_prefix = data_path_prefix

        if '~' in self.project_root:
            self.project_root = os.path.expanduser(self.project_root)
        elif not os.path.isabs(self.project_root):
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

        self._scanned_code = None

    def __str__(self):
        return "\n".join([str(r) for r in self.scanned_code])

    @property
    def scanned_code(self):
        return self._scanned_code or self.scan()

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
        self._scanned_code = []

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
                        self._scanned_code.append(res)

                    break  # break out of parser_list, we found our match

        return self._scanned_code

    def DAG(self, color_orphans=True, trim_dangling_data_nodes=True):
        """Create the Directed Acyclic Graph (DAG) for the codebase.

        Returns:
            networkx.DiGraph: DiGraph of the codebase, represented in networkX format.
        """
        G = nx.DiGraph()

        def add_file_node(file_node_or_list, color=None, shape="note"):
            if isinstance(file_node_or_list, str):
                file_node_or_list = [file_node_or_list]
            G.add_nodes_from(file_node_or_list, color=color or self._file_node_color, shape=shape, _type="file")

        def add_data_node(data_node):
            if data_node not in G:
                G.add_node(data_node, _type="dataset")

        # First add the scanned files themselves
        add_file_node([code.path_relative for code in self.scanned_code])

        # Then add all their connections
        for code in self.scanned_code:
            for in_f in code.input_files:
                # If this file isn't in G it wasn't scanned, so add it and set color to self._orphaned_node_color
                if in_f not in G:
                    add_file_node(in_f, color=self._orphan_node_color)
                G.add_edge(in_f, code.path_relative, link_type="file")

            for in_d in code.input_datasets:
                if in_d in code.output_datasets:
                    continue
                add_data_node(in_d)
                G.add_edge(in_d, code.path_relative, link_type="dataset")

            for out_d in code.output_datasets:
                add_data_node(out_d)
                G.add_edge(code.path_relative, out_d, link_type="dataset")

        # Add a warning node if the DAG isn't acyclic
        if not nx.is_directed_acyclic_graph(G):
            G.add_node("CYCLES DETECTED, DAG IS NOT ACYCLIC!", shape="plain", fontsize="24", color="white")

        if color_orphans:
            for node in G:
                # Ignore orphaned nodes if they are files (check with _type=='file', set above)
                if G.nodes[node].get("_type") == "file":
                    continue
                # Otherwise, make all nodes without ancestors self._orphan_node_color
                if not nx.ancestors(G, node):
                    G.nodes[node]["color"] = self._orphan_node_color

        if trim_dangling_data_nodes:
            trim_nodes = []
            for node in G:
                # Ignore dangling nodes if they are files (check with _type=='file', set above)
                if G.nodes[node].get("_type") == "file":
                    continue
                # Otherwise, remove all nodes with no decendents
                if not nx.descendants(G, node):
                    trim_nodes.append(node)
            for node in trim_nodes:
                G.remove_node(node)

        return G

    def DAG_to_file(self, filepath, G=None):
        """Write a graphviz-style *.dot file to be converted into

        Args:
            filepath (str,Path,File): Path (or open file object) to write the .dot file to.
        """
        G = G or self.DAG()
        notDAG = not nx.is_directed_acyclic_graph(G)

        dot_str = StringIO()
        nx.nx_pydot.write_dot(G, dot_str)
        lines = dot_str.getvalue().split("\n")

        extra = []
        for attr_name, attr_vals in self.default_dot_attributes.items():
            if notDAG and attr_name == "graph":
                attr_vals = [x for x in attr_vals if "bgcolor" not in x]
                attr_vals.append("bgcolor=red")

            extra.append(f"{attr_name} [{' '.join(attr_vals)}];")

        dot = "\n".join([lines[0], *extra, *lines[1:]])

        if hasattr(filepath, "write"):
            filepath.write(dot)
        else:
            with open(filepath, "w") as fh:
                fh.write(dot)

        filepath, ext = os.path.splitext(filepath)
        ext = ext.strip(os.path.extsep) or 'pdf'

        Source(dot).render(filepath, format=ext, cleanup=True)

        return dot
