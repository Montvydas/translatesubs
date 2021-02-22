from translatesubs.translator.googletrans import GoogleTrans
from translatesubs.translator.google_trans_new import GoogleTransNew


AVAILABLE_TRANSLATORS = {'googletrans': GoogleTrans,            # Does not keep newlines for pronunciation only
                         'google_trans_new': GoogleTransNew}    # Does not keep newlines
TRANSLATORS_PRINT = ', '.join(AVAILABLE_TRANSLATORS.keys())

ENDS_OF_SENTENCES = {
    'Usual': '.!?"\')',
    'Japanese': 'よねのさぞなか！。」…',
}

USE_DEFAULT_SEPS = 'default'
DEFAULT_SEPS = [' $$$ ', ' ### ', ' ∞ ', '@@@', " ™ ", ' @@@ ', '$$$', '€€€', '££', ' ## ', '@@', '$$']
DEFAULT_SEPS_PRINT = ', '.join((f'\"{sep}\"' for sep in DEFAULT_SEPS))

SEP_MAX_LENGTH = 7

SUB_FORMATS = ('srt', 'ass', 'ssa', 'mpl2', 'tmp', 'vtt', 'microdvd')
