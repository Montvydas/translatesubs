#!/usr/bin/env python

import argparse
import logging
import sys

from .language_manager import LanguageManager
from .subs_manager import SubsManager


def main():
    parser = argparse.ArgumentParser(
        description='It is a tool to translate movie subtitles from one language into another, or even show multiple '
                    'language subtitles together.',
        usage='python translatesubs.py video.mkv output.ass --video_file --combine --to_lang fr')
    parser.add_argument('input', type=str,
                        help='Input file to translate; By default it is a subtitle file but if flag --video_file is'
                             ' set, then this is video file name.')
    parser.add_argument('output', type=str, help='Generated translated subtitle file.')
    parser.add_argument('--to_lang', default='es', type=str,
                        help='language to which translate to.')
    parser.add_argument('--combine', action='store_true',
                        help='Set this if you want to see the original and the translated subtitles together.')
    parser.add_argument('--line_char_limit', default=30, type=int,
                        help='Decide if keep short lines together or merge into one. Useful to set to ~70 '
                             'when used with --combine flag, since then extra lines are added. Default is 30.')
    parser.add_argument('--video_file', action='store_true',
                        help='Set this if video file is used instead of a subtitle file.')
    parser.add_argument('--subs_track', default=0, type=int,
                        help='Select subtitle tract, if video has multiple subtitles attached to it. Default is 0.')
    parser.add_argument('--debug_level', default=40, type=int,
                        help='NOTSET - 0, DEBUG - 10, INFO - 20, WARNING - 30, ERROR - 40, CRITICAL - 50')
    parser.add_argument('--separator', default=' ## ', type=str,
                        help='Special subs separator when sending to be translated. Suggested " ## ", " $$ ".. ')
    args = parser.parse_args()

    subs_file = args.input

    logging.basicConfig(stream=sys.stderr, level=args.debug_level)
    logging.info(f'Using logging level {logging.getLogger()} - lvl {logging.getLogger().level}.')

    # Ensure that the language is valid and is supported
    language_manager = LanguageManager.create_instance(args.to_lang, args.separator)
    if language_manager:
        print(f'Translating to "{language_manager.to_lang["full"]}".')
    else:
        exit(f'Cannot detect language "{args.to_lang}". Supported either abbreviation or full language name:\n'
             f'{LanguageManager.get_supported()}')

    # If we process the video rather than subtitle file, then simply extract the subtitle and place it into output
    if args.video_file:
        if not SubsManager.extract_from_video(args.input, args.subs_track, args.output):
            exit('Could not extract the subtitles!')
        subs_file = args.output
        print(f'Extracted subtitles from "{args.input}" into "{args.output}".')

    subs_manager = SubsManager(subs_file)
    subs_manager.clean_line_formatting()
    subs_manager.merge_long_lines(char_limit=args.line_char_limit)

    language_manager.prepare_for_translation(subs_manager.just_text())
    translated = language_manager.translate_prepared_text()

    subs_manager.update_subs(translated, args.combine)
    subs_manager.save_subs(args.output)
    print('Finished!')


if __name__ == "__main__":
    main()
