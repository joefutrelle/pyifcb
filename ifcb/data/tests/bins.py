from itertools import izip

import numpy as np

def assert_bin_equals(in_bin, out_bin):
    # test keys
    assert set(in_bin) == set(out_bin)
    for k in in_bin.keys():
        assert k in in_bin, 'inconsistent dict behavior'
        assert k in out_bin, 'key membership does not match'
    assert 0 not in in_bin, 'zero-based index'
    assert 0 not in out_bin, 'zero-based index'
    # test ADC data
    for k in in_bin.keys():
        for a, b in zip(in_bin[k], out_bin[k]):
            assert np.isclose(a, b, equal_nan=True)
    # pid
    assert in_bin.pid == out_bin.pid, 'pid mismatch'
    assert in_bin.lid == out_bin.lid, 'lid mismatch'
    # timestamp
    assert in_bin.timestamp == out_bin.timestamp, 'timestamp mismatch'
    # schema
    assert in_bin.schema == out_bin.schema, 'schema mismatch'
    # headers
    assert set(in_bin.headers) == set(out_bin.headers), 'header keys mismatch'
    for k in in_bin.headers.keys():
        # headers should all have same names and values
        assert in_bin.headers[k] == out_bin.headers[k], 'header values mismatch'
    # images
    assert set(in_bin.images) == set(out_bin.images), 'image target numbers mismatch'
    for k in in_bin.images:
        assert np.all(in_bin.images[k] == out_bin.images[k]), 'image data mismatch'

