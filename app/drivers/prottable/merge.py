import os

from app.actions.prottable import merge as preparation
from app.drivers.prottable.base import ProttableMergeDriver


class BuildProteinTableDriver(ProttableMergeDriver):
    outsuffix = ''
    lookuptype = 'prottable'

    def __init__(self, **kwargs):
        """Build protein table has no input file (though it has a lookup),
        which is why we set it to outfile name so the infile fetching
        and outfile creating wont error."""
        kwargs['infile'] = os.path.join(os.getcwd(),
                                        'built_protein_table.txt')
        self.genecentric = kwargs.get('genecentric', False)
        if self.genecentric:
            self.lookuptype = {'genes': 'genetable',
                               'assoc': 'associdtable'}[self.genecentric]
        super().__init__(**kwargs)
        self.isobaricquant = kwargs.get('isobaric', False)
        self.precursorquant = kwargs.get('precursor', False)
        self.probability = kwargs.get('probability', False)
        self.fdr = kwargs.get('fdr', False)
        self.pep = kwargs.get('pep', False)

    def set_feature_generator(self):
        """Generates proteins with quant from the lookup table"""
        self.features = preparation.build_proteintable(self.lookup,
                                                       self.header,  # FIXME?
                                                       self.headerfields,
                                                       self.isobaricquant,
                                                       self.precursorquant,
                                                       self.probability,
                                                       self.fdr, self.pep,
                                                       self.genecentric)
