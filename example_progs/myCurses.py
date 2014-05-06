import curses
import time
import curses.textpad

def fill_area(area):
	#  These loops fill the pad with letters; this is
	# explained in the next section
	for y in range(0, 100):
		for x in range(0, 100):
			try:
				area.addch(y,x, ord('a') + (x*x+y*y) % 26)
			except curses.error:
				pass

def floodFill(area, val1, val2):
	nlines, ncols = area.getmaxyx()
	for y in range(nlines):
		for x in range(ncols):
			try:
				if (((x+1)+(y+1)) % 2) is 0:
					area.addch(y, x, val1)
				else:
					area.addch(y, x, val2)
			except curses.error:
				pass

def refresh_pad(pad, pad_pos, pad_loca, newpad_area, pad_demin):
	pminrow = min((newpad_area['nlines'] - pad_demin['nlines'] - 1), pad_loca['pad_y'])
	pmincol = min((newpad_area['ncols'] - pad_demin['ncols'] - 1), pad_loca['pad_x'])
	smaxrow = pad_pos['begin_y'] + pad_demin['nlines'] - 1
	smaxcol = pad_pos['begin_x'] + pad_demin['ncols'] - 1
	pad.refresh( pminrow, pmincol, pad_pos['begin_y'], pad_pos['begin_x'], smaxrow, smaxcol )

def refresh_mbar(mbar):
	mbar.erase()
	mbar.refresh()

def refresh_work_area(work_area):
	work_area.erase()
	#floodFill(work_area, curses.ACS_CKBOARD, curses.ACS_CKBOARD)
	work_area_demin = work_area.getmaxyx()
	msg = "This is a String"
	work_area.addstr(((work_area_demin[0] / 2) - 1), ((work_area_demin[1] / 2) - (len(msg)/2)), msg)
	msg = "Positioned String"
	work_area.addstr(((work_area_demin[0] / 2) + 0), ((work_area_demin[1] / 2) - (len(msg)/2)), msg)
	msg = "Reverse Styled String"
	work_area.addstr(((work_area_demin[0] / 2) + 1), ((work_area_demin[1] / 2) - (len(msg)/2)), msg, curses.A_REVERSE)
	work_area.refresh()

def refresh_screen(screen, work_area, pad, mbar, pad_pos, pad_loca, newpad_area, pad_demin):
	msg = 'Pad X position: {0:<3}   Pad Y position: {1:<3}   '.format(pad_loca['pad_x'], pad_loca['pad_y'])
	screen.addstr(pad_pos['begin_y'] - 2, pad_pos['begin_x'] - 1, msg)
	screen.refresh()
	refresh_pad(pad, pad_pos, pad_loca, newpad_area, pad_demin)
	refresh_mbar(mbar)
	refresh_work_area(work_area)

def main(screen):
	screen_demin = screen.getmaxyx()
	floodFill(screen, curses.ACS_BULLET, ord(' '))
	
	subwin_area = {
		'nlines': 24,
		'ncols': 80,
		'begin_y': 4,
		'begin_x': 4,
	}
	scr_border = screen.subwin(
		subwin_area['nlines'], subwin_area['ncols'],
		subwin_area['begin_y'], subwin_area['begin_x'] )
	scr_border.box()
	scr_border.hline(2, 1, curses.ACS_HLINE, 78)
	scr_border.addch(2, 0, curses.ACS_LTEE)
	scr_border.addch(2, (subwin_area['ncols'] - 1), curses.ACS_RTEE)
	# menubar screen
	mbar = screen.subwin(
		1, (subwin_area['ncols'] - 2),
		(subwin_area['begin_y'] + 1), (subwin_area['begin_x'] + 1) )
	mbar.erase()
	# work screen
	work_area = screen.subwin(
		(subwin_area['nlines']-4), (subwin_area['ncols']-2),
		(subwin_area['begin_y'] + 3), (subwin_area['begin_x'] + 1) )
	
	newpad_area = {'nlines': 100, 'ncols': 100,}
	pad = curses.newpad(
		newpad_area['nlines'], newpad_area['ncols'])
	fill_area(pad)
	pad_loca = {'pad_y': 0, 'pad_x': 0}
	pad_pos = {'begin_y': (subwin_area['begin_y'] + subwin_area['nlines'] + 4), 'begin_x': 5}
	pad_demin = {'nlines': subwin_area['nlines'] - 2, 'ncols': subwin_area['ncols'] - 2 }
	curses.textpad.rectangle(screen,
		pad_pos['begin_y'] - 1, pad_pos['begin_x'] - 1,
		(pad_pos['begin_y'] + pad_demin['nlines']),
		(pad_pos['begin_x'] + pad_demin['ncols']))

	while True:
		refresh_screen(screen, work_area, pad, mbar, pad_pos, pad_loca, newpad_area, pad_demin)
		event = screen.getch() 
		if event == ord("q"):
			break
		elif event == curses.KEY_UP:
			pad_loca['pad_y'] = max(0, pad_loca['pad_y'] - 1)
		elif event == curses.KEY_DOWN:
			pad_loca['pad_y'] = min((newpad_area['nlines'] - pad_demin['nlines'] - 1), pad_loca['pad_y'] + 1)
		elif event == curses.KEY_LEFT:
			pad_loca['pad_x'] = max(0, pad_loca['pad_x'] - 1)
		elif event == curses.KEY_RIGHT:
			pad_loca['pad_x'] = min((newpad_area['ncols'] - pad_demin['ncols'] - 1), pad_loca['pad_x'] + 1)



if __name__ == '__main__':
	curses.wrapper(main)
