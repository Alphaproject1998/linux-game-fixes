#!/usr/bin/env python3
import argparse
import ctypes
import ctypes.util
import json
import os
import select
import sys
import time

LAUNCHER_EXES = ('launcher_main.exe', 'launcher_updater.exe')
XC_LEFT_PTR = 68
SHAPE_BOUNDING = 0
SHAPE_INPUT = 2
SHAPE_SET = 0
ZPIXMAP = 2
IS_VIEWABLE = 2
EXPOSE = 12
MAP_NOTIFY = 19
CONFIGURE_NOTIFY = 22
EXPOSURE_MASK = 1 << 15
STRUCTURE_NOTIFY_MASK = 1 << 17
SUBSTRUCTURE_NOTIFY_MASK = 1 << 19
REPAINT_RETRY = 0.5
MIN_INSET = 2
MAX_INSET = 48
MEASURE_TRIES = 120
DEFAULT_SHAPE_CACHE = os.path.join(os.environ.get('XDG_CACHE_HOME') or os.path.expanduser('~/.cache'), 'linux-game-fixes', 'wuwa-launcher-shapes.json')


class XWindowAttributes(ctypes.Structure):
	_fields_ = [
		('x', ctypes.c_int),
		('y', ctypes.c_int),
		('width', ctypes.c_int),
		('height', ctypes.c_int),
		('border_width', ctypes.c_int),
		('depth', ctypes.c_int),
		('visual', ctypes.c_void_p),
		('root', ctypes.c_ulong),
		('class_', ctypes.c_int),
		('bit_gravity', ctypes.c_int),
		('win_gravity', ctypes.c_int),
		('backing_store', ctypes.c_int),
		('backing_planes', ctypes.c_ulong),
		('backing_pixel', ctypes.c_ulong),
		('save_under', ctypes.c_int),
		('colormap', ctypes.c_ulong),
		('map_installed', ctypes.c_int),
		('map_state', ctypes.c_int),
		('all_event_masks', ctypes.c_long),
		('your_event_mask', ctypes.c_long),
		('do_not_propagate_mask', ctypes.c_long),
		('override_redirect', ctypes.c_int),
		('screen', ctypes.c_void_p),
	]


class XClassHint(ctypes.Structure):
	_fields_ = [('res_name', ctypes.c_void_p), ('res_class', ctypes.c_void_p)]


class XRectangle(ctypes.Structure):
	_fields_ = [('x', ctypes.c_short), ('y', ctypes.c_short), ('width', ctypes.c_ushort), ('height', ctypes.c_ushort)]


class XConfigureEvent(ctypes.Structure):
	_fields_ = [
		('type', ctypes.c_int),
		('serial', ctypes.c_ulong),
		('send_event', ctypes.c_int),
		('display', ctypes.c_void_p),
		('event', ctypes.c_ulong),
		('window', ctypes.c_ulong),
		('x', ctypes.c_int),
		('y', ctypes.c_int),
		('width', ctypes.c_int),
		('height', ctypes.c_int),
	]


class XExposeEvent(ctypes.Structure):
	_fields_ = [
		('type', ctypes.c_int),
		('serial', ctypes.c_ulong),
		('send_event', ctypes.c_int),
		('display', ctypes.c_void_p),
		('window', ctypes.c_ulong),
		('x', ctypes.c_int),
		('y', ctypes.c_int),
		('width', ctypes.c_int),
		('height', ctypes.c_int),
		('count', ctypes.c_int),
	]


class XEvent(ctypes.Union):
	_fields_ = [('type', ctypes.c_int), ('configure', XConfigureEvent), ('expose', XExposeEvent), ('pad', ctypes.c_long * 24)]


ERROR_HANDLER = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)


def load_x11():
	x11 = ctypes.CDLL(ctypes.util.find_library('X11'))
	xext = ctypes.CDLL(ctypes.util.find_library('Xext'))
	x11.XOpenDisplay.restype = ctypes.c_void_p
	x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
	x11.XDefaultRootWindow.restype = ctypes.c_ulong
	x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
	x11.XInternAtom.restype = ctypes.c_ulong
	x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
	x11.XQueryTree.argtypes = [
		ctypes.c_void_p,
		ctypes.c_ulong,
		ctypes.POINTER(ctypes.c_ulong),
		ctypes.POINTER(ctypes.c_ulong),
		ctypes.POINTER(ctypes.POINTER(ctypes.c_ulong)),
		ctypes.POINTER(ctypes.c_uint),
	]
	x11.XGetWindowAttributes.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(XWindowAttributes)]
	x11.XGetClassHint.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(XClassHint)]
	x11.XGetWindowProperty.argtypes = [
		ctypes.c_void_p,
		ctypes.c_ulong,
		ctypes.c_ulong,
		ctypes.c_long,
		ctypes.c_long,
		ctypes.c_int,
		ctypes.c_ulong,
		ctypes.POINTER(ctypes.c_ulong),
		ctypes.POINTER(ctypes.c_int),
		ctypes.POINTER(ctypes.c_ulong),
		ctypes.POINTER(ctypes.c_ulong),
		ctypes.POINTER(ctypes.c_void_p),
	]
	x11.XGetImage.restype = ctypes.c_void_p
	x11.XGetImage.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong, ctypes.c_int]
	x11.XGetPixel.restype = ctypes.c_ulong
	x11.XGetPixel.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
	x11.XDestroyImage.argtypes = [ctypes.c_void_p]
	x11.XFree.argtypes = [ctypes.c_void_p]
	x11.XCreateFontCursor.restype = ctypes.c_ulong
	x11.XCreateFontCursor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
	x11.XDefineCursor.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong]
	x11.XFlush.argtypes = [ctypes.c_void_p]
	x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
	x11.XSetErrorHandler.argtypes = [ERROR_HANDLER]
	x11.XConnectionNumber.argtypes = [ctypes.c_void_p]
	x11.XSelectInput.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_long]
	x11.XPending.argtypes = [ctypes.c_void_p]
	x11.XNextEvent.argtypes = [ctypes.c_void_p, ctypes.POINTER(XEvent)]
	x11.XSendEvent.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_long, ctypes.POINTER(XEvent)]
	xext.XShapeCombineRectangles.argtypes = [
		ctypes.c_void_p,
		ctypes.c_ulong,
		ctypes.c_int,
		ctypes.c_int,
		ctypes.c_int,
		ctypes.POINTER(XRectangle),
		ctypes.c_int,
		ctypes.c_int,
		ctypes.c_int,
	]
	xext.XShapeQueryExtents.argtypes = [ctypes.c_void_p, ctypes.c_ulong] + [ctypes.POINTER(ctypes.c_int)] * 4 + [ctypes.POINTER(ctypes.c_uint)] * 2 + [ctypes.POINTER(ctypes.c_int)] * 4 + [ctypes.POINTER(ctypes.c_uint)] * 2
	return x11, xext


class LauncherWindows:
	def __init__(self, appid, verbose, repaint_after, repaint_tries, shape_cache):
		self.x11, self.xext = load_x11()
		# Wine destroys windows between our query and our use of them, and the BadWindow that follows would end us under Xlib's default handler.
		self._ignore_errors = ERROR_HANDLER(lambda display, event: 0)
		self.x11.XSetErrorHandler(self._ignore_errors)
		self.display = self.x11.XOpenDisplay(None)
		if not self.display:
			raise RuntimeError('cannot open the X display')
		self.root = self.x11.XDefaultRootWindow(self.display)
		self.pid_atom = self.x11.XInternAtom(self.display, b'_NET_WM_PID', 0)
		self.cardinal_atom = self.x11.XInternAtom(self.display, b'CARDINAL', 0)
		self.arrow = self.x11.XCreateFontCursor(self.display, XC_LEFT_PTR)
		self.wanted_class = f'steam_app_{appid}'.encode() if appid else None
		self.verbose = verbose
		self.repaint_after = repaint_after
		self.repaint_tries = repaint_tries
		self.connection = self.x11.XConnectionNumber(self.display)
		self.handled = {}
		self.geometry = {}
		self.repaints = {}
		self.shape_cache = shape_cache
		self.known_shapes = self.load_shapes()
		self.x11.XSelectInput(self.display, self.root, SUBSTRUCTURE_NOTIFY_MASK)

	def log(self, message):
		if self.verbose:
			print(f'launcher-window: {message}', file=sys.stderr, flush=True)

	def top_level_windows(self):
		root_return = ctypes.c_ulong()
		parent_return = ctypes.c_ulong()
		children = ctypes.POINTER(ctypes.c_ulong)()
		count = ctypes.c_uint()
		if not self.x11.XQueryTree(self.display, self.root, ctypes.byref(root_return), ctypes.byref(parent_return), ctypes.byref(children), ctypes.byref(count)):
			return []
		windows = [children[index] for index in range(count.value)]
		if children:
			self.x11.XFree(children)
		return windows

	def window_class(self, window):
		hint = XClassHint()
		if not self.x11.XGetClassHint(self.display, window, ctypes.byref(hint)):
			return None
		value = ctypes.string_at(hint.res_class) if hint.res_class else None
		for pointer in (hint.res_name, hint.res_class):
			if pointer:
				self.x11.XFree(pointer)
		return value

	def window_pid(self, window):
		actual_type = ctypes.c_ulong()
		actual_format = ctypes.c_int()
		item_count = ctypes.c_ulong()
		bytes_after = ctypes.c_ulong()
		data = ctypes.c_void_p()
		status = self.x11.XGetWindowProperty(
			self.display, window, self.pid_atom, 0, 1, 0, self.cardinal_atom,
			ctypes.byref(actual_type), ctypes.byref(actual_format), ctypes.byref(item_count), ctypes.byref(bytes_after), ctypes.byref(data),
		)
		if status != 0 or not data.value:
			return None
		pid = ctypes.cast(data, ctypes.POINTER(ctypes.c_ulong))[0] if item_count.value else None
		self.x11.XFree(data)
		return pid

	def is_launcher_process(self, pid):
		try:
			with open(f'/proc/{pid}/cmdline', 'rb') as handle:
				command = handle.read().lower()
		except OSError:
			return False
		return any(exe.encode() in command for exe in LAUNCHER_EXES)

	def row_pixels(self, window, x, y, width, height):
		image = self.x11.XGetImage(self.display, window, x, y, width, height, 0xFFFFFFFF, ZPIXMAP)
		if not image:
			return None
		pixels = [self.x11.XGetPixel(image, column, row) for row in range(height) for column in range(width)]
		self.x11.XDestroyImage(image)
		return pixels

	def clear_pixels(self, window, x, y, size):
		pixels = self.row_pixels(window, x, y, size, size)
		if not pixels:
			return None
		return [(x + index % size, y + index // size) for index, pixel in enumerate(pixels) if pixel >> 24 == 0]

	def content_rect(self, window, width, height):
		# WPF fills the space around the webview with an opaque near-black, the area the Windows build leaves see-through for its shadow.
		# The webview's own rounded corners come through with real alpha, so its edges are where the fully transparent corner pixels sit.
		corner = MAX_INSET + 16
		margin = self.row_pixels(window, 0, 0, 1, 1)
		if not margin or margin[0] >> 24 != 0xff:
			return None
		top_left = self.clear_pixels(window, 0, 0, corner)
		bottom_right = self.clear_pixels(window, width - corner, height - corner, corner)
		if not top_left or not bottom_right:
			return None
		left = min(x for x, _ in top_left)
		top = min(y for _, y in top_left)
		right = max(x for x, _ in bottom_right)
		bottom = max(y for _, y in bottom_right)
		insets = (left, top, width - 1 - right, height - 1 - bottom)
		if not all(MIN_INSET <= inset <= MAX_INSET for inset in insets):
			return None
		return left, top, right - left + 1, bottom - top + 1

	def is_shaped(self, window):
		values = [ctypes.c_int() for _ in range(4)] + [ctypes.c_uint() for _ in range(2)] + [ctypes.c_int() for _ in range(4)] + [ctypes.c_uint() for _ in range(2)]
		if not self.xext.XShapeQueryExtents(self.display, window, *(ctypes.byref(value) for value in values)):
			return False
		return bool(values[0].value)

	def apply_shape(self, window, rect):
		rectangle = XRectangle(*rect)
		for kind in (SHAPE_BOUNDING, SHAPE_INPUT):
			self.xext.XShapeCombineRectangles(self.display, window, kind, 0, 0, ctypes.byref(rectangle), 1, SHAPE_SET, 0)

	def load_shapes(self):
		if not self.shape_cache:
			return {}
		try:
			with open(self.shape_cache) as handle:
				shapes = json.load(handle)
		except (OSError, ValueError):
			return {}
		return shapes if isinstance(shapes, dict) else {}

	def remember_shape(self, size, rect):
		key = f'{size[0]}x{size[1]}'
		if not self.shape_cache or self.known_shapes.get(key) == list(rect):
			return
		self.known_shapes[key] = list(rect)
		try:
			os.makedirs(os.path.dirname(self.shape_cache), exist_ok=True)
			with open(self.shape_cache, 'w') as handle:
				json.dump(self.known_shapes, handle)
		except OSError as error:
			self.log(f'cannot save {self.shape_cache}: {error}')

	def known_shape(self, size):
		rect = self.known_shapes.get(f'{size[0]}x{size[1]}')
		if not isinstance(rect, list) or len(rect) != 4 or not all(isinstance(value, int) for value in rect):
			return None
		left, top, width, height = rect
		insets = (left, top, size[0] - left - width, size[1] - top - height)
		return tuple(rect) if all(MIN_INSET <= inset <= MAX_INSET for inset in insets) else None

	def scan(self):
		seen = set()
		for window in self.top_level_windows():
			attributes = XWindowAttributes()
			if not self.x11.XGetWindowAttributes(self.display, window, ctypes.byref(attributes)):
				continue
			if attributes.map_state != IS_VIEWABLE or attributes.width < 400 or attributes.height < 300:
				continue
			if self.wanted_class and self.window_class(window) != self.wanted_class:
				continue
			pid = self.window_pid(window)
			if not pid or not self.is_launcher_process(pid):
				continue
			seen.add(window)
			if window not in self.geometry:
				self.x11.XSelectInput(self.display, window, STRUCTURE_NOTIFY_MASK)
				self.geometry[window] = (attributes.x, attributes.y, attributes.width, attributes.height)
			# Wine routes WebView2's cursor to the launcher's process, which can't read another process's cursor handles and leaves an empty one.
			self.x11.XDefineCursor(self.display, window, self.arrow)
			size = (attributes.width, attributes.height)
			state = self.handled.get(window)
			if state and state['size'] == size and state['rect'] and self.is_shaped(window):
				if state['measured'] or state['tries'] >= MEASURE_TRIES:
					continue
			tries = state['tries'] + 1 if state and state['size'] == size else 1
			rect = self.content_rect(window, *size)
			if rect:
				self.remember_shape(size, rect)
				if state and state['rect'] == rect and self.is_shaped(window):
					state['measured'] = True
					continue
				self.handled[window] = {'size': size, 'rect': rect, 'measured': True, 'tries': tries}
				self.apply_shape(window, rect)
				self.log(f'shaped {window:#x} to {rect}')
				continue
			# The edge can only be measured once the webview has drawn its corners, which takes a few seconds after the window opens.
			# Until then, the edge measured on an earlier launch keeps the black margin off from the first frame.
			rect = self.known_shape(size)
			self.handled[window] = {'size': size, 'rect': rect, 'measured': False, 'tries': tries}
			if rect and not self.is_shaped(window):
				self.apply_shape(window, rect)
				self.log(f'shaped {window:#x} to {rect} from an earlier launch')
		for window in list(self.handled):
			if window not in seen:
				del self.handled[window]
				self.geometry.pop(window, None)
				self.repaints.pop(window, None)
		self.x11.XFlush(self.display)

	def read_events(self):
		event = XEvent()
		mapped = False
		while self.x11.XPending(self.display):
			self.x11.XNextEvent(self.display, ctypes.byref(event))
			if event.type == MAP_NOTIFY:
				mapped = True
				continue
			if event.type != CONFIGURE_NOTIFY or event.configure.window not in self.geometry:
				continue
			configure = event.configure
			geometry = (configure.x, configure.y, configure.width, configure.height)
			if geometry == self.geometry[configure.window]:
				continue
			self.geometry[configure.window] = geometry
			if self.repaint_after > 0 and self.repaint_tries > 0:
				self.repaints[configure.window] = [time.monotonic() + self.repaint_after, self.repaint_tries]
		return mapped

	def mostly_black(self, window):
		state = self.handled.get(window)
		if state and state['rect']:
			x, y, width, height = state['rect']
		else:
			_, _, width, height = self.geometry[window]
			x, y, width, height = MAX_INSET, MAX_INSET, width - 2 * MAX_INSET, height - 2 * MAX_INSET
		image = self.x11.XGetImage(self.display, window, x, y, width, height, 0xFFFFFFFF, ZPIXMAP)
		if not image:
			return False
		points = [(width * column // 32, height * row // 20) for row in range(20) for column in range(32)]
		black = 0
		for column, row in points:
			pixel = self.x11.XGetPixel(image, column, row)
			if all((pixel >> shift) & 0xff < 6 for shift in (0, 8, 16)):
				black += 1
		self.x11.XDestroyImage(image)
		return black > len(points) // 2

	def repaint_due(self, now):
		# Moving the launcher to another monitor leaves it black until focus changes, apart from whatever the page animates.
		# WPF rebuilds its swapchain for each monitor, so the first Expose can land before there's a frame to show, hence the retries.
		for window, (due, tries_left) in list(self.repaints.items()):
			if now < due:
				continue
			if tries_left < self.repaint_tries and not self.mostly_black(window):
				del self.repaints[window]
				continue
			_, _, width, height = self.geometry[window]
			event = XEvent()
			event.expose.type = EXPOSE
			event.expose.window = window
			event.expose.width = width
			event.expose.height = height
			self.x11.XSendEvent(self.display, window, 0, EXPOSURE_MASK, ctypes.byref(event))
			self.log(f'repainted {window:#x} after a move, try {self.repaint_tries - tries_left + 1}')
			if tries_left > 1:
				self.repaints[window] = [now + REPAINT_RETRY, tries_left - 1]
			else:
				del self.repaints[window]
		self.x11.XFlush(self.display)

	def wait(self, timeout):
		deadline = time.monotonic() + timeout
		while True:
			if self.read_events():
				return
			now = time.monotonic()
			self.repaint_due(now)
			remaining = deadline - now
			if remaining <= 0:
				return
			if self.repaints:
				remaining = min(remaining, min(due for due, _ in self.repaints.values()) - now)
			select.select([self.connection], [], [], max(remaining, 0))


def parent_alive(pid):
	if not pid:
		return True
	return os.path.exists(f'/proc/{pid}')


def parent_has_company(pid):
	own = os.getpid()
	for entry in os.scandir('/proc'):
		if not entry.name.isdigit() or int(entry.name) == own:
			continue
		try:
			with open(f'/proc/{entry.name}/stat') as stat:
				parent = int(stat.read().rsplit(')', 1)[1].split()[1])
		except (OSError, ValueError, IndexError):
			continue
		if parent == pid:
			return True
	return False


def main():
	parser = argparse.ArgumentParser(description="Trim the Wuthering Waves launcher's opaque margin, give it a visible cursor and redraw it after it moves screens, under Wine.")
	parser.add_argument('--appid', default=os.environ.get('SteamAppId', ''))
	parser.add_argument('--parent', type=int, default=0, help='exit once this process is gone, or has no children left but this helper')
	parser.add_argument('--interval', type=float, default=0.5, help='seconds between looks for new launcher windows')
	parser.add_argument('--repaint-after', type=float, default=0.4, help='seconds a moved launcher has to sit still before it is told to redraw, 0 to never')
	parser.add_argument('--repaint-tries', type=int, default=10, help='redraws to send, half a second apart, while a moved launcher still reads mostly black')
	parser.add_argument('--shape-cache', default=DEFAULT_SHAPE_CACHE, help="where the measured edge is kept, so it can be trimmed before the page draws on later launches, '' to not keep it")
	parser.add_argument('--once', action='store_true', help='scan a single time and exit')
	parser.add_argument('--verbose', action='store_true')
	arguments = parser.parse_args()

	if not os.environ.get('DISPLAY'):
		return 0
	try:
		windows = LauncherWindows(arguments.appid, arguments.verbose, arguments.repaint_after, arguments.repaint_tries, arguments.shape_cache)
	except (OSError, RuntimeError) as error:
		print(f'launcher-window: {error}', file=sys.stderr)
		return 1

	# Under Steam the parent is the reaper, which waits for every child, this helper included, before telling Steam the game has closed.
	# It's a subreaper too, so the game's orphans land back on it, and once this helper is all it has left, the game is gone.
	had_company = False
	while parent_alive(arguments.parent):
		if arguments.parent:
			has_company = parent_has_company(arguments.parent)
			if had_company and not has_company:
				break
			had_company = had_company or has_company
		windows.scan()
		if arguments.once:
			break
		windows.wait(arguments.interval)
	return 0


if __name__ == '__main__':
	sys.exit(main())
