def flatten(complex_list):
    return [inner for outer in complex_list for inner in outer]


def nth_only_positive_index(lst, index, default=None):
    return (lst[index:index + 1] + [default])[0]


def nth(lst, index, default=None):
    try:
        return lst[index]
    except IndexError:
        return default
