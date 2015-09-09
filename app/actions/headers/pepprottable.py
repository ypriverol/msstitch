from collections import OrderedDict


def generate_general_header(headerfields, fieldtypes, firstfield,
                            oldheader=False):
    if not oldheader:
        header = [firstfield]
    else:
        header = oldheader[:]
    for fieldtype in fieldtypes:
        try:
            fields = headerfields[fieldtype]
        except KeyError:
            continue
        if type(fields) == list:
            header.extend(fields)
        else:
            for pools in fields.values():
                header.extend(pools.values())
    return header


def generate_headerfields(headertypes, allfield_defs, lookup, poolnames):
    """Returns a headerfields object (dict) which contains information on
    fields of the header, including optional pool names"""
    hfields = {}
    for fieldtype in headertypes:
        hfields[fieldtype] = OrderedDict()
        hfield_definitions = allfield_defs[fieldtype]
        for fieldname, poolnames in hfield_definitions.items():
            hfields[fieldtype][fieldname] = get_header_field(lookup, poolnames)
    return hfields


def get_header_field(field, poolnames=False):
    if poolnames:
        return OrderedDict([(pool, '{}_{}'.format(pool, field))
                            for pool in poolnames])
    else:
        return {None: field}