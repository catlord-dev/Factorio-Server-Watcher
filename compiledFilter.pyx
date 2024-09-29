


cdef bint filterWord(str word, str filter):
    cdef bint negate = filter.startswith("!")
    if negate:
        filter = filter[1:]
    cdef bint match = filter in word
    return match != negate


cpdef set filterString(str string, filters: set | tuple):


    cdef str subfilter
    cdef bint hit
    cdef bint match

    cdef set hitFilters = set()
    for filter in filters:
        if isinstance(filter, tuple):
            
            hit = True
            for subfilter in filter:
                if not filterWord(string, subfilter):
                    hit = False
                    break
            if hit:
                hitFilters.add(filter)
                continue
        else:
            match = filterWord(string, filter)
            if match:
                hitFilters.add(filter)
    return hitFilters