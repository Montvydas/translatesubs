# TranslateSubs
It is a tool to translate movie subtitles from one language into another, or even show multiple language subtitles together. The tool is powered by Google Translate, thus even though the translations might not be perfect, it supports a very wide range of languages!

# About

The translator can be either used to automatically extract the subtitle from the video file (e.g. .avi, .mkv) and then perform translation on that subtitle file or process a subtitle file (e.g. .srt, .ass) instead. The first required an ffpmeg installed and setup to work from terminal. If you extract subtitle yourself, note that often the file format for subtitles is SRT. This only has minimal styling thus Anime usually uses ASS format, which can even do animations. I recommend naming output file as some_name.ass if you want the styling to remain and some_name.srt if you do not want styling.

Another really nice feature is being able to merge both the translation AND the original subtitles together. The original can be made smaller and slightly opaque to not distract and not take up too much space:

<p align="center">
  <img src="translated_example.png">
</p>

# Installation

The package lives in PyPI, thus you can install it thorugh pip. The tool is then accessible through terminal:

    pip install translatesubs
    translatesubs -h

## Basic Example

To translate an existing subtitle file (e.g. the provided truncated.ass) and translate to Spanish (default is Spanish):

    translatesubs truncated.ass out.ass --to_lang es

This will generate out.ass subtitle file, which can be imported in the VLC player via `Subtitles -> Add Subtitle File...`

## Use video file

If a video file is being used instead e.g. video.mkv, add `--video_file` flag and the first parameter becomes a video file:

    translatesubs video.mkv out.ass --video_file

## Display two languages

If you would like to learn a new language you might as well show both the original AND the translated languages (original letters are smaller and slightly transparent, as shown in the example picture) using flag `--combine`:

    translatesubs truncated.ass out.ass --combine

## Select different subtitle track

Some video files might have multiple subtitle tracks. You can select the track you want to use (starting from 0) using argument `--subs_track`:

    translatesubs video.mkv out.ass --video_file --subs_track 1

# Note

The tool uses a free googletrans API, which uses one of the google domains e.g. translate.google.com or translate.google.co.uk to perform translation. After a couple of calls that domain gets blocked and thus another one is selected instead. I added 17 domains, which should ensure that you will always have a domain that still works, because after about 1h that domain gets unblocked. Don't worry, you can still go to chrome and use the google translate :)

The tool works best with English language, since some others might have strange characters that might make things funny... I did see Portugese fail for some reason, might have to investigate later. Although I made sure that even if it fails, it continues and produces the subs, just they imght be misaligned...

# Development

During development it is worth loading the whole project folder, then every time the project gets edited and rebuilt, the scrip automatically gets updated. `dist/` folder will also get generated which will contain the wheel file, that can be installed by pip manually.

    pip install -e .
    python setup.py sdist bdist_wheel
