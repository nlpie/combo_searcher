from itertools import combinations, product

class Node:
    #class of ensemble systems
    def __init__(self, l, r, op):
        self.l = l
        self.r = r
        self.op = op

    @property
    def cardinality(self):
        return self.l.cardinality + self.r.cardinality
    @property
    def name_set(self):
        return set([*self.l.set, *self.r.set])


class Leaf:
    cardinality = 1
    #class of individual systems
    def __init__(self, leaf):
        self.leaf = leaf

    @property
    def name_set(self):
        return set([self.leaf.name])

class ResultSet:
    @classmethod
    def set_score_method(cls, f):
        #Set the class's score method before using it. It should either take individual systems
        #or ensembles of systems as input and return a float as output
        cls.score_method = f

    def __init__(self, input1, input2=None, operator=None):
        if not (
            (input1 is not None and input2 is  None)
            or
            (input1 is None and input2 is None)
        ):
            raise TypeError('arguments must either be input1 or input1, input2, and operator')
        if input2 is None and operator is None:
            self.scoree = Leaf(input1)
        else:
            self.scoree = Node(input1, input2, operator)
        self.name_set = self.scoree.name_set
        self.cardinality = self.scoree.cardinality
        self.score = self.score_method()


def binary_summands(n):
    half = n // 2
    for i in range(1, half+1):
        yield i, n-i


class ComboTabulation:
    def __init__(self, ensemblees, operators, minimum_increase=0):
        self.cardinality_dict = {}
        order = len(ensemblees)
        self.ensemblees = ensemblees
        for i in range(1, order + 1):
            self.cardinality_dict[i] = []
        for e in ensemblees:
            self.cardinality_dict[e] = ResultSet(e)
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
                            result.score > result.scoree.l.score + minimum_increase):
                                self.cardinality_dict[i].append(result)

    def get_best(self, number_to_retrieve=10):
        search_list = [value for values in self.cardinality_dict.values() for value in values]
        search_list.sort(key=lambda x: x.score, reverse=True)
        return search_list[:number_to_retrieve]







