The evaluation process is done through the `evaluate` function that is located in the [evaluation.py](ucca/evaluation.py) script.
A wrapping script of the `evaluation.py` script is [evaluate_standard.py](scripts/evaluate_standard.py). For more details on how the scripts receives its argument, please write `evaluate_standard --help` in the prompt.
The evaluation process compares the gold-standard annotation of a specific passage, with the calculated annotation of that same passage.
Both passages are of `Passage` object type, which is an object that contains the connected graph that represents the annotation of the passage.
The evaluation includes the recall, precision and F1 scores. The calculation of these scores is done by comparing each edge's labels and yield, which are the literals that are under the edge's child node (if we look at the annotation as a tree).
We can also do an unlabeled evaluation, and then for each edge only its yield will be compared. It is important to know that when there is a remote edge, it is ignored in the yield comparison, but we do look at it when comparing lables of edges.
Also, when there is an implicit node, edges going into them are evaluated by their parent's yield.

Now let us look more closely at the `evaluate` function:

The `evaluate` function receives the following input parameters:
1. guessed: Passage object to evaluate
2. ref: reference (gold standard) Passage object to compare to
3. converter: optional function to apply to passages before evaluation. One can choose to convert passages from the following formats to the `Passage` class:
    - site XML
    - standard XML
    - conll (CoNLL-X dependency parsing shared task)
    - sdp (SemEval 2015 semantic dependency parsing shared task)
4. verbose: whether to print the results
5. constructions: names of construction types to include in the evaluation. By construction we mean that the evaluation can be done on specific types of edges, for example just on the Proccess and State edges. If there is a need in doing the evaluation based on specific labels, a useful flag is `--constructions=categories` , which shows evaluation results per edge label (category).
The default construction includes the following edges:
    - primary edges (`--constructions=primary`)
    - remote edges (`--constructions=remote`)
    - implicit edges (`--constructions=implicit`)
Other types of edges that can be included are:
    - aspectual verbs (`--constructions=aspectual_verbs`)
    - light verbs (`--constructions=light_verbs`)
    - multi-word expressions (mwe) (`--constructions=mwe`)
    - predicate nouns (`--constructions=pred_nouns`)
    - predicate adjectives (`--constructions=pred_adjs`)
    - expletives (`--constructions=expletives`)

If there is a need in doing the evaluation based on specific labels, a useful flag is `--constructions=categories` , which shows evaluation results per edge label (category).
6. units: whether to evaluate common units
7. fscore: whether to compute precision, recall and f1 score
8. errors: whether to print the mistakes (prints something similar to a confusion matrix). It is worth mentioning the `--as-table` option in the [evaluate_standard.py](scripts/evaluate_standard.py) script, that prints the confusion matrix as a table.
9. normalize: flatten centers and move common functions to root before evaluation - modifies passages. There's an option to normalize the passages jointly. In order to normalize them seperately, it should be done before calling `evaluate`. 
10. eval_type: specific evaluation type(s) to limit to. One can choose one of the following evaluation types:
    - labeled - in the process of evaluation, both the labels of the edges and their yields are compared.
    - unlabeled - in the process of evaluation, only the edges' yields are compared.
    - weak_labeled - in the process of evaluation, certain types of labels will be considered the same - for example Process and State edges will be considered the same and only their yields will be compared,  while Process and Participant will not be considered the same.
11. ref_yield_tags: reference passage for fine-grained evaluation. In other words, it enables us to do evaluation to edges of different types of labels (that are not part of the UCCA labels), such as subject, object and so on. Nevertheless, the recall, precision and f1 scores will still be calculated based on the UCCA parsing. 

The function evaluate returns a `Score` object, which contains the recall, precision and f1 scores of the generated annotation.
For example, by running [test_validation.py](ucca/tests/test_validation.py), the line [Score](ucca/tests/test_evaluation.py#L331) generates a `Score` class. One of its elements is called `evaluators`, which comprises of three `EvaluatorResults` classes:
- 'labeled'
- 'unlabeled'
- 'weak_labeled'

Each of those `EvaluatorResults` classes may contain the results for any of the edges mentioned above. As a default it contains the results for 3 types of edges:
- primary
- remote
- impicit

The results for each such type of edges comprise of:
- errors
- f1
- num_guessed
- num_matches
- num_only_guessed
- num_unly_ref
- num_ref
- p (precision)
- r (recall)

For more details on the `evaluate` function, please see the following links:

[evaluate](https://ucca.readthedocs.io/en/latest/api/ucca.evaluation.evaluate.html#ucca.evaluation.evaluate)

[Scores](https://ucca.readthedocs.io/en/latest/api/ucca.evaluation.Scores.html#ucca.evaluation.Scores)
