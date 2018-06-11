import textwrap
import types

sphinx_directive_dict = {types.FunctionType: 'func',
                         type: 'class', }


def table_obj(objs, name_width=21, doc_width=50):
    """Create a table from a list of data objects.

    This is similar to sphinx's `autosummary` directive, but for
    operating within Python.
    """
    hsep = '+' + '-' * (name_width + 2) + '+' + '-' * (doc_width + 2) + '+\n'
    form = '| {: <%d} | {: <%d} |\n' % (name_width, doc_width)
    out = hsep
    for obj in objs:
        if obj.__doc__ is not None:
            nm = obj.__name__
            tp = type(obj)
            if tp in sphinx_directive_dict:
                nm = ':{type}:`.{name}`'.format(type=sphinx_directive_dict[type(obj)],
                                                name=nm)
            hdr = textwrap.wrap(obj.__doc__.split('\n')[0], doc_width)
            out += form.format(nm, hdr[0])
            for h in hdr[1:]:
                out += form.format('', h)
            out += hsep
    return out
