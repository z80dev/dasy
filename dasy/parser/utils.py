from hy import models

def counter_gen():
    _counter = 0
    while True:
        yield _counter
        _counter += 1

def next_node_id_maker():
    counter = counter_gen()

    def next_num():
        return next(counter)

    return next_num

def pairwise(iterable):
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return zip(a, a)

def has_return(tree):
    match tree:
        case models.Symbol(sym) if str(sym) == "return":
            return True
        case models.Sequence(seq):
            for el in seq:
                if has_return(el):
                    return True
        case _:
            return False
    return False


next_nodeid = next_node_id_maker()
