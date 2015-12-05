'''Manage X-Plane input device settings'''

# The MIT License (MIT)
# Copyright (c) 2015 Stefan Steinheimer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Directory in which X-Plane is installed
XPLANE_DIR = 'C:/Games/X-Plane 10'

# Directory in which to save files
XPCTRL_DIR = 'C:/Users/Public/Documents/xpctrl'

# Don't touch anything below unless you know what you're doing
import fileinput
import os
import shutil
import subprocess
import tkinter as tk
import tkinter.messagebox as tkmessagebox
from pathlib import Path

# Path constants
PREFS_DIR = 'Output/preferences'
KEYS_FILE = 'X-Plane Keys.prf'
PREFS_FILE = 'X-Plane.prf'
JOY_PREFIX = '_joy'
XPLANE_EXE_FILE = 'X-Plane.exe'

XPPath = Path(XPLANE_DIR)
SavePath = Path(XPCTRL_DIR)
PrefsPath = XPPath / PREFS_DIR
KeysFile = PrefsPath / KEYS_FILE
PrefsFile = PrefsPath / PREFS_FILE


def save(name):
	'''Saves a profile as name'''
	# simply copy the keys file
	DstPath = SavePath / name
	KeysDstFile =  DstPath / KEYS_FILE
	PrefsDstFile = DstPath / PREFS_FILE
	try:
		DstPath.mkdir(parents=True)
	except FileExistsError:
		pass
	shutil.copy2(str(KeysFile), str(KeysDstFile))
	# extract the joystick config from prefs
	with PrefsFile.open(mode='r') as src:
		joylines = [line for line in src.readlines() if line.startswith(JOY_PREFIX)]
	with PrefsDstFile.open(mode='w') as dst:
		dst.writelines(joylines)


def load(name):
	'''Loads a profile into X-Plane'''
	SrcPath = SavePath / name
	KeysSrcFile =  SrcPath / KEYS_FILE
	PrefsSrcFile = SrcPath / PREFS_FILE
	if not SrcPath.is_dir():
		raise RuntimeError("Name does not exist: %r" % name)
	# copy the keys file
	shutil.copy2(str(KeysSrcFile), str(KeysFile))
	# inject the joystick config into prefs
	with PrefsSrcFile.open(mode='r') as src:
		joylines = [line for line in src.readlines() if line.startswith(JOY_PREFIX)]
	with PrefsFile.open(mode='r') as prefs:
		nonjoylines = [line for line in prefs.readlines() if not line.startswith(JOY_PREFIX)]
	with PrefsFile.open(mode='w') as dst:
		dst.writelines(nonjoylines)
		dst.writelines(joylines)


def list():
	'''Returns a list of names of saved profiles'''
	return [p.name for p in SavePath.iterdir() if p.is_dir()]


def remove(name):
	'''Removes a profile'''
	DelPath = SavePath / name
	if not DelPath.is_dir():
		raise RuntimeError("Name does not exist: %r" % name)
	shutil.rmtree(str(DelPath))


def launch(name=None):
	'''Launches X-Plane with the specified profile'''
	if name is not None:
		load(name)
	# launch X-Plane
	os.chdir(str(XPPath))
	subprocess.run([XPLANE_EXE_FILE])



class TextInputDlg(tk.Toplevel):
	'''Text input dialog'''
	def __init__(self, master=None, title='Text Input', caption='Enter text here:'):
		tk.Toplevel.__init__(self, master)
		self.transient(master)
		self.title = title
		self.master = master

		self.caption = caption
		self.result = None

		body = tk.Frame(self)
		self.initial_focus = self.createWidgets(body)
		body.pack(padx=5, pady=5)

		self.grab_set()

		if not self.initial_focus:
			self.initial_focus = self

		self.bind("<Return>", self.onOk)
		self.bind("<Escape>", self.onCancel)
		self.protocol("WM_DELETE_WINDOW", self.onCancel)
		self.geometry("+%d+%d" % (master.winfo_rootx()+50, master.winfo_rooty()+50))
		self.initial_focus.focus_set()
		self.wait_window(self)


	def createWidgets(self, parent):
		'''Adds widgets to the dialog.'''
		pad = 5

		# Frame for text iput & caption
		self.frm_txt = tk.Frame(parent)
		self.frm_txt.pack(side=tk.TOP, padx=pad, pady=pad, expand=1, fill=tk.BOTH)

		# Frame for buttons
		self.frm_btn = tk.Frame(parent)
		self.frm_btn.pack(side=tk.BOTTOM, padx=pad, pady=pad, expand=1, fill=tk.BOTH)

		# Caption
		self.lbl_caption = tk.Label(self.frm_txt)
		self.lbl_caption["text"] = self.caption
		self.lbl_caption.pack(side=tk.TOP)

		# Entry
		self.en = tk.Entry(self.frm_txt)
		self.en.pack(side=tk.BOTTOM)

		# OK button
		self.btn_ok = tk.Button(self.frm_btn)
		self.btn_ok["text"] = "Ok"
		self.btn_ok["command"] = self.onOk
		self.btn_ok.pack(side=tk.LEFT, ipadx=10, fill=tk.X, padx=pad)

		# Cancel button
		self.btn_cancel = tk.Button(self.frm_btn)
		self.btn_cancel["text"] = "Cancel"
		self.btn_cancel["command"] = self.onCancel
		self.btn_cancel.pack(side=tk.RIGHT, ipadx=10, fill=tk.X, padx=pad)

		# Set focus on the text field
		return self.en


	def onOk(self, Event=None):
		'''Called when the OK-button is clicked.
		Fills result with text from Entry widget.
		Closes Window and returns control to the main window.
		'''
		self.result = self.en.get()
		self.onCancel()


	def onCancel(self, Event=None):
		'''Called when the Cancel.button is clicked.
		Closes Window and returns control to the main window.
		Does not set result.
		'''
		self.master.focus_set()
		self.destroy()



class XPCtrlFrame(tk.Frame):
	'''Main Window'''
	def __init__(self, master=None):
		tk.Frame.__init__(self, master)
		self.master.title('XP-Ctrl')
		self.pack(expand=1)
		self.createWidgets()


	def createWidgets(self):
		'''Creates all widgets in the main window'''
		pad = 5

		# Frame for right side buttons
		self.frm_btn_r = tk.Frame(self)
		self.frm_btn_r.pack(side=tk.RIGHT, padx=pad, pady=pad, expand=1, fill=tk.Y)

		# Frame for name selection
		self.frm_names = tk.Frame(self)
		self.frm_names.pack(side=tk.TOP, padx=pad, pady=pad, expand=1, fill=tk.BOTH)

		# Fly button.
		self.btn_fly = tk.Button(self)
		self.btn_fly["text"] = "Fly!"
		self.btn_fly["command"] = self.onFly
		self.btn_fly.pack(side=tk.BOTTOM, ipadx=10, fill=tk.X, padx=pad, pady=pad)

		# Name selection list with scrollbar...
		self.scrl_names = tk.Scrollbar(self.frm_names, orient=tk.VERTICAL)
		self.lst_names = tk.Listbox(self.frm_names, selectmode=tk.SINGLE,
									width=30, yscrollcommand=self.scrl_names.set)
		self.scrl_names.config(command=self.lst_names.yview)
		# ...fill...
		self.fillNamesList()
		self.lst_names.selection_set(0)
		# ...and add to frame.
		self.scrl_names.pack(side=tk.RIGHT, fill=tk.Y)
		self.lst_names.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

		# Save button
		self.btn_save = tk.Button(self.frm_btn_r)
		self.btn_save["text"] = "Save"
		self.btn_save["command"] = self.onSave
		self.btn_save.pack(side=tk.TOP, ipadx=10, fill=tk.X)

		# Delete button
		self.btn_delete = tk.Button(self.frm_btn_r)
		self.btn_delete["text"] = "Delete"
		self.btn_delete["command"] = self.onDelete
		self.btn_delete.pack(side=tk.TOP, ipadx=10, pady=5, fill=tk.X)


	def fillNamesList(self):
		'''Fills the list control with data'''
		self.lst_names.delete(0, tk.END)
		self.lst_names_content = ['<Current>']
		self.lst_names_content += list()
		for name in self.lst_names_content:
			self.lst_names.insert(tk.END, name)


	def getSelectedName(self):
		'''Returns the selected name, None if no valid name is selected.'''
		sel = self.lst_names.curselection()
		if sel and sel[0] != 0:
			sel = self.lst_names_content[int(sel[0])]
		else:
			sel = None
		return sel


	def askOverwrite(self, title, name):
		'''Shows a messagebox asking to confirm overwrite'''
		message = "Overwrite '{}'?".format(name)
		return tkmessagebox.askyesno(title, message)


	def askDelete(self, title, name):
		'''Shows a messagebox asking to confirm deletion'''
		message = "Delete '{}'?".format(name)
		return tkmessagebox.askyesno(title, message)


	def txtInput(self, title, caption):
		'''Lets the user enter a text and returns it.'''
		print("txtInput: {} - {}".format(title, caption))
		dlg = TextInputDlg(self, "XP-Ctrl: Profile name", "Profile name:")

		return dlg.result


	def onSave(self):
		'''Saves a profile. Called when btn_save is clicked.'''
		name = self.getSelectedName()
		if not name:
			print("onSave: User Input needed.")
			name = self.txtInput("Save", "Profile Name:")

		if name in self.lst_names_content and not self.askOverwrite("Save", name):
			name = None

		if name:
			try:
				save(name)
			except RuntimeError as err:
				tkmessagebox.showerror("Save", str(err))
			self.fillNamesList()

	def onDelete(self):
		'''Deletes a profile. Asks for confirmation.'''
		name = self.getSelectedName()
		if name in self.lst_names_content and not self.askDelete("Delete", name):
			name = None

		if name:
			try:
				remove(name)
			except RuntimeError as err:
				tkmessagebox.showerror("Delete", str(err))
			self.fillNamesList()


	def onFly(self):
		'''Starts X-Plane with the selected profile. Called when btn_fly is clicked.'''
		launch(self.getSelectedName())

	def run(self):
		self.mainloop()

if __name__ == "__main__":
	root = tk.Tk()
	F = XPCtrlFrame(root)
	F.run()
