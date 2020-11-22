import googletrans
import re
from typing import List
import logging
from .tools import flatten


class LanguageManager:
    CHUNK_CHAR_LIMIT = 5000

    def __init__(self, to_lang, separator):
        self.to_lang = to_lang
        self.prepared_to_translate = None
        self.grouped_chunks = None
        # Separator was chosen after noting that not all will be treated as non-text object and others
        # such as @@ will not translate all words e.g. "Connect  @@  Something else..." Will not translate correctly :/
        # While Connect  ##  Something else... will do.
        self.separator = separator

    @classmethod
    def create_instance(cls, to_lang: str, separator):
        language = LanguageManager.detect_language(to_lang)
        return cls(language, separator) if language else None

    @staticmethod
    def detect_language(to_lang: str):
        return next(({'abbreviation': abb, 'full': full} for abb, full in googletrans.LANGUAGES.items()
                     if to_lang == abb or to_lang == full), None)

    @staticmethod
    def get_supported() -> str:
        return ', '.join([f'{abb} - {full}' for abb, full in googletrans.LANGUAGES.items()])

    def translate_prepared_text(self) -> List[str]:
        translated = self.translate_text(self.prepared_to_translate)
        # Separate the subs by the used separator
        return flatten(partial.text.split(self.separator) for partial in translated)

    def prepare_for_translation_using_regex(self, text_lst: List[str]):
        """Prepares list of text to be translated by firstly joining the lines using a special separator
        and then taking a chunk of max allowed char and looking back for matching sentence end.

        E.g. the bottom list of text using char limit of 40 will be firstly joined into one string:
        ["This is an,", "example text!", "I am writing this now..."] ->
        "This is an, ## example text! ## I am writing this now..."

        Then it will be separated into two parts:
        "This is an, ## example text! ## I am wri(here 40 char)ting this now..." ->
        "This is an, ## example text!(here regex finds a match) ## I am writing this now..." ->
        ["This is an, ## example text!", "I am writing this now..."]

        Using regex overall is slower than using the other method, thus I used the other method :)"""
        splitter = re.compile(f'.+[.!?"\')]({self.separator}).+$')
        full_text = self.separator.join(text_lst)

        curr_index = 0
        self.prepared_to_translate = []
        total_length = len(full_text)

        while curr_index + LanguageManager.CHUNK_CHAR_LIMIT < total_length:
            curr_split = full_text[curr_index:curr_index + LanguageManager.CHUNK_CHAR_LIMIT]
            split_place = splitter.search(curr_split)
            self.prepared_to_translate.append(curr_split[:split_place.start(1)])
            curr_index += split_place.end(1)
        self.prepared_to_translate.append(full_text[curr_index:curr_index + LanguageManager.CHUNK_CHAR_LIMIT])

    def prepare_for_translation(self, text_lst: List[str]):
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

        This method works ~200 times faster than regex one :)"""
        self.grouped_chunks = []
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
                self.grouped_chunks.append(single_chunk)
                char_count = 0
                single_chunk = []

            char_count += sentence_length
            single_chunk.extend(sentence)

        if single_chunk:
            self.grouped_chunks.append(single_chunk)

        # Combine text chunks by some GOOD separator, such as ' ## ' that google translate would keep in place instead
        # of removing after translation. This will allow us to send all of the text to be sent for translation,
        # yet still track of the what lines belong to which timestamp
        self.prepared_to_translate = [self.separator.join(partial) for partial in self.grouped_chunks]
        logging.info(f'Prepared {len(self.prepared_to_translate)} chunks to be translated.')

    @staticmethod
    def _next_available_sentence(text_lst: List[str]) -> List[str]:
        """Generates a list of text, that comprise a full sentence."""
        sentence_endings = re.compile(r'[.!?"\')]$')
        collected = []

        for sentence in text_lst:
            collected.append(sentence)
            if sentence_endings.search(sentence):
                yield collected
                collected = []

        if collected:
            yield collected
        return

    def translate_text(self, text):
        # Google API provider should allow new access every 1h, but if more translations need to be done,
        # a number of different country providers are given
        provider_endings = ['com', 'co.kr', 'lt', 'ru', 'es', 'lv', 'ee', 'pl', 'de',
                            'sk', 'fr', 'co.uk', 'ae', 'ro', 'gy', 'pt', 'ms']
        provider_base = 'translate.google.'

        for ending in provider_endings:
            provider = f'{provider_base}{ending}'
            translator = googletrans.Translator(service_urls=[provider])
            try:
                return translator.translate(text, dest=self.to_lang['abbreviation'])
            except AttributeError:
                logging.info(f'Provider "{provider}" got blocked, trying another one...')
        exit('No more providers left to try, try updating the provider list.')
