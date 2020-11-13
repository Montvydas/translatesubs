#!/usr/bin/env python

import pysubs2
import argparse
import json
import configparser
from googletrans import Translator
import subprocess


def translate_sub_file(file_name, to_lang, combine):
    subs = pysubs2.load(file_name)
    translated_subs = translate_subs(subs, to_lang)

    original_len = len(subs)
    translated_len = len(translated_subs)

    if original_len != translated_len:
        translated_subs.extend(['error'] * (original_len - translated_len))
        for sub, trans in zip(subs, translated_subs):
            print(to_plaintext(sub))
            print(trans)
        print('total subs:', original_len)
        print('total translated:', translated_len)
        print('Something went wrong, potentially need to use a different separator, such as " @@ ", which is worse.. But might work better in this occassion. Still try playing the video, maybe it is something wrong in the end...')

    # Update the original subs with the translation and also combine them if needed
    return update_subs(subs, translated_subs, combine)


def translate_subs(subs, to_lang):
    # Separator was chosen after noting that not all will be treated as non-text object and others
    # such as @@ will not translate all words e.g. Connect  @@  Something else... Will not translate Connect :/
    # While Connect  ##  Something else... will do.
    separator = ' ## '
    # logic is that it get's rid of line based styling if has one. Noticed, that sometimes plaintext is None, then
    # simply use the text. It would be better if anything within brackets {...} would be preserved, but it's ok for now.
    plaintext_subs = [to_plaintext(sub) for sub in subs]
    # Combine by some GOOD separator, such as ' ## ' that google translate would keep in place instead of removing
    # after translation. This will allow us to send all of the text to be sent for translation, yet still track of the
    # what lines belong to which timestamp
    combined_subs_to_translate = separator.join(plaintext_subs)
    # Send ALL of the text file for translation. It might be too large, then gotta crop it somehow,
    # but didn't experience this problem yet so for now good enough!
    combined_subs_translated = translate_text(
        combined_subs_to_translate, to_lang)
    # Separate the subs by the used separator
    return combined_subs_translated.split(separator)


def update_subs(original_subs, translated_subs, combine):
    for i, sub in enumerate(original_subs):
        # For now ignore the line based styling.
        # Also replace \n with \N as otherwise only the first subtitle line will be shown as others will be treated as
        # separate event Could just write into plaintext, but if combined flag is used, then still have to perform these
        original = replace_with_capital_newline(to_plaintext(sub))
        translated = replace_with_capital_newline(translated_subs[i])

        original_styled = style_down(original) if combine else ''
        sub.text = f'{translated}{original_styled}'
    return original_subs


def style_down(text):
    # Make text smaller than original as it's less important, plus add transparency
    style = '\\N{\\fscx70\\fscy70\\alpha&H80&}'
    return f'{style}{text}'


def translate_text(text, to_lang):
    # Google API provider should allow new access every 1h, but if more translations need to be done,
    # a number of different country providers are given
    provider_endings = ['com', 'co.kr', 'lt', 'ru', 'es', 'lv', 'ee', 'pl', 'de',
                        'sk', 'fr', 'co.uk', 'ae', 'ro', 'gy', 'pt', 'ms']
    provider_base = 'translate.google.'

    for ending in provider_endings:
        provider = f'{provider_base}{ending}'
        translator = Translator(service_urls=[provider])
        try:
            return translator.translate(text, dest=to_lang).text
        except AttributeError:
            print(f'Provider "{provider}" got blocked :/')
    print('No more providers left to try, try updating the provider list.')
    exit()


def replace_with_capital_newline(multiline):
    return multiline.replace('\n', '\\N')


def to_plaintext(sub):
    return sub.plaintext if sub.plaintext else sub.text


def extract_subtitles(input, subs_track, output):
    operation = ['ffmpeg', '-i', input, '-map', f'0:s:{subs_track}', output]
    status = subprocess.run(operation)
    if status.returncode != 0:
        print('Could not extract the subtitle!')
        exit()


def main():
    parser = argparse.ArgumentParser(
        description='python translatesubs.py input.srt output.srt es')
    parser.add_argument('input', type=str,
                        help='input subtitle file by default. If flag --video_file set, then this is video file name.')
    parser.add_argument('output', type=str, help='output subtitles file')
    parser.add_argument('--to_lang', default='es', type=str,
                        help='language to which translate to')
    parser.add_argument('--combine', action='store_true',
                        help='Set this if you want to combine two languages at once.')

    parser.add_argument('--video_file', action='store_true',
                        help='Set this if video file is used instead of subtitle file.')
    parser.add_argument('--subs_track', default=0, type=int,
                        help='Subtitle tract, if video has multiple tracks. Default is 0.')
    args = parser.parse_args()

    subs_file = args.input

    # If we process the video rather than subtitle file, then simply extract the subtitle and place it into output
    if args.video_file:
        extract_subtitles(args.input, args.subs_track, args.output)
        subs_file = args.output

    # now pick the correct subtitle file and perform translation
    translate_sub_file(subs_file, args.to_lang, args.combine).save(args.output)
    print('Finished!')


if __name__ == "__main__":
    main()
