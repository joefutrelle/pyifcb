from itertools import izip

import numpy as np

def assert_bin_equals(in_bin, out_bin):
    # test keys
    assert set(in_bin) == set(out_bin)
    for k in in_bin.keys():
        assert k in in_bin
        assert k in out_bin
    assert 0 not in in_bin
    assert 0 not in out_bin
    # test ADC data
    for k in in_bin.keys():
        for a, b in zip(in_bin[k], out_bin[k]):
            assert a == b or (np.isnan(a) and np.isnan(b))
    # pid
    assert in_bin.pid == out_bin.pid
    assert in_bin.lid == out_bin.lid
    # timestamp
    assert in_bin.timestamp == out_bin.timestamp
    # schema
    assert in_bin.schema == out_bin.schema
    # headers
    assert set(in_bin.headers) == set(out_bin.headers)
    for k in in_bin.headers.keys():
        # it's ok if lists come back as arrays, use np.all so
        # that tests won't spuriously fail in that case
        assert np.all(in_bin.headers[k] == out_bin.headers[k])
    # images
    assert set(in_bin.images) == set(out_bin.images)
    for k in in_bin.images:
        assert np.all(in_bin.images[k] == out_bin.images[k])
        

