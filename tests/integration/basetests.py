import unittest
import subprocess
import os
import shutil
import sqlite3
import re
from lxml import etree
from tempfile import mkdtemp


class BaseTest(unittest.TestCase):
    testdir = 'tests'
    fixdir = os.path.join(testdir, 'fixtures')
    outdir = os.path.join(testdir, 'test_output')

    def setUp(self):
        self.infile = os.path.join(self.fixdir, self.infilename)
        os.makedirs(self.outdir, exist_ok=True)
        self.workdir = mkdtemp(dir=self.outdir)
        self.resultfn = os.path.join(self.workdir,
                                     self.infilename + self.suffix)

    def tearDown(self):
        print(os.listdir(self.workdir))
        shutil.rmtree(self.workdir)

    def run_command(self, options=[]):
        cmd = ['python3', '{0}'.format(self.executable), self.command,
               '-d', self.workdir, '-i']
        if type(self.infile) != list:
            self.infile = [self.infile]
        cmd.extend(self.infile)
        cmd.extend(options)
        try:
            subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            print('Failed to run executable {}'.format(self.executable))
            raise



class BaseTestPycolator(BaseTest):
    executable = 'pycolator.py'
    infilename = 'percolator_out.xml'

    def get_psm_pep_ids_from_file(self, fn):
        contents = self.read_percolator_out(fn)
        return {'psm_ids': self.get_element_ids(contents['psms'],
                                                'psm_id', contents['ns']),
                'peptide_ids': self.get_element_ids(contents['peptides'],
                                                    'peptide_id',
                                                    contents['ns']),
                'psm_seqs': self.get_psm_seqs(contents['psms'],
                                              contents['ns'])
                }

    def read_percolator_out(self, fn):
        ns = self.get_namespace(fn)['xmlns']
        contents = {'ns': ns, 'psms': [], 'peptides': []}
        xml = etree.iterparse(fn)
        for ac, el in xml:
            if el.tag == '{%s}psm' % ns:
                contents['psms'].append(el)
            elif el.tag == '{%s}peptide' % ns:
                contents['peptides'].append(el)
        return contents

    def get_element_ids(self, elements, id_attrib, ns):
        return [x.attrib['{%s}%s' % (ns, id_attrib)] for x in elements]

    def get_psm_seqs(self, psms, ns):
        return [pepseq.attrib['seq'] for pepseq in
                self.get_subelements(psms, 'peptide_seq', ns)]

    def get_svms(self, elements, ns):
        return [svm.text for svm in
                self.get_subelements(elements, 'svm_score', ns)]

    def get_qvals(self, elements, ns):
        return [qval.text for qval in
                self.get_subelements(elements, 'q_value', ns)]

    def get_peps(self, elements, ns):
        return [pep.text for pep in
                self.get_subelements(elements, 'pep', ns)]

    def get_subelements(self, elements, subel, ns):
        return [element.find('{%s}%s' % (ns, subel)) for element in elements]

    def get_root_el(self, fn):
        rootgen = etree.iterparse(fn, events=('start',))
        root = next(rootgen)[1]
        for child in root.getchildren():
            root.remove(child)
        return root

    def get_namespace(self, fn):
        root = self.get_root_el(fn)
        ns = {}
        for prefix in root.nsmap:
            separator = ':'
            nsprefix = prefix
            if prefix is None:
                nsprefix = ''
                separator = ''
            ns['xmlns{0}{1}'.format(separator, nsprefix)] = root.nsmap[prefix]
        return ns

    def strip_modifications(self, pep):
        return re.sub('\[UNIMOD:\d*\]', '', pep)


class LookupTestsPycolator(BaseTestPycolator):
    def seq_in_db(self, dbconn, seq, seqtype):
        comparator = '='
        if seqtype == 'ntermfalloff':
            comparator = ' LIKE '
            seq = '{0}%'.format(seq[::-1])
        seq = seq.replace('L', 'I')
        sql = ('SELECT EXISTS(SELECT seqs FROM known_searchspace WHERE '
               'seqs{0}? LIMIT 1)'.format(comparator))
        return dbconn.execute(sql, (seq,)).fetchone()[0] == 1

    def all_seqs_in_db(self, dbfn, sequences, seqtype):
        db = sqlite3.connect(dbfn)
        seqs_in_db = set()
        for seq in sequences:
            seqs_in_db.add(self.seq_in_db(db, seq, seqtype))
        db.close()
        return seqs_in_db == set([True])


class MzidTSVBaseTest(BaseTest):
    executable = 'mzidplus.py'