import string
from itertools import groupby
from operator import attrgetter

from ucca import layer0, layer1
from ucca.layer0 import NodeTags as L0Tags
from ucca.layer1 import EdgeTags as ETags, NodeTags as L1Tags

LINKAGE = {ETags.LinkArgument, ETags.LinkRelation}
NON_SCENE = {ETags.Center, ETags.Elaborator, ETags.Quantifier, ETags.Connector} # FIXME: AVIV SLOBODKIN: added this too
SUPP_FUNC = {ETags.Relator, ETags.Function, ETags.Unanalyzable, ETags.Uncertain} # FIXME: AVIV SLOBODKIN: added this too
SCENE = {ETags.Participant, ETags.State, ETags.Process, ETags.Adverbial, ETags.Time} # FIXME: AVIV SLOBODKIN: added this too (Missing CMR)

def validate(passage, linkage=True, multigraph=False):
    for node in passage.layer(layer0.LAYER_ID).all:
        yield from NodeValidator(node).validate_terminal()
    heads = list(passage.layer(layer1.LAYER_ID).heads)
    found_linkage = False
    for node in heads:
        if node.tag == L1Tags.Linkage:
            found_linkage = True
        yield from NodeValidator(node).validate_top_level()
    stack = [heads]
    visited = set()
    path = []
    path_set = set(path)
    while stack:
        for node in stack[-1]:
            if node in path_set:
                yield "Detected cycle (%s)" % "->".join(n.ID for n in path)
            elif node not in visited:
                visited.add(node)
                path.append(node)
                path_set.add(node)
                stack.append(node.children)
                yield from NodeValidator(node).validate_non_terminal(linkage=linkage and found_linkage,
                                                                     multigraph=multigraph)
                break
        else:
            if path:
                path_set.remove(path.pop())
            stack.pop()


class NodeValidator:
    def __init__(self, node):
        self.node = node
        self.node_id = self.node.ID
        tree_id = self.node.extra.get("tree_id")
        if tree_id:
            self.node_id += ", %s" % tree_id
        self.incoming = tag_to_edge(node.incoming)
        self.outgoing = tag_to_edge(node)
        self.incoming_tags = set(self.incoming)
        self.outgoing_tags = set(self.outgoing)

    def validate_terminal(self):
        if not self.node.text:
            yield "Empty terminal text (%s)" % self.node_id
        if set(self.node.text).intersection(string.whitespace):
            yield "Whitespace in terminal text (%s): '%s'" % (self.node_id, self.node)
        if not self.incoming:
            yield "Orphan %s terminal (%s) '%s'" % (self.node.tag, self.node_id, self.node)
        elif len(self.node.incoming) > 1:
            yield "Reentrant %s terminal (%s) '%s'" % (self.node.tag, join(self.node.incoming), self.node)
        # FIXME: AVIV SLOBODKIN: update from here

    def validate_top_level(self):
        if self.node not in self.node.layer.heads and self.node.tag != L1Tags.Linkage:
            yield "Extra root (%s)" % self.node_id
        terminals = [n for n in self.node.children if n.layer.ID == layer0.LAYER_ID]
        if terminals:
            yield "Terminal children (%s) of root (%s)" % (join(terminals), self.node_id)
        s = self.outgoing_tags.difference((ETags.ParallelScene, ETags.Linker, ETags.Function, ETags.Ground,
                                           ETags.Punctuation, ETags.LinkRelation, ETags.LinkArgument))
        if s:
            yield "Top-level unit (%s) with %s children: %s" %\
                  (self.node_id, join(s), join(e.child for e in self.node if s.intersection(e.tags)))
        # FIXME: AVIV SLOBODKIN: update from here

    def validate_non_terminal(self, linkage=False, multigraph=False):
        if linkage and self.node.tag == L1Tags.Linkage:
            yield from self.validate_linkage()
        elif self.node.tag == L1Tags.Foundational:
            yield from self.validate_foundational()
        primary_incoming = [e for e in self.node.incoming if not e.attrib.get("remote") and
                            not LINKAGE.intersection(e.tags)]
        if len(primary_incoming) > 1:
            yield "Unit (%s) with multiple non-remote parents (%s)" % (self.node_id, join(primary_incoming))
        remote_incoming = [e for e in self.node.incoming if e.attrib.get("remote")]
        if remote_incoming and not primary_incoming:
            yield "Unit (%s) with remote parents but no primary parents" % self.node_id
        for edge in self.node:
            if (ETags.Punctuation in edge.tags) != (edge.child.tag == L1Tags.Punctuation):
                yield "%s edge (%s) with %s child" % (edge.tags, edge, edge.child.tag)
            # FN parent of Punctuation is disallowed unless the FN is unanalyzable
            if (self.node.tag == L1Tags.Foundational) and (edge.child.tag == L0Tags.Punct) and \
                    not len(self.node.terminals) + len(self.node.punctuation) == len(self.node.children) > 1 or \
                    (self.node.tag == L1Tags.Punctuation) and not (edge.child.tag == L0Tags.Punct):
                yield "%s unit (%s) with %s child (%s)" % (self.node.tag, self.node_id, edge.child.tag, edge.child.ID)
        if self.node.attrib.get("implicit"):
            if self.node.outgoing:
                yield "Implicit unit (%s) with children (%s)" % (self.node_id, join(self.node.children))
        elif self.node.tag in (L1Tags.Foundational, L1Tags.Linkage, L1Tags.Punctuation) and \
                all(e.attrib.get("remote") for e in self.node):
            yield "Non-implicit unit (%s) with no primary children" % (self.node_id)
        for tag in (ETags.Function, ETags.ParallelScene, ETags.Linker, ETags.LinkRelation,
                    ETags.Connector, ETags.Punctuation, ETags.Terminal):
            s = self.incoming.get(tag, ())
            if len(s) > 1:
                yield "Unit (%s) with multiple %s parents (%s)" % (self.node_id, tag, join(e.parent for e in s))
        for tag in (ETags.LinkRelation, ETags.Process, ETags.State):
            s = self.outgoing.get(tag, ())
            if len(s) > 1:
                yield "Unit (%s) with multiple %s children (%s)" % (self.node_id, tag, join(e.child for e in s))
        if ETags.Function in self.incoming:
            s = self.outgoing_tags.difference((set.union({ETags.Terminal, ETags.Punctuation}, NON_SCENE, SUPP_FUNC))) #FIXME: missing CMR. Also, updated this one. Old version: #s = self.outgoing_tags.difference((ETags.Terminal, ETags.Punctuation))
            if s:
                yield "%s unit (%s) with %s children: %s" % (ETags.Function, self.node_id, join(s), self.node)
        if ETags.Linker in self.incoming_tags and linkage and ETags.LinkRelation not in self.incoming_tags:
            yield "%s unit (%s) with no incoming %s" % (ETags.Linker, self.node_id, ETags.LinkRelation)
        if not multigraph:
            key = attrgetter("child.ID")
            for child_id, edges in groupby(sorted(self.node, key=key), key=key):
                edges = list(edges)
                if len(edges) > 1:
                    yield "Multiple edges from %s to %s: %s" % (self.node_id, child_id, ", ".join(
                        "%d %s" % (len(e), t) for t, e in tag_to_edge(edges).items()))
        # FIXME: AVIV SLOBODKIN: update from here
        no_sub_non_scene = (ETags.Process, ETags.Adverbial, ETags.Linker, ETags.Time,
                            ETags.Quantifier, ETags.Connector, ETags.State)
        if any(k in self.incoming for k in no_sub_non_scene):
            s = self.outgoing_tags.difference((set.union({ETags.Terminal, ETags.Punctuation}, NON_SCENE, SUPP_FUNC))) #FIXME: missing CMR
            edges_to_check =  [k for k in self.incoming if k in no_sub_non_scene]
            if s:
                yield "%s unit (%s) with %s children: %s" % (join(edges_to_check), self.node_id, join(s), self.node)
        if ETags.Unanalyzable in self.incoming:
            if self.outgoing:
                yield "%s unit (%s) with children: %s" % (ETags.Unanalyzable, self.node_id, self.node) # FIXME: should include punctuation and terminal?
        if ETags.Ground in self.incoming:
            s = {k for k in {ETags.ParallelScene, ETags.Linker, ETags.Ground} if k in self.outgoing_tags}
            if s:
                yield "%s unit (%s) with %s children: %s" % (ETags.Ground, self.node_id, join(s), self.node)
        if ETags.ParallelScene in self.incoming:
            s = {k for k in {ETags.ParallelScene, ETags.Linker} if k in self.outgoing_tags}
            if s:
                yield "%s unit (%s) with %s children: %s" % (ETags.ParallelScene, self.node_id, join(s), self.node)
        if ETags.State in self.outgoing_tags:
            forbidden = {ETags.ParallelScene, ETags.Linker, ETags.Process, ETags.Center, ETags.Elaborator,
                         ETags.Quantifier, ETags.Connector}
            s = {k for k in forbidden if k in self.outgoing_tags}
            if s:
                yield "%s unit with %s siblings: under %s" % (ETags.State, join(s), self.node)
        if ETags.Adverbial in self.outgoing_tags:
            s = {k for k in {ETags.ParallelScene, ETags.Linker} if k in self.outgoing_tags}
            if s:
                yield "%s unit with %s siblings: under %s" % (ETags.Adverbial, join(s), self.node)
        if ETags.Center in self.outgoing_tags:
            s = self.outgoing_tags.difference((set.union({ETags.Terminal, ETags.Punctuation}, {ETags.Adverbial},
                                                         NON_SCENE, SUPP_FUNC))) #FIXME: missing CMR
            if s:
                yield "%s unit with %s siblings: under %s" % (ETags.Center, join(s), self.node)
        if any(k in self.outgoing_tags for k in (ETags.Time, ETags.Participant)):
            forbidden = set.union(NON_SCENE, ETags.ParallelScene, ETags.Linker)
            s = {k for k in forbidden if k in self.outgoing_tags}
            edges_to_check = [k for k in self.outgoing_tags if k in (ETags.Time, ETags.Participant)]
            if s:
                yield "%s unit with %s siblings: under %s" % (join(edges_to_check), join(s), self.node)
        if any(k in self.outgoing_tags for k in (ETags.ParallelScene, ETags.Linker)):
            forbidden = set.union(NON_SCENE, SCENE)
            s = {k for k in forbidden if k in self.outgoing_tags}
            edges_to_check = [k for k in self.outgoing_tags if k in (ETags.ParallelScene, ETags.Linker)]
            if s:
                yield "%s unit with %s siblings: under %s" % (join(edges_to_check), join(s), self.node)
        if ETags.Elaborator in self.outgoing_tags:
            forbidden = set.union(SCENE, ETags.ParallelScene, ETags.Linker, ETags.Ground, ETags.Connector)
            s = {k for k in forbidden if k in self.outgoing_tags}
            if s:
                yield "%s unit with %s siblings: under %s" % (ETags.Elaborator, join(s), self.node)
        if ETags.Quantifier in self.outgoing_tags:
            forbidden = set.union(SCENE, ETags.ParallelScene, ETags.Linker, ETags.Ground)
            s = {k for k in forbidden if k in self.outgoing_tags}
            if s:
                yield "%s unit with %s siblings: under %s" % (ETags.Quantifier, join(s), self.node)
        if ETags.Connector in self.outgoing_tags:
            forbidden = set.union(SCENE, ETags.ParallelScene, ETags.Linker, ETags.Ground, ETags.Elaborator, ETags.Quantifier)
            s = {k for k in forbidden if k in self.outgoing_tags}
            if s:
                yield "%s unit with %s siblings: under %s" % (ETags.Connector, join(s), self.node)
        if ETags.Process in self.outgoing_tags:
            forbidden = set.union(NON_SCENE, ETags.State)
            s = {k for k in forbidden if k in self.outgoing_tags}
            if s:
                yield "%s unit with %s siblings: under %s" % (ETags.Process, join(s), self.node)
        if any(k in self.outgoing_tags for k in (ETags.Elaborator, ETags.Quantifier, ETags.Connector)):
            edges_to_check = [k for k in self.outgoing_tags if k in (ETags.Elaborator, ETags.Quantifier, ETags.Connector)]
            if ETags.Center not in self.outgoing_tags:
                yield "%s unit without %s sibling: under %s" % (join(edges_to_check), ETags.Center, self.node)
        if any(k in self.outgoing_tags for k in (ETags.Time, ETags.Participant)):
            edges_to_check = [k for k in self.outgoing_tags if k in (ETags.Time, ETags.Participant)]
            required = {ETags.State, ETags.Process}
            if ETags.State not in self.outgoing_tags and ETags.Process not in self.outgoing_tags:
                yield "%s unit without %s siblings: under %s" % (join(edges_to_check), join(required), self.node)
        if ETags.Linker in self.outgoing_tags:
            if ETags.ParallelScene not in self.outgoing_tags:
                yield "%s unit without %s sibling: under %s" % (ETags.Linker, ETags.ParallelScene, self.node)
        if any(k in self.incoming_tags for k in (ETags.State, ETags.Process)):
            edges_to_check = [k for k in self.incoming_tags if k in (ETags.State, ETags.Process)]
            forbidden = set.union(SCENE, ETags.ParallelScene, ETags.Linker, ETags.Ground)
            itr = self.node.iter()
            for i in itr:
                if not isinstance(i, layer0.Terminal):
                    if i.parallel_scenes or i.linkers or i.grounds or i.participants or i.state or i.process or i.adverbials or i.times:
                        yield "%s unit (%s) with at least one of the %s descendants: %s" % (join(edges_to_check), self.node_id, join(forbidden), self.node)
        if ETags.Relator in self.incoming_tags or ETags.Function in self.incoming_tags:
            s = [e for e in self.node.incoming if
                         e.attrib.get('remote') and e.tag in {ETags.Relator, ETags.Function}]
            if s:
                yield "%s remote edges (%s)" % (join({e.tag for e in s}), join(s))


    def validate_linkage(self):
        if self.node.incoming:
            yield "Non-root %s unit (%s)" % (self.node.tag, self.node_id)
        s = self.outgoing_tags.difference(LINKAGE)
        if s:
            yield "%s unit (%s) with %s children" % (self.node.tag, self.node_id, join(s))
        if ETags.LinkRelation not in self.outgoing:
            yield "%s unit without %s child" % (self.node.tag, ETags.LinkRelation)
        # FIXME: AVIV SLOBODKIN: update from here

    def validate_foundational(self):
        if self.node.participants and not self.node.is_scene():
            yield "Unit (%s) with participants but without main relation: %s" % (self.node_id, self.node)
        if self.node.process and self.node.state:
            yield "Unit (%s) with both process (%s) and state (%s)" % (self.node_id, self.node.process, self.node.state)
        if self.node.parallel_scenes:
            s = self.outgoing_tags.difference((ETags.ParallelScene, ETags.Punctuation, ETags.Linker,
                                               ETags.Ground, ETags.Relator, ETags.Function))
            if s:
                yield "Unit (%s) with parallel scenes has %s children: %s" %\
                      (self.node_id, join(s), join(e.child for e in self.node if s.intersection(e.tags)))
        s = self.outgoing_tags.intersection(LINKAGE)
        if s:
            yield "Non-linkage unit (%s) with %s children: %s" %\
                  (self.node_id, join(s), join(e.child for e in self.node if s.intersection(e.tags)))
        # FIXME: AVIV SLOBODKIN: update from here



def tag_to_edge(edges):
    d = {}
    for edge in edges:
        for tag in edge.tags:
            d.setdefault(tag, []).append(edge)
    return d


def join(items):
    return ", ".join(map(str, items))
