from itertools import combinations, product
import random


class Node:
    #class of ensemble systems
    def __init__(self, l, r, op):
        self.l = l
        self.r = r
        self.op = op

    @property
    def name_set(self):
        return set([*self.l.name_set, *self.r.name_set])

    @property
    def expr(self):
        return f'({self.l.expr}{self.op}{self.r.expr})'


class Leaf:
    #class of individual systems
    def __init__(self, leaf):
        self.leaf = leaf

    @property
    def name_set(self):
        return set([self.leaf])

    @property
    def expr(self):
        return self.leaf



class ResultSet:
    @classmethod
    def set_score_method(cls, f):
        #Set the class's score method before using it. It should either take individual systems
        #or ensembles of systems as input and return a float as output
        cls.score_method = staticmethod(f)

    def __init__(self, input1, input2=None, operator=None):
        if (
            (input2 is not None and operator is  None)
            or
            (input2 is None and operator is not None)
        ):
            raise TypeError('arguments must either be input1 or input1, input2, and operator')
        if input2 is None and operator is None:
            self.scoree = Leaf(input1)
        else:
            self.scoree = Node(input1, input2, operator)
        self.name_set = self.scoree.name_set
        self.score = self.score_method(self.scoree.expr)
        self.expr = self.scoree.expr

    @property
    def score_print(self):
        if type(self.scoree) == Leaf:
            return f'{self.scoree.expr}:{self.score}'
        elif type(self.scoree) == Node:
            return f'({self.scoree.l.score_print}{self.scoree.op} {self.scoree.r.score_print}):{self.score}'


def binary_summands(n):
    half = n // 2
    for i in range(1, half+1):
        yield i, n-i


class ComboTabulation:
    def __init__(self, score_method, ensemblees, operators, max_order=None, minimum_increase=0):
        ResultSet.set_score_method(score_method)
        self.cardinality_dict = {}
        order = len(ensemblees) if max_order is None else max_order
        self.ensemblees = ensemblees
        for i in range(1, order + 1):
            self.cardinality_dict[i] = []
        for e in ensemblees:
            self.cardinality_dict[1].append(ResultSet(e))
        for i in range(2, order + 1):
            for ll, rr in binary_summands(i):
                if ll == rr:
                    generator = combinations(self.cardinality_dict[ll], 2)
                else:
                    generator = product(self.cardinality_dict[ll], self.cardinality_dict[rr])
                for left, right in generator:
                    for o in operators:
                        if not left.name_set.intersection(right.name_set):
                            result = ResultSet(left, right, o)
                            if (result.score > result.scoree.l.score + minimum_increase
                            and
                            result.score > result.scoree.r.score + minimum_increase):
                                self.cardinality_dict[i].append(result)

    def get_best(self, number_to_retrieve=10):
        search_list = [value for values in self.cardinality_dict.values() for value in values]
        search_list.sort(key=lambda x: x.score, reverse=True)
        search_list = [(r.expr, r.score) for r in search_list]
        return search_list[:number_to_retrieve]

    def print_all(self):
        [print(value.score_print) for values in self.cardinality_dict.values() for value in values]

def length_score(expr):
    return len(expr)

def random_score(expr):
    return random.random()


#give this function a score method which takes expressions,
#a list of system names
#a list of operator symbols
#order specifies how long the ensembles can get (it defaults to the number of system names
#minimum increase specifies how much a given ensemble must improve over its components to be considered valid
#it currently is 0, meaning any improvement at all counts
#call result.get_best(number_to_return) on the return value to get the best ensembles.
def get_best_ensembles(score_method=random_score,
              names=['quick_umls', 'metamap', 'biomedicus', 'clamp', 'ctakes'],
              operators=['&', '|', '^'],
              order=None,
              minimum_increase=0):
    return ComboTabulation(score_method, names, operators, order, minimum_increase)






