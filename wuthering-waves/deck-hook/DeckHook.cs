using System;
using System.Diagnostics;
using System.Threading;

internal class StartupHook
{
	// In Steam Deck mode the launcher skips its transparent window, which Wine shows as nothing at all.
	public static void Initialize()
	{
		string name = Process.GetCurrentProcess().ProcessName;
		if (!name.Equals("launcher_main", StringComparison.OrdinalIgnoreCase) && !name.Equals("launcher_updater", StringComparison.OrdinalIgnoreCase)) return;
		if (Environment.GetEnvironmentVariable("WUWA_LAUNCHER_DECK") != "1") return;

		Environment.SetEnvironmentVariable("SteamDeck", "1");
		Thread watcher = new Thread(ClearOnceShown);
		watcher.IsBackground = true;
		watcher.Start();
	}

	// The launcher reads the flag once, before its window exists, and caches it.
	// Anything it starts later, the game included, has to come out without it.
	private static void ClearOnceShown()
	{
		Process self = Process.GetCurrentProcess();
		for (int waited = 0; waited < 120000; waited += 200)
		{
			self.Refresh();
			if (self.MainWindowHandle != IntPtr.Zero) break;
			Thread.Sleep(200);
		}
		Environment.SetEnvironmentVariable("SteamDeck", null);
		Environment.SetEnvironmentVariable("SteamOS", null);
	}
}
