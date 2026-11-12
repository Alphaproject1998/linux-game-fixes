# Wuthering Waves launcher on Steam

**Gets the launcher Steam now ships for Wuthering Waves working under Proton.**

Version 1.0.0, see the [changelog](#changelog). `wuwa-launch --version` says which one you have.

Since 3.8 (November 2026) the Steam version isn't the game anymore. Steam gives you Kuro's launcher, the same one the standalone Windows version uses, and that downloads and updates the game itself.

Under Proton that launcher is broken in a handful of ways, starting with its window not showing up at all. This is a launch option that fixes them. Nothing gets installed on your system: it all happens in the game's own Proton prefix each time you launch, and taking the launch option out turns it off again.

I've used it to download the game and play a few hours of story, with cutscenes, Convene history and the pity pages all working and no crashes. That's on my machine only, listed under Requirements, so other setups are still untested.

https://github.com/user-attachments/assets/e85d2766-f492-457e-a318-2c5c99f50a1c

Unofficial, and nothing to do with Kuro Games.

## What's broken without it, and what fixes it

- **The launcher window is invisible.** It's a see-through window with a web page inside, and Wine never draws the page into it, so there's a window there that you just can't see. In Steam Deck mode the launcher uses a normal window instead, and it decides that from the `SteamDeck` variable when it starts. A small .NET startup hook (`deck-hook/`) sets it for the launcher, then clears it once the window is up, so the game doesn't think it's on a Deck too. That breaks its videos.
- **"Failed to retrieve space info".** The launcher checks free space through a part of Windows that Proton's Wine doesn't have (`wminet_utils.dll`), so the wrapper puts regular Wine's copy into the prefix. Drives still show as "Unknown", but that's only a label.
- **A black frame around it.** On Windows the edge around the page is see-through, for the window's shadow. Under Wine it's solid black, and so are the page's rounded corners. The prefix gets set to give the launcher 32-bit windows so the corners keep their transparency, and a helper trims the black edge off. It can only measure the edge once the page has drawn, so on the very first launch the frame shows for a few seconds; after that it remembers where the edge was and trims it as the window opens.
- **No mouse cursor over it.** The page's cursors belong to another process and Wine can't show them, so the pointer disappears over the launcher. The helper gives it a normal arrow. It's always the arrow, but at least it's there.
- **It goes black when you move it to another screen**, and stays that way until you click into something else. The helper waits for the window to stop moving, tells Wine to redraw it, and keeps at it until it's back. It still flashes black while you drag it across screens.
- **The game opens to a white screen.** That's not the game, it's the notice popup on top of it, fullscreen and blank. The game's popups are a separate browser that hands each page over as a shared GPU texture, and Proton's Wine can't open those. The game has a switch of its own for drawing them on the CPU instead, an empty `usebitmap.flag` next to `KRWebClient.exe`, so the wrapper puts that in the game folder on every launch. The game folder only exists once the launcher has started downloading it, so this lands from the launch after that. It also fixes the other in-game web pages, like Convene history, which used to sit on a solid black background and now get the same dimmed backdrop as on Windows.

## Requirements

- Steam on Linux with a Proton build set for the game. I've only tested Proton-CachyOS 11.0 (20260703). Others will probably work, and I'd like to hear either way.
- `python3`, `libX11` and `libXext` for the helper. Pretty much every desktop has them already. Without them the launcher still works, just with the black frame, no cursor and no redraw.
- Mine is Arch with KDE Plasma 6.8 on Wayland and an NVIDIA card (driver 615.78). Proton runs on Xwayland there, which is what the helper talks to.

## Setup

Clone it somewhere with no spaces in the path, then run `wuwa-launch` on its own:

```
git clone https://github.com/Alphaproject1998/linux-game-fixes.git ~/.local/share/linux-game-fixes
~/.local/share/linux-game-fixes/wuthering-waves/wuwa-launch
```

That prints the launch options with the full path filled in, something like:

```
/home/you/.local/share/linux-game-fixes/wuthering-waves/wuwa-launch %command%
```

In Steam, right click Wuthering Waves, open Properties and paste it into Launch Options on the General tab. If you already have launch options, it goes anywhere before `%command%`:

```
gamemoderun mangohud /home/you/.local/share/linux-game-fixes/wuthering-waves/wuwa-launch %command%
```

Then launch it from Steam like normal. If it's the very first time the game has been launched, Proton only makes the prefix during that launch, so the fixes that go into the prefix only land from the second one. Close the launcher and start it again.

## Updating

```
git -C ~/.local/share/linux-game-fixes pull
```

The next launch copies over whatever changed. Nothing in Steam needs touching.

## Options

These go in the launch options, in front of the wrapper: `WUWA_SCREEN_DEPTH=0 /home/you/.../wuwa-launch %command%`.

- `WUWA_LAUNCHER_DECK=0` starts the launcher in its normal mode. That's the invisible window, so it's only useful for checking whether a newer Proton has fixed it.
- `WUWA_LAUNCHER_WINDOW=0` turns the helper off: no edge trim, no cursor and no redraw after moving.
- `WUWA_LAUNCHER_WINDOW_ARGS` passes options to the helper, like `WUWA_LAUNCHER_WINDOW_ARGS=--repaint-tries=20`. `python3 launcher-window.py --help` lists them.
- `WUWA_SCREEN_DEPTH=0` takes the 32-bit window setting back out of the prefix.
- `WUWA_WEBVIEW_BITMAP=0` takes `usebitmap.flag` back out of the game folder, so the popups go back to the GPU.

## Removing it

Take it out of the launch options. If you want the prefix and game folder back exactly how they were, launch once with `WUWA_SCREEN_DEPTH=0 WUWA_WEBVIEW_BITMAP=0` first. The two DLLs it added stay in the prefix, but the startup hook does nothing without the wrapper, and the other one only fills in something Proton's Wine is missing.

## Files

- `wuwa-launch` is the launch option. It sets up the prefix, starts the helper and hands over to Steam's own command.
- `deck-hook/` is the startup hook. The DLL is already built, but `build.sh` rebuilds it from `DeckHook.cs` with the C# compiler that comes with every Proton build, so you don't need to install anything for that either.
- `wine/wminet_utils.dll` comes from Arch's `wine` 11.21 package, unchanged. It's Wine's own code under the LGPL 2.1 or later, and the source is at [winehq.org](https://www.winehq.org/).
- `launcher-window.py` is the helper: the edge trim, the cursor and the redraw.

## When something's wrong

The launcher logs to `pfx/drive_c/users/steamuser/AppData/Roaming/KRLauncher/C50019/log` in the game's prefix (`steamapps/compatdata/3513350`), but they're scrambled: every byte is XORed with `0x09`. This reads one:

```
python3 -c "import sys; sys.stdout.write(bytes(b ^ 9 for b in open(sys.argv[1], 'rb').read()).decode(errors='replace'))" App_<date>.log
```

For Wine's side, put `PROTON_LOG=1` at the start of the launch options and it writes `~/steam-3513350.log`. Take it back out after, it grows quickly.

If something breaks, open an issue with what happened, your Proton build and anything from those logs that looks relevant.

## Changelog

### 1.0.0 (2026-11-12)

First release: the Steam Deck mode hook for the invisible window, Wine's `wminet_utils.dll` for the space info error, 32-bit windows and the edge trim for the black frame, the cursor, the redraw after moving screens, and `usebitmap.flag` for the white popups in game.

## About AI

This was built with some help from an AI coding assistant. It did most of the digging through Kuro's launcher, Proton, Wine and game files, including finding the Steam Deck check and the `usebitmap.flag` switch. I tested every change on my own desktop. The launcher's internals are hard to check by eye, so if anything looks wrong, please open an issue.
