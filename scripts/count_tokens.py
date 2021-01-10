import argparse
import os
import sys
import urllib.request
from itertools import product

from ucca import layer0
from uccaapp.download_task import TaskDownloader


## def main(output = None, comment = False, sentence_level = False, categories = (), tokens = (), tokens_mode = CONSECUTIVE,
##          case_insensitive = False, tokens_by_file = False, remotes = False, write = False, **kwargs):
##     if tokens_by_file:
##         with open(tokens[0]) as f:
##             token_lists = [line.strip().split() for line in f]
##     elif tokens != ():
##         token_lists = [tokens]
##     else:
##         token_lists = ()

##     filtered_nodes = []
##     for passage, task_id, user_id in TaskDownloader(**kwargs).download_tasks(write=False, **kwargs):
##         if sentence_level:
##             cur_passages = convert.split2sentences(passage)
##             all_nodes = [p.layer(layer1.LAYER_ID).heads[0] for p in cur_passages]
##         else:
##             all_nodes = list(passage.layer(layer1.LAYER_ID).all)
##         for node in all_nodes:
##             if comment and node.extra.get("remarks"):
##                 filtered_nodes.append(("comment",node,task_id,user_id))
##             if remotes and len([n for n in node.outgoing if n.attrib.get("remote")]) > 0:
##                 filtered_nodes.append(("remotes", node, task_id, user_id))
##             if token_lists and not node.attrib.get("implicit"):
##                 for token_list in token_lists:
##                     unit_tokens = [t.text for t in node.get_terminals(punct=True)]
##                     if case_insensitive:
##                         unit_tokens = [x.lower() for x in unit_tokens]
##                         token_list = [x.lower() for x in token_list]
##                     if tokens_match(unit_tokens, token_list, tokens_mode):
##                         filtered_nodes.append(('TOKENS', node, task_id, user_id))
##             else:
##                 all_tags = [c.tag for edge in node for c in edge.categories]
##                 intersection = set(categories).intersection(all_tags)

def count_tokens(**kwargs):
    output = []
    for passage, task_id, user_id in TaskDownloader(**kwargs).download_tasks(**kwargs):
        num_tokens = len(passage.layer(layer0.LAYER_ID).all)
        output.append((num_tokens,task_id,user_id))
    return output

def main(output=None, tokens=(), **kwargs):
    kwargs["write"] = False
    f = open(output, 'w', encoding="utf-8") if output else sys.stdout
    for num_tokens, task_id, user_id in count_tokens(**kwargs):
        print(str(num_tokens), task_id, user_id, file=f, sep="\t", flush=True)
    if output:
        f.close()


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    TaskDownloader.add_arguments(argument_parser)
    argument_parser.add_argument("--output", help="output file name")
    main(**vars(argument_parser.parse_args()))

