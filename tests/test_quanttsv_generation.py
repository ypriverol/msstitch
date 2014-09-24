import unittest
from unittest.mock import patch, Mock
from app.preparation.mzidtsv import quant as prep
from app.dataformats import mzidtsv

def mock_quantmaps(self):
    return (('116',), ('117',), ('118',))


def mock_findquants(self, fn, scannr):
    return (('116', 1024), ('117', 4352), ('118', 4543))


def mock_tsv_header(fn):
    yield 'this\tis\ta\ttest\theader'.split('\t')


def mock_tsv_psms(fn, header):
    yield {k: 0 for k in [mzidtsv.HEADER_SPECFILE,
                          mzidtsv.HEADER_SCANNR,
                          mzidtsv.HEADER_PEPTIDE,
                          mzidtsv.HEADER_PROTEIN,]
                          }


class TestQuantDBLookups(unittest.TestCase):
    def setUp(self):
        self.mockdb = Mock
        self.mockdb.lookup_quant = mock_findquants
        self.mockdb.get_all_quantmaps = mock_quantmaps
        self.mockreader = Mock
        self.mockreader.generate_tsv_psms = mock_tsv_psms

    def test_get_quantheader(self):
        fn = 'test'
        with patch('app.preparation.mzidtsv.quant.sqlite.QuantDB', self.mockdb):
            gqh = prep.get_quant_header
            assert gqh([], fn) == ['116', '117', '118']

    def test_lookup_quant(self):
        result = prep.lookup_quant('fn', '1234', self.mockdb())
        assert result == {'116': 1024,
                          '117': 4352,
                          '118': 4543,
                          }

    def test_generate_mzidtsv_quanted(self):
        with patch('app.preparation.mzidtsv.quant.sqlite.QuantDB', self.mockdb), patch('app.preparation.mzidtsv.quant.readers', self.mockreader):
            psms = prep.generate_psms_quanted('fn', 'tsvfn',
                                              list([x[0] for x in
                                                    mock_quantmaps(self)]),
                                              next(mock_tsv_header('fn')))
            result = next(psms)
        line = next(mock_tsv_psms('test', 'fakeheader'))
        line.update({k: v for k, v in mock_findquants('test', 'test', 'test')})
        self.assertEqual(result, line)


class TestQuantLines(unittest.TestCase):
    def test_convert_quantdict(self):
        qdata = {'116': '1024', '117': '2048'}
        allin = prep.get_quant_NAs(qdata, ['116', '117'])
        self.assertEqual(allin, {'116': '1024', '117': '2048'})
        notfound = prep.get_quant_NAs(qdata,
                                      ['116', '117', '118'])
        self.assertEqual(notfound, {'116': '1024', 
                                    '117': '2048', '118': 'NA'})

    def create_tsv_header(self):
        qhead = list(mock_quantmaps(self))
        with patch('app.preparation.mzidtsv.quant.readers.get_tsv_header',
                   mock_tsv_header):
            result = prep.create_tsv_header_quant('test', qhead)
        desired = next(mock_tsv_header()) + qhead
        self.assertEqual(result, desired)
