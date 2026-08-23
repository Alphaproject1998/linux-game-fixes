# Getting Star Rail working on Linux

**This is just what worked for me.**

Version 1.0.0, see the [changelog](#changelog).

I'm not a Proton or Linux expert and I don't fully understand every part of it, but I spent a while looking for this and never found anything that explained it, so here it is.

Two things really. Getting the game to launch at all, which took me a while and a lot of Proton builds, and then fixing the videos, which are broken because of the way I had to launch it.

## Getting it to run

I could not get Star Rail to start any of the normal ways. Steam, the Steam Linux Runtime, the other launchers (Lutris, ProtonPlus, etc), all of them gave me something different, a black screen or a white one, a crash on startup, or just nothing happening. Steam was no help.

I went through a lot of Proton builds getting nowhere. The one that ended up working was DW-Proton.

ProtonPlus is what got me there in the end, but not the way you'd normally use it. Adding the game and running it in there like anything else fails the same as everything else did. The custom exe path is the only one that worked.

What I ended up with:

- ProtonPlus (the Flatpak, `com.vysp3r.ProtonPlus`), which is where I got DW-Proton from
- HoYoPlay installed through it, into its own prefix rather than an existing one
- HoYoPlay downloading Star Rail itself into that same prefix
- "Run custom EXE" pointed at `launcher.exe` in the prefix

That got me into the game and it's still the prefix I use. Gameplay was fine from there, ran well, no complaints with the game itself.

`star-rail-launch` in this folder is the same thing without opening ProtonPlus every time. Same prefix, same Proton build, it just calls `proton run` on `launcher.exe`.

## The videos

Every video in the game is broken, and not in the sense of playing without picture or stuttering. It locks. Black screen, no skip, and it sits there.

On the event tab it's a preview panel so I could ignore it, and I did for a while. Then I got to the Holy Grail event with Rin and the cinematic there does exactly the same thing, except that one is mid-game and there's no way past it. Locked on black, couldn't continue, couldn't back out, and restarting put me right back into it. At that point I couldn't play.

The reason is the way I have to launch it. "Run custom EXE" is a bare `proton run` with nothing around it, no Steam Linux Runtime container, and that container is what would normally make the video work. So the only setup that got the game running is the one that breaks the video. Great...

Which is also why "just use SteamLinuxRuntime sniper" doesn't help me. It's probably the proper fix and it sorts out more than mine does, but the game doesn't start under it, which is where I came in. If it starts for you, use that.

## What it turned out to be

The game's log was the only thing that said anything useful:

```
$PREFIX/pfx/drive_c/users/steamuser/AppData/LocalLow/Cognosphere/Star Rail/Player.log
```

```
[CRIWARE] Error:E2025040803M:Failed in criV264Mft_Start(), mft_decoder is NULL.
```

Following that up, cutscenes are `.usm` files that CriWare decodes, and it asks Wine for an H.264 Media Foundation Transform, which comes out of winegstreamer, which gets `avdec_h264` from GStreamer's `libgstlibav.so`. So nothing was really missing, the decoder just never loaded.

Checking that plugin is where it showed up. Proton's own libraries have to be on the path first or every dependency looks broken:

```sh
export LD_LIBRARY_PATH="$PROTON/files/lib/x86_64-linux-gnu"
ldd "$PROTON/files/lib/x86_64-linux-gnu/gstreamer-1.0/libgstlibav.so" | grep 'not found'
```

```
libvpx.so.9 => not found
```

Proton's ffmpeg was built against `libvpx.so.9` and Arch has `libvpx.so.12`. With the Steam runtime the container provides the old one, but there's no container here and nothing on my system answers to `.9`, so it fails to load.

Then there's the part that would have had me going round in circles. GStreamer writes off a plugin that fails and caches that, so it never tries it again. The symlink on its own does nothing until that cache is gone.

```sh
strings "$PREFIX/gstreamer-1.0/registry.x86_64.bin" | grep -c '^avdec'
```

Mine said `0`, which is how you know it's this and not something else.

## What I did

```sh
mkdir -p ~/.local/share/proton-compat-libs
ln -s /usr/lib/libvpx.so.12 ~/.local/share/proton-compat-libs/libvpx.so.9
rm "$PREFIX/gstreamer-1.0/registry.x86_64.bin"
```

Then this in the launch script, before it runs Proton:

```sh
export LD_LIBRARY_PATH="$HOME/.local/share/proton-compat-libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

Proton puts its own library folders ahead of that, so it only ever gets used for something Proton asked for and couldn't find anywhere else.

I keep the symlink outside the Proton folder because ProtonPlus overwrites "Latest" builds when it updates, so anything in there would just disappear and I'd be back to black screens wondering what happened.

`star-rail-launch` is my actual launch script, only thing changed is my home folder swapped for `$HOME`.

If you want to be careful, make the symlink somewhere temporary first and run that `ldd` again with the temp folder on `LD_LIBRARY_PATH`. If it still says not found then it's the wrong library and you haven't changed anything permanent.

## Testing it

Launch once so the cache rebuilds, then run the same `strings` command. Mine went from `0` to `211`.

Videos and cinematics have played every time since, no lockups. Nothing else changed, no game patch, just the symlink and deleting the cache.

## The script

Nothing to it. Paths at the top, a couple of exports, then hand off to Proton. Edit the paths in `star-rail-launch` to match yours and run it.

```sh
prefix="/path/to/steamapps/compatdata/<id>"
proton="$HOME/.local/share/Steam/compatibilitytools.d/<build>/proton"
exe="$prefix/HoYoPlay/launcher.exe"

export STEAM_COMPAT_DATA_PATH="$prefix"
export STEAM_COMPAT_CLIENT_INSTALL_PATH="$HOME/.local/share/Steam"
export LD_LIBRARY_PATH="$HOME/.local/share/proton-compat-libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

exec "$proton" run "$exe"
```

If you want it in Steam, add the script itself as a non-Steam game and leave the compatibility tool off for that shortcut, since the script calls Proton itself and forcing another one just tries to run bash through Wine. Launch options still work, `mangohud %command%` and so on.

## Known bugs

**Lights flicker.** Lamps and light glows blink on and off, even with the camera standing still. It's a different set of lights each launch with nothing changed, so it's hard to tell if anything I try actually helps. I don't know how to fix it yet.

What I've tried that made no difference: DLSS on and off, bloom, TAA, a few DXVK options (descriptor heap off, compute barriers, `zeroMappedMemory`), `PROTON_DXVK_LOWLATENCY=1`, and turning NVAPI off with the card reported as AMD. The only thing that came close was `PROTON_DXVK_SAREK=1`, the old DXVK 1.12, which left one light flickering, but it stutters, has graphical glitches and no DLSS, so it's worse overall.

I couldn't find anyone else reporting it, on Linux or Windows. If you've seen it, or fixed it, please open an issue.

## If your setup is different

Your versions almost certainly won't match mine. Run the same `ldd` and link whatever it says is missing, it's the same fix either way.

My specs are [below](#my-setup), everything here was done on that and it's the only machine I can speak for.

I'll update this if it breaks again, or if some Proton update makes it pointless, since I do play the game pretty much every day (dailies and weeklies at least, events when I have to, I am FAR behind on the story!).

## My setup

- Arch, kernel 7.1.8-zen1-3-zen
- DW-Proton 11.0-10
- libvpx 1.16.0-3, gstreamer 1.28.6-1
- nvidia-open-dkms 610.57.04
- HoYoPlay set up through ProtonPlus, launched with "Run custom EXE"

## Changelog

### 1.0.0 (2026-08-23)

First release: the launch script and the `libvpx.so.9` fix for the videos.

## About AI

I worked this out with some help from an AI coding assistant. It helped dig through the logs and Proton's libraries to find out why the videos broke. The fix itself is what I created and run, and it's what I'm playing on now.
