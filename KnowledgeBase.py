#!/usr/bin/env python
__author__ = 'jesse'

import PerceptionClassifiers


# Load and store static facts from file. These facts can be created by hand or generated by another
# script from, for example, the BWI ASP using the StaticFactQuery service.
# For use with grounding, static fact predicates and atoms should match those in the corresponding ontology
# being used to create parses for grounding. E.g. if the ontology calls possession 'possesses(x, y)' then
# so should the facts read in from file.
class KnowledgeBase:

    # Initialize given a facts filename.
    def __init__(self, static_facts_fn, perception_source_dir, perception_feature_dir):
        self.static_facts = None
        self.static_preds = None
        self.perceptual_preds = None

        # Initialize static_facts and static_preds from facts file.
        self.extract_facts_from_file(static_facts_fn)

        # Initialize perception classifiers from source directories.
        self.pc = PerceptionClassifiers.PerceptionClassifiers(perception_source_dir, perception_feature_dir,
                                                              kernel='linear')
        self.perceptual_preds = self.pc.predicates  # Should make perceptual_preds a reference for pc preds.

    # Read in facts from file.
    # Fact format is 'predicate(arg1, arg2, ...)'
    # Facts not present in the facts file are considered false (closed-world assumption)
    def extract_facts_from_file(self, fn):
        self.static_facts = set()  # tuples (pred, arg1, arg2, ..., argN) each with arbitrary N
        self.static_preds = set()

        with open(fn, 'r') as f:
            for line in f.readlines():

                l = line.strip()
                if len(l) == 0 or l[0] == '#':
                    continue
                if l.count('(') != 1 or l.count(')') != 1:
                    print "WARNING: unreadable fact '" + str(l) + "' parens errors"
                    continue

                p = l.split('(')
                pred = p[0]
                args = [a.strip() for a in p[1].strip(')').split(',')]

                self.static_facts.add(tuple([pred] + args))
                self.static_preds.add(pred)

    # Query fact structures.
    # q is a fact query in the form (pred, arg1, arg2, ..., argN)
    # Returns a tuple of (answer, confidence) for answer a bool and confidence a value in [0, 1]
    def query(self, q):
        assert type(q) is tuple

        pred = q[0]
        if pred in self.static_preds:
            if q in self.static_facts:
                return True, 1.0
            else:
                return False, 1.0
        elif pred in self.perceptual_preds:
            # perceptual predicates are all unary p(x) for x an object, p a predicate
            # objects in the database are expected to appear as 'e' atoms with name "oidx_N" for N in [0, 31]
            oidx = int(q[1].split('_')[1])
            self.pc.run_classifier(self.pc.predicates.index(pred), oidx)

    # Add additional fact.
    def add_static_fact(self, f):
        assert type(f) is tuple
        self.static_facts.add(f)

    # Remove fact.
    # KeyError will be raised if f is not in facts.
    def remove_static_fact(self, f):
        assert type(f) is tuple
        self.static_facts.remove(f)
