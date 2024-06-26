from dataclasses import dataclass
from typing import Any, Iterable, List, Tuple

from typing_extensions import Protocol

from collections import deque, defaultdict

# ## Task 1.1
# Central Difference calculation


def central_difference(f: Any, *vals: Any, arg: int = 0, epsilon: float = 1e-6) -> Any:
    r"""
    Computes an approximation to the derivative of `f` with respect to one arg.

    See :doc:`derivative` or https://en.wikipedia.org/wiki/Finite_difference for more details.

    Args:
        f : arbitrary function from n-scalar args to one value
        *vals : n-float values $x_0 \ldots x_{n-1}$
        arg : the number $i$ of the arg to compute the derivative
        epsilon : a small constant

    Returns:
        An approximation of $f'_i(x_0, \ldots, x_{n-1})$
    """
    vals = list(vals)
    vals[arg] += epsilon
    v1 = f(*vals)
    vals[arg] -= 2 * epsilon
    v2 = f(*vals)
    return (v1 - v2) / (2 * epsilon)


variable_count = 1


class Variable(Protocol):
    def accumulate_derivative(self, x: Any) -> None:
        pass

    @property
    def unique_id(self) -> int:
        pass

    def is_leaf(self) -> bool:
        pass

    def is_constant(self) -> bool:
        pass

    @property
    def parents(self) -> Iterable["Variable"]:
        pass

    def chain_rule(self, d_output: Any) -> Iterable[Tuple["Variable", Any]]:
        pass


def topological_sort(variable: Variable) -> Iterable[Variable]:
    """
    Computes the topological order of the computation graph.

    Args:
        variable: The right-most variable

    Returns:
        Non-constant Variables in topological order starting from the right.
    """

    # vars that need derivatives computed first are before others
    sorted_variables = deque()
    visited = set()

    def _traverse(variable: Variable) -> None:
        if variable.unique_id in visited: return
        visited.add(variable.unique_id)

        for input_var in variable.history.inputs:
            _traverse(input_var)
        
        sorted_variables.appendleft(variable)
    
    _traverse(variable)
    return sorted_variables


def backpropagate(variable: Variable, deriv: Any) -> None:
    """
    Runs backpropagation on the computation graph in order to
    compute derivatives for the leave nodes.

    Args:
        variable: The right-most variable
        deriv  : Its derivative that we want to propagate backward to the leaves.

    No return. Should write to its results to the derivative values of each leaf through `accumulate_derivative`.
    """
    sorted_variables = topological_sort(variable)
    states = defaultdict(int) # intermediate scalars : cumulative gradient from later in the graph
    states[variable.unique_id] += deriv
    
    for var in sorted_variables:
        if var.is_leaf(): # we would have accumulated the derivs for leaf vars below
            continue
        grad_from_later = states[var.unique_id]
        grads_for_inputs = var.chain_rule(grad_from_later)
        for (input_var, d) in grads_for_inputs:
            if input_var.is_leaf():
                input_var.accumulate_derivative(d)
            else:
                states[input_var.unique_id] += d


@dataclass
class Context:
    """
    Context class is used by `Function` to store information during the forward pass.
    """

    no_grad: bool = False
    saved_values: Tuple[Any, ...] = ()

    def save_for_backward(self, *values: Any) -> None:
        "Store the given `values` if they need to be used during backpropagation."
        if self.no_grad:
            return
        self.saved_values = values

    @property
    def saved_tensors(self) -> Tuple[Any, ...]:
        return self.saved_values
