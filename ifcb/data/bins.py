"""
Bin API. Provides consistent access to IFCB raw data stored
in various formats.
"""
    
class BaseBin(object):
    """
    Abstract base class for Bin implementations.

    The bin PID is available as a Pid object via the "pid" property.
    Subclasses must implement this.

    Bins are dict-like. Keys are target numbers, values are ADC records.
    ADC records are tuples.

    Also supports an "adc" property that is a Pandas DataFrame containing
    ADC data. Subclasses are required to provide this. The default dictlike
    implementation uses that property.

    Context manager support is provided for implementations
    that must open files or other data streams.
    """
    @property
    def lid(self):
        """
        :returns str: the bin's LID.
        """
        return self.pid.bin_lid
    @property
    def timestamp(self):
        """
        :returns datetime: the bin's timestamp.
        """
        return self.pid.timestamp
    @property
    def schema(self):
        """
        The IFCB schema in use. Schemas provide indices into
        ADC records. For example, given a bin ``B`` with a
        target number 5, the following code retrieves the x
        position of the target ROI:

        :Example:

        >>> B[5][B.schema.ROI_X]
        234

        """
        from .adc import SCHEMA
        return SCHEMA[self.pid.schema_version]
    # context manager default implementation
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    # dictlike interface
    def iterkeys(self):
        for k in self.adc.index:
            yield k
    def __iter__(self):
        return self.iterkeys()
    def has_key(self, k):
        return k in self.adc.index
    def keys(self):
        return list(self.adc.index)
    def __len__(self):
        return len(self.adc.index)
    def get_target(self, target_number):
        """
        Retrieve a target record by target number

        :param target_number: the target number
        """
        d = tuple(self.adc[c][target_number] for c in self.adc.columns)
        return d
    def __getitem__(self, target_number):
        return self.get_target(target_number)
    # convenience APIs for writing in different formats
    def to_hdf(self, hdf_file, group=None, replace=True):
        from .hdf import bin2hdf
        bin2hdf(self, hdf_file, group=group, replace=replace)
    def to_zip(self, zip_path):
        from .zip import bin2zip
        bin2zip(self, zip_path)
    def to_mat(self, mat_path):
        from .matlab import bin2mat
        bin2mat(self, mat_path)
