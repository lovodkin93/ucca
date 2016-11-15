#!/usr/bin/env bash

case "$TEST_SUITE" in
unit)
    # unit tests
    python -m unittest discover -v || exit 1
    # basic conversion test
    ci/test_convert_toy.sh || exit 1
    # basic parser tests
    python parsing/parse.py -I 10 -t doc/toy.xml -d doc/toy.xml -vm model_toy || exit 1
    python parsing/parse.py doc/toy.xml -evm model_toy || exit 1
    python parsing/parse.py -I 10 -t doc/toy.xml -d doc/toy.xml -svm model_toy_sentences || exit 1
    python parsing/parse.py doc/toy.xml -esvm model_toy_sentences || exit 1
    python parsing/parse.py -I 10 -t doc/toy.xml -d doc/toy.xml -avm model_toy_paragraphs || exit 1
    python parsing/parse.py doc/toy.xml -esvm model_toy_paragraphs || exit 1
    ;;
sparse)
    python parsing/parse.py -c sparse -WeLMCbs pickle/dev -t pickle/dev
    ;;
dense)
    python parsing/parse.py -c dense -WeLMCbs pickle/dev -t pickle/dev
    ;;
mlp)
    python parsing/parse.py -c mlp -WeLMCbs pickle/dev -t pickle/dev --dynet-mem=3072
    ;;
bilstm)
    python parsing/parse.py -c bilstm -WeLMCbs pickle/dev -t pickle/dev --dynet-mem=3072 -w 10 --layerdim=10 --layers=1 --lstmlayerdim=10 --lstmlayers=1 --minibatchsize=50
    ;;
tune)
    export W2V_FILE=word_vectors/sskip.100.vectors.txt
    export PARAMS_NUM=10
    python parsing/tune.py doc/toy.xml -t doc/toy.xml --dynet-mem=3072 || exit 1
    column -t -s, params.csv
    ;;
convert)
    ci/test_convert_all.sh
    ;;
convert_sentences)
    mkdir -p pickle/sentences
    python scripts/standard_to_sentences.py pickle/*.pickle -o pickle/sentences -p "ucca_passage" -b || exit 1
    ci/test_convert_all_sentences.sh || exit 1
    ;;
esac
