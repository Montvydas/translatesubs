#!/usr/bin/env python

import argparse
import logging
import sys
from typing import List
import os

from .language_manager import LanguageManager
from .subs_manager import SubsManager
from .constants import AVAILABLE_TRANSLATORS, TRANSLATORS_PRINT, DEFAULT_SEPS_PRINT, USE_DEFAULT_SEPS, DEFAULT_SEPS, \
    SEP_MAX_LENGTH, SUB_FORMATS

"""
Future Development:
1) Automatically detect the subs language using "from_lang" argument, which would be more automatic than subs_track.
"""


def main():
    parser = argparse.ArgumentParser(
        description='It is a tool to translate movie subtitles from one language into another, or even show multiple '
                    'language subtitles together.',
        usage='python translatesubs.py video.mkv output.ass --merge --to_lang fr')
    parser.add_argument('input', type=str,
                        help='Input file to translate; By default it is a subtitle file but if flag --video_file is'
                             ' set, then this is video file name.')
    parser.add_argument('output', type=str, help='Generated translated subtitle file.')
    parser.add_argument('--encoding', default='utf-8', type=str,
                        help='Input file encoding, which defaults to "utf-8". To determine it automatically use "auto"')
    parser.add_argument('--to_lang', default='es', type=str, help='Language to which translate to.')
    parser.add_argument('--pronounce_original', action='store_true',
                        help='Use pronunciation rather than writing form for origin subs e.g. useful for Japanese')
    parser.add_argument('--pronounce_translated', action='store_true',
                        help='Use pronunciation rather than writing form for translated subs e.g. useful for Japanese')
    parser.add_argument('--merge', action='store_true',
                        help='Set to see both, the original (at bottom) and the translated (on top), subtitles.')
    parser.add_argument('--reverse', action='store_true',
                        help='Display original subs on top and translated at the bottom instead, when --merge is set.')
    parser.add_argument('--secondary_scale', default=80, type=int,
                        help='Specify the secondary subs scale factor where 100 is its original size.')
    parser.add_argument('--line_char_limit', default=30, type=int,
                        help='Decide if keep multiple, often short, lines or merge them into one instead. Best '
                             'used with --merge flag since then extra lines are added. Recommended value 30 or 70.')
    parser.add_argument('--input_type', default='auto', choices=['auto', 'video', 'subs'],
                        help='Specify input file type. By default it tries to automatically deduce the type.')
    parser.add_argument('--subs_track', default=0, type=int,
                        help='Select subtitle track, if video has multiple subtitles attached to it.')
    parser.add_argument('--translator', default='google_trans_new', type=str,
                        help=f'One of the Translate services to use: {TRANSLATORS_PRINT}. googletrans does a better '
                             'job when pronunciation is needed, since it preserves new lines, however it very easily '
                             'gets corrupted, thus often many different separators have to be tried. On the other hand '
                             'google_trans_new seems to work very well, but removes new line chars in pronunciation...')

    parser.add_argument('--logging', default=40, type=int,
                        help='NOTSET - 0, DEBUG - 10, INFO - 20, WARNING - 30, ERROR - 40, CRITICAL - 50')
    parser.add_argument('--ignore_line_ends', action='store_true',
                        help='Set this when you are sure that subs do not have line end characters such as ?!. or'
                             'others, since we rely on them to split the text correctly! e.g. machine generated subs'
                             'will not include line end characters.')
    parser.add_argument('--separator', default=USE_DEFAULT_SEPS, type=str,
                        help='Special subtitle separator when sending it to be translated. Sometimes will just have to '
                             'experiment, since different language combinations require different one. I found " $$$ " '
                             'to work with majority of languages, however not all of them. The separators are created '
                             'using some weird character in various combinations like "X", " X ", "XX", " XX ", '
                             f'"XXX", " XXX ", where X is that weird character. Do not use more than {SEP_MAX_LENGTH} '
                             'chars as a separator. Separators for these languages work best:\n'
                             'Japanese - " ∞ ", " ™ ", "$$$"\n'
                             'Simplified Chinese - "@@", "@@@"\n'
                             'Albanian - "@@", "@@@"\n'
                             'Polish - "@@@", "$$$", "€€€"\n'
                             'Greek - "$$", " $$ ", "$$$", " $$$ "\n'
                             '...\n'
                             'Be careful when using $ sign, since terminal treats it as argument input, thus need a '
                             'backslash for it.\n'
                             f'Default behavior tries separators one by one from the list: {DEFAULT_SEPS_PRINT}. '
                             'If these do not work, then only some good hack can help u :)')
    args = parser.parse_args()

    logging.basicConfig(stream=sys.stderr, level=args.logging)
    logging.info(f'Using logging level {logging.getLogger()} - lvl {logging.getLogger().level}.')

    # Prepare original subs: extract text and styling
    filename = get_subs_file(args)
    subs_manager = SubsManager(filename=filename, encoding=get_encoding(args.encoding, filename))
    subs_manager.extract_line_styling()

    # Perform translation: prepare extracted subs for translating and try different separators to see which will work
    translator = get_translator(args.translator)
    language_manager = get_language_manager(args.to_lang, args.ignore_line_ends, translator)
    language_manager.prep_for_trans(subs_manager.just_text())
    original, translated = translate(language_manager, separators_to_try(args.separator),
                                     args.pronounce_original, args.pronounce_translated)

    # To display firstly original and translated below instead
    if args.reverse:
        original, translated = translated, original

    subs_manager.update_subs(main_subs=translated, secondary_subs=original,
                             merge=args.merge, secondary_scale=args.secondary_scale,
                             char_limit=args.line_char_limit)
    subs_manager.save_subs(args.output)
    print('Finished!')


def get_encoding(encoding, filename):
    if encoding == 'auto':
        import chardet
        with open(filename, "rb") as f:
            res = chardet.detect(f.read())
        return res['encoding']
    return encoding
    
def get_subs_file(args):
    extension = os.path.splitext(args.input)[1].strip('.')
    if args.input_type == 'subs' or (args.input_type == 'auto' and extension in SUB_FORMATS):
        return args.input

    # must have selected video, simply extract the subtitle and return it's path
    if not SubsManager.extract_from_video(video_in=args.input, subs_track=args.subs_track, subs_out=args.output):
        exit('Could not extract the subtitles!')

    print(f'Extracted subtitles from "{args.input}" into "{args.output}".')
    return args.output


def get_language_manager(to_lang, ignore_line_ends, translator):
    # Ensure that the language is valid and is supported
    language_manager = LanguageManager.create_instance(to_lang=to_lang,
                                                       ignore_line_ends=ignore_line_ends,
                                                       translator=translator)
    if not language_manager:
        exit(f'Cannot detect language "{to_lang}". Supported either abbreviation or full language name:\n'
             f'{translator.get_supported()}.')

    print(f'Translating to "{language_manager.to_lang.full_name}".')
    return language_manager


def get_translator(translator_name):
    # Instantiate one of the translators
    translator = AVAILABLE_TRANSLATORS.get(translator_name, None)
    if not translator:
        exit(f'Translator "{translator_name}" is not supported. '
             f'Try one of the supported ones: {TRANSLATORS_PRINT}.')

    return translator()


def translate(language_manager, separators, pronounce_origin, pronounce_trans):
    for sep in separators:
        print(f'Trying separator "{sep}"...')
        language_manager.set_separator(sep)
        original, translated = language_manager.translate_text(pronounce_origin=pronounce_origin,
                                                               pronounce_trans=pronounce_trans)
        if LanguageManager.valid_translation(original, translated):
            return original, translated

    # This we do not want to reach!
    exit('It seems like all tries to translate got corrupted. Try to manually set the separator using '
         f'--separator argument to be DIFFERENT from: {DEFAULT_SEPS_PRINT}. Check --help menu for more information.')


def separators_to_try(separator_input) -> List[str]:
    if separator_input != USE_DEFAULT_SEPS:
        return [separator_input]

    return DEFAULT_SEPS


if __name__ == "__main__":
    main()
