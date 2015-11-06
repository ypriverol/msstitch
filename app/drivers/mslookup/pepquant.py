from app.actions.mslookup import proteinquant as lookups
from app.drivers.mslookup.proteinquant import ProteinQuantLookupDriver


class PeptideQuantLookupDriver(ProteinQuantLookupDriver):
    """Creates lookup of peptide tables that contain quant data"""
    lookuptype = 'peptidetable'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.peptidecol = kwargs.get('pepcol', None)

    def create_lookup(self):
        self.peptidecol = self.peptidecol - 1
        lookups.create_peptidequant_lookup(self.fn, self.lookup,
                                           self.poolnames,
                                           self.peptidecol,
                                           self.precursorquantcolpattern,
                                           self.quantcolpattern,
                                           self.psmnrcolpattern,
                                           self.fdrcolpattern,
                                           self.pepcolpattern)
