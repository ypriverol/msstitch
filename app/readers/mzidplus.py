"""Reader methods for mzIdentML as generated by MSGF+"""

import basereader
import ml


def get_mzid_namespace(mzidfile):
    return basereader.get_namespace_from_top(mzidfile, None)


def mzid_spec_result_generator(mzidfile, namespace):
    return basereader.generate_tags_multiple_files(
        [mzidfile],
        'SpectrumIdentificationResult',
        ['cvList',
         'AnalysisSoftwareList',
         'SequenceCollection',
         'AnalysisProtocolCollection',
         'AnalysisCollection',
         ],
        namespace)


def mzid_specdata_generator(mzidfile, namespace):
    return basereader.generate_tags_multiple_files(
        [mzidfile],
        'SpectraData',
        ['cvList',
         'AnalysisSoftwareList',
         'SequenceCollection',
         'AnalysisProtocolCollection',
         'AnalysisCollection',
         'AnalysisData',
         ],
        namespace)


def get_mzid_specfile_ids(mzidfn, namespace):
    """Returns mzid spectra data filenames and their IDs used in the
    mzIdentML file as a dict. Keys == IDs, values == fns"""
    sid_fn = {}
    for specdata in mzid_specdata_generator(mzidfn, namespace):
        sid_fn[specdata.attrib['id']] = specdata.attrib['name']
    return sid_fn


def get_specresult_scan_nr(result):
    """Returns scan nr of an mzIdentML PSM as a str. The PSM is given
    as a SpectrumIdentificationResult element."""
    return ml.get_scan_nr(result, 'spectrumID')


def get_specresult_mzml_id(specresult):
    return specresult.attrib['spectraData_ref']


def get_specidentitem_percolator_data(item, namespace):
    def get_xpath(it, ns, tag, select_key, select_val):
        it.xpath('{0}{1}[@{2}="{3}"]'.format(ns['xmlns'],
                                             tag,
                                             select_key,
                                             select_val)
                 )[0].attrib['value']
    svm = get_xpath(item, namespace, 'userParam', 'name', 'svm-score')
    psmq = get_xpath(item, namespace, 'cvParam', 'name', 'MS-GF:QValue')
    pepq = get_xpath(item, namespace, 'cvParam', 'name', 'MS-GF:PepQValue')
    psmpep = get_xpath(item, namespace, 'cvParam', 'name', 'MS-GF:PEP')
    ppep = get_xpath(item, namespace, 'userParam', 'name', 'peptide-level-PEP')
    return {'svm': svm,
            'psmq': psmq,
            'pepq': pepq,
            'psmpep': psmpep,
            'peppep': ppep,
            }
