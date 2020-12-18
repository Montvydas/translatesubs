#!/usr/bin/env python

import argparse
import logging
import sys

from .language_manager import LanguageManager
from .subs_manager import SubsManager
from .constants import AVAILABLE_TRANSLATORS
from .constants import TRANSLATORS_PRINT


def main():
    parser = argparse.ArgumentParser(
        description='It is a tool to translate movie subtitles from one language into another, or even show multiple '
                    'language subtitles together.',
        usage='python translatesubs.py video.mkv output.ass --video_file --merge --to_lang fr')
    parser.add_argument('input', type=str,
                        help='Input file to translate; By default it is a subtitle file but if flag --video_file is'
                             ' set, then this is video file name.')
    parser.add_argument('output', type=str, help='Generated translated subtitle file.')
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
    parser.add_argument('--video_file', action='store_true',
                        help='Set this if video file is used instead of a subtitle file.')
    parser.add_argument('--subs_track', default=0, type=int,
                        help='Select subtitle tract, if video has multiple subtitles attached to it.')
    parser.add_argument('--translator', default='googletrans', type=str,
                        help=f'One of the Translate services to use: {TRANSLATORS_PRINT}.')

    parser.add_argument('--logging_level', default=40, type=int,
                        help='NOTSET - 0, DEBUG - 10, INFO - 20, WARNING - 30, ERROR - 40, CRITICAL - 50')
    parser.add_argument('--ignore_line_ends', action='store_true',
                        help='Set this when you are sure that subs do not have line end characters such as ?!. or'
                             'others, since we rely on them to split the text correctly! e.g. machine generated subs'
                             'will not include line end characters.')
    parser.add_argument('--separator', default=' $$ ', type=str,
                        help='Special subtitle separator when sending it to be translated. Sometimes will just have to '
                             'experiment, since different languages might require different one... I found " $$$ " '
                             '(default) to work with most languages, however can also try " ∞ ", " ™ ", "££", " ## " '
                             'or some other weird character in various combinations like "X", " X ", "XX", " XX ", '
                             '"XXX", " XXX ", where X is that special character. I found these languages to work best:'
                             'Japanese - " ∞ ", " ™ ", "$$$"\nSimplified Chinese - "@@", "@@@"\nAlbanian - "@@", "@@@"'
                             'Polish - "@@@", "$$$", "€€€"\nGreek - "\\\\$\\\\$", " \\\\$\\\\$ ", "\\\\$\\\\$\\\\$", '
                             '" \\\\$\\\\$\\\\$ "\n... '
                             'Also note - Avoid using $ sign in general, since it messes up with regex and other...')
    args = parser.parse_args()

    logging.basicConfig(stream=sys.stderr, level=args.logging_level)
    logging.info(f'Using logging level {logging.getLogger()} - lvl {logging.getLogger().level}.')

    translator = get_translator(args)
    language_manager = get_language_manager(args, translator)
    subs_file = get_subs_file(args)

    subs_manager = SubsManager(filename=subs_file)
    subs_manager.merge_long_lines(char_limit=args.line_char_limit)
    subs_manager.extract_line_styling()

    original, translated = language_manager.translate_text(text=subs_manager.just_text(),
                                                           pronounce_origin=args.pronounce_original,
                                                           pronounce_trans=args.pronounce_translated)
    # To display firstly original and translated below
    if args.reverse:
        original, translated = translated, original

    subs_manager.update_subs(main_subs=translated, secondary_subs=original,
                             merge=args.merge, secondary_scale=args.secondary_scale)
    subs_manager.save_subs(args.output)
    print('Finished!')


def get_subs_file(args):
    if not args.video_file:
        return args.input
    # If we process the video rather than subtitle file, then simply extract the subtitle and place it into output
    if not SubsManager.extract_from_video(video_in=args.input, subs_track=args.subs_track, subs_out=args.output):
        exit('Could not extract the subtitles!')
    print(f'Extracted subtitles from "{args.input}" into "{args.output}".')
    return args.output


def get_language_manager(args, translator):
    # Ensure that the language is valid and is supported
    language_manager = LanguageManager.create_instance(to_lang=args.to_lang, separator=args.separator,
                                                       ignore_line_ends=args.ignore_line_ends, translator=translator)
    if language_manager:
        print(f'Translating to "{language_manager.to_lang.full_name}".')
    else:
        exit(f'Cannot detect language "{args.to_lang}". Supported either abbreviation or full language name:\n'
             f'{translator.get_supported()}.')
    return language_manager


def get_translator(args):
    # Instantiate one of the translators
    translator = AVAILABLE_TRANSLATORS.get(args.translator, None)
    if translator:
        translator = translator()
    else:
        exit(f'Translator "{args.translator}" is not supported. '
             f'Try one of the supported ones: {TRANSLATORS_PRINT}.')
    return translator


if __name__ == "__main__":
    main()
