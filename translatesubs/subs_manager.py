import pysubs2
import subprocess
import logging


class SubsManager:
    def __init__(self, filename):
        self.subs = pysubs2.load(filename)

    def update_subs(self, translated_subs, combine):
        for sub, trans in zip(self.subs, translated_subs):
            # For now ignore the line based styling.
            # Also replace \n with \N as otherwise only the first subtitle line will be shown as others will be treated as
            # separate event Could just write into plaintext, but if combined flag is used, then still have to perform these
            original = SubsManager.replace_with_capital_newline(SubsManager.to_plaintext(sub))
            translated = SubsManager.replace_with_capital_newline(trans)

            original_styled = SubsManager.style_down(original) if combine else ''
            sub.text = f'{translated}{original_styled}'

    def save_subs(self, subs_out):
        return self.subs.save(subs_out)

    def just_text(self):
        return (sub.text for sub in self.subs)

    def clean_line_formatting(self):
        # logic is that it get's rid of line based styling if has one. Noticed, that sometimes plaintext is None, then
        # simply use the text. It would be better if anything within brackets {...} would be preserved in the future..
        for sub in self.subs:
            sub.text = SubsManager.to_plaintext(sub)
        # return (SubsManager.to_plaintext(sub) for sub in self.subs)

    def merge_long_lines(self, char_limit):
        for sub in self.subs:
            multiline = sub.text
            sub.text = multiline.replace('\n', ' ').replace(' ,', ',') if len(multiline) < char_limit else multiline
        # return (line.replace('\n', ' ') if len(line) < char_limit else line for sub in self.subs)

    # def extract_from_file(self, video_filename):
    @staticmethod
    def extract_from_video(video_in, subs_track, subs_out):
        operation = ['ffmpeg', '-i', video_in, '-map', f'0:s:{subs_track}', subs_out]
        logging.debug(f'Extracting subs using {" ".join(operation)}')
        status = subprocess.run(operation)
        return status.returncode == 0

    @staticmethod
    def to_plaintext(sub):
        return sub.plaintext if sub.plaintext else sub.text

    @staticmethod
    def style_down(text: str) -> str:
        # Make text smaller than original as it's less important, plus add transparency
        style = '\\N{\\fscx70\\fscy70\\alpha&H80&}'
        return f'{style}{text}'

    @staticmethod
    def replace_with_capital_newline(multiline):
        return multiline.replace('\n', '\\N')