from functools import reduce
from typing import Callable, Any, List

def pipe(*funcs: Callable) -> Callable:
    """
    Создает композицию функций, где результат одной передается в качестве аргумента следующей.
    pipe(f, g, h)(x) эквивалентно h(g(f(x))).
    """
    def piped_function(initial_value: Any) -> Any:
        return reduce(lambda acc, func: func(acc), funcs, initial_value)
    return piped_function
