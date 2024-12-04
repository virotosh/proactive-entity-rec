import logging
import os
import nltk
import gensim
from gensim import corpora
import sys
import math
import operator
import json
import itertools
import numpy
from urlparse import urlparse
from itertools import groupby
from subprocess import check_output
from numpy import exp, log, dot, zeros, outer, random, dtype, float32 as REAL,\
uint32, seterr, shape, array, uint8, vstack, fromstring, sqrt, newaxis,\
ndarray, empty, sum as np_sum, prod, ones, ascontiguousarray
import scholarly
import urllib




allpeople = json.loads(open('peopleurl.json').read().decode('utf-8'))

for person, url in allpeople.items():
	if url != '':
		print person, url
		urllib.urlretrieve(url, "profile/"+person+".jpg")