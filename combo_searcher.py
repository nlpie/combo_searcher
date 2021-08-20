from itertools import product
import random



class Expression:
    def __init__(self, op, *children):
        self.op = op
        self.children = list(children)
        self.canonize()

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)




    @property
    def associative_set(self):
        if not hasattr(self, '_associative_set'):
            retval = set()
            for child in self.children:
                if child.op == self.op:
                    retval.update(child.associative_set)
                else:
                    retval.add(child)
            self._associative_set = retval
        return self._associative_set

    @property
    def child_set(self):
        if not hasattr(self, '_child_set'):
            self._child_set = set(self.children)
        return self._child_set

    def __gt__(self, other):
        return str(self) > str(other)

    def getstr(self):
        if self.op.unary:
            return f'{self.op.symbol}({self.children[0]})'
        else:
            return self.op.symbol.join(f'({child})' for child in self.children)

    def __str__(self):
        if not hasattr(self, '_str'):
            self._str = self.getstr()
        return self._str

    def canonize(self):
        startstr = self.getstr()
        while True:
            for c in self.children:
                c.canonize()
            nl = []
            if self.op == notop and self.children[0].op == notop:
                self.op = self.children[0].children[0].op
                if type(self.children[0].children[0]) == Expression:
                    self.children = self.children[0].children[0].children
                else:
                    self.name = self.children[0].children[0].name
                    self.__class__ = Leaf
                    break
            elif self.op == notop and self.children[0].op == orop:
                self.op = andop
                a = self.children[0].children[0]
                b = self.children[0].children[1]
                self.children = [Expression(notop, a), Expression(notop, b)]
            elif self.op == notop and self.children[0].op == andop:
                self.op = orop
                a = self.children[0].children[0]
                b = self.children[0].children[1]
                self.children = [Expression(notop, a), Expression(notop, b)]
            elif self.op == xorop and self.children[0].op == notop and self.children[1].op == notop:
                self.children = [self.children[0].children[0], self.children[1].children[0]]
            if self.op.associative:
                for c in self.children:
                    if c.op == self.op:
                        nl += c.children
                    else:
                        nl.append(c)
                self.children = nl
            if self.op.commutative:
                self.children.sort()
            if self.getstr() == startstr:
                break
            else:
                startstr = self.getstr()
        self._str = startstr



    @property
    def leaves(self):
        if not hasattr(self, '_leaves'):
            self._leaves = set().union(*[child.leaves for child in self.children])
        return self._leaves

class Op:
    def __init__(self, symbol = "", associative=False, commutative=False, unary=False):
        self.symbol = symbol
        self.associative = associative
        self.commutative = commutative
        self.unary = unary

    def __str__(self):
        return self.symbol

andop = Op('&', associative = True, commutative=True)
orop = Op('|', associative = True, commutative=True)
xorop = Op('^', commutative = True)
notop = Op('~', unary=True)
leafop = Op('')

class Leaf(Expression):
    op = leafop
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return str(self) == str(other)

    def getstr(self):
        return self.name

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(str(self))

    @property
    def leaves(self):
        return {self.name}

    def canonize(self):
        pass
    

def test_scoring_function(e):
    return random.random()

#used_binops is the binary operators being combined. used_unops is the unary_operators being combined
#used_leaves is the name of all the sources for the ensembles
#minimum_improvement is how much improvement needs to occur each step for a subensemble to be added to the search list
#no_overlap, if True, forbids the same source being used twice in an expression
def get_best_ensembles(score_method=test_scoring_function, 
           names=['metamap', 'ctakes', 'clamp', 'biomedicus', 'quick_umls'], 
           used_binops=[andop, orop, xorop], 
           used_unops = [notop], 
           minimum_increase=0.1, 
           no_overlap=True):
    tiers = {}
    minimum_improvement = minimum_increase
    used_leaves = names
    def scoref(e):
        return score_method(str(e))
    tiers[1] = []
    leaf_no = len(used_leaves)
    for leaf in used_leaves:
        leaf = Leaf(leaf)
        score = scoref(leaf)
        leaf.score = score
        tiers[1].append(leaf)
    for outsize in range(1, leaf_no+1):
        tiers[outsize] = tiers.get(outsize, [])
        for insize in range(1, outsize):
            lsize = insize
            rsize = outsize - insize
            for l, r in product(tiers[lsize], tiers[rsize]):
                if no_overlap:
                    if not l.leaves.isdisjoint(r.leaves): 
                        continue
                for b in used_binops:
                    e = Expression(b, l, r)
                    if e in tiers[outsize]: 
                        continue
                    lscore = l.score
                    rscore = r.score
                    escore = scoref(e)
                    e.score = escore
                    compscore = max(lscore, rscore)
                    if escore > compscore + minimum_improvement:
                        print(e, e.score)
                        tiers[outsize].append(e)
        appendend = []
        for negator in tiers[outsize]:
            for unop in used_unops:
                if negator.op == notop:
                    break
                e = Expression(unop, negator)
                escore = scoref(e)
                e.score = escore
                if e.score > leaf.score + minimum_improvement:
                    print(e, e.score)
                    appendend.append(e)
        tiers[outsize] += appendend 
    retval = []
    for v in tiers.values():
        for vv in v:
            retval.append((str(vv), vv.score))
    retval.sort(key=lambda x: x[1], reverse=True)
    return retval



##associative
aa = Expression(orop, Expression(orop, Leaf('a'), Leaf('b')), Leaf('c'))
bb = Expression(orop, Expression(orop, Leaf('b'), Leaf('c')), Leaf('a'))
print('commutative should be true', aa == bb)
print(str(aa), str(bb))


aa = Expression(xorop, Expression(xorop, Leaf('a'), Leaf('b')), Leaf('c'))
bb = Expression(xorop, Expression(xorop, Leaf('b'), Leaf('c')), Leaf('a'))
print('associative should not be true', aa==bb)
print(str(aa), str(bb))

aa = Expression(xorop, Expression(xorop, Leaf('a'), Leaf('b')), Leaf('c'))
bb = Expression(xorop, Expression(xorop, Leaf('b'), Leaf('a')), Leaf('c'))

print('commutative should be true', aa==bb)
print(str(aa), str(bb))

aa = Expression(notop, Expression(andop, Leaf('a'), Leaf('b')))
bb = Expression(orop, Expression(notop, Leaf('a')), Expression(notop, Leaf('b')))
print('demorgans 1 should be true', aa==bb)
print(str(aa), str(bb))


aa = Expression(notop, Expression(orop, Leaf('a'), Leaf('b')))
bb = Expression(andop, Expression(notop, Leaf('a')), Expression(notop, Leaf('b')))
print('demorgans 2 should be true', aa==bb)
print(str(aa), str(bb))

aa = Expression(notop, Expression(orop, Leaf('a'), Leaf('b')))
bb = Expression(andop, Expression(notop, Leaf('a')), Expression(notop, Leaf('b')))
print('demorgans 3 should be true', bb==aa)
print(str(aa), str(bb))

aa = Expression(notop, Expression(andop, Leaf('a'), Leaf('b')))
bb = Expression(orop, Expression(notop, Leaf('a')), Expression(notop, Leaf('b')))
print('demorgans 4 should be true', bb==aa)
print(str(aa), str(bb))


aa = Expression(notop, Expression(andop, Leaf('a'), Leaf('b')))
bb = Expression(orop, Expression(notop, Leaf('a')), Expression(andop, Leaf('b')))
print('demorgans difference 1 should not be true', aa==bb)
print(str(aa), str(bb))


aa = Expression(notop, Expression(andop, Leaf('a'), Leaf('b')))
bb = Expression(andop, Expression(notop, Leaf('a')), Expression(notop, Leaf('b')))
print('demorgans difference 2 should not be true', aa==bb)
print(str(aa), str(bb))


aa = Expression(notop, Expression(orop, Leaf('a'), Leaf('b')))
bb = Expression(orop, Expression(notop, Leaf('a')), Expression(notop, Leaf('b')))
print('demorgans difference 3 should not be true', aa==bb)
print(str(aa), str(bb))


aa = Expression(notop, Expression(orop, Leaf('a'), Leaf('b')))
bb = Expression(orop, Expression(notop, Leaf('a')), Expression(andop, Leaf('b')))
print('demorgans difference 4 should not be true', aa==bb)
print(str(aa), str(bb))


aa = Expression(notop, Expression(andop, Leaf('a'), Leaf('b')))
bb = Expression(orop, Expression(notop, Leaf('a')), Expression(notop, Leaf('c')))
print('demorgans difference 5 should not be true', aa==bb)
print(str(aa), str(bb))


aa = Expression(xorop, Leaf('a'), Leaf('b'))
bb = Expression(xorop, Expression(notop, Leaf('a')), Expression(notop, Leaf('b')))
print('demorgans xor should be true', aa==bb)
print(str(aa), str(bb))
