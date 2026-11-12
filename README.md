# linux-game-fixes

**Fixes for games I couldn't get running on Linux any of the normal ways.**

Each game has its own folder with everything for it: the script, a README with what was broken and what fixed it, how to set it up, and the options for tweaking it. Pick the game, read its README, and ignore the rest.

- [Star Rail](star-rail/README.md), through a bare Proton prefix: no Steam Linux Runtime container and no gamescope, the way ProtonPlus' "Run custom EXE" does it. Fixes the game not starting and every video locking up on black.
- [Wuthering Waves](wuthering-waves/README.md), the Steam version since 3.8, through a launch option in Steam. Fixes Kuro's launcher being invisible, black backgrounds, and the game opening to a white screen once it's downloaded.

## Why this is here

I couldn't find anything that actually worked for me. Plenty of threads with the same symptoms, nothing that fixed it on my machine, so I worked it out myself and put it up here in case someone else is stuck in the same place.

I'm not a Proton or Wine expert, I just play these games. There's probably a better way to do some of it, and if a Proton update makes any of this pointless I'd like to know.

## Something not working?

Every README lists the machine it was worked out on, and that's the only one I can speak for. If it works on something different, or doesn't, open an issue with what happened and your Proton build and I'll add it.

## About AI

These were worked out with some help from an AI coding assistant, and each game's README says what it did for that one. I tested every change on my own machine.

## Licence

GNU General Public License, version 2 or (at your option) any later version. See [LICENSE](LICENSE). `wuthering-waves/wine/wminet_utils.dll` is Wine's own, under the LGPL 2.1 or later.
