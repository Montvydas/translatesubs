import pysubs2
import subprocess
import logging
from typing import List, Generator, Iterable
import re


class Sub:
    def __init__(self, text: pysubs2.SSAEvent, plaintext: str):
        self.origin_text = text
        self.plaintext = plaintext
        self.open_style = None
        self.close_style = None

    @staticmethod
    def to_plaintext(sub: pysubs2.SSAEvent):
        return sub.plaintext if sub.plaintext else sub.text

    def merge_long_lines(self, char_limit: int):
        multiline = self.plaintext
        self.plaintext = multiline.replace('\n', ' ').replace(' ,', ',') if len(multiline) < char_limit else multiline

    def extract_line_styling(self):
        # TODO Add the line styling back to the text after translation
        # TODO check why plaintext isn't considered str, add casting if really needed
        match = re.search(r'^{.+?}', self.origin_text, flags=re.DOTALL)
        if match:
            logging.info(f'Opening: {match.group()}')
            self.open_style = match.group()

        match = re.search(r'.+({.+?})$', self.origin_text, flags=re.DOTALL)
        if match:
            logging.info(f'Closing: {match.group(1)}')
            self.close_style = match.group(1)


class SubsManager:
    def __init__(self, filename: str):
        self.origin_subs = pysubs2.load(filename)
        self.subs = [Sub(sub.text, Sub.to_plaintext(sub)) for sub in self.origin_subs]

    def merge_long_lines(self, char_limit: int):
        logging.info(f'Merging long lines with char limit of "{char_limit}"')
        [sub.merge_long_lines(char_limit) for sub in self.subs]

    def extract_line_styling(self):
        logging.info('Extracting line styling')
        [sub.extract_line_styling() for sub in self.subs]

    # TODO Add -> Generator[str] and make sure it doesn't break :))
    def just_text(self):
        return (sub.plaintext for sub in self.subs)

    def update_subs(self, updated: List[str], merge: bool):
        for origin_sub, sub in zip(self.origin_subs, self.subs, updated):
            # origin_sub.text =
            pass

        for sub, trans in zip(self.origin_subs, updated):
            # For now ignore the line based styling.
            # Also replace \n with \N as otherwise only the first subtitle line will be shown as others will be treated as
            # separate event Could just write into plaintext, but if combined flag is used, then still have to perform these
            original = SubsManager.replace_with_capital_newline(SubsManager.to_plaintext(sub))
            translated = SubsManager.replace_with_capital_newline(trans)

            original_styled = SubsManager.style_down(original) if merge else ''
            sub.text = f'{translated}{original_styled}'

    def save_subs(self, subs_out: str):
        self.origin_subs.save(subs_out)

    @staticmethod
    def extract_from_video(video_in: str, subs_track: int, subs_out: str) -> bool:
        operation = ['ffmpeg', '-i', video_in, '-map', f'0:s:{subs_track}', subs_out]
        logging.debug(f'Extracting subs using {" ".join(operation)}')
        status = subprocess.run(operation)
        return status.returncode == 0

    @staticmethod
    def style_down(text: str) -> str:
        # Make text smaller than original as it's less important, plus add transparency
        style = '\\N{\\fscx70\\fscy70\\alpha&H80&}'
        return f'{style}{text}'

    @staticmethod
    def replace_with_capital_newline(multiline):
        return multiline.replace('\n', '\\N')


"""
    def clear_line_formatting(self):
        # logic is that it get's rid of line based styling if has one. Noticed, that sometimes plaintext is None, then
        # simply use the text. It would be better if anything within brackets {...} would be preserved in the future..
        self.subs = (sub.plaintext for sub in self.subs)

        for sub in self.origin_subs:
            sub.text = Sub.to_plaintext(sub)
        # return (SubsManager.to_plaintext(sub) for sub in self.subs)"""