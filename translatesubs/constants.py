from translatesubs.translator.googletrans import GoogleTrans
from translatesubs.translator.google_trans_new import GoogleTransNew


AVAILABLE_TRANSLATORS = {'googletrans': GoogleTrans,            # Does not keep newlines for pronunciation only
                         'google_trans_new': GoogleTransNew}    # Does not keep newlines
TRANSLATORS_PRINT = ', '.join(AVAILABLE_TRANSLATORS.keys())

ENDS_OF_SENTENCES = {
    'Usual': '.!?"\')',
    'Japanese': 'よねのさぞなか！。」…',
}