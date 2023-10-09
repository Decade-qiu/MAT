# -*- coding: utf-8 -*-
from collections import defaultdict, Counter
import os

current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(current_path)

with open(os.path.join(parent_path, "data/bview.20230901.0000"), 'r') as f:
    lines = f.readlines()
    for line in lines:
        print(line)
        break
