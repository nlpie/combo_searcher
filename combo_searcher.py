from itertools import combinations, product
import random


_minimum_increase = -1


def compose(names, op):
    r = names[0].expr + op + names[1].expr
    for n in names[2:]:
        r = f'({r}){op}{n.expr}'
    return r

def partitions(n, I=1, start=True):
    if not start:
        yield (n,)
        for i in range(I, n//2 + 1):
            for p in partitions(n-i, i, False):
                yield (i,) + p
    elif start:
        for i in range(I, n//2 + 1):
            for p in partitions(n-i, i, False):
                yieldval = {}
                for j in ( (i,) + p):
                    yieldval[j] = yieldval.get(j, 0) + 1
                yield yieldval



class Node:
    inner = False
    def __init__(self, name, scorer):
        self.names = set([name])
        self.expr = name
        self.scorer = scorer
        self.components = self

    @property
    def score(self):
        if not hasattr(self, '_score'):
            self._score = self.scorer(self.expr)
        return self._score

    def __repr__(self):
        return f'{self.expr}'


class UnionSet(Node):
    def __init__(self, names, op, scorer):
        self.names = set().union(*(n.names for n in names))
        self.components = names
        self.op = op
        self.scorer = scorer


    @property
    def expr(self):
        retval = compose(self.components, self.op)
        if self.inner:
            return f'({retval})'
        return retval




class TierSearcher:
    def __init__(self, names, op, order, scorer):
        self.tiers = {i:{'contents': [], 'union': {1:set()}} for i in range(1, order + 1)}
        self.op = op
        self.scorer = scorer
        self.order = order
        self.tiers[1]['contents'] = names
        self.tiers[1]['union'][1] = self.tiers[1]['union'][1].union(names)
        for o in range(2, order + 1):
            for combo in combinations((n for n in self.tiers[o-1]['union'][1]), o):
                insert_val = UnionSet(combo, op, scorer)
                if all(insert_val.score > n.score + _minimum_increase for n in insert_val.components):
                    self.tiers[o]['contents'].append(insert_val)
                    self.tiers[o]['union'][1] = self.tiers[o]['union'][1].union(combo)

    def insert(self, exprs, size):
        for e in exprs:
            e.inner = True
        order_new_union = {size:set()}
        for o in range(size + 1, self.order + 1):
            inssize = set()
            for p in partitions(o):
                if size in p:
                    for sizechoose in range(1, p[size] + 1):
                        oldchoose = p[size] - sizechoose
                        for combo in product(
                            combinations(exprs, sizechoose),
                            combinations(self.tiers[o -1]['union'].get(size, []), oldchoose),
                            *(combinations(self.tiers[o -1]['union'].get(s, []), pp) for s, pp in p.items()
                              if s!= size)
                        ):
                            news = combo[0]
                            combo = sum(combo, ())
                            total_size = sum(len(c.names) for c in combo)
                            union_size = len(combo[0].names.union(*(c1.names for c1 in combo[1:])))
                            if union_size == total_size:
                                insert_val = UnionSet(combo, self.op, self.scorer)
                                if all(insert_val.score > v.score + _minimum_increase for v in insert_val.components):
                                    self.tiers[o]['contents'].append(insert_val)
                                    inssize = inssize.union(news)
            order_new_union[o] = inssize
        for o, v in order_new_union.items():
            self.tiers[o]['union'][size] = self.tiers[o]['union'].get(size, set()).union(v)

    def __repr__(self):
        return repr(self.tiers)



def rs(n):
    return random.random()

def get_best_ensembles(score_method,
                       names = ['biomedicus', 'quick_umls', 'ctakes', 'clamp', 'metamap'],
                       operators = ['&', '|', '^'],
                       order = None, minimum_increase=0):
    names = [Node(name, score_method) for name in names]
    operators = set(operators)
    if order is None:
        order = len(names)
    global _minimum_increase
    _minimum_increase = minimum_increase
    opdict = {o: TierSearcher(names, o, order, score_method) for o in operators}
    for size in range(2, order):
        for others in combinations(operators, len(operators) - 1):
            original = opdict[next(iter(operators.difference(others)))]
            for o in others:
                o = opdict[o]
                original.insert(o.tiers[size]['contents'], size)
    retval =  [(n.expr, n.score)
        for o in opdict.values()
        for tier in list(o.tiers.values())[1:]
        for n in tier['contents']
    ] + [(n.expr, n.score)
        for o in list(opdict.values())[0:1]
        for tier in list(o.tiers.values())[0:1]
        for n in tier['contents']
    ]
    retval.sort(key=lambda x: x[1], reverse=True)
    return retval


