# m3u2volumio
Translate .[m3u](https://en.wikipedia.org/wiki/M3U#Extended_M3U) files into a [Volumio](https://volumio.org/) conform playlist. 

# Version
0.3

# Dependencies
* `python3 >= 3.1`
* `paramiko`

# Usage
`./m3u2volumio <filename.m3u>`

```
-c, --changelog
-h, --help
-v, --version
```
`Edit user environmental variables in m3u2volumio before running.`

Custom playlists are located in:
* `/data/playlist/` (custom playlists)
* `/data/favourites/my-web-radio` (*My Web Radios*)
* `/data/favourites/radio-favourites` (*Favorite Radios*)

# Assumptions
* Assumes that ssh authorized key is configured on Volumio system 
    * Reference https://www.raspberrypi.org/documentation/remote-access/ssh/passwordless.md
* Assuming proper formatting:
    * Weblinks contain `http://` or `https://`
    * [EXTINF](https://en.wikipedia.org/wiki/M3U#Extended_M3U) is structured:
        * `#EXTINF:length,Artist Name - Track Title` 
        or
        * `#EXTINF:length,Title`
* Non-weblinks will be considered filelinks
* In regular (non-EXT) m3u:
    * If the filename contains a single '-', it will be considered as `artist - title` formatting
    * Otherwise the extention will be removed and the filename taken as title
* Existing playlists and radio-favourites files will overwritten


# Examples

## Webradio

**./m3u2volumio web-radio.m3u**
```
#EXTM3U
#EXTINF:-1,RadioParadise -- 320k
http://stream-uk1.radioparadise.com/aac-320
#EXTINF:-1,OrganLive
http://play2.organlive.com:7000/320
#EXTINF:-1,KlassikRadio - Pure Bach
http://stream.klassikradio.de/purebach/mp3-192/stream.klassikradio.de/
```
Results in the following output being placed in `/data/favourites/radio-favourites` file.

```
[{"service":"webradio","name":"RadioParadise -- 320k","name":"RadioParadise -- 320k","uri":"http://stream-uk1.radioparadise.com/aac-320"},
{"service":"webradio","name":"OrganLive","name":"OrganLive","uri":"http://play2.organlive.com:7000/320"},
{"service":"webradio","name":"KlassikRadio - Pure Bach","name":"KlassikRadio - Pure Bach","uri":"http://stream.klassikradio.de/purebach/mp3-192/stream.klassikradio.de/"}]
```

## Files

# Example 1 - with EXT tags
**./m3u2volumio example1.m3u**
```
#EXTM3U
#EXTINF:123, Sample artist - Sample title
Sample.mp3
#EXTINF:321,Example Artist - Example title
Greatest Hits\Example.ogg
```
Results in the following output being placed in the `/data/favourites/Example` file.

```
[{"service":"mpd","title":"Sample title","artist":"Sample artist","uri":"mnt/NAS/Sample.mp3"},
{"service":"mpd","title":"Example title","artist":"Example Artist","uri":"mnt/NAS/path/Greatest Hits/Example.ogg"}]

```

# Example 2 - without EXT tags
**./m3u2volumio example1.m3u**
```
Sample.mp3
Greatest Hits\Example.ogg
```
Results in the following output being placed in the `/data/favourites/Example` file.

```
[{"service":"mpd","title":"Sample title","artist":"Sample artist","uri":"mnt/NAS/Sample.mp3"},
{"service":"mpd","title":"Example title","artist":"Example Artist","uri":"mnt/NAS/path/Greatest Hits/Example.ogg"}]

```
