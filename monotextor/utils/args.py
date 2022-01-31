#  This file is part of Bitextor.
#
#  Bitextor is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Bitextor is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Bitextor.  If not, see <https://www.gnu.org/licenses/>.

import sys
import os
import pprint

from cerberus import Validator

def genericerror(msg):
    def f(field, value, error):
        error(field, msg)

    return f

def isfile(field, value, error):
    if isinstance(value, list):
        for element in value:
            if not os.path.isfile(os.path.expanduser(element)):
                error(field, f'{element} does not exist')
    elif not os.path.isfile(os.path.expanduser(value)):
        error(field, f'{value} does not exist')


def isstrlist(field, value, error):
    if not isinstance(value, list):
        error(field, f'{value} should be a list')
    for element in value:
        if not isinstance(element, str):
            error(field, f'{element} should be an string')


def isduration(field, value, error):
    if len(value) == 0:
        return False
    suffix_correct = value[-1].isalpha()
    prefix_correct = sum(not x.isnumeric() for x in value[:-1]) == 0
    if not suffix_correct or not prefix_correct:
        error(field, f"format is an integer followed by a single letter suffix")


def istrue(field, value, error):
    if value != True:
        error(field, f'{value} is not True')

def validate_args(config):
    schema = {
        # required parameters
        # output folders
        'dataDir': {'type': 'string', 'required': True},
        'permanentDir': {'type': 'string', 'required': True},
        'transientDir': {'type': 'string', 'required': True},
        'tempDir': {
            'type': 'string',
            'default_setter': lambda doc: doc["transientDir"] if "transientDir" in doc else ""
        },
        # profiling
        'profiling': {'type': 'boolean', 'default': False},
        # execute until X:
        'until': {
            'type': 'string',
            'allowed': [
                'crawl', 'preprocess', 'shard', 'split', 'translate', 'tokenise',
                'tokenise_src', 'tokenise_trg', 'docalign', 'segalign', 'filter'
            ]
        },
        'parallelWorkers': {
            'type': 'dict',
            'allowed': [
                'split', 'translate', 'tokenise', 'docalign', 'segalign', 'sents'
            ],
            'valuesrules': {'type': 'integer', 'min': 1}
        },
        # data definition
        # TODO: check that one of these is specified?
        'hosts': {'type': 'list', 'dependencies': 'crawler'},
        'hostsFile': {'type': 'string', 'dependencies': 'crawler', 'check_with': isfile},
        'warcs': {'type': 'list', 'check_with': isfile},
        'warcsFile': {'type': 'string', 'check_with': isfile},
        'preverticals': {'type': 'list', 'check_with': isfile},
        'preverticalsFile': {'type': 'string', 'check_with': isfile},
        # crawling
        'crawler': {'type': 'string', 'allowed': ["wget", "heritrix", "linguacrawl"]},
        'crawlTimeLimit': {
            'type': 'string', 'dependencies': 'crawler',
            'check_with': isduration
        },
        ## wget or linguacrawl:
        'crawlerUserAgent': {'type': 'string', 'dependencies': {'cralwer': ['wget', 'linguacrawl']}},
        'crawlWait': {'type': 'integer', 'dependencies': {'crawler': ['wget', 'linguacrawl']}},
        'crawlFileTypes': {'type': 'list', 'dependencies': {'crawler': ['wget', 'linguacrawl']}},
        ## only linguacrawl:
        'crawlTLD': {'type': 'list', 'check_with': isstrlist, 'dependencies': {'crawler': ['linguacrawl']}},
        'crawlSizeLimit': {'type': 'integer', 'dependencies': {'crawler': ['linguacrawl']}},
        'crawlCat': {'type': 'boolean', 'dependencies': {'crawler': 'linguacrawl'}},
        'crawlCatMaxSize': {'type': 'integer', 'dependencies': {'crawlCat': True}},
        'crawlMaxFolderTreeDepth': {'type': 'string', 'dependencies': {'crawler': 'linguacrawl'}},
        'crawlScoutSteps': {'type': 'string', 'dependencies': {'crawler': 'linguacrawl'}},
        'crawlBlackListURL': {'type': 'list', 'check_with': isstrlist, 'dependencies': {'crawler': 'linguacrawl'}},
        'crawlPrefixFilter': {'type': 'list', 'check_with': isstrlist, 'dependencies': {'crawler': 'linguacrawl'}},
        'crawlerNumThreads': {'type': 'integer', 'dependencies': {'crawler': ['linguacrawl']}},
        'crawlerConnectionTimeout': {'type': 'integer', 'dependencies': {'crawler': ['linguacrawl']}},
        'dumpCurrentCrawl': {'type': 'boolean', 'dependencies': {'crawler': ['linguacrawl']}},
        'resumePreviousCrawl': {'type': 'boolean', 'dependencies': {'crawler': ['linguacrawl']}},
        ## only heritrix
        'heritrixPath': {'type': 'string', 'dependencies': {'crawler': 'heritrix'}},
        'heritrixUrl': {'type': 'string', 'dependencies': {'crawler': 'heritrix'}},
        'heritrixUser': {'type': 'string', 'dependencies': {'crawler': 'heritrix'}},
        # preprocessing
        'preprocessor': {'type': 'string', 'allowed': ['warc2text', 'warc2preprocess'], 'default': 'warc2text'},
        'langs': {'type': 'list'},
        'shards': {'type': 'integer', 'min': 0, 'default': 8},
        'batches': {'type': 'integer', 'min': 1, 'default': 1024},
        'paragraphIdentification': {'type': 'boolean', 'default': False},
        # specific to warc2text:
        'writeHTML': {'type': 'boolean', 'dependencies': {'preprocessor': ['warc2text']}},
        # specific to warc2preprocess:
        'cleanHTML': {'type': 'boolean', 'dependencies': {'preprocessor': 'warc2preprocess'}},
        'ftfy': {'type': 'boolean', 'dependencies': {'preprocessor': 'warc2preprocess'}},
        'langID': {
            'type': 'string',
            'allowed': ['cld2', 'cld3'],
            'dependencies': {'preprocessor': 'warc2preprocess'}
        },
        'parser': {
            'type': 'string',
            'allowed': ['bs4', 'modest', 'simple', 'lxml'],
            'dependencies': {'preprocessor': 'warc2preprocess'}
        },
        'html5lib': {'type': 'boolean', 'dependencies': {'preprocessor': 'warc2preprocess'}},
        # pdfEXTRACT
        'PDFextract': {'type': 'boolean', 'dependencies': {'preprocessor': 'warc2preprocess'}},
        'PDFextract_configfile': {'type': 'string', 'dependencies': 'PDFextract'},
        'PDFextract_sentence_join_path': {'type': 'string', 'dependencies': 'PDFextract'},
        'PDFextract_kenlm_path': {'type': 'string', 'dependencies': 'PDFextract'},
        # boilerplate (prevertical2text, i.e. preverticals, and warc2preprocess)
        'boilerplateCleaning': {'type': 'boolean', 'default': False},
        # sentence splitting
        'pruneThreshold': {'type': 'integer', 'min': 0, 'default': 0},
        'pruneType': {'type': 'string', 'allowed': ['words', 'chars'], 'default': 'words'},
        # post processing
        'deferred': {'type': 'boolean', 'default': False},
        'monofixer': {'type': 'boolean', 'default': False},
        # mark near duplicates as duplicates
        'aggressiveDedup': {'type': 'boolean', 'dependencies': {'monofixer': True}},
        # cleaning
        'monocleaner': {'type': 'boolean', 'default': False},
        'monocleanerModels': {'type': 'dict', 'dependencies': {'monocleaner': True}},
        'monocleanerThreshold': {'type': 'float'},
        'skipSentenceSplitting': {'type': 'boolean', 'default': False},
    }

    provided_in_config = {} # contains info about the definition of rules in the configuration file

    # initialize with the default values if no value was provided
    for key in schema:
        provided_in_config[key] = True if key in config else False

        if key not in config and 'default' in schema[key]:
            config[key] = schema[key]['default']

    if 'crawler' in config:
        if config['crawler'] == 'heritrix':
            schema['heritrixPath']['required'] = True

    schema['langs']['required'] = True

    if config['boilerplateCleaning'] and config['preprocessor'] != 'warc2preprocess':
        if not provided_in_config['preverticals'] and not provided_in_config['preverticalsFile']:
            schema['boilerplateCleaning']['check_with'] = \
                genericerror("mandatory: preprocessor warc2preprocess or provide prevertical files")

    if config['preprocessor'] == 'warc2preprocess':
        if provided_in_config['preverticals'] or provided_in_config['preverticalsFile']:
            schema['preverticals']['dependencies'] = {'preprocessor': ['warc2text']}
            schema['preverticalsFile']['dependencies'] = {'preprocessor': ['warc2text']}


    if provided_in_config['deferred']:
        schema['until']['allowed'].append('deferred')
        schema['parallelWorkers']['allowed'].append('deferred')

    if provided_in_config['monofixer']:
        schema['until']['allowed'].append('monofixer')
        schema['parallelWorkers']['allowed'].append('monofixer')

    if config['monocleaner']:
        schema['until']['allowed'].append('monocleaner')
        schema['parallelWorkers']['allowed'].append('monocleaner')
        schema['monocleanerModels']['required'] = True

    if provided_in_config['until'] and (config['until'] == 'filter' or config['until'] == 'monofixer'):
        print(
            "WARNING: your target consists of temporary files. Make sure to use --notemp parameter to preserve your output",
            file=sys.stderr)

    v = Validator(schema)
    b = v.validate(config)

    if not b:
        print("Validation errors. Stopping.", file=sys.stderr)
        pprint.pprint(v.errors, indent=2, stream=sys.stderr, width=100)
        return b, {}

    config.update({k: os.path.expanduser(v) if isinstance(v, str) else v for k, v in config.items()})
    config.update({k: [os.path.expanduser(i) for i in v] if v is list else v for k, v in config.items()})

    return b, v.normalized(config)
