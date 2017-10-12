#!/usr/bin/env python
__author__ = 'jesse'

import itertools
import PerceptionClassifiers


# Load and store static facts from file. These facts can be created by hand or generated by another
# script from, for example, the BWI ASP using the StaticFactQuery service.
# For use with grounding, static fact predicates and atoms should match those in the corresponding ontology
# being used to create parses for grounding. E.g. if the ontology calls possession 'possesses(x, y)' then
# so should the facts read in from file.
class KnowledgeBase:

    # Initialize given a facts filename.
    def __init__(self, static_facts_fn, perception_source_dir, perception_feature_dir, ontology):
        self.static_facts = None
        self.static_preds = None
        self.perceptual_preds = None
        self.ontology = ontology

        # Initialize static_facts and static_preds from facts file.
        self.extract_facts_from_file(static_facts_fn)

        # Initialize perception classifiers from source directories.
        self.pc = PerceptionClassifiers.PerceptionClassifiers(perception_source_dir, perception_feature_dir,
                                                              kernel='linear')
        self.perceptual_preds = self.pc.predicates  # Should make perceptual_preds a reference for pc preds.

    # Read in facts from file.
    # Fact format is 'predicate(arg1, arg2, ...)'
    # If a predicate is prefixed with a '*' it is treated as symmetric, e.g. "*beside(a,b)" adds "beside(b,a)"
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

                # Validate against ontology.
                if pred not in self.ontology.preds:
                    raise ValueError("predicate '" + pred + "' in static facts not found in ontology")
                for a in args:
                    if a not in self.ontology.preds:
                        raise ValueError("argument '" + a + "' in static facts not found in ontology")

                # Add the fact commutatively (with all argument permutations).
                if self.ontology.preds.index(pred) in self.ontology.commutative:
                    for perm_idxs in itertools.permutations(range(len(args))):
                        self.static_facts.add(tuple([pred] + [args[idx] for idx in perm_idxs]))
                # Add the fact with arguments in-place.
                else:
                    self.static_facts.add(tuple([pred] + args))
                self.static_preds.add(pred)

    # Query fact structures.
    # q is a fact query in the form (pred, arg1, arg2, ..., argN)
    # Returns a tuple of (answer, confidence) for answer a pos_conf, neg_conf tuple each in [0, 1]
    # pos_conf + neg_conf = 1.0 or pos_conf = neg_conf = 0.0
    def query(self, q):
        assert type(q) is tuple

        pred = q[0]
        if pred in self.static_preds:
            if q in self.static_facts:
                return 1.0, 0.0
            else:
                return 0.0, 1.0
        elif pred in self.perceptual_preds:
            # perceptual predicates are all unary p(x) for x an object, p a predicate
            # objects in the database are expected to appear as 'e' atoms with name "oidx_N" for N in [0, 31]
            oidx = int(q[1].split('_')[1])
            return self.pc.run_classifier(self.pc.predicates.index(pred), oidx)
        else:  # pred doesn't appear in static facts or in known perceptual preds
            return 0.0, 1.0  # return confident false by closed-world assumption

    # Add additional fact.
    def add_static_fact(self, f):
        assert type(f) is tuple
        self.static_facts.add(f)

    # Remove fact.
    # KeyError will be raised if f is not in facts.
    def remove_static_fact(self, f):
        assert type(f) is tuple
        self.static_facts.remove(f)
