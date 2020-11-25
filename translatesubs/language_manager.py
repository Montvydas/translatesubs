from __future__ import annotations

import googletrans
from googletrans.models import Translated
import re
from typing import List, Dict, Generator
import logging


class LanguageManager:
    CHUNK_CHAR_LIMIT = 5000
    ENDS_OF_SENTENCES = {
        'Usual': '.!?"\')',
        'Japanese': 'よねのさぞなか！。」…',
    }

    def __init__(self, to_lang: Dict[str, str], separator: str, ignore_line_ends: bool):
        self.to_lang = to_lang
        # Separator was chosen after noting that not all will be treated as non-text object and others
        # such as @@ will not translate all words e.g. "Connect  @@  Something else..." Will not translate correctly :/
        # While Connect  ##  Something else... will do.
        self.separator = separator
        self.ignore_line_ends = ignore_line_ends

    @classmethod
    def create_instance(cls, to_lang: str, separator: str, ignore_line_ends: bool) -> LanguageManager:
        language = LanguageManager._detect_language(to_lang)
        return cls(language, separator, ignore_line_ends) if language else None

    @staticmethod
    def _detect_language(to_lang: str) -> Dict[str, str]:
        return next(({'abbreviation': abb, 'full': full} for abb, full in googletrans.LANGUAGES.items()
                     if to_lang == abb or to_lang == full), None)

    @staticmethod
    def get_supported() -> str:
        return ', '.join([f'{abb} - {full}' for abb, full in googletrans.LANGUAGES.items()])

    def translate_text(self, lst_text: Generator[str], pronounce_origin: bool, pronounce_trans: bool) -> Dict[str, List[str]]:
        chunks_to_translate = self._prepare_for_translation_using_regex(lst_text)

        exit(chunks_to_translate)
        translated_chunks = self.google_translate(chunks_to_translate)
        # Noticed that when separator contains spaces e.g. ' ∞ ', translated to certain languages separator gets
        # modified e.g. English to Japanese "Hello ∞ everyone" -> "みなさん、こんにちは∞" OR "Minasan, kon'nichiwa ∞"
        sep = self.separator.strip()
        result = {"origin": [], "translated": []}

        for chunk in translated_chunks:
            result['origin'].extend(LanguageManager._extract_translation(
                LanguageManager._origin_pronunciation(chunk) if pronounce_origin else chunk.origin, sep))

            result['translated'].extend(
                LanguageManager._extract_translation(chunk.pronunciation if pronounce_trans else chunk.text, sep))

        # TODO write some better message about this
        if len(result['origin']) != len(result['translated']):
            exit('It seems like there was some problem with translating, '
                 'repeat using a different separator - check help menu')
        return result
        # return [sub_text.strip() for chunk in translated_chunks for sub_text in chunk.split(sep)]
        # return flatten(chunk.split(sep) for chunk in translated_chunks)

    @staticmethod
    def _extract_translation(chunk, separator):
        return [sub.strip() for sub in chunk.split(separator)]

    def _prepare_for_translation(self, text_lst: Generator[str]) -> List[str]:
        """Prepares list of text to be translated by going through every text element in the list and
        grouping them into allowed char 5000 limits, which is placed by google translate service.
        _next_available_sentence function generates a list of text, that comprise a full sentence. Then
        sentences are grouped into larger list, which ensures that if line separator is added, the total
        character count doesn't take up more than the allowed limit.

        E.g. the bottom list of text using char limit of 40 will be require going sentence by sentence
        (using _next_available_sentence) and checking if new sentence fits within char limits:
        ["This is an,", "example text!", "I am writing this now..."] ->
        new_sentence = ["This is an,", "example text!"] ->
        24 chars in new_sentence, 0 + 24 = 24 chars in total inside this part, thus save it in:
        single_chunk.extend(new_sentence)

        Get a new sentence and check if that still fits:
        new_sentence = ["I am writing this now..."] ->
        24 chars in new_sentence, 24 + 24 = 48 chars in total - TOO MUCH! Save previous part and store this in new:
        chunks.append(new_sentence)
        single_chunk = []
        single_chunk.extend(new_sentence)

        This will finally generate such a nested list:
        [["This is an,", "example text!"], ["I am writing this now..."]]

        This is overall slower than the regex solution for large chunk size"""
        grouped_chunks = []
        single_chunk = []
        char_count = 0
        separator_length = len(self.separator)
        for sentence in self._next_available_sentence(text_lst):
            sentence_length = sum([len(part) for part in sentence]) + len(sentence) * separator_length
            logging.debug(f'sentence: {sentence[0][:10]}...{sentence[-1][-10:]} with {len(sentence)} texts, '
                          f'{char_count} (char count) + {sentence_length} (sentence length) '
                          f'= {char_count + sentence_length} (total)')
            if char_count + sentence_length > LanguageManager.CHUNK_CHAR_LIMIT:
                logging.debug(f'Reached the {LanguageManager.CHUNK_CHAR_LIMIT} char limit!')
                grouped_chunks.append(single_chunk)
                char_count = 0
                single_chunk = []

            char_count += sentence_length
            single_chunk.extend(sentence)

        if single_chunk:
            grouped_chunks.append(single_chunk)

        # Combine text chunks by some GOOD separator, such as ' ## ' that google translate would keep in place instead
        # of removing after translation. This will allow us to send all of the text to be sent for translation,
        # yet still track of the what lines belong to which timestamp
        chunks_to_translate = [self.separator.join(partial) for partial in grouped_chunks]
        logging.debug(f'Prepared {len(chunks_to_translate)} chunks to be translated.')

        return chunks_to_translate

    @staticmethod
    def _next_available_sentence(text_lst: Generator[str]) -> Generator[str]:
        """Generates a list of text, that comprise a full sentence."""
        all_possible_endings = ''.join(LanguageManager.ENDS_OF_SENTENCES.values())
        sentence_endings = re.compile(f'[{all_possible_endings}]$', flags=re.DOTALL)
        collected = []

        for sentence in text_lst:
            collected.append(sentence)
            if sentence_endings.search(sentence):
                yield collected
                collected = []

        if collected:
            yield collected
        return

    def _prepare_for_translation_using_regex(self, text_lst: Generator[str]) -> List[str]:
        """Prepares list of text to be translated by firstly joining the lines using a special separator
        and then taking a chunk of max allowed char and looking back for matching sentence end.

        E.g. the bottom list of text using char limit of 40 will be firstly joined into one string:
        ["This is an,", "example text!", "I am writing this now..."] ->
        "This is an, ## example text! ## I am writing this now..."

        Then it will be separated into parts:
        "This is an, ## example text! ## I am wri" AND "ting this now..." -> (take first 40 chars)
        "This is an, ## example text!" AND " ## I am writing this now..." -> (use regex to find last full sentence)
        ["This is an, ## example text!", "I am writing this now..."] -> (repeat for the second part until done)
        """
        # Slower method
        # .+[.!?"\')]( ## ).+$
        # Quicker method
        # TODO check if need to use * or + at the end: *$ vs +$, original was +$
        # [.!?"\')]( ## )(?:.(?![.!?"\')] ## ))*$
        # OR when no valid endings found e.g. some strange language or subs don't have sentence endings incorporated..
        # ( ## )(?:.(?! ## ))*$
        full_text = self.separator.join(text_lst)
        valid_endings = self._determine_valid_endings(full_text)

        # Note that when no valid endings found, simply separate by the closest subtitle instead
        splitter = re.compile(f'{valid_endings}({self.separator})'
                              f'(?:.(?!{valid_endings}{self.separator}))*$', flags=re.DOTALL)
        curr_index = 0
        chunks_to_translate = []
        total_length = len(full_text)

        while curr_index + LanguageManager.CHUNK_CHAR_LIMIT < total_length:
            curr_split = full_text[curr_index:curr_index + LanguageManager.CHUNK_CHAR_LIMIT]
            split_place = splitter.search(curr_split)
            chunks_to_translate.append(curr_split[:split_place.start(1)])
            curr_index += split_place.end(1)
        chunks_to_translate.append(full_text[curr_index:curr_index + LanguageManager.CHUNK_CHAR_LIMIT])
        logging.debug(f'Prepared {len(chunks_to_translate)} chunks to be translated.')

        return chunks_to_translate

    def _determine_valid_endings(self, full_text):
        if self.ignore_line_ends:
            return ''
        for name, endings in LanguageManager.ENDS_OF_SENTENCES.items():
            re_endings = f'[{endings}]'
            if re.search(re_endings, full_text, flags=re.DOTALL):
                logging.info(f'Using "{name}" endings "{endings}"')
                return re_endings
        return ''

    def google_translate(self, text):
        """
        Call google translate API to translate given text

        :param text: The source text(s) to be translated. Batch translation is supported via sequence input.
        :type text: UTF-8 :class:`str`; :class:`unicode`; string sequence (list, tuple, iterator, generator)

        :return: translated text in the same form it was provided
        """
        # Google API provider should allow new access every 1h, but if more translations need to be done,
        # a number of different country providers are given
        # E.g. from here https://sites.google.com/site/tech4teachlearn/googleapps/google-country-codes
        # But have to make sure the site actually loads first :)
        provider_endings = ('com', 'co.kr', 'lt', 'ru', 'es', 'lv', 'ee', 'pl', 'de', 'us'
                                                                                      'sk', 'fr', 'co.uk', 'ae', 'ro',
                            'gy', 'pt', 'ms', 'ca', 'be'
                                                    'co.jp', 'it', 'nl', 'gr', 'in', 'dk', 'ch', 'ie', 'at', 'cl')
        provider_base = 'translate.google.'

        for ending in provider_endings:
            provider = f'{provider_base}{ending}'
            translator = googletrans.Translator(service_urls=[provider])
            try:
                return translator.translate(text, dest=self.to_lang['abbreviation'])
            except AttributeError:
                logging.info(f'Provider "{provider}" got blocked, trying another one...')
        exit('No more providers left to try, try updating the provider list.')

    @staticmethod
    def _origin_pronunciation(translated: Translated) -> str:
        return translated.extra_data['translation'][-1][-1]
