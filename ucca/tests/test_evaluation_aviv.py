import os
from functools import partial
from io import StringIO
from itertools import repeat

import pytest

from ucca import core, layer0, layer1, convert
from ucca.evaluation import evaluate, LABELED, UNLABELED, WEAK_LABELED
from ucca.validation import validate
from .conftest import PASSAGES, load_xml



def main():
    print("hello world!")

if __name__ == "__main__":
    main()