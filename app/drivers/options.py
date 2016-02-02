import argparse

shared_options = {
    'fn': {'driverattr': 'fn', 'dest': 'infile', 'type': 'file', 'clarg': '-i',
           'help': 'Input file'},
    'outdir': {'driverattr': 'outdir', 'dest': 'outdir', 'clarg': '-d',
               'help': 'Directory to output in', 'type': 'file'},
    'multifiles': {'driverattr': 'fn', 'dest': 'infile', 'clarg': '-i',
                   'help': 'Multiple input files for use in merging data. ',
                   'type': 'file', 'nargs': '+'},
    'lookupfn': {'driverattr': 'lookupfn', 'clarg': '--dbfile',
                 'type': 'file', 'help': 'Database lookup file'},
    'setnames': {'driverattr': 'setnames', 'dest': 'setnames',
                 'type': str, 'nargs': '+', 'clarg': '--setnames',
                 'help': 'Names of biological sets. Can be '
                 'specified with quotation marks if spaces are '
                 'used'},
    'spectracol': {'driverattr': 'spectracol', 'dest': 'spectracol',
                   'type': int, 'clarg': '--spectracol', 'help':
                   'Column number in which spectra file names are, '
                   'in case some framework has changed the file '
                   'names. First column number is 1.'},
    'decoyfn': {'driverattr': 'decoyfn', 'dest': 'decoyfn',
                'help': 'Decoy input file (percolator out XML) for qvality',
                'type': 'file', 'clarg': '--decoyfn'},
    # FIXME CLARG got updated for --decoy to --decoyfn
    'falloff': {'driverattr': 'falloff', 'dest': 'falloff',
                'clarg': '--ntermwildcards', 'action': 'store_const',
                'const': True, 'default': False, 'help': 'Flag to '
                'filter against both intact peptides and those '
                'that match to the C-terminal part of a tryptic peptide '
                'from the database. Database should be built with this'
                'flag in order for the lookup to work, since sequences'
                'will be stored and looked up reversed', 'required': False
                },
    'proline': {'driverattr': 'proline', 'dest': 'proline', 'required': False,
                'clarg': '--cutproline', 'action': 'store_const',
                'const': True, 'default': False, 'help': 'Flag to make '
                'trypsin before a proline residue. Then filtering will be '
                'done against both cut and non-cut peptides.',
                },
    'trypsinize': {'driverattr': 'trypsinize', 'dest': 'trypsinize',
                   'clarg': '--notrypsin', 'required': False,
                   'action': 'store_const', 'const': False, 'default': True,
                   'help': 'Do not trypsinize. User is expected to deliver a'
                   'pretrypsinized FASTA file'
                   },
    'featuretype': {'driverattr': 'featuretype', 'dest': 'featuretype',
                    'help': 'Feature type to use for qvality. Can either be '
                    'psm or peptide.', 'clarg': '--feattype',
                    'type': 'pick', 'picks': ['psm', 'peptide']},
    # FIXME CLARG changes -f to --feattype
    'unroll': {'driverattr': 'unroll', 'clarg': '--unroll', 'const': True,
               'action': 'store_const', 'default': False, 'help': 'PSM table '
               'from Mzid2TSV contains either one PSM per line with all '
               'the proteins of that shared peptide on the same line (not'
               ' unrolled, default), or one PSM/protein match per line '
               'where each protein from that shared peptide gets its own '
               'line (unrolled).', 'required': False},
    'genecentric': {'driverattr': 'genecentric', 'dest': 'genecentric',
                    'clarg': '--genecentric', 'type': 'pick',
                    'picks': ['assoc', 'genes'], 'required': False,
                    'default': False, 'help': 'Do not include protein group '
                    'data in output. Should be one of [genes, assoc]. '
                    'With assoc, associated gene IDs are used from e.g. '
                    'Biomart rather than the ones found in the FASTA db used '
                    'for PSM search. These need to have been stored when '
                    'creating a PSM lookup.'},
    'isobaric': {'driverattr': 'isobaric', 'clarg': '--isobaric',
                 'action': 'store_const', 'const': True, 'default': False,
                 'help': 'Specifies to add isobaric quant data from lookup DB '
                 'to output table', 'required': False,
                 },
    'precursor': {'driverattr': 'precursor', 'clarg': '--precursor',
                  'action': 'store_const', 'const': True, 'default': False,
                  'help': 'Specifies to add precursor quant data from lookup '
                  'DB to output table', 'required': False,
                  },
    'quantcolpattern': {'driverattr': 'quantcolpattern',
                        'clarg': '--isobquantcolpattern', 'type': str,
                        'default': None, 'required': False,
                        'help': 'Unique text pattern to identify '
                        'isobaric quant column in protein table.'},
    # FIXME quantcolpattern is required for "addisoquant" in prottable,
    # but not for mslookup or peptable-psm2pep
    'precursorquantcolpattern': {'driverattr': 'precursorquantcolpattern',
                                 'type': str, 'required': False,
                                 'dest': 'precursorquantcolpattern',
                                 'clarg': '--ms1quantcolpattern',
                                 'default': None,
                                 'help': 'Unique text pattern to identify '
                                 'precursor quant column in protein table.'},
    'quantacccolpattern': {'driverattr': 'quantcolpattern',
                           'clarg': '--qaccpattern', 'type': str,
                           'help': 'Unique text pattern to identify '
                           'accession column in table containing quant info.'},
    'qvalityout': {'driverattr': 'qvalityout', 'dest': 'qvalityout',
                   'help': 'Qvality output file to fetch q-values and PEP '
                   'from', 'type': 'file', 'clarg': ['-q', '--qvality']},
    'proteincol': {'driverattr': 'proteincol', 'clarg': '--protcol',
                   'type': int, 'required': False, 'help': 'Column number in '
                   'PSM table in which protein or gene accessions are. '
                   'stored. First column number is 1. Use in case of not '
                   'using standard master protein column.'},
    'fdrcolpattern': {'driverattr': 'fdrcolpattern', 'dest': 'fdrcolpattern',
                      'clarg': '--fdrcolpattern', 'type': str,
                      'required': False, 'default': None,
                      'help': 'Unique text pattern to identify '
                      'protein FDR column in protein table.'},
}

mslookup_options = {
    'mapfn': {'driverattr': 'mapfn', 'dest': 'mapfn',
              'type': 'file', 'clarg': '--map',
              'required': False, 'help': 'File that contains '
              'a map obtained from ENSEMBL BioMart which '
              'should contain mappings from protein accession '
              'to Gene ENSG and Symbol.'},
    'decoy': {'driverattr': 'decoy', 'dest': 'decoy', 'clarg': '--decoy',
              'action': 'store_const', 'const': True,
              'default': False, 'help': 'Specifies lookup is '
              'for decoy PSMs, use with --map in case there '
              'are no decoy symbols in the FASTA used to '
              'search.', 'required': False},
    'fasta': {'driverattr': 'fasta', 'dest': 'fasta',
              'type': 'file', 'help': 'FASTA sequence database'
              ' to use when extracting gene names to the PSM '
              'table from proteins', 'required': False,
              'default': False, 'clarg': '--fasta'},
    'spectrafns': {'driverattr': 'spectrafns', 'dest': 'spectra',
                   'type': 'file', 'help': 'Spectra files in mzML '
                   'format. Multiple files can be specified, if '
                   'order is important, e.g. when matching them '
                   'with quant data, the order will be their input '
                   'order at the command line.', 'clarg': '--spectra'},
    'quantfiletype': {'driverattr': 'quantfiletype', 'dest': 'quanttype',
                      'clarg': '--quanttype', 'type': 'pick', 'help':
                      'Filetype of '
                      'precursor quants to store. One of kronik or openms.',
                      'picks': ['kronik', 'openms']},
    'rttol': {'driverattr': 'rt_tol', 'dest': 'rttol', 'clarg': '--rttol',
              'type': float, 'help': 'Specifies tolerance in seconds for '
              'retention time when mapping MS1 feature quant info to '
              'identifications in the PSM table.'},
    'mztol': {'driverattr': 'mz_tol', 'dest': 'mztol', 'clarg': '--mztol',
              'type': float, 'help': 'Specifies tolerance in mass-to-charge '
              'when mapping MS1 feature quant info to identifications in '
              'the PSM table.'},
    'mztoltype': {'driverattr': 'mz_toltype', 'dest': 'mztoltype',
                  'type': 'pick', 'picks': ['ppm', 'Da'],
                  'clarg': '--mztoltype',
                  'help': 'Type of tolerance in mass-to-charge when mapping '
                  'MS1 feature quant info to identifications in the PSM table.'
                  ' One of ppm, Da.'},
    'psmnrcolpatter': {'driverattr': 'psmnrcolpattern',
                       'dest': 'psmnrcolpattern', 'clarg': '--psmnrcolpattern',
                       'type': str, 'default': None, 'required': False,
                       'help': 'Unique text pattern to identify '
                       'number-of-psms column in protein table.'},
    'probcolpattern': {'driverattr': 'probcolpattern',
                       'dest': 'probcolpattern', 'clarg': '--probcolpattern',
                       'type': str, 'required': False,
                       'default': None,
                       'help': 'Unique text pattern to identify '
                       'protein probability column in protein table.'},
    'pepcolpattern': {'driverattr': 'pepcolpattern', 'dest': 'pepcolpattern',
                      'clarg': '--pepcolpattern', 'type': str,
                      'required': False, 'default': None,
                      'help': 'Unique text pattern to identify '
                      'protein PEP column in protein table.'},
}

pycolator_options = {
    'maxlength': {'driverattr': 'maxlength', 'dest': 'maxlength',
                  'default': None, 'required': False,
                  'help': 'Maximum length of peptide to be included in '
                  'filtered data.', 'type': int, 'clarg': '--maxlen'},
    'minlength': {'driverattr': 'minlength', 'dest': 'minlength', 'default': 0,
                  'help': 'Minimum length of peptide to be included in '
                  'filtered data.', 'type': int, 'clarg': '--minlen',
                  'required': False},
    'score': {'driverattr': 'score', 'dest': 'score', 'default': 'svm',
              'help': 'Score to filter unique peptides on, e.g. svm',
              'type': 'pick', 'picks': ['svm', 'q', 'pep', 'p'], 'clarg': '-s',
              'required': False},
    'qoptions': {'driverattr': 'qoptions', 'dest': 'qoptions',
                 'required': False, 'clarg': '--qoptions', 'default': None,
                 'help': 'Extra options that may be passed to qvality. '
                 'Option form: --qoptions ***flag value ***flag ***flag value',
                 'nargs': '+', 'type': str},
    # FIXME qoptions is now --qoptions, not -o
}

mzidtsv_options = {
    'confcol': {'driverattr': 'confcol', 'clarg': '--confidence-col',
                'help': 'Confidence column number or name in the tsv file. '
                'First column has number 1.'},
    'conflvl': {'driverattr': 'conflvl', 'clarg': '--confidence-lvl',
                'help': 'Confidence cutoff level as a floating point number',
                'type': float},
    'conftype': {'driverattr': 'conftype', 'clarg': '--confidence-better',
                 'help': 'Confidence type to define if higher or lower score '
                 'is better. One of [higher, lower]', 'type': 'pick',
                 'picks': ['higher', 'lower']},
    'mzidfn': {'driverattr': 'mzidfn', 'clarg': '--mzid', 'help': 'mzIdentML',
               'type': 'file'},
    'bioset': {'driverattr': 'bioset', 'clarg': '--bioset', 'const': True,
               'action': 'store_const', 'default': False,
               'help': 'this enables automatic splitting on '
               'biological set names, for which a a column specifying '
               'these must exist.', 'required': False},
    'splitcol': {'driverattr': 'splitcol', 'clarg': '--splitcol', 'type': int,
                 'help': 'Column number to split a PSM table on. First column '
                 'is number 1'
                 },
}

pepprottable_options = {
    # a mock infile to make sure we don't show or need an infile, e.g. in
    # case of building something from lookup
    'mock_infn': {'driverattr': 'fn', 'clarg': '-i', 'required': False,
                  'help': argparse.SUPPRESS},
    'fdr': {'driverattr': 'fdr', 'clarg': '--fdr', 'action': 'store_const',
            'default': False, 'const': True, 'required': False,
            'help': 'Output FDR data to table'},
    'pep': {'driverattr': 'pep', 'clarg': '--pep', 'action': 'store_const',
            'default': False, 'const': True, 'required': False,
            'help': 'Output posterior error probabilities (PEP) to table.'},
    'quantfile': {'driverattr': 'quantfile', 'clarg': '--quantfile',
                  'type': 'file', 'help': 'File containing isobaric quant '
                  'data to add to table.'},
    'scorecolpattern': {'driverattr': 'scorecolpattern', 'type': str,
                        'clarg': '--scorecolpattern', 'help': 'Regular '
                        'expression pattern to find column where score '
                        'to filter on is written.'},

}


prottable_options = {k: v for k, v in pepprottable_options.items()}
prottable_options.update({
    'setname': {'driverattr': 'setname', 'clarg': '--setname', 'type': str,
                'help': 'Name of biological set to use when adding protein '
                'info to the table'},
    'probability': {'driverattr': 'probability', 'clarg': '--probability',
                    'action': 'store_const', 'default': False, 'const': True,
                    'help': 'Output protein probability to table.',
                    'required': False},
    'psmfile': {'driverattr': 'psmfile', 'clarg': '--psmtable', 'type': 'file',
                'help': 'PSM table file containing precursor quant data to '
                'add to table.'},
    'pepfile': {'driverattr': 'pepfile', 'clarg': '--peptable', 'type': 'file',
                'help': 'Peptide table file'},
    'minlogscore': {'driverattr': 'minlogscore', 'clarg': '--logscore',
                    'action': 'store_const', 'default': False, 'const': True,
                    'required': False, 'help': 'Score, e.g. q-values will '
                    'be converted to -log10 values.'},
    'featuretype': {'driverattr': 'featuretype', 'dest': 'featuretype',
                    'help': 'Feature type to use for qvality. Can be one of '
                    '[probability, svm, qvalue].', 'clarg': '--feattype',
                    'type': 'pick', 'picks': ['probability', 'svm', 'qvalue']},
    't_fasta': {'driverattr': 't_fasta', 'clarg': '--targetfasta',
                'type': 'file', 'help': 'FASTA file with target proteins '
                'to determine best scoring proteins of target/decoy pairs '
                'for pickqvality.'},
    'd_fasta': {'driverattr': 'd_fasta', 'clarg': '--decoyfasta',
                'type': 'file', 'help': 'FASTA file with decoy proteins '
                'to determine best scoring proteins of target/decoy pairs '
                'for pickqvality.'},
    'picktype': {'driverattr': 'picktype', 'clarg': '--picktype',
                 'type': 'pick', 'picks': ['fasta', 'result'],
                 'help': 'Feature type to use for qvality. Can be one of '
                 '[fasta, result].'},
})


peptable_options = {k: v for k, v in pepprottable_options.items()}
peptable_options.update({
    'spectracol': {'driverattr': 'spectracol', 'dest': 'spectracol',
                   'type': int, 'clarg': '--spectracol', 'help':
                   'Specify this column number (first col. is 1) '
                   'containing PSM table spectrafiles (e.g. mzML) '
                   'if you want to track PSMs when creating peptide '
                   'tables', 'required': False},
})