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

## FAQ

**How do I use this on Windows?**

lol
