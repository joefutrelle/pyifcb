from ifcb.data.hdr import TEMPERATURE, HUMIDITY

from .ml_analyzed import compute_ml_analyzed

class BinMetrics(object):
    def __init__(self, b):
        self.bin = b
        self._ml_analyzed = None
    def _get_ml_analyzed(self):
        if self._ml_analyzed is None:
            self._ml_analyzed = compute_ml_analyzed(self.bin)
        return self._ml_analyzed
    def ml_analyzed(self):
        ma, _, _ = self._get_ml_analyzed()
        return ma
    def look_time(self):
        _, lt, _ = self._get_ml_analyzed()
        return lt
    def run_time(self):
        _, _, rt = self._get_ml_analyzed()
        return rt
    def inhibit_time(self):
        return self.run_time() - self.look_time()
    def trigger_rate(self):
        """return trigger rate in triggers / s"""
        return 1.0 * len(self.bin) / self.run_time()
    def temperature(self):
        return self.bin.headers[TEMPERATURE]
    def humidity(self):
        return self.bin.headers[HUMIDITY]
