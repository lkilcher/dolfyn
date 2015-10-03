

def within(arr, range):
    """Find the values in `arr` that are inside of `range`.

    This is equivalent to range[0] < arr < range[1], but it works on
    arrays.

    """
    return (range[0] < arr) & (arr < range[1])
