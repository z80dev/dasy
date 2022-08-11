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


next_nodeid = next_node_id_maker()
