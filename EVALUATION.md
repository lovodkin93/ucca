The evaluation process is done through the evaluate function that is located in the evaluation.py script (https://github.com/lovodkin93/ucca/blob/master/ucca/evaluation.py).
A wrapping script of the evaluation.py script is evaluate_standard.py (https://github.com/lovodkin93/ucca/blob/master/scripts/evaluate_standard.py). For more details on how the scripts receives its argument, please write evaluate_standard --help in the prompt.
The evaluation process compares the gold-standard annotation of a specific passage, with the calculated annotation of that same passage, which is calculated by our model.
Both passages are of Passage object type, which is an object that contains the connected graph that represents the annotation of the passage.
Our evaluation includes the recall, precision and F1 scores. The calculation of these scores is done by comparing each edge's labels and yield, which are the literals that are under the edge's child node (if we look at the annotation as a tree).
We can also do an unlabled evaluation, and then for each edge only its yield will be compared. It is important to know that when there is a remote edge, it is ignored in the yield comparison, but we do look at it when comparing lables of edges.
Also, when there is an implicit node, edges going into them are evaluated by their parent's yield.

Now let us look more closely at the evaluate function:

The evaluate function receives the following input parameters:
1. guessed: Passage object to evaluate
2. ref: reference (gold standard) Passage object to compare to
3. converter: optional function to apply to passages before evaluation. One can choose to convert to the following formats:
    - site XML
    - standard XML
    - conll (CoNLL-X dependency parsing shared task)
    - sdp (SemEval 2015 semantic dependency parsing shared task)
4. verbose: whether to print the results
5. constructions: names of construction types to include in the evaluation. By construction we mean that the evaluation can be done on specific types of edges, for example just on the Proccess and State edges. The default construction includes the following edges:
    - primary edges
    - remote edges
    - aspectual verbs
    - light verbs
    - multi-word expressions (mwe)
    - predicate nouns
    - predicate adjectives
    - expletives
    - implicit edges
    If there is a need in doing the evaluation based on specific labels, a useful flag is --constructions=categories , which shows evaluation results per edge label (category).
6. units: whether to evaluate common units
7. fscore: whether to compute precision, recall and f1 score
8. errors: whether to print the mistakes (prints something similar to a confusion matrix). It is worth mentioning the --as-table option in the evaluate_standard script (https://github.com/lovodkin93/ucca/blob/master/scripts/evaluate_standard.py), that prints the confusion matrix as a table.
9. normalize: flatten centers and move common functions to root before evaluation - modifies passages. There's an option to normalize seperately each passage or to normalize them jointly. 
10. eval_type: specific evaluation type(s) to limit to. One can choose one of the following evaluation types:
    - labeled - in the process of evaluation, both the labels of the edges and their yields are compared.
    - unlabeld - in the process of evaluation, only the edges' yields are compared.
    - weak_labeld - in the process of evaluation, certain types of labels will be considered the same - for example process and state edges will be considered the same and only their yields will be compared,  while process and participant will not be considered the same.
11. ref_yield_tags: reference passage for fine-grained evaluation. In other words, it enables us to do evaluation to edges of different types of labels (that are not part of the UCCA labels), such as subject, object and so on. Nevertheless, the recall, precision and f1 scores will still be calculated based on the UCCA parsing. 
The function evaluate returns a Score object, which contains the recall, precision and f1 scores of the generated annotation.

For more details of the evaluate function, please see the following links:
https://ucca.readthedocs.io/en/latest/api/ucca.evaluation.evaluate.html#ucca.evaluation.evaluate
https://ucca.readthedocs.io/en/latest/api/ucca.evaluation.Scores.html#ucca.evaluation.Scores
