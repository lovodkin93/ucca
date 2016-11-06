import argparse

import numpy as np
import sys

from ucca import convert


class Singleton(type):
    instance = None

    def __call__(cls, *args, **kwargs):
        if not cls.instance:
            cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instance

    def reload(cls):
        cls.instance = None

SPARSE_PERCEPTRON = "sparse"
DENSE_PERCEPTRON = "dense"
FEEDFORWARD_NN = "nn"
CLASSIFIERS = (SPARSE_PERCEPTRON, DENSE_PERCEPTRON, FEEDFORWARD_NN)

# Multiple choice options: the first one is always the default
ACTIVATIONS = ("sigmoid", "tanh", "relu", "cube")
INITIALIZATIONS = ("glorot_uniform", "normal", "uniform", "const")
OPTIMIZERS = ("adam", "sgd", "momentum", "adagrad", "adadelta")
OBJECTIVES = ("categorical_crossentropy",)


class Config(object, metaclass=Singleton):
    def __init__(self, *args):
        argparser = argparse.ArgumentParser(description="""Transition-based parser for UCCA.""",
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        argparser.add_argument("passages", nargs="*", help="passage files/directories to test on/parse")
        argparser.add_argument("-m", "--model", default="ucca", help="model file to load/save")
        argparser.add_argument("-c", "--classifier", choices=CLASSIFIERS, default=SPARSE_PERCEPTRON, help="model type")
        argparser.add_argument("-B", "--beam", choices=(1,), default=1, help="beam size for beam search (1 for greedy)")
        argparser.add_argument("-e", "--evaluate", action="store_true", help="evaluate parsed passages")
        argparser.add_argument("-v", "--verbose", action="store_true", help="detailed parse output")
        group = argparser.add_mutually_exclusive_group()
        group.add_argument("-s", "--sentences", action="store_true", help="separate passages to sentences")
        group.add_argument("-a", "--paragraphs", action="store_true", help="separate passages to paragraphs")
        group = argparser.add_argument_group(title="Training parameters")
        group.add_argument("-t", "--train", nargs="+", default=(), help="passage files/directories to train on")
        group.add_argument("-d", "--dev", nargs="+", default=(), help="passage files/directories to tune on")
        group.add_argument("-I", "--iterations", type=int, default=1, help="number of training iterations")
        group.add_argument("--folds", type=int, choices=(3, 5, 10), help="#folds for cross validation")
        group.add_argument("--seed", type=int, default=1, help="random number generator seed")
        group = argparser.add_argument_group(title="Output files")
        group.add_argument("-o", "--outdir", default=".", help="output directory for parsed files")
        group.add_argument("-p", "--prefix", default="", help="output filename prefix")
        group.add_argument("-W", "--nowrite", action="store_true", help="do not write parsed passages to files")
        group.add_argument("-l", "--log", help="output log file (default: model filename + .log)")
        group.add_argument("--devscores", help="output CSV file for dev scores (default: model filename + .dev.csv)")
        group.add_argument("--testscores", help="output CSV file for test scores (default: model filename + .test.csv)")
        group = argparser.add_argument_group(title="Structural constraints")
        group.add_argument("-L", "--nolinkage", action="store_true", help="ignore linkage nodes and edges")
        group.add_argument("-M", "--noimplicit", action="store_true", help="ignore implicit nodes and edges")
        group.add_argument("-R", "--noremote", action="store_true", help="ignore remote edges")
        group.add_argument("-C", "--constraints", action="store_true", help="constrained inference by UCCA rules")
        group.add_argument("--maxnodes", type=float, default=3.0, help="maximum non-terminal/terminal ratio")
        group.add_argument("--maxheight", type=int, default=20, help="maximum graph height")
        group = argparser.add_mutually_exclusive_group()
        group.add_argument("-S", "--noswap", action="store_true", help="disable Swap transitions entirely")
        group.add_argument("--compoundswap", action="store_true", help="enable compound swap")
        group = argparser.add_argument_group(title="Sanity checks")
        group.add_argument("--checkloops", action="store_true", help="abort if the parser enters a state loop")
        group.add_argument("--verify", action="store_true", help="verify oracle reproduces original passage")
        group = group.add_mutually_exclusive_group()
        group.add_argument("-b", "--binary", action="store_true", help="read and write passages in Pickle")
        group.add_argument("-f", "--format", choices=convert.CONVERTERS, help="output format for parsed files")
        group = argparser.add_argument_group(title="General classifier training parameters")
        group.add_argument("--importance", type=int, default=2, help="learning rate factor for Swap")
        group.add_argument("--earlyupdate", action="store_true", help="move to next example on incorrect prediction")
        group = argparser.add_argument_group(title="Perceptron parameters")
        group.add_argument("--learningrate", type=float, default=1.0, help="rate for model weight updates")
        group.add_argument("--decayfactor", type=float, default=1.0, help="learning rate decay per iteration")
        group.add_argument("--minupdate", type=int, default=5, help="minimum #updates for using a feature")
        group = argparser.add_argument_group(title="Neural network parameters")
        group.add_argument("-w", "--wordvectors", default=100, help="dimensions for random init, or file to load")
        group.add_argument("--tagdim", type=int, default=10, help="dimension for POS tag embeddings")
        group.add_argument("--labeldim", type=int, default=20, help="dimension for edge label embeddings")
        group.add_argument("--punctdim", type=int, default=2, help="dimension for separator punctuation embeddings")
        group.add_argument("--gapdim", type=int, default=2, help="dimension for gap type embeddings")
        group.add_argument("--actiondim", type=int, default=5, help="dimension for action type embeddings")
        group.add_argument("--layerdim", type=int, default=500, help="dimension for hidden layers")
        group.add_argument("--layers", type=int, default=2, help="number of hidden layers")
        group.add_argument("--activation", choices=ACTIVATIONS, default=ACTIVATIONS[0], help="activation function")
        group.add_argument("--init", choices=INITIALIZATIONS, default=INITIALIZATIONS[0], help="weight initialization")
        group.add_argument("--maxlabels", type=int, default=100, help="maximum number of actions to allow")
        group.add_argument("--batchsize", type=int, default=10, help="fit model every this many passages")
        group.add_argument("--minibatchsize", type=int, default=200, help="mini-batch size for optimization")
        group.add_argument("--nbepochs", type=int, default=5, help="number of epochs for optimization")
        group.add_argument("--optimizer", choices=OPTIMIZERS, default=OPTIMIZERS[0], help="algorithm for optimization")
        group.add_argument("--loss", choices=OBJECTIVES, default=OBJECTIVES[0], help="loss function for optimization")
        group.add_argument("--maxwords", default=10000, help="maximum number of words to keep embeddings for")
        group.add_argument("--maxtags", type=int, default=100, help="maximum number of POS tags to keep embeddings for")
        group.add_argument("--maxedgelabels", type=int, default=15, help="maximum number of edge labels for embeddings")
        group.add_argument("--maxpuncts", type=int, default=5, help="maximum number of punctuations for embeddings")
        group.add_argument("--maxgaps", type=int, default=3, help="maximum number of gap types to keep embeddings for")
        group.add_argument("--maxactions", type=int, default=10, help="maximum number of action types for embeddings")
        group.add_argument("--worddropout", type=float, default=0.3, help="word dropout parameter")
        group.add_argument("--dropout", type=float, default=0.5, help="dropout parameter for all inputs")
        group.add_argument("--validationsplit", type=float, default=0.1, help="ratio of train set to use as validation")
        group.add_argument("--saveeverybatch", action="store_true", help="save model every training batch")
        group.add_argument("--saveeveryepoch", action="store_true", help="save model every training epoch")
        group = argparser.add_argument_group(title="DyNet parameters")
        group.add_argument("--dynet-mem", help="memory for dynet")
        group.add_argument("--dynet-l2", type=float, help="level of l2 regularization (default 1e-6)")
        group.add_argument("--dynet-gpu", action="store_true", help="use the GPU")
        group.add_argument("--dynet-gpus", type=int, help="how many GPUs you want to use")
        group.add_argument("--dynet-gpu-ids", help="the GPUs that you want to use by device ID")
        group.add_argument("--dynet-viz", action="store_true", help="visualize NN and exit")
        self.args = argparser.parse_args(args if args else None)

        assert self.args.passages or self.args.train,\
            "Either passages or --train is required (use -h for help)"
        assert self.args.model or self.args.train or self.args.folds,\
            "Either --model or --train or --folds is required"
        assert not (self.args.train or self.args.dev) or self.args.folds is None,\
            "--train and --dev are incompatible with --folds"
        assert self.args.train or not self.args.dev,\
            "--dev is only possible together with --train"
        
        if self.args.model:
            if not self.args.log:
                self.args.log = self.args.model + ".log"
            if self.args.dev and not self.args.devscores:
                self.args.devscores = self.args.model + ".dev.csv"
            if self.args.passages and not self.args.testscores:
                self.args.testscores = self.args.model + ".test.csv"
        elif not self.args.log:
            self.args.log = "parse.log"

        self._log_file = None
        self.set_external()
        self.random = np.random

    def set_external(self):
        np.random.seed(self.args.seed)
        sys.argv += ["--dynet-seed", str(self.args.seed)]
        if self.args.dynet_mem:
            sys.argv += ["--dynet-mem", str(self.args.dynet_mem)]
        if self.args.dynet_l2:
            sys.argv += ["--dynet-l2", str(self.args.dynet_l2)]
        if self.args.dynet_gpu:
            sys.argv += ["--dynet-gpu"]
        if self.args.dynet_gpus:
            sys.argv += ["--dynet-gpus", str(self.args.dynet_gpus)]
        if self.args.dynet_gpu_ids:
            sys.argv += ["--dynet-gpu-ids", str(self.args.dynet_gpu_ids)]
        if self.args.dynet_viz:
            sys.argv += ["--dynet-viz"]

    def update(self, params):
        for name, value in params.items():
            setattr(self.args, name, value)
        self.set_external()

    @property
    def split(self):
        return self.args.sentences or self.args.paragraphs

    @property
    def line_end(self):
        return "\n" if self.args.verbose else " "  # show all in one line unless verbose

    def log(self, message):
        if self._log_file is None:
            self._log_file = open(self.args.log, "w")
        print(message, file=self._log_file, flush=True)
        if self.args.verbose:
            print(message)

    def close(self):
        if self._log_file is not None:
            self._log_file.close()

    def __str__(self):
        return " ".join("%s=%s" % item for item in sorted(vars(self.args).items()))
