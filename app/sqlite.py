import sqlite3
import os
from tempfile import mkstemp


class DatabaseConnection(object):
    def __init__(self, fn=None, foreign_keys=False):
        self.fn = fn
        if self.fn is not None:
            self.cursor = self.connect(self.fn)

    def create_db(self, tables, outfn=None, foreign_keys=False):
        """Creates a sqlite db file.
        tables is a dict with keys=table names, values=lists of cols.
        """
        if outfn is None:
            fd, outfn = mkstemp(prefix='msstitcher_tmp_')
            os.close(fd)
        self.fn = outfn
        self.cursor = self.connect(outfn, foreign_keys)
        for table in tables:
            columns = tables[table]
            self.cursor.execute('CREATE TABLE {0}({1})'.format(
                table, ', '.join(columns)))
        self.conn.commit()

    def connect(self, fn, foreign_keys=False):
        self.conn = sqlite3.connect(fn)
        cur = self.conn.cursor()
        if foreign_keys:
            cur.execute('PRAGMA FOREIGN_KEYS=ON')
        return cur

    def close_connection(self):
        self.conn.close()

    def index_column(self, index_name, table, column):
        self.cursor.execute(
            'CREATE INDEX {0} on {1}({2})'.format(index_name, table, column))
        self.conn.commit()


class SearchSpaceDB(DatabaseConnection):
    def create_searchspacedb(self, outfn):
        self.create_db({'known_searchspace': ['seqs TEXT']}, outfn)

    def write_peps(self, peps, reverse_seqs):
        """Writes peps to db. We can reverse to be able to look up
        peptides that have some amino acids missing at the N-terminal.
        This way we can still use the index.
        """
        if reverse_seqs:
            peps = [(x[0][::-1],) for x in peps]
        self.cursor.executemany(
            'INSERT INTO known_searchspace(seqs) VALUES (?)', peps)
        self.conn.commit()

    def index_peps(self):
        self.index_column('seqs_index', 'known_searchspace', 'seqs')

    def check_seq_exists(self, seq, ntermwildcards=False):
        """Look up sequence in sqlite DB. Returns True or False if it
        exists (or not). When looking up a reversed DB with
        ntermwildcards: we reverse the sequence of the pep and add
        a LIKE and %-suffix to the query.
        """
        if ntermwildcards:
            seq = seq[::-1]
            comparator, seqmod = ' LIKE ', '%'
        else:
            comparator, seqmod = '=', ''

        sql = ('select exists(select seqs from known_searchspace '
               'where seqs{0}? limit 1)'.format(comparator))
        seq = '{0}{1}'.format(seq, seqmod)
        self.cursor.execute(sql, (seq, ))
        return self.cursor.fetchone()[0] == 1


class QuantDB(DatabaseConnection):
    def create_quantdb(self):
        self.create_db({'quant': ['spectra_filename TEXT', 'scan_nr TEXT',
                                  'quantmap TEXT', 'intensity REAL']})

    def store_quants(self, quants):
        self.cursor.executemany(
            'INSERT INTO quant(spectra_filename, scan_nr, quantmap, intensity)'
            ' VALUES (?, ?, ?, ?)',
            quants)
        self.conn.commit()

    def index_quants(self):
        self.index_column('spec_index', 'quant', 'spectra_filename')
        self.index_column('scan_index', 'quant', 'scan_nr')

    def lookup_quant(self, spectrafile, scannr):
        self.cursor.execute(
            'SELECT quantmap, intensity FROM quant WHERE '
            'spectra_filename=? AND scan_nr=?', (spectrafile, scannr))
        return self.cursor.fetchall()

    def get_all_quantmaps(self):
        self.cursor.execute(
            'SELECT DISTINCT quantmap FROM quant')
        return self.cursor.fetchall()


class PeptideFilterDB(DatabaseConnection):
    pass


class ProteinPeptideDB(DatabaseConnection):
    def create_pgdb(self):
        self.create_db({'peptides': ['peptide_id TEXT PRIMARY KEY NOT NULL',
                                     'scan_nr INTEGER', 'spectra_file TEXT'],
                        'protein_peptide': ['protein_acc TEXT',
                                            'peptide_id TEXT, FOREIGN KEY'
                                            '(peptide_id) REFERENCES '
                                            'peptides(peptide_id)']
                        }, foreign_keys=True)

    def store_peptide_proteins(self, ppmap):
        def generate_proteins(pepprots):
            for pep_id, pepvals in pepprots.items():
                for protein in pepvals['proteins']:
                    yield protein, pep_id
        peptides = ((k, v['scan_nr'], v['specfn']) for k, v in ppmap.items())
        self.cursor.executemany(
            'INSERT INTO peptides(peptide_id, scan_nr, spectra_file) '
            'VALUES(?, ?, ?)', peptides)
        self.cursor.executemany(
            'INSERT INTO protein_peptide(protein_acc, peptide_id) VALUES '
            '(?, ?)', generate_proteins(ppmap))
        self.conn.commit()

    def index(self):
        self.index_column('spec_index', 'peptides', 'spectra_file')
        self.index_column('scan_index', 'peptides', 'scan_nr')
        self.index_column('peptide_id_index', 'protein_peptide', 'peptide_id')
