import sys
from argparse import ArgumentParser
from ucca.constructions import extract_candidates, add_argument
import xml.etree.ElementTree as ETree
from ucca import layer0, layer1, convert, textutil
from operator import attrgetter, itemgetter
from ucca.convert import split2sentences
from ucca.ioutil import get_passages, get_passages_with_progress_bar, external_write_mode
import re

# Script by Sriram Chaudhury


descr = {'Q':'Unknown', 'T':'Unknown', 'Terminal':'Terminal_node','P':'Process' ,'S':'State', 'A':'Participant', 'D':'Adverbial', 'C':'Center', 'E':'Elaborator', 'N':'Connector', 'R':'Relator', 'H':'Parallel_Scene', 'L':'Linker' ,'G':'Ground', 'F':'Function', 'U':'Punctuation'
}

def find_path(node,path):
        if(len(node.parents) >= 1):
            if(node.tag != 'Word') and (node.tag != 'Punctuation'):
                #path.append(node.ID+'--'+node.ftag+':'+descr[node.ftag]+'-->'+node.parents[0].ID)
                path.append(('-->('+node.ftag+':'+descr[node.ftag]+')-->'+node.parents[0].ID))
            else:
                #path.append(node.text+'--'+'Terminal'+'-->'+node.parents[0].ID)
                path.append((node.text+'('+str(node.ID)+')'+'--Terminal-->'+node.parents[0].ID))
            for j in node.parents:
                find_path(j,path)
        return path


def find_children(node, path, level):
    remote_found = 0
    for edge in node:
        if(edge.attrib.get('remote')):
            t12 = edge
            remote_found = 1

    for ch in node.children:
        if (ch.tag != 'Word') and (ch.tag != 'Punctuation'):
            if(remote_found) and (ch.ID == t12.child.ID):
                path.append((ch.ftag, ch.ID+'*', level+1,True))
            else:
                path.append((ch.ftag, ch.ID, level+1,False))
            find_children(ch, path, level+1)
        else:
            path.append((ch.text, ch.ID, level+1,False))
            path.append('End')

    return path




def main(args):

    for passage in get_passages_with_progress_bar(args.passages):
        t = split2sentences(passage)
        sen_no = 0
        for sen in t:
            #print('sentence %d\n\n%s\n%s' %(i,convert.to_text(sen), convert.to_sequence(sen)))
            print('sentence %d\n\n%s\n' %(sen_no, convert.to_text(sen)))

            root = sen.nodes['1.1']
            first = 1
            tab_len = {}
            tab_len[0] = len('1.1')
            for i in root.children:
                print('\n')
                path = []
                level = 1
                path.append((i.ftag, i.ID, level,False))
                path = find_children(i, path, level)
                end = 0
                if(first):
                    pstr = root.ID
                    first = 0
                else:
                    for k in range(0, tab_len[0]):
                        pstr = pstr + ' '
                for j in path:
                    if(j == 'End'):
                        print(pstr)
                        pstr = ''
                        end = 1
                        continue
                    rel = j[0]
                    nd = j[1]
                    tab = int(j[2])
                    remote = j[3]
                    if(end):
                        q_mark = 0
                        for k in range(0,tab_len[tab-1]):
                            if(k == tab_len[q_mark]):
                                pstr = pstr + '.'
                                q_mark += 1
                            else:
                                pstr = pstr+' '
                            end = 0
                    if(rel in descr):
                        rel_desc = rel+':' +descr[rel]
                    else:
                        rel_desc = rel
                    if(remote):
                        pstr = pstr + '|-->Remote(' + rel_desc + ')-->' + nd
                    else:
                        pstr = pstr+'|-->('+rel_desc+')-->'+nd
                    tab_len[tab] = len(pstr)

            print('-----------------------------------\n')
            sen_no += 1



if __name__ == "__main__":
    argparser = ArgumentParser(description="Xml to conll and find the path of the word from UCCA xml file.")
    argparser.add_argument("passages", nargs="+", help="the corpus, given as xml/pickle file names")
    add_argument(argparser, False)
    main(argparser.parse_args())
