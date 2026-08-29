# deezer-flac-download

A program to freely download Deezer FLAC files. Tested and working in October 2022.
Verified to produce the same audio as other downloaders being used for files present
on the internet. A paid Deezer account is required.

The program also downloads cover art, and embeds it, as well as metadata tags, in
the FLAC files.

## Setup

Create a file at `~/.config/deezer-flac-download/config.toml` based on
`example_config.toml`. The contents are as follows:

* `arl`: Can be obtained from the `arl` cookie in your browser.
* `license_token`: Navigate to a song page, open the "Network" tab in your
  browser's dev tools, click the play button, click the "get_url" request, find
  the request data in the right sidebar and you'll find the `license_token`
  there.
* `dest_dir`: Choose any folder.
* `pre_key` and `iv`: Fill them in with the values you magically found at https://bin.0xfc.de/?489876949a0c544c#3UYL7DBfD2RjHRjW86BFVFeJJBwrTftop5Lvgrvo3Wsb

## Usage

1. Find the album's ID by navigating to it and looking at the URL. It's the
  string of numbers.
1. `go run . album <album_id>`

You can also download multiple albums: `go run . album 1234 2345 3456`.

## Preparing tracks for CDJs

`track_format_converter` turns a folder of downloads into a library a
CDJ-2000 class player can read. Run `./track_format_converter --help` for the
full reference; the short version:

```bash
./track_format_converter --source-dir ~/Downloads --output-prefix-dir ~/dj/music
```

The destination format follows the source, so there is nothing to pick:

| Source | Becomes |
| --- | --- |
| flac, wav, aiff, alac, ape, wv, tta | aiff, capped at 24-bit / 48kHz |
| mp3 | mp3, copied with its audio untouched |
| aac, m4a, ogg, opus, wma | mp3 320k |

Nothing is ever upsampled — 44.1kHz/16-bit stays exactly that — and rates only
come down within their own family (88.2 → 44.1, 96 → 48) so each reduction is
an exact ratio. Lossy audio is never expanded into a lossless container, and
mp3 is never re-encoded. Levels are measured into `PEAK_DBFS` and
`LOUDNESS_LUFS` tags but never altered, since a gain change cannot be undone
exactly. Tracks under three minutes are skipped.

Output is organised from each track's own tags as
`{Band}/{Album}/{Artist} - {Title}`, and a single `playlist.cdj.m3u` is written
at the root of the destination. The name is always the same, so every run keeps
building the same list; re-running adds to it rather than replacing it. Entries
are ordered by path and each track appears once, so the same library always
produces the same playlist. That file is refused as a source, so it cannot be
overwritten while being read.

Add `--cleanup` to any normal run to also migrate what is already in the
destination, so a library built by an older version catches up with the
current rules:

```bash
./track_format_converter --source-dir ~/Downloads --output-prefix-dir ~/dj/music --cleanup
```

It drops entries whose files have gone or that are too short, re-encodes
anything above spec, measures level tags that were never recorded, and moves
files sitting at out-of-date paths into the current layout. Nothing is
deleted — anything removed goes to `/tmp/deleted/<timestamp>/cleanup`.

Requires `ffmpeg`, `ffprobe` and `python3`.

## FAQ

**How do I use this on Windows?**

lol
