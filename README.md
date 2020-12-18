# TranslateSubs
It is a tool to translate movie subtitles from one language into another, or even show multiple language subtitles together. The tool is powered by Google Translate, thus even though the translations might not always be perfect, it supports a very wide range of languages!

# About

The translator can be either used to automatically extract the subtitle from the video file (e.g. .avi, .mkv) and then perform translation on that subtitle file or process a subtitle file (e.g. .srt, .ass) instead. The first required an ffpmeg installed and setup to work from terminal. If you extract subtitle yourself, note that often the file format for subtitles is SRT. This only has minimal styling thus Anime usually uses ASS format, which can even do animations. I recommend naming output file as some_name.ass if you want the styling to remain and some_name.srt if you do not want styling.

Another really nice feature is being able to merge both the translation AND the original subtitles together. The original can be made smaller and slightly opaque to not distract and not take up too much space:

<p align="center">
  <img src="translated_example.png">
</p>

# Installation

The package lives in PyPI, thus you can install it through pip. The tool is then accessible through terminal:

    pip install translatesubs
    translatesubs -h

## Basic Example

To translate an existing subtitle file (e.g. the provided truncated.ass) and translate to Spanish (default is Spanish):

    translatesubs truncated.ass out.ass --to_lang es

This will generate out.ass subtitle file, which can be imported in the VLC player via `Subtitles -> Add Subtitle File...`

## Use video file

If a video file is being used instead e.g. video.mkv, add `--video_file` flag and the first parameter becomes a video file:

    translatesubs video.mkv english(translated).ass --video_file --to_lang en

Some video files might have multiple subtitle tracks. You can select the track you want to use (starting from 0) using argument `--subs_track`:

    translatesubs video.mkv english(translated).ass --video_file --to_lang en --subs_track 1

## Display two languages at once

If you would like to learn a new language, you might as well show both, the language you would like to learn (Main) AND the one you speak very well (Secondary) (slightly smaller font and slightly opaque to not disturb, as shown in the example picture).
 
E.g. If the language you speak is English and you would like to learn Spanish for some series, that does NOT provide Spanish subtitles, simply use flag `--merge` and English subs will be translated into `Spanish(translated) + English`:

    translatesubs english.ass spanish(translated)+english.ass --to_lang es --merge

If, however, the series DOES have spanish subtitles, I would instead recommend translating the Spanish into English, since Google translate does not give 100% accurate text, thus by translating FROM Spanish you will get better Spanish subs quality, while English will not matter that much, since that is secondary subtitles. To make sure that you still see the Spanish on top and English at the bottom use flag `--reverse`, which will then generate `Spanish + English(translated)` subs: 

    translatesubs spanish.ass spanish+english(translated).ass --to_lang en --merge --reverse

Another flag, which is useful when merging two languages together is `--line_char_limit`. Often instead of showing one long line, two or even three lines are displayed in subs. While they all would still fit within a single line after being translated, when `--merge` is used, that would double the line count and would block a large portion of the video. To solve this add `--line_char_limit` with a number of around 70. This basically means that if there are less than 70 characters within a sub, remove all new lines. Of course, for some subs this number could be higher, or smaller, depending on the font size, thus might have to test a little bit before getting perfect result or count how many characters is safe to read within a single line.

    translatesubs spanish.ass spanish+english(translated).ass --to_lang en --merge --reverse --line_char_limit 70

You can also change the subs that are at the bottom fond scale using `--secondary_scale`. 100% will represent fond size equal to the main subs at the top and smaller value will make them proportionally smaller:

    translatesubs spanish.ass english(translated)+spanish.ass --to_lang en --merge --secondary_scale 50 

## Display pronunciation

Languages like Japanese, Chinese and many others use a non-latin characters. If you are learning a new language, it is likely you can't read the new alphabet as quickly as it is required to follow the subs. For that purpose `--pronounce_translated` to show pronunciation of the translation and `--pronounce_original` to show pronunciation of the original subs.


E.g. you might be learning Japanese and can't be bothered learning all the Hiragana, Katakana and Kanji, but you want to start understanding better Anime as you watch it. In that case it is best to find Japanese subs on `kitsunekko.net` and use `--pronounce_original` flag (also note `--merge` and `--reverse`):

    translatesubs japanese.ass japanese(pronounced)+english(translated).ass --to_lang en --merge --reverse --pronounce_original
    
If you have more advanced Japanese understanding (yet cannot read the characters), you can remove English subs altogether:

    translatesubs japanese.ass japanese(pronounced).ass --to_lang ja --pronounce_translated

Alternatively, if you cannot find the japanese subs you can translate the english ones straight to Japanese, however can't guarantee that what is being spoken is exactly what you will be reading...

    translatesubs english.ass japanese(pronounced)+english.ass --to_lang en --pronounce_translated

## Select the translator provider

By default the tool uses googletrans API. For now two are supported: `googletrans` and `google_trans_new`. You ca choose which one to use with flag `--translator`:

    translatesubs truncated.ass out.ass --to_lang es --translator google_trans_new
    
In the future I would like to add official google translate API support, but that would require acquiring Google Translation API Key and passing it into the tool. If, however, you're translating 1-5 episodes per day, then using one of the two supported APIs is OK, however for very large amount official API would be best, since then you could extend quota limits.

Note: `google_trans_new` ignores ALL new lines, meaning if there was some new lines `\n` within original subs, they will ALL get removed in both translations AND pronunciations. `googletrans` on the other hand keeps the new lines within translations, however removes them for pronunciations. 

## Advanced Stuff

Instead of sending subs one by one to be translated the tool combines as many subs as possible into large chunks and sends those chunks instead. Otherwise 1) you would get blocked by Google after translating 1-2 series and 2) Since some subs do not contain a full sentence, the translation will be more accurate when sending full sentences. To achieve this, however, one needs some special character (or character set), that Google Translate would treat as something non-translatable, however would still keep it. A couple of perfect examples would be ` ∞ `, `@@`, ` ### `, ` \\$\\$\\$ `... This separator needs to be adjusted by the language and it might be done so in the future automatically. For now need to either experiment if you get error message when performing translations or note that " $$$ " works with most languages, however can also try " ∞ ", " ™ ", "££", " ## " or some other weird character in various combinations like "X", " X ", "XX", " XX ", "XXX", " XXX ", where X is that special character. When translating to these languages I found these characters to work best:
- Japanese - " ∞ ", " ™ ", "$$$"
- Simplified Chinese - "@@", "@@@"
- Albanian - "@@", "@@@"
- Polish - "@@@", "$$$", "€€€"
- Greek - "\\$\\$", " \\$\\$ ", "\\$\\$\\$", " \\$\\$\\$ "

# Note

The tool uses a free googletrans API, which uses one of the google domains e.g. translate.google.com or translate.google.co.uk to perform translation. After a couple of calls that domain gets blocked and thus another one is selected instead. I added 17 domains, which should ensure that you will always have a domain that still works, because after about 1h that domain gets unblocked. Don't worry, you can still go to chrome and use the google translate :)

The tool works best with English language, since some others might have strange characters that might make things funny... I did see Portugese fail for some reason, might have to investigate later. Although I made sure that even if it fails, it continues and produces the subs, just they imght be misaligned...

# Development

During development it is worth loading the whole project folder, then every time the project gets edited and rebuilt, the scrip automatically gets updated. `dist/` folder will also get generated which will contain the wheel file, that can be installed by pip manually.

    pip install -e .
    python setup.py sdist bdist_wheel

# Automatic subs extraction from a video

If you cannot get the subtitles for some video, there is a way to get "unpredictable" quality subs by extracting the audio from a video file and then using Google Web Speech API to create subs. Two projects that worked pretty smoothly were [autosub](https://github.com/agermanidis/autosub) and [pyTranscriber](https://github.com/raryelcostasouza/pyTranscriber). The first is only supported on python2 and the second is a GUI application, which is based on the first utility, with the code updated to work with python3. One problem with that one is not being able to select all kinds of file formats, only some specific ones. A way around this is to download the source code and modifying file `pytranscriber/control/ctr_main.py` line that contains `"All Media Files (*.mp3 *.mp4 *.wav *.m4a *.wma)"`. You need to add some file e.g. if .mkv is required, then add *.mkv. I personally would just download both projects source code and replace the `__init__.py` file within autosub project with `autosub/__init__.py` from pyTranscriber. Then just use autosub as per documentation with python3. Of course you can build wheel and install it or just do `pip install -e .` to install without building the wheel. This way is still far from perfect, however one day the transcription will get a lot better results, hopefully that day is on the corner!