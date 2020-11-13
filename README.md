# TranslateSubs
It's a tool to translate subtitles into any language, that is supported by google translator :)

# About

The translator can be either used to extract the subtitle from the video file and then perform translation on that file or process a subtitle file instead. The first required an ffpmeg installed and setup to work from terminal. If you extract subtitle yourself, note that often the file format for subtitles is SRT. This only has minimal styling and anime usually ASS format, which can even do animations. I recommend sticking to ACC if you want the styling to remain.

Another really nice feature is being able to merge both the translation AND the original subtitles together. The original can be made smaller and slightly opaque to not distract and not take up too much space:

<p align="center">
  <img src="translated_example.png">
</p>

# Usage

## Basic Example

To translate an existing subtitle file (e.g. the provided truncated.ass) and translate to Spanish (default is Spanish):

`python substranslator.py truncated.ass out.ass --to_lang es`

This will generate out.ass subtitle file, which can be imported in the VLC player via `Subtitles -> Add Subtitle File...`

## Use video file

If a video file is being used instead e.g. video.mkv, add --video_file flag and the first parameter becomes a video file:

`python substranslator.py video.mkv out.ass --video_file`

## Display two languages

If you would like to learn a new language you might as well show both the original AND the translated languages (original letters are smaller and slightly transparent, as shown in the example picture) using flag --combine:

`python substranslator.py truncated.ass out.ass --combine`

## Select different subtitle track

Some video files might have multiple subtitle tracks. You can select the track you want to use (starting from 0) using argument --subs_track:

`python substranslator.py video.mkv out.ass --video_file --subs_track 1`

# Note

The tool uses a free googletrans API, which uses one of the google domains e.g. translate.google.com or translate.google.co.uk to perform translation. After a couple of calls that domain gets blocked and thus another one is selected instead. I added 17 domains, which should ensure that you will always have a domain that still works, because after about 1h that domain gets unblocked. Don't worry, you can still go to chrome and use the google translate :)

The tool works best with English language, since some others might have strange characters that might make things funny... I did see Portugese fail for some reason, might have to investigate later. Although I made sure that even if it fails, it continues and produces the subs, just they imght be misaligned...

# Building

`python setup.py sdist bdist_wheel`

# Debug

`pip install -e .`

- Where e is for editable

Then can perform building and after every build `translatesubs` will get updated.
