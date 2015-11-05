from app.lookups.sqlite.base import ResultLookupInterface


class ProtPepTable(ResultLookupInterface):
    table_map = {'protein': {'fntable': 'protein_tables',
                             'feattable': 'proteins',
                             'isoqtable': 'protein_iso_quanted',
                             'isochtable': 'protquant_channels',
                             'prectable': 'protein_precur_quanted',
                             'fdrtable': 'protein_fdr',
                             'peptable': 'protein_pep',
                             'probabilitytable': 'protein_probability',
                             },
                 'gene': {'fntable': 'gene_tables',
                          'feattable': 'genes',
                          'isoqtable': 'gene_iso_quanted',
                          'isochtable': 'genequant_channels',
                          'prectable': 'gene_precur_quanted',
                          'fdrtable': 'gene_fdr',
                          'peptable': 'gene_pep',
                          'probabilitytable': 'gene_probability',
                          },
                 'assoc': {'fntable': 'gene_tables',
                           'feattable': 'associated_ids',
                           'isoqtable': 'assoc_iso_quanted',
                           'isochtable': 'genequant_channels',
                           'prectable': 'assoc_precur_quanted',
                           'fdrtable': 'assoc_fdr',
                           'peptable': 'assoc_pep',
                           'probabilitytable': 'assoc_probability',
                           },
                 'peptide': {'fntable': 'peptide_tables',
                             'feattable': 'peptide_sequences',
                             'isoqtable': 'peptide_iso_quanted',
                             'isochtable': 'pepquant_channels',
                             'prectable': 'peptide_precur_quanted',
                             'fdrtable': 'peptide_fdr',
                             'peptable': 'peptide_pep',
                             }
                 }

    def get_all_poolnames(self):
        cursor = self.get_cursor()
        cursor.execute(
            'SELECT DISTINCT set_name, set_id FROM biosets ORDER BY set_name')
        return cursor

    def store_table_files(self, tables):
        self.store_many(
            'INSERT INTO {}(set_id, filename) VALUES(?, ?)'.format(
                self.table_map[self.datatype]['fntable']),
            tables)

    def get_tablefn_map(self):
        table = self.table_map[self.datatype]['fntable']
        cursor = self.get_cursor()
        cursor.execute('SELECT * FROM {} '.format(table))
        return {fn: table_id for (table_id, setid, fn) in cursor}

    def get_feature_map(self):
        columns = {'protein': ['pacc_id', 'protein_acc'],
                   'gene': ['gene_id', 'gene_acc'],
                   'peptide': ['pep_id', 'sequence'],
                   'assoc': ['gene_id', 'assoc_id'],
                   }
        table = self.table_map[self.datatype]['feattable']
        columns = columns[self.datatype]
        cursor = self.get_cursor()
        cursor.execute('SELECT {}, {} FROM {}'.format(columns[0], columns[1],
                                                      table))
        return {acc: table_id for (table_id, acc) in cursor}

    def store_singlecol(self, tablekey, vals):
        table = self.table_map[self.datatype][tablekey]
        cols = self.colmap[table]
        self.store_many('INSERT INTO {}({}, {}, {}) '
                        'VALUES (?, ?, ?)'.format(table, cols[0], cols[1],
                                                  cols[2]), vals)

    def store_precursor_quants(self, quants):
        self.store_singlecol('prectable', quants)

    def store_fdr(self, fdr):
        self.store_singlecol('fdrtable', fdr)

    def store_pep(self, pep):
        self.store_singlecol('peptable', pep)

    def store_probability(self, probabilities):
        self.store_singlecol('probabilitytable', probabilities)

    def update_selects(self, selectmap, fields, fieldcount):
        selectmap.update({field: i + fieldcount
                          for i, field in enumerate(fields)})
        fieldcount = max(selectmap.values()) + 1
        return selectmap, fieldcount

    def get_proteingroup_content(self):
        cursor = self.get_cursor()
        sql = ('SELECT pgm.protein_acc, pgc.protein_acc FROM '
               'protein_group_master AS pgm '
               'JOIN protein_group_content AS pgc USING(master_id)')
        return cursor.execute(sql)

    def get_proteins_psms_for_map(self):
        """Gets protein-PSM combinations and other info for creating a map
        of protein data. This particular version is protein-group centric"""
        fields = ['p.protein_acc', 'sets.set_name',
                  'pep.sequence', 'psm.psm_id', 'pd.description',
                  'pcov.coverage', 'g.gene_acc', 'aid.assoc_id']
        extrajoins = ('LEFT OUTER JOIN prot_desc AS pd USING(protein_acc) '
                      'LEFT OUTER JOIN protein_coverage '
                      'AS pcov USING(protein_acc) '
                      'LEFT OUTER JOIN genes AS g USING(protein_acc) '
                      'LEFT OUTER JOIN associated_ids AS aid '
                      'USING(protein_acc)'
                      )
        firstjoin = ('psm_protein_groups', 'ppg', 'master_id')
        return self.get_proteins_psms('protein_group_master', fields,
                                      firstjoin, extrajoins)

    def get_proteins_psms(self, firsttable, fields, firstjoin,
                          extrajoins=False):
        joins = [firstjoin]
        joins.extend([('psms', 'psm', 'psm_id'),
                      ('peptide_sequences', 'pep', 'pep_id'),
                      ('mzml', 'sp', 'spectra_id'),
                      ('mzmlfiles', 'mzfn', 'mzmlfile_id'),
                      ('biosets', 'sets', 'set_id'),
                      ])
        join_sql = ' '.join(['JOIN {} AS {} USING({})'.format(
            j[0], j[1], j[2]) for j in joins])
        if extrajoins:
            join_sql = '{} {}'.format(join_sql, extrajoins)
        sql = ('SELECT {} FROM {} '
               'AS p'.format(', '.join(fields), firsttable))
        sql = '{} {} ORDER BY {}, sets.set_name'.format(sql, join_sql,
                                                        fields[0])
        cursor = self.get_cursor()
        return cursor.execute(sql)

    def prepare_mergetable_sql(self, precursor=False, isobaric=False,
                               probability=False, fdr=False, pep=False):
        featcol = self.colmap[self.table_map[self.datatype]['feattable']][1]
        selects = ['g.{}'.format(featcol), 'bs.set_name']
        selectmap, count = self.update_selects({}, ['p_acc', 'set_name'], 0)
        joins = []
        if isobaric:
            selects.extend(['pc.channel_name',
                            'pc.amount_psms_name', 'giq.quantvalue',
                            'giq.amount_psms'])
            joins.extend([(self.table_map[self.datatype]['isochtable'], 'pc',
                           ['gt']),
                          (self.table_map[self.datatype]['isoqtable'], 'giq',
                           ['g', 'pc'], True),
                          ])
            fld = ['channel', 'isoq_psmsfield', 'isoq_val',
                   'isoq_psms']
            selectmap, count = self.update_selects(selectmap, fld, count)
        if precursor:
            selects.extend(['preq.quant'])
            joins.append((self.table_map[self.datatype]['prectable'], 'preq',
                          ['g', 'gt'], True))
            fld = ['preq_val']
            selectmap, count = self.update_selects(selectmap, fld, count)
        if probability:
            selects.extend(['gprob.probability'])
            joins.append((self.table_map[self.datatype]['probabilitytable'],
                          'gprob', ['g', 'gt'], True))
            fld = ['prob_val']
            selectmap, count = self.update_selects(selectmap, fld, count)
        if fdr:
            selects.extend(['gfdr.fdr'])
            joins.append((self.table_map[self.datatype]['fdrtable'], 'gfdr',
                          ['g', 'gt'], True))
            fld = ['fdr_val']
            selectmap, count = self.update_selects(selectmap, fld, count)
        if pep:
            selects.extend(['gpep.pep'])
            joins.append((self.table_map[self.datatype]['peptable'], 'gpep',
                          ['g', 'gt'], True))
            fld = ['pep_val']
            selectmap, count = self.update_selects(selectmap, fld, count)
        sql = ('SELECT {} FROM {} AS g JOIN biosets AS bs '
               'JOIN {} AS gt ON gt.set_id=bs.set_id'.format(
                   ', '.join(selects),
                   self.table_map[self.datatype]['feattable'],
                   self.table_map[self.datatype]['fntable']))
        sql = self.get_sql_joins_mergetable(sql, joins, self.datatype)
        sql = '{} ORDER BY g.{}'.format(sql, featcol)
        return sql, selectmap

    def get_sql_joins_mergetable(self, sql, joins, pep_or_prot):
        protein_j_cols = {'g': 'pacc_id', 'gt': 'prottable_id'}
        peptide_j_cols = {'g': 'pep_id', 'gt': 'peptable_id'}
        gene_j_cols = {'g': 'gene_id', 'gt': 'genetable_id'}
        colpick = {'peptide': peptide_j_cols, 'protein': protein_j_cols,
                   'gene': gene_j_cols, 'assoc': gene_j_cols}
        join_cols = {'pc': 'channel_id'}
        join_cols.update(colpick[pep_or_prot])
        if joins:
            joinsql = ''
            for j in joins:
                joincmd = 'JOIN'
                if j[-1] is True:
                    joincmd = 'LEFT OUTER {}'.format(joincmd)
                joinmatchsql = ' AND '.join(['{0}.{1}={2}.{1}'.format(
                    j[1], join_cols[jj], jj) for jj in j[2]])
                joinsql = '{4} {0} {1} AS {2} ON {3}'.format(
                    joincmd, j[0], j[1], joinmatchsql, joinsql)
            sql = '{} {}'.format(sql, joinsql)
        return sql

    def get_merged_features(self, sql):
        return self.execute_sql(sql)
