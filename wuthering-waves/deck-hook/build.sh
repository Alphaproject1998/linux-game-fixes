#!/usr/bin/env bash
# usage: build.sh [path to a Proton build, default the first one found in Steam's folders]
# Every Proton build's wine-mono carries Roslyn's csc.exe, so this needs nothing installed.

here="$(dirname "$(readlink -f "$0")")"

find_csc() {
	find "$1/files/share/wine/mono" -path '*/lib/mono/4.5/csc.exe' 2>/dev/null | sort | tail -n 1
}

if [[ -n "$1" ]]; then
	proton_dir="$1"
else
	for proton_dir in "$HOME/.local/share/Steam/compatibilitytools.d"/* "$HOME/.local/share/Steam/steamapps/common"/Proton*; do
		[[ -n "$(find_csc "$proton_dir")" ]] && break
	done
fi

csc="$(find_csc "$proton_dir")"
if [[ -z "$csc" ]]; then
	echo "no Proton build with wine-mono's csc.exe found, pass one: build.sh /path/to/proton" >&2
	exit 1
fi

windows_path() {
	local path="$1"
	echo "Z:${path//\//\\}"
}

build_prefix="$(mktemp -d)"
cleanup() {
	WINEPREFIX="$build_prefix" "$proton_dir/files/bin/wineserver" -k 2>/dev/null
	rm -rf "$build_prefix"
}
trap cleanup EXIT

export WINEPREFIX="$build_prefix" WINEDEBUG=-all WINEDLLOVERRIDES='mshtml='
"$proton_dir/files/bin/wine" "$(windows_path "$csc")" /nologo /target:library /optimize+ /deterministic \
	"/out:$(windows_path "$here/DeckHook.dll")" "$(windows_path "$here/DeckHook.cs")" || exit 1
sha256sum "$here/DeckHook.dll"
