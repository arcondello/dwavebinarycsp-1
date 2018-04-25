from functools import reduce
from math import factorial
from operator import mul
from random import choice, sample, random

from six.moves import range

import dimod

from dwavecsp.core.csp import ConstraintSatisfactionProblem
from dwavecsp.factories.constraint.sat import sat2in4
from dwavecsp.factories.constraint.gates import xor_gate

__all__ = ['random_2in4sat',
           'random_xorsat']


def random_2in4sat(num_variables, num_clauses, vartype=dimod.BINARY, satisfiable=True):
    """todo"""

    if num_variables < 4:
        raise ValueError("a 2in4 problem needs at least 4 variables")
    if num_clauses > 16 * _nchoosek(num_variables, 4):  # 16 different negation patterns
        raise ValueError("too many clauses")

    # also checks the vartype argument
    csp = ConstraintSatisfactionProblem(vartype)

    variables = list(range(num_variables))

    constraints = set()

    if satisfiable:
        values = tuple(vartype.value)
        planted_solution = {v: choice(values) for v in variables}

        configurations = [(0, 0, 1, 1), (0, 1, 0, 1), (1, 0, 0, 1),
                          (0, 1, 1, 0), (1, 0, 1, 0), (1, 1, 0, 0)]

        while len(constraints) < num_clauses:
            # sort the variables because constraints are hashed on configurations/variables
            # because 2-in-4 sat is symmetric, we would not get a hash conflict for different
            # variable orders
            constraint_variables = sorted(sample(variables, 4))

            # pick (uniformly) a configuration and determine which variables we need to negate to
            # match the chosen configuration
            config = choice(configurations)
            pos = tuple(v for idx, v in enumerate(constraint_variables) if config[idx] == (planted_solution[v] > 0))
            neg = tuple(v for idx, v in enumerate(constraint_variables) if config[idx] != (planted_solution[v] > 0))

            const = sat2in4(pos=pos, neg=neg, vartype=vartype)

            assert const.check(planted_solution)

            constraints.add(const)
    else:
        while len(constraints) < num_clauses:
            # sort the variables because constraints are hashed on configurations/variables
            # because 2-in-4 sat is symmetric, we would not get a hash conflict for different
            # variable orders
            constraint_variables = sorted(sample(variables, 4))

            # randomly determine negations
            pos = tuple(v for v in constraint_variables if random() > .5)
            neg = tuple(v for v in constraint_variables if v not in pos)

            const = sat2in4(pos=pos, neg=neg, vartype=vartype)

            constraints.add(const)

    for const in constraints:
        csp.add_constraint(const)

    # in case any variables didn't make it in
    for v in variables:
        csp.add_variable(v)

    return csp


def random_xorsat(num_variables, num_clauses, vartype=dimod.BINARY, satisfiable=True):
    """todo"""
    if num_variables < 3:
        raise ValueError("a xor problem needs at least 3 variables")
    if num_clauses > 8 * _nchoosek(num_variables, 3):  # 8 different negation patterns
        raise ValueError("too many clauses")

    # also checks the vartype argument
    csp = ConstraintSatisfactionProblem(vartype)

    variables = list(range(num_variables))

    constraints = set()

    if satisfiable:
        values = tuple(vartype.value)
        planted_solution = {v: choice(values) for v in variables}

        configurations = [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)]

        while len(constraints) < num_clauses:
            # because constraints are hashed on configurations/variables, and because the inputs
            # to xor can be swapped without loss of generality, we can order them
            x, y, z = sample(variables, 3)
            if y > x:
                x, y = y, x

            # get the constraint
            const = xor_gate([x, y, z], vartype=vartype)

            # pick (uniformly) a configuration and determine which variables we need to negate to
            # match the chosen configuration
            config = choice(configurations)

            for idx, v in enumerate(const.variables):
                if config[idx] != (planted_solution[v] > 0):
                    const.flip_variable(v)

            assert const.check(planted_solution)

            constraints.add(const)
    else:
        while len(constraints) < num_clauses:
            # because constraints are hashed on configurations/variables, and because the inputs
            # to xor can be swapped without loss of generality, we can order them
            x, y, z = sample(variables, 3)
            if y > x:
                x, y = y, x

            # get the constraint
            const = xor_gate([x, y, z], vartype=vartype)

            # randomly flip each variable in the constraint
            for idx, v in enumerate(const.variables):
                if random() > .5:
                    const.flip_variable(v)

            assert const.check(planted_solution)

            constraints.add(const)

    for const in constraints:
        csp.add_constraint(const)

    # in case any variables didn't make it in
    for v in variables:
        csp.add_variable(v)

    return csp


def _nchoosek(n, k):
    return reduce(mul, range(n, n - k, -1), 1) // factorial(k)
