import pysubs2
import subprocess
import logging
from typing import List, Iterator
import re


class Sub:
    def __init__(self, text: str, plaintext: str):
        self.origin_text = text
        self.plaintext = plaintext
        self.open_style = ''
        self.close_style = ''

    @staticmethod
    def to_plaintext(sub: pysubs2.SSAEvent):
        return sub.plaintext if sub.plaintext else sub.text

    @staticmethod
    def merge_multiline(multiline: str, char_limit: int):
        lines_length = len(multiline.replace('\n', ''))
        return multiline.replace('\n', ' ').replace(' ,', ',') if lines_length < char_limit else multiline

    def extract_line_styling(self):
        match = re.search(r'^{.+?}', self.origin_text, flags=re.DOTALL)
        if match:
            # logging.info(f'Opening: {match.group()}')
            self.open_style = match.group()

        match = re.search(r'.+({.+?})$', self.origin_text, flags=re.DOTALL)
        if match:
            # logging.info(f'Closing: {match.group(1)}')
            self.close_style = match.group(1)


class SubsManager:
    def __init__(self, filename: str, encoding: str='utf-8'):
        try:
            self.origin_subs = pysubs2.load(filename, encoding)
        except UnicodeDecodeError as e:
            exit(f'{e}\nTry changing encoding manually or allow "chardet" lib to determine it with: --encoding auto')
        self.subs = [Sub(sub.text, Sub.to_plaintext(sub)) for sub in self.origin_subs]

    def extract_line_styling(self):
        logging.info('Extracting individual line styling..')
        [sub.extract_line_styling() for sub in self.subs]

    def just_text(self) -> Iterator[str]:
        return (sub.plaintext for sub in self.subs)

    def update_subs(self, main_subs: List[str], secondary_subs: List[str], merge: bool, secondary_scale: int, char_limit: int):
        # original --> secondary
        # translated --> main
        for main, secondary, sub, origin_sub in zip(main_subs, secondary_subs, self.subs, self.origin_subs):
            main = Sub.merge_multiline(main, int(char_limit))
            secondary = Sub.merge_multiline(secondary, int(char_limit * 100 / secondary_scale))

            # 1. For now ignore the in-line based styling e.g. bold single word.
            # 2. Replace \n with \N as otherwise the same sub will be treated as separate event aka next sub.
            # NOTE: When writing into plaintext, \n is replaced with \N. But we also want to add custom styling..
            main = SubsManager._replace_with_capital_newline(main)
            secondary = SubsManager._replace_with_capital_newline(secondary)

            secondary = SubsManager._style_secondary(secondary, merge, secondary_scale)

            origin_sub.text = f'{sub.open_style}{main}{secondary}{sub.close_style}'

    def save_subs(self, subs_out: str):
        self.origin_subs.save(subs_out)

    @staticmethod
    def extract_from_video(video_in: str, subs_track: int, subs_out: str) -> bool:
        operation = ['ffmpeg', '-i', video_in, '-map', f'0:s:{subs_track}', subs_out]
        logging.debug(f'Extracting subs using {" ".join(operation)}')
        status = subprocess.run(operation)
        return status.returncode == 0

    @staticmethod
    def _style_secondary(text: str, merge: bool, scale: int) -> str:
        # Make text smaller than original and add 50% transparency - note it's HEX, not decimal.
        open_style = f'\\N{{\\fscx{scale}\\fscy{scale}\\alpha&H75&}}'
        close_style = '\\N{\\fscx100\\fscy100\\alpha&H00&}'
        return f'{open_style if merge else ""}{text}{close_style if merge else ""}'

    @staticmethod
    def _replace_with_capital_newline(multiline):
        return multiline.replace('\n', '\\N')
