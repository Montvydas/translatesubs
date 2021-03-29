from __future__ import annotations

import re
import logging
from typing import List, Tuple, Iterator
from translatesubs.translator.itranslator import ITranslator
from translatesubs.translator.language import Language
from translatesubs.constants import ENDS_OF_SENTENCES, DEFAULT_SEPS, SEP_MAX_LENGTH


class LanguageManager:

    def __init__(self, to_lang: Language, ignore_line_ends: bool, translator: ITranslator):
        self.to_lang = to_lang
        # Separator was chosen after noting that not all will be treated as non-text object and others
        # such as @@ will not translate all words e.g. "Connect  @@  Something else..." Will not translate correctly :/
        # While Connect  ##  Something else... will do.
        self.separator = DEFAULT_SEPS[0]
        self.ignore_line_ends = ignore_line_ends
        self.translator = translator
        self.prepared = None

    @classmethod
    def create_instance(cls, to_lang: str, ignore_line_ends: bool, translator: ITranslator) -> LanguageManager:
        language = translator.detect_language(to_lang)
        return cls(language, ignore_line_ends, translator) if language else None

    def set_separator(self, new_separator: str):
        self.separator = new_separator

    def prep_for_trans(self, text: Iterator[str]):
        self.prepared = self._prepare_for_translation(text)

    def translate_text(self, pronounce_origin: bool, pronounce_trans: bool) -> Tuple[List[str], List[str]]:
        if not self.prepared:
            raise Exception('Text needs to be prepared for translation first.')

        properly_separated_chunks = self.combine_with_separator()
        translated = self.translator.translate(properly_separated_chunks, self.to_lang.abbreviation)

        # Noticed that when separator contains spaces e.g. ' ∞ ', translated to certain languages separator gets
        # modified e.g. English to Japanese "Hello ∞ everyone" -> "みなさん、こんにちは∞" OR "Minasan, kon'nichiwa ∞"
        sep = self.separator.strip()

        extracted_original = []
        extracted_translated = []

        for trans in translated:
            extracted_original.extend(LanguageManager._extract_translation(
                trans.pronounce_original if pronounce_origin else trans.original, sep))

            extracted_translated.extend(LanguageManager._extract_translation(
                trans.pronounce_translated if pronounce_trans else trans.translated, sep))

        return extracted_original, extracted_translated

    @staticmethod
    def valid_translation(original, translated):
        valid = original and translated and len(original) == len(translated)
        if not valid:
            print(f'original length={len(original)}, translated length={len(translated)}')
        return valid

    @staticmethod
    def _extract_translation(chunk, separator):
        return [sub.strip() for sub in chunk.split(separator)]

    def _prepare_for_translation(self, text_lst: Iterator[str]) -> List[List[str]]:
        """Prepares list of text to be translated by going through every text element in the list and
        grouping them into allowed char 5000 limits, which is placed by google translate service.
        _next_available_sentence function generates a list of text, that comprise a full sentence. Then
        sentences are grouped into larger list, which ensures that if SEP_MAX_LENGTH line separator is added, the total
        character count doesn't take up more than the allowed 5000 limit.

        If this is not done, too many requests will be generated and Google will block the translate service. It should
        also improve the accuracy, since Translator has the access to the whole sentence rather than just a part of it.

        Example:
        The bottom list of text using char limit of 40 will be require going sentence by sentence
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
        separator_length = SEP_MAX_LENGTH
        for sentence in self._next_available_sentence(text_lst):
            sentence_length = sum([len(part) for part in sentence]) + len(sentence) * separator_length
            logging.debug(f'sentence: {sentence[0][:10]}...{sentence[-1][-10:]} with {len(sentence)} texts, '
                          f'{char_count} (char count) + {sentence_length} (sentence length) '
                          f'= {char_count + sentence_length} (total)')
            if char_count + sentence_length > self.translator.get_char_limit():
                logging.debug(f'Reached the {self.translator.get_char_limit} char limit!')
                grouped_chunks.append(single_chunk)
                char_count = 0
                single_chunk = []

            char_count += sentence_length
            single_chunk.extend(sentence)

        if single_chunk:
            grouped_chunks.append(single_chunk)

        return grouped_chunks

    def combine_with_separator(self):
        # Combine text chunks by some GOOD separator, such as ' ## ' that google translate would keep in place instead
        # of removing after translation. This will allow us to send all of the text to be sent for translation,
        # yet still track of the what lines belong to which timestamp
        chunks_to_translate = [self.separator.join(partial) for partial in self.prepared]
        logging.debug(f'Prepared {len(chunks_to_translate)} chunks to be translated.')
        return chunks_to_translate

    @staticmethod
    def _next_available_sentence(text_lst: Iterator[str]) -> Iterator[str]:
        """Generates a list of text, that comprise a full sentence."""
        all_possible_endings = ''.join(ENDS_OF_SENTENCES.values())
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

    def _prepare_for_translation_using_regex(self, text_lst: Iterator[str]) -> List[str]:
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

        # special regex characters need to be escaped. For now $ works very well but in regex it also matches the end
        # of sentence, thus escape it :)
        processed_separator = self.separator.replace('$', '\\$')
        # Note that when no valid endings found, simply separate by the closest subtitle instead
        splitter = re.compile(f'{valid_endings}({processed_separator})'
                              f'(?:.(?!{valid_endings}{processed_separator}))*$', flags=re.DOTALL)

        curr_index = 0
        chunks_to_translate = []
        total_length = len(full_text)

        while curr_index + self.translator.get_char_limit() < total_length:
            curr_split = full_text[curr_index:curr_index + self.translator.get_char_limit()]
            split_place = splitter.search(curr_split)
            if not split_place:
                exit('It seems like some translations got corrupted. Try a different separator using --separator '
                     'argument. Check --help menu for more information.')
            chunks_to_translate.append(curr_split[:split_place.start(1)])
            curr_index += split_place.end(1)
        chunks_to_translate.append(full_text[curr_index:curr_index + self.translator.get_char_limit()])
        logging.debug(f'Prepared {len(chunks_to_translate)} chunks to be translated.')

        return chunks_to_translate

    def _determine_valid_endings(self, full_text):
        if self.ignore_line_ends:
            return ''
        for name, endings in ENDS_OF_SENTENCES.items():
            re_endings = f'[{endings}]'
            if re.search(re_endings, full_text, flags=re.DOTALL):
                logging.info(f'Using "{name}" endings "{endings}"')
                return re_endings
        logging.info(f'No valid line ends found, thus ignoring them.')
        return ''
