# """
#     sphinx.directives.other
#     ~~~~~~~~~~~~~~~~~~~~~~~

#     :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
#     :license: BSD, see LICENSE for details.
# """

# import re
from typing import Any, Dict, List, cast

from docutils import nodes
from docutils.nodes import Element, Node
from docutils.parsers.rst import directives
# from docutils.parsers.rst.directives.admonitions import BaseAdmonition
# from docutils.parsers.rst.directives.misc import Class
# from docutils.parsers.rst.directives.misc import Include as BaseInclude

from sphinx import addnodes
# from sphinx.deprecation import RemovedInSphinx40Warning, deprecated_alias
# from sphinx.domains.changeset import VersionChange  # NOQA  # for compatibility
# from sphinx.locale import _
from sphinx.util import docname_join, url_re
from sphinx.util.docutils import SphinxDirective
from sphinx.util.matching import Matcher, patfilter
from sphinx.util.nodes import explicit_title_re

# if False:
#     # For type annotation
#     from sphinx.application import Sphinx


# glob_re = re.compile(r'.*[*?\[].*')


# def int_or_nothing(argument: str) -> int:
#     if not argument:
#         return 999
#     return int(argument)
#
from sphinx.directives.other import int_or_nothing

class MyTocTree(SphinxDirective):
    """
    Directive to notify Sphinx about the hierarchical structure of the docs,
    and to include a table-of-contents like tree in the current document.
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'maxdepth': int,
        'name': directives.unchanged,
        'caption': directives.unchanged_required,
        'glob': directives.flag,
        'hidden': directives.flag,
        'includehidden': directives.flag,
        'numbered': int_or_nothing,
        'numberedfrom': int,
        'titlesonly': directives.flag,
        'reversed': directives.flag,
    }

    def run(self) -> List[Node]:
        subnode = addnodes.toctree()
        subnode['parent'] = self.env.docname

        # (title, ref) pairs, where ref may be a document, or an external link,
        # and title may be None if the document's title is to be used
        subnode['entries'] = []
        subnode['includefiles'] = []
        subnode['maxdepth'] = self.options.get('maxdepth', -1)
        subnode['caption'] = self.options.get('caption')
        subnode['glob'] = 'glob' in self.options
        subnode['hidden'] = 'hidden' in self.options
        subnode['includehidden'] = 'includehidden' in self.options
        subnode['numbered'] = self.options.get('numbered', 0)
        subnode['numberedfrom'] = self.options.get('numberedfrom', 0)
        #print("DOCNAME %s" % docname)
        print("NUMBEREDFROM = %s" % subnode['numberedfrom'])
        subnode['titlesonly'] = 'titlesonly' in self.options
        self.set_source_info(subnode)
        wrappernode = nodes.compound(classes=['toctree-wrapper'])
        wrappernode.append(subnode)
        self.add_name(wrappernode)

        ret = self.parse_content(subnode)
        ret.append(wrappernode)
        return ret

    def parse_content(self, toctree: addnodes.toctree) -> List[Node]:
        suffixes = self.config.source_suffix

        # glob target documents
        all_docnames = self.env.found_docs.copy()
        all_docnames.remove(self.env.docname)  # remove current document

        ret = []  # type: List[Node]
        excluded = Matcher(self.config.exclude_patterns)
        for entry in self.content:
            if not entry:
                continue
            # look for explicit titles ("Some Title <document>")
            explicit = explicit_title_re.match(entry)
            if (toctree['glob'] and glob_re.match(entry) and
                    not explicit and not url_re.match(entry)):
                patname = docname_join(self.env.docname, entry)
                docnames = sorted(patfilter(all_docnames, patname))
                for docname in docnames:
                    all_docnames.remove(docname)  # don't include it again
                    toctree['entries'].append((None, docname))
                    toctree['includefiles'].append(docname)
                if not docnames:
                    ret.append(self.state.document.reporter.warning(
                        'toctree glob pattern %r didn\'t match any documents'
                        % entry, line=self.lineno))
            else:
                if explicit:
                    ref = explicit.group(2)
                    title = explicit.group(1)
                    docname = ref
                else:
                    ref = docname = entry
                    title = None
                # remove suffixes (backwards compatibility)
                for suffix in suffixes:
                    if docname.endswith(suffix):
                        docname = docname[:-len(suffix)]
                        break
                # absolutize filenames
                docname = docname_join(self.env.docname, docname)
                if url_re.match(ref) or ref == 'self':
                    toctree['entries'].append((title, ref))
                elif docname not in self.env.found_docs:
                    if excluded(self.env.doc2path(docname, None)):
                        message = 'toctree contains reference to excluded document %r'
                    else:
                        message = 'toctree contains reference to nonexisting document %r'

                    ret.append(self.state.document.reporter.warning(message % docname,
                                                                    line=self.lineno))
                    self.env.note_reread()
                else:
                    all_docnames.discard(docname)
                    toctree['entries'].append((title, docname))
                    toctree['includefiles'].append(docname)

        # entries contains all entries (self references, external links etc.)
        if 'reversed' in self.options:
            toctree['entries'] = list(reversed(toctree['entries']))
            toctree['includefiles'] = list(reversed(toctree['includefiles']))

        return ret

directives.register_directive('mytoctree', MyTocTree)

from sphinx.environment import BuildEnvironment

def assign_section_numbers(self, env: BuildEnvironment) -> List[str]:
    """Assign a section number to each heading under a numbered toctree."""
    # a list of all docnames whose section numbers changed
    rewrite_needed = []

    assigned = set()  # type: Set[str]
    old_secnumbers = env.toc_secnumbers
    env.toc_secnumbers = {}

    def _walk_toc(node: Element, secnums: Dict, depth: int, titlenode: nodes.title = None) -> None:  # NOQA
        # titlenode is the title of the document, it will get assigned a
        # secnumber too, so that it shows up in next/prev/parent rellinks
        for subnode in node.children:
            if isinstance(subnode, nodes.bullet_list):
                numstack.append(0)
                _walk_toc(subnode, secnums, depth - 1, titlenode)
                numstack.pop()
                titlenode = None
            elif isinstance(subnode, nodes.list_item):
                _walk_toc(subnode, secnums, depth, titlenode)
                titlenode = None
            elif isinstance(subnode, addnodes.only):
                # at this stage we don't know yet which sections are going
                # to be included; just include all of them, even if it leads
                # to gaps in the numbering
                _walk_toc(subnode, secnums, depth, titlenode)
                titlenode = None
            elif isinstance(subnode, addnodes.compact_paragraph):
                numstack[-1] += 1
                reference = cast(nodes.reference, subnode[0])
                if depth > 0:
                    number = list(numstack)
                    secnums[reference['anchorname']] = tuple(numstack)
                else:
                    number = None
                    secnums[reference['anchorname']] = None
                reference['secnumber'] = number
                if titlenode:
                    titlenode['secnumber'] = number
                    titlenode = None
            elif isinstance(subnode, addnodes.toctree):
                _walk_toctree(subnode, depth)

    def _walk_toctree(toctreenode: addnodes.toctree, depth: int) -> None:
        if depth == 0:
            return
        for (title, ref) in toctreenode['entries']:
            if url_re.match(ref) or ref == 'self':
                # don't mess with those
                continue
            elif ref in assigned:
                logger.warning(__('%s is already assigned section numbers '
                                  '(nested numbered toctree?)'), ref,
                               location=toctreenode, type='toc', subtype='secnum')
            elif ref in env.tocs:
                secnums = {}  # type: Dict[str, Tuple[int, ...]]
                env.toc_secnumbers[ref] = secnums
                assigned.add(ref)
                _walk_toc(env.tocs[ref], secnums, depth, env.titles.get(ref))
                if secnums != old_secnumbers.get(ref):
                    rewrite_needed.append(ref)

    for docname in env.numbered_toctrees:
        assigned.add(docname)
        doctree = env.get_doctree(docname)

        # Autonumber
        if docname == "refman":
            numberedfrom = 0
            for node in doctree.traverse():
                #print(node.tagname)
                #if node.tagname == 'title':
                #    print(node)
                if node.tagname == 'toctree':
                    att = node.attributes
                    #print(att.keys())
                    if att.get('numberedfrom',0) < 0:
                        att['numberedfrom'] = numberedfrom
                    nentries = len(att['entries'])
                    #print(numberedfrom,nentries)
                    numberedfrom += nentries
                    #print(att)

        for toctreenode in doctree.traverse(addnodes.toctree):
            depth = toctreenode.get('numbered', 0)
            fromn = toctreenode.get('numberedfrom', 0)
            #print("DEPTH %s, FROM %s" % (depth,fromn))
            if depth:
                # every numbered toctree gets new numbering
                numstack = [fromn]
                _walk_toctree(toctreenode, depth)

    return rewrite_needed

from sphinx.environment.collectors.toctree import TocTreeCollector
TocTreeCollector.assign_section_numbers = assign_section_numbers
