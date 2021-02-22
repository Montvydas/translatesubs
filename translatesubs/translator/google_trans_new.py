import google_trans_new
from typing import List, Iterator
import logging
import re

from translatesubs.translator.itranslator import ITranslator
from translatesubs.translator.language import Language
from translatesubs.translator.translated import Translated


class GoogleTransNew(ITranslator):
    """
    Google_trans_new suffers from a bug in the API: within the pronunciation, new line characters are removed and
    thus if it is important to preserve perfect styling, you are better off using another translation service.
    """

    def get_char_limit(self) -> int:
        return 5000

    def translate(self, text: List[str], to_lang: str) -> Iterator[Translated]:
        for original in text:
            pronounced = self._do_translate(original, to_lang, pronounce=True)
            translated = self._do_translate(original, to_lang).strip()
            yield Translated(original=original,
                             translated=translated,
                             pronounce_original=GoogleTransNew._pronounce_origin(pronounced, original),
                             pronounce_translated=GoogleTransNew._pronounce_translated(pronounced, translated))

    def detect_language(self, to_lang: str) -> Language:
        return next((Language(full, abb) for abb, full in google_trans_new.LANGUAGES.items()
                     if to_lang == abb or to_lang == full), None)

    def get_supported(self) -> str:
        return ', '.join([f'{abb} - {full}' for abb, full in google_trans_new.LANGUAGES.items()])

    @staticmethod
    def _do_translate(text: str, to_lang: str, pronounce=False):
        """
        Call google translate API to translate given text

        :param **kwargs:
        :param text: The source text(s) to be translated. Batch translation is supported via sequence input.
        :type text: UTF-8 :class:`str`; :class:`unicode`; string sequence (list, tuple, iterator, generator)

        :return: translated text in the same form it was provided
        """
        # Google API provider should allow new access every 1h, but if more translations need to be done,
        # a number of different country providers are given
        # E.g. from here https://sites.google.com/site/tech4teachlearn/googleapps/google-country-codes
        # But have to make sure the site actually loads first :)
        ending_formula = re.compile(r'translate\..*?\.(.+)$')  # for for com, co.uk, lt or others
        provider_endings = (ending_formula.search(url).group(1) for url in google_trans_new.DEFAULT_SERVICE_URLS)

        for ending in provider_endings:
            translator = google_trans_new.google_translator(url_suffix=ending)
            try:
                return translator.translate(text, lang_tgt=to_lang, pronounce=pronounce)
            except AttributeError:
                logging.info(f'Provider "translate.google.{ending}" got blocked, trying another one...')
        exit('No more providers left to try, try updating the provider list or wait 1h until you get unblocked.')

    @staticmethod
    def _pronounce_origin(translated: List[str], default: str) -> str:
        return translated[1] if translated[1] else default

    @staticmethod
    def _pronounce_translated(translated: List[str], default: str) -> str:
        return translated[2] if translated[2] else default
