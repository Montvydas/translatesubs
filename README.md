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

If a video file is being used instead e.g. video.mkv, subs will be extracted automatically using ffmpeg library before processing them:

    translatesubs video.mkv english_translated.ass --to_lang en

Some video files might have multiple subtitle tracks. You can select the track you want to use (starting from 0) using argument `--subs_track`:

    translatesubs video.mkv english_translated.ass --to_lang en --subs_track 1

## Display two languages at once

If you would like to learn a new language, you might as well show both, the language you would like to learn (Main) AND the one you speak very well (Secondary) (slightly smaller font and slightly opaque to not disturb, as shown in the example picture).
 
E.g. If the language you speak is English and you would like to learn Spanish for some series, that does NOT provide Spanish subtitles, simply use flag `--merge` and English subs will be translated into `Spanish(translated) + English`:

    translatesubs english.ass spanish_translated+english.ass --to_lang es --merge

If, however, the series DOES have spanish subtitles, I would instead recommend translating the Spanish into English, since Google translate does not give 100% accurate text, thus by translating FROM Spanish you will get better Spanish subs quality, while English will not matter that much, since that is secondary subtitles. To make sure that you still see the Spanish on top and English at the bottom use flag `--reverse`, which will then generate `Spanish + English(translated)` subs: 

    translatesubs spanish.ass spanish+english_translated.ass --to_lang en --merge --reverse

Another flag, which is useful when merging two languages together is `--line_char_limit`. Often instead of showing one long line, two or even three lines are displayed in subs. While they all would still fit within a single line after being translated, when `--merge` is used, that would double the line count and would block a large portion of the video. To solve this add `--line_char_limit` with a number of around 70. This basically means that if there are less than 80 characters within a sub, remove all new lines. Of course, for some subs this number could be higher, or smaller, depending on the font size, thus might have to test a little bit before getting perfect result or count how many characters is safe to read within a single line.

    translatesubs spanish.ass spanish+english_translated.ass --to_lang en --merge --reverse --line_char_limit 80

You can also change the subs that are at the bottom fond scale using `--secondary_scale`. 100 will represent font size equal to the main subs at the top (100%) and smaller value will make them proportionally smaller:

    translatesubs spanish.ass english_translated+spanish.ass --to_lang en --merge --secondary_scale 50 

## Display pronunciation

Languages like Japanese, Chinese and many others use a non-latin characters. If you are learning a new language, it is likely you can't read the new alphabet as quickly as it is required to follow the subs. For that purpose `--pronounce_translated` to show pronunciation of the translation and `--pronounce_original` to show pronunciation of the original subs.


E.g. you might be learning Japanese and can't be bothered learning all the Hiragana, Katakana and Kanji, but you want to start understanding better Anime as you watch it. In that case it is best to find Japanese subs on `kitsunekko.net` and use `--pronounce_original` flag (also note `--merge` and `--reverse`):

    translatesubs japanese.ass japanese_pronounced+english_translated.ass --to_lang en --merge --reverse --pronounce_original
    
If you have more advanced Japanese understanding (yet cannot read the characters), you can remove English subs altogether by performing Japanese to Japanese translation, but adding `--pronounce_translated` flag:

    translatesubs japanese.ass japanese_pronounced.ass --to_lang ja --pronounce_translated

Alternatively, if you cannot find the japanese subs you can translate the english ones straight to Japanese, however can't guarantee that what is being spoken is exactly what you will be reading since Japanese language is more difficult to translate...

    translatesubs english.ass japanese_pronounce+english.ass --to_lang en --pronounce_translated

## Select the translator provider

The tool supports a couple of translation libraries: `googletrans` and `google_trans_new`. In rare cases the translation might fail using one of the libraries. When that happens simply try another one :) You can choose which one to use with flag `--translator`:

    translatesubs truncated.ass out.ass --to_lang es --translator google_trans_new
    
In the future I would like to add official google translate API support, but that would require acquiring Google Translation API Key and passing it into the tool. If, however, you're translating 1-5 episodes per day, then using one of the two supported APIs is OK, however for very large amounts official API would be best, since then you could extend quota limits.

Note: `google_trans_new` ignores ALL new lines, meaning if there was some new lines `\n` within original subs, they will ALL get removed in both translations AND pronunciations. `googletrans` on the other hand keeps the new lines within translations, however removes them for pronunciations. Also note that the behavior might change in the future, since I am not responsible for maintaining these libraries. 

## Advanced Stuff

Instead of sending subs one by one to be translated the tool combines as many subs as possible into large chunks and sends those chunks instead. Otherwise 1) you would get blocked by Google after translating 1-2 series and 2) Since some subs do not contain a full sentence, the translation will be more accurate when sending full sentences. To achieve this, however, one needs some special character (or character set), that Google Translate would treat as something non-translatable, however would still keep it e.g. separate each sub with ` ∞ `, `@@`, ` ### `, ` $$$ `. This separator needs to be different depending on the subtitle stream and the tool tries one separator after another until translation succeeds. Separator is created by using a single special character in combinations like "X", " X ", "XX", " XX ", "XXX", " XXX ", where X is that special character. I found that different languages work best with certain separators best:
- Japanese - " ∞ ", " ™ ", "$$$"
- Simplified Chinese - "@@", "@@@"
- Albanian - "@@", "@@@"
- Polish - "@@@", "$$$", "€€€"
- Greek - "$$", " $$ ", "$$$", " $$$ "

You can overwrite the default behavior of trying separator one by one by passing one yourself e.g. `--separator " ### "`

# Note

The tool uses a free googletrans API, which uses one of the google domains e.g. translate.google.com or translate.google.co.uk to perform translation. After a couple of calls that domain gets blocked and thus another one is selected instead. I added 17 domains, which should ensure that you will always have a domain that still works, because after about 1h that domain gets unblocked. Don't worry, you can still go to chrome and use the google translate :)

The tool works best with English language, since some others might have strange characters that might make things funny... However the use of different separators selected automatically should ensure that things work (I did see Portugese fail for some reason, might have to investigate later). Although even in case of failure I made sure that even if it fails, it continues and produces the subs, just they might be misaligned with the main subs text...

# Development

During the development process, it is worth loading the whole project folder (aka watch lib updates) rather than rebuilding and performing installation after every code change. This is done using `pip install -e .`. To generate installable wheel, do `python setup.py sdist bdist_wheel`, which will output build files within  `dist/` folder.

# Automatic subs extraction from a video

If you cannot get the subtitles for some video, there is a way to get "unpredictable" quality subs by extracting the audio from a video file and then using Google Web Speech API to create subs. Two projects that worked pretty smoothly were [autosub](https://github.com/agermanidis/autosub) and [pyTranscriber](https://github.com/raryelcostasouza/pyTranscriber). The first is only supported on python2 and the second is a GUI application, which is based on the first utility, with the code updated to work with python3. One problem with that one is not being able to select all kinds of file formats, only some specific ones. A way around this is to download the source code and modifying file `pytranscriber/control/ctr_main.py` line that contains `"All Media Files (*.mp3 *.mp4 *.wav *.m4a *.wma)"`. You need to add some file e.g. if .mkv is required, then add *.mkv. I personally would just download both projects source code and replace the `__init__.py` file within autosub project with `autosub/__init__.py` from pyTranscriber. Then just use autosub as per documentation with python3. Of course you can build wheel and install it or just do `pip install -e .` to install without building the wheel. This way is still far from perfect, however one day the transcription will get a lot better results, hopefully that day is on the corner!