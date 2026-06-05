# -*- coding: utf-8 -*- 
# Python modules that have to be installed first!
import wx                                        # wx gui
from wx.lib.embeddedimage import PyEmbeddedImage # wx module for icon
import wx.lib.inspection                         # wx debug stuff --> see mainloop entrypoint
import psutil                                    # to get processID
import pyperclip                                 # cross platform clipboard handling
# Default python modules
import csv
import subprocess
import os
import sys
import time
import ctypes
import argparse

import locale
locale.setlocale(locale.LC_ALL, 'C')


# Configuration flags
USE_TC = True # Set to True to use Total commander or False to use Windows explorer

# Theme support: allow dark or light mode via command-line flags.
THEME_DARK = "dark"
THEME_LIGHT = "light"
CURRENT_THEME = THEME_DARK

DARK_BG = wx.Colour(32, 32, 32)
DARK_PANEL = wx.Colour(43, 43, 43)
DARK_FIELD = wx.Colour(25, 25, 25)
DARK_BORDER = wx.Colour(64, 64, 64)
DARK_TEXT = wx.Colour(240, 240, 240)
DARK_MUTED_TEXT = wx.Colour(180, 180, 180)
DARK_ACCENT = wx.Colour(0, 120, 215)

LIGHT_BG = wx.Colour(255, 255, 255)
LIGHT_PANEL = wx.Colour(240, 240, 240)
LIGHT_FIELD = wx.Colour(255, 255, 255)
LIGHT_BORDER = wx.Colour(200, 200, 200)
LIGHT_TEXT = wx.Colour(0, 0, 0)
LIGHT_MUTED_TEXT = wx.Colour(100, 100, 100)
LIGHT_ACCENT = wx.Colour(0, 120, 215)


def is_dark_theme():
    return CURRENT_THEME == THEME_DARK


def get_theme_color(dark_color, light_color):
    return dark_color if is_dark_theme() else light_color


def set_theme(theme):
    global CURRENT_THEME
    if theme not in (THEME_DARK, THEME_LIGHT):
        theme = THEME_DARK
    CURRENT_THEME = theme

    if os.name == "nt":
        wx.SystemOptions.SetOption("msw.dark-mode", 2 if is_dark_theme() else 0)


def parse_command_line():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--theme", choices=(THEME_DARK, THEME_LIGHT), help="Theme to use")
    parser.add_argument("--dark", dest="theme", action="store_const", const=THEME_DARK, help="Use dark theme")
    parser.add_argument("--light", dest="theme", action="store_const", const=THEME_LIGHT, help="Use light theme")
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit")
    args, unknown = parser.parse_known_args()
    if args.theme:
        set_theme(args.theme)
    else:
        set_theme(CURRENT_THEME)

    if unknown:
        print(f"[WARN] Ignoring unknown arguments: {' '.join(unknown)}")


def enable_windows_dark_widgets(window):
    if os.name != "nt" or window is None:
        return

    try:
        hwnd = window.GetHandle()
    except Exception:
        hwnd = None

    if not hwnd:
        return

    try:
        value = ctypes.c_int(1)
        # Windows 10 20H1+ uses attribute 20; older dark-mode builds used 19.
        for attribute in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd),
                ctypes.c_uint(attribute),
                ctypes.byref(value),
                ctypes.sizeof(value)
            )
        ctypes.windll.user32.RedrawWindow(
            ctypes.c_void_p(hwnd),
            None,
            None,
            0x0001 | 0x0400 | 0x0020
        )
    except Exception:
        pass

    try:
        ctypes.windll.uxtheme.SetWindowTheme(
            ctypes.c_void_p(hwnd),
            ctypes.c_wchar_p("DarkMode_Explorer"),
            None
        )
    except Exception:
        pass


def make_search_cancel_bitmap():
    size = 18
    bmp = wx.Bitmap(size, size)
    dc = wx.MemoryDC(bmp)
    dc.SetBackground(wx.Brush(DARK_FIELD))
    dc.Clear()

    button_fill = wx.Brush(wx.Colour(45, 45, 45))
    button_pen = wx.Pen(wx.Colour(110, 110, 110), 1)
    dc.SetBrush(button_fill)
    dc.SetPen(button_pen)
    dc.DrawCircle(size // 2, size // 2, 7)

    x_pen = wx.Pen(wx.Colour(205, 205, 205), 1)
    dc.SetPen(x_pen)
    dc.DrawLine(6, 6, size - 5, size - 5)
    dc.DrawLine(size - 6, 6, 5, size - 5)

    dc.SelectObject(wx.NullBitmap)
    return bmp


def apply_theme(window):
    if window is None:
        return

    if is_dark_theme():
        enable_windows_dark_widgets(window)

    if isinstance(window, (wx.TextCtrl, wx.SearchCtrl)):
        window.SetBackgroundColour(get_theme_color(DARK_FIELD, LIGHT_FIELD))
        window.SetForegroundColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))
        if isinstance(window, wx.SearchCtrl) and is_dark_theme():
            try:
                window.SetCancelBitmap(make_search_cancel_bitmap())
            except Exception:
                pass
    elif isinstance(window, wx.TreeCtrl):
        window.SetBackgroundColour(get_theme_color(DARK_FIELD, LIGHT_FIELD))
        window.SetForegroundColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))
    elif isinstance(window, wx.Button):
        window.SetBackgroundColour(get_theme_color(DARK_PANEL, LIGHT_PANEL))
        window.SetForegroundColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))
    elif isinstance(window, (wx.Frame, wx.Dialog, wx.Panel)):
        window.SetBackgroundColour(get_theme_color(DARK_BG, LIGHT_BG))
        window.SetForegroundColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))
    elif isinstance(window, wx.Menu):
        try:
            window.SetBackgroundColour(get_theme_color(DARK_PANEL, LIGHT_PANEL))
            window.SetTextColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))
        except Exception:
            pass
        for item in window.GetMenuItems():
            try:
                item.SetBackgroundColour(get_theme_color(DARK_PANEL, LIGHT_PANEL))
                item.SetTextColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))
            except Exception:
                pass
    elif isinstance(window, wx.StaticText):
        window.SetForegroundColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))

    if hasattr(window, 'GetChildren'):
        for child in window.GetChildren():
            apply_theme(child)

    if hasattr(window, 'Refresh'):
        window.Refresh()


def _create_dialog_buttons(panel, style):
    button_sizer = wx.StdDialogButtonSizer()
    created = []

    def add_button(button_id, label):
        button = wx.Button(panel, button_id, label)
        button_sizer.AddButton(button)
        created.append(button)

    if style & wx.OK:
        add_button(wx.ID_OK, "OK")
    if style & wx.YES:
        add_button(wx.ID_YES, "Yes")
    if style & wx.NO:
        add_button(wx.ID_NO, "No")
    if style & wx.CANCEL:
        add_button(wx.ID_CANCEL, "Cancel")
    if style & wx.CLOSE and not (style & (wx.OK | wx.CANCEL | wx.YES | wx.NO)):
        add_button(wx.ID_CLOSE, "Close")

    if created:
        button_sizer.Realize()
    return button_sizer


def show_dark_text_dialog(parent, message, caption, value=""):
    dlg = wx.Dialog(parent, title=caption, style=wx.DEFAULT_DIALOG_STYLE)
    panel = wx.Panel(dlg)

    text = wx.StaticText(panel, label=message)
    text.Wrap(520)

    text_ctrl = wx.TextCtrl(panel, value=value, style=wx.TE_LEFT)

    button_sizer = _create_dialog_buttons(panel, wx.OK | wx.CANCEL)

    main_sizer = wx.BoxSizer(wx.VERTICAL)
    main_sizer.Add(text, 0, wx.ALL | wx.EXPAND, 12)
    main_sizer.Add(text_ctrl, 0, wx.ALL | wx.EXPAND, 12)
    main_sizer.Add(button_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 8)

    panel.SetSizer(main_sizer)
    main_sizer.Fit(dlg)
    dlg.SetMinSize((560, dlg.GetSize().GetHeight()))

    apply_theme(dlg)
    result = dlg.ShowModal()
    text_value = text_ctrl.GetValue()
    dlg.Destroy()
    return result, text_value


def show_dark_message(parent, message, caption, style=wx.OK):
    dlg = wx.Dialog(parent, title=caption, style=wx.DEFAULT_DIALOG_STYLE)
    panel = wx.Panel(dlg)

    text = wx.StaticText(panel, label=message)
    text.Wrap(520)

    button_sizer = _create_dialog_buttons(panel, style)

    main_sizer = wx.BoxSizer(wx.VERTICAL)
    main_sizer.Add(text, 0, wx.ALL | wx.EXPAND, 12)
    main_sizer.Add(button_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 8)

    panel.SetSizer(main_sizer)
    main_sizer.Fit(dlg)
    dlg.SetMinSize((560, dlg.GetSize().GetHeight()))

    apply_theme(dlg)
    result = dlg.ShowModal()
    dlg.Destroy()
    return result

# icon stored as py embedded image
main_icon = PyEmbeddedImage(
    b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAACuUlEQVR4Ae1WQU8TQRR+BVtr'
    b'TWOVQtySGLwsXjho+QH1ogexB+OhlIPxQDEeAc+FO+KVtnfw3JYz5aKXlpMXS0xMjJSoFcIW'
    b'UgoW55tml87sbssB0st+yWYzszPzvve99+ata/zhlzPqIfqox3AIOAQcAtfoCuD395ES8rB3'
    b'P2naPyp/rdOFCEw8D/Dn3dwPvrETIhE/xeIDtPx+1zCg7w+P3xTWalqTNjcOKJ36RZXKifBN'
    b'CEFl54RvjsXvUDfE4kEKMS9149MzQ5RcHDYZB6DIRDRA2XWVwmHxu6BAqXRIpeIRTTLPMqnf'
    b'draZvG5myEeLyZ98DKOJmcHzc4qHVC7XuYqqeoNGH3hJUdxUYCrAhi0BIMNkWsmMcKbyYh0J'
    b'5i3Uyuf2+fhR2Gd8g9E3ie+We3LZPdO8qQpgFIdMt3lEkveIM7zUgWQT1jBvZVjF35IAsLb6'
    b'l8sqxwvQ53Cgjs0NTSCDWK+kR2h2/i5FHvt5DtihP6S8XZAnt1n8Xry8TY3GGX3+VBO+LX24'
    b'xw3m8/vGHDxDQqqjXmMO47ExHz15eotevR6kkNJK2FqtSV0VQAgQX0jdLi/GkFePfTuQkHis'
    b'ZOZ7WRWkMvdN4bJUAKj+OaXJqQE6bjRpq3TE52bnFZZ8DcqkrSsEmb+2WuUEt1g1VaunFAy6'
    b'DaN4e667BFVtg4PD9JIE9NKz8l4GKqRQOKDlpV2ain0TLjVV9QprO/YClCRYI/Hk0msHyCHp'
    b'ECIZrav42NZGx16Aktxmm5HNSDD94pGRXGjdgK0LaYiX6E6lwcnDYyinQ3agazPK5vZojhHg'
    b'hIrmiwlGQsMeY8zviWjA8iyEVSbQtR2vsw0on48suawyHBJHn5W5OnZdD6HD1Y58kOG67N9y'
    b'3oqV81ZcYaFAN7TDpf8PwJim1S+83vklcwg4BHpO4D+WRzRdteYYeQAAAABJRU5ErkJggg==')

class HideableWidget(wx.Frame):
    def __init__(self, parent, title):

        self.size = (275, 420)
        
        super(HideableWidget, self).__init__(parent, title=u"favorit3S.ai", pos = wx.DefaultPosition, size = wx.Size(self.size[0],self.size[1]), style = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.STAY_ON_TOP|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL)

        '''
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour('light blue')

        self.hide_button = wx.Button(self.panel, label='Hide', pos=(10, 10))
        self.hide_button.Bind(wx.EVT_BUTTON, self.on_hide)

        self.side_panel = SidePanel(None, "Handle", self)

        # Bind the event for minimizing the window
        self.Bind(wx.EVT_ICONIZE, self.on_hide)
        '''
        #self.size = (275, 420)

        #self.frame = wx.Frame.__init__ (self, None, id = wx.ID_ANY, title = u"Favorites2.1", pos = wx.DefaultPosition, size = wx.Size(self.size[0],self.size[1]), style = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.STAY_ON_TOP|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL)
        self.SetIcon(main_icon.GetIcon()) # Fix icon first
        self.SetBackgroundColour(get_theme_color(DARK_BG, LIGHT_BG))
        self.SetForegroundColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))
        #self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)
        
        # we only have a single tree controller
        tree_style = wx.TR_DEFAULT_STYLE
        if is_dark_theme():
            tree_style |= wx.BORDER_SIMPLE
        self.m_treeCtrl2 = wx.TreeCtrl(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(self.size[0] - 15, self.size[1] - 80), tree_style)

        search_style = wx.TE_LEFT
        if is_dark_theme():
            search_style |= wx.BORDER_SIMPLE
        self.search_bar = wx.SearchCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(self.size[0] - 45,-1), search_style)
        self.search_bar.ShowCancelButton(True)
        self.search_bar.SetDescriptiveText("Find your favorites here!")
        if is_dark_theme():
            self.search_bar.SetBackgroundColour(DARK_FIELD)
            self.search_bar.SetForegroundColour(DARK_TEXT)
            for child in self.search_bar.GetChildren():
                try:
                    child.SetBackgroundColour(DARK_FIELD)
                    child.SetForegroundColour(DARK_TEXT)
                    child.Refresh()
                except Exception:
                    pass
        self.help_button = wx.Button(self, wx.ID_ANY, "?", wx.DefaultPosition, wx.Size(15,-1), wx.BORDER_NONE)
        font = wx.Font(8, wx.FONTFAMILY_MODERN, 0, 90, underline = False, faceName ="")
        self.help_button.SetFont(font)
        apply_theme(self)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        verticalSizer = wx.BoxSizer(wx.VERTICAL)
        
        topSizer.Add(self.search_bar, 0, wx.ALL, 0)
        topSizer.Add(self.help_button, 0, wx.LEFT, 5)
        verticalSizer.Add(topSizer, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        verticalSizer.Add(self.m_treeCtrl2, 0, wx.ALL, 5)
        
        self.timer = wx.Timer(self, -1)
        
        # bind events
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OpenMenu, self.m_treeCtrl2)     # right click event
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.Open, self.m_treeCtrl2)           # double click event
        self.Bind(wx.EVT_TREE_ITEM_GETTOOLTIP, self.OnTreeTooltip, self.m_treeCtrl2) # hover tooltip event
        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnExpanded, self.m_treeCtrl2)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnCollapsed, self.m_treeCtrl2)
        self.Bind(wx.EVT_TEXT,self.TextChange,self.search_bar)                       # search bar event
        self.Bind(wx.EVT_BUTTON,self.HelpWindow,self.help_button)                    # help button event
        self.Bind(wx.EVT_TIMER, self.SearchbarTimer)                                 # search timer event
        
        # right click context menu
        self.addMenu = None
        #self.openMenu = None # open is not really needed in right click context menu
        self.deleteMenu = None
        self.renameMenu = None
        self.copyMenu = None
        self.editMenu = None
        self.createMenu()
        
        self.target = None
        self.SetSizer(verticalSizer)
        self.Layout()
        self.Centre(wx.BOTH)
        
        # setup tool-tip fade in/out times
        wx.ToolTip.SetDelay(1000)
        wx.ToolTip.SetAutoPop(4000)
        
        # search string parameters
        self.searchTimeout = 0.15                      # search string refresh rate in sec
        self.timer.Start(int(self.searchTimeout*1000)) # start timer (it is in ms)
        self.lastChange = time.time()                  # storing last typing timestamp
        self.lastSearchString = ""                     # storing last search string
        self.searchTimerTriggered = False              # storing the armed trigger

        self.side_panel = SidePanel(None, "Handle", self)
        ##################
        
        self.Bind(wx.EVT_CLOSE, self.on_close)
        # Bind the event for minimizing the window
        self.Bind(wx.EVT_ICONIZE, self.on_hide)

        # Bind the activate event
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)
        # Bind the focus events
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)

        self.Centre()
        self.Show()
        apply_theme(self)

    def on_activate(self, event):
        if event.GetActive():
            print("Window activated\n")
        else:
            print("Window deactivated\n")
        event.Skip()  # Ensure the event is processed further

    def on_set_focus(self, event):
        print("Window gained focus\n")
        event.Skip()  # Ensure the event is processed further

    def on_kill_focus(self, event):
        print("Window lost focus\n")
        event.Skip()  # Ensure the event is processed further

    def on_hide(self, event):
        self.side_panel.Show()
        self.Restore() # patch minimize
        self.Hide()

    def on_close(self, event):
        self.side_panel.Destroy()
        self.Destroy()

    def OnCollapsed(self, event):
        item = event.GetItem()

        if len(self.search_bar.GetValue()) != 0:
            return

        def traverse_tree(item, level=0):
            global file_parent
            global file_child
            # Get the item text
            item_text = self.m_treeCtrl2.GetItemText(item)
            #print("  " * level + str(level) + " " + item_text)
            #print(len(self.search_bar.GetValue()))
            if level == 1 and self.m_treeCtrl2.IsExpanded(item):
                file_parent = item_text
                section_file.write(f"{file_parent}\n")
            if level == 2 and self.m_treeCtrl2.IsExpanded(item):
                file_child = item_text
                section_file.write(f"{file_parent}{file_child}\n")
                
            # Check if the item is expanded
            if self.m_treeCtrl2.IsExpanded(item):
                # Get the first child
                child, cookie = self.m_treeCtrl2.GetFirstChild(item)
                
                # Traverse through all children
                while child.IsOk():
                    traverse_tree(child, level + 1)
                    child, cookie = self.m_treeCtrl2.GetNextChild(item, cookie)
        
        # Start traversal from the root
        root = self.m_treeCtrl2.GetRootItem()
        section_file = open('open_sections.txt', "w", encoding="utf-8")
        file_parent = ""
        file_child = ""
        traverse_tree(root)
        section_file.close()

    def OnExpanded(self, event):
        item = event.GetItem()

        if len(self.search_bar.GetValue()) != 0:
            return

        def traverse_tree(item, level=0):
            global file_parent
            global file_child
            # Get the item text
            item_text = self.m_treeCtrl2.GetItemText(item)
            #print("  " * level + str(level) + " " + item_text)
            #print(len(self.search_bar.GetValue()))
            if level == 1 and self.m_treeCtrl2.IsExpanded(item):
                file_parent = item_text
                section_file.write(f"{file_parent}\n")
            if level == 2 and self.m_treeCtrl2.IsExpanded(item):
                file_child = item_text
                section_file.write(f"{file_parent}{file_child}\n")
                
            # Check if the item is expanded
            if self.m_treeCtrl2.IsExpanded(item):
                # Get the first child
                child, cookie = self.m_treeCtrl2.GetFirstChild(item)
                
                # Traverse through all children
                while child.IsOk():
                    traverse_tree(child, level + 1)
                    child, cookie = self.m_treeCtrl2.GetNextChild(item, cookie)
        
        # Start traversal from the root
        root = self.m_treeCtrl2.GetRootItem()
        section_file = open('open_sections.txt', "w", encoding="utf-8")
        file_parent = ""
        file_child = ""
        traverse_tree(root)
        section_file.close()

    def OpenMenu(self, event):
        self.target = event.GetItem()
        self.m_treeCtrl2.SelectItem(self.target)
        
        item = self.m_treeCtrl2.GetSelection() # double clicked item
        
        # get all parents of hovered item organized in a list
        pieces = []
        while self.m_treeCtrl2.GetItemParent(item):
          piece = self.m_treeCtrl2.GetItemText(item)
          pieces.insert(0, piece)
          item = self.m_treeCtrl2.GetItemParent(item)
        
        if len(pieces) == 3:
            self.addMenu.Enable(False)
            self.copyMenu.Enable(True)
            self.editMenu.Enable(True)
            #self.openMenu.Enable(True)
        else:
            self.addMenu.Enable(True)
            self.copyMenu.Enable(False)
            self.editMenu.Enable(False)
            #self.openMenu.Enable(False)
            
        if len(pieces) == 0:
            self.deleteMenu.Enable(False)
            self.renameMenu.Enable(False)
        else:
            self.deleteMenu.Enable(True)
            self.renameMenu.Enable(True)
        
        # print self.m_treeCtrl2.GetItemText(self.target)
        position = self.ScreenToClient(wx.GetMousePosition())
        self.PopupMenu(self.menu,position)
        
    def Open(self, event):
        self.target = event.GetItem()
        self.m_treeCtrl2.SelectItem(self.target)
        self.OnPopupItemSelected(event)
        
    def TextChange(self, event):
        # the actual search string
        eventString = event.GetString()
        #print(eventString)
        if eventString == "": # clearing the searchbar
            print("[INFO] Searchbar cleared")
            self.lastSearchString = ""
            self.searchTimerTriggered = False
            self.m_treeCtrl2.DeleteAllItems()
            loadDataBase()
        # when one types a search string the script doesn't filter the database immediately,
        # instead it buffers the search string and filters in a timer event,
        # this avoids fast blinking of window and avoids unnecessary file IO
        else:
            self.lastSearchString = eventString # storing last search string typed in
            self.searchTimerTriggered = True    # triggering the timer that a search will happen
            self.lastChange = time.time()       # last typing timestamp is stored
            
        event.Skip()

    def SearchbarTimer(self, event):
        # this is the search timer event,
        # it checks if it's triggered and last typing timestamp is "old" enough
        if time.time() - self.lastChange > self.searchTimeout and self.searchTimerTriggered:
            print(f"[INFO] Timer was triggered with search string: {self.lastSearchString}")
            self.searchTimerTriggered = False # disarm the trigger
            self.m_treeCtrl2.DeleteAllItems() # clear window only here
            loadSearch(self.lastSearchString) # filter the database

    def OnTreeTooltip(self, event):
        item = event.GetItem() # hovered item
        # get all parents of hovered item organized in a list
        pieces = []
        while self.m_treeCtrl2.GetItemParent(item):
          piece = self.m_treeCtrl2.GetItemText(item)
          pieces.insert(0, piece)
          item = self.m_treeCtrl2.GetItemParent(item)
          
        path = "root"
        if len(pieces) == 3:
            path = database[pieces[0]][pieces[1]][pieces[2]]["path"]
          
        # enable/disable is only needed to hide the old and fade in the new tool-tip
        wx.ToolTip.Enable(False)
        wx.ToolTip.Enable(True)
        # hide tool-tip on root level
        if path != "root":
            event.SetToolTip("%s" % path) 
        event.Skip()

    def OnPopupItemSelected(self, event):
        
        item = self.m_treeCtrl2.GetSelection() # double clicked item
        
        # get all parents of hovered item organized in a list
        pieces = []
        while self.m_treeCtrl2.GetItemParent(item):
          piece = self.m_treeCtrl2.GetItemText(item)
          pieces.insert(0, piece)
          item = self.m_treeCtrl2.GetItemParent(item)
        
        path = "root"
        linkType = None
        
        if len(pieces) == 3:
            path = database[pieces[0]][pieces[1]][pieces[2]]["path"]
            linkType = database[pieces[0]][pieces[1]][pieces[2]]["type"]

        if path != "root":
            if linkType == "file":                                                                            # if it's a file execute it with explorer
                subprocess.Popen(["explorer", path])
            elif linkType == "folder":                                                                        # open folder with TC or explorer
                if USE_TC:                                                                                    # check USE_TC flag
                    subprocess.Popen(["cmd", "/c", "C:\\totalcmd\\TOTALCMD64.EXE", "/O", "/T", f"/L={path}"]) # to open with total commander
                    # https://www.ghisler.ch/wiki/index.php/Command_line_parameters#.2FO
                else:
                    subprocess.Popen(["explorer", path])                                                      # to open with windows file explorer
            elif linkType == "link":                                                                          # it will open with the default web browser
               subprocess.Popen(["cmd", "/c", "start", path])
            elif linkType == "svn":                                                                           # it will open the SVN link with Tortoise
               tortoise = r'C://Program Files//TortoiseSVN//bin//TortoiseProc.exe'
               subprocess.Popen('"' +tortoise+ '" /command:repobrowser /path:"%s"' % path, shell=True)
            elif linkType == "password":
               pyperclip.copy(path)
            else:
                print(f"[WARN] no appropriate category for {linkType}, path: {path}")

    def OnPopupItemAdd(self, event):
        global database
        
        item = self.m_treeCtrl2.GetSelection() # double clicked item
        
        # get all parents of hovered item organized in a list
        pieces = []
        while self.m_treeCtrl2.GetItemParent(item):
          piece = self.m_treeCtrl2.GetItemText(item)
          pieces.insert(0, piece)
          item = self.m_treeCtrl2.GetItemParent(item)
          
        print(pieces)
    
        if len(pieces) == 0:
            result, newItem = show_dark_text_dialog(self, 'Add a new main folder:', 'New main folder', '')
            
            if result != wx.ID_OK:
                return
                
            # check for invalid characters: , and ;
            if "," in newItem or ";" in newItem:
                print(f"[WARN] , or ; is not allowed in the name!")
                show_dark_message(self, "Error: `,` or `;` is not allowed in the name due to imitations of the CSV file!", "Name error", wx.OK | wx.ICON_ERROR)
                return
                
            database[newItem] = {}
            print(f"[INFO] New main folder {newItem} was added")
            
        elif len(pieces) == 1:
            result, newItem = show_dark_text_dialog(self, 'Add a new subfolder:', 'New subfolder', '')
            
            if result != wx.ID_OK:
                return
                
            # check for invalid characters: , and ;
            if "," in newItem or ";" in newItem:
                print(f"[WARN] , or ; is not allowed in the name!")
                show_dark_message(self, "Error: `,` or `;` is not allowed in the name due to imitations of the CSV file!", "Name error", wx.OK | wx.ICON_ERROR)
                return
                
            database[pieces[0]][newItem] = {}
            print(f"[INFO] New subfolder {newItem} was added")
            
        elif len(pieces) == 2:
            result, alias = show_dark_text_dialog(self, 'Add a new favorite:', 'New favorite', 'alias')
            
            if result != wx.ID_OK:
                return
                
            # check for invalid characters: , and ;
            if "," in alias or ";" in alias:
                print(f"[WARN] , or ; is not allowed in the name!")
                show_dark_message(self, "Error: `,` or `;` is not allowed in the name due to imitations of the CSV file!", "Name error", wx.OK | wx.ICON_ERROR)
                return
                
            result, item = show_dark_text_dialog(self, 'Add the path to this favorite:\n%s' % alias, 'New path', 'path')
            
            if result != wx.ID_OK:
                return
                
            # check for invalid characters: , and ;
            if "," in item or ";" in item:
                print(f"[WARN] , or ; is not allowed in the name!")
                show_dark_message(self, "Error: `,` or `;` is not allowed in the name due to imitations of the CSV file!", "Name error", wx.OK | wx.ICON_ERROR)
                return
    
            # \\prestagroup.com\\global was added to handle files and folders from the network drive instead of X:\
            if item[0:3].lower() in ["c:\\", "x:\\", "t:\\", "k:\\", "m:\\", "q:\\"] or "\\prestagroup.com\\global" in item:
                if os.path.isfile(item):
                    linkType = "file"
                    print(f"[INFO] New file {item} was added")
                else:
                    linkType = "folder"
                    print(f"[INFO] New folder {item} was added")
            elif 'http://d1dapsvn01/svn/' in item:
                linkType = "svn"
                print(f"[INFO] New SVN path {item} was added")
            elif "http://" in item or "https://" in item:
                print(f"[INFO] New website {item} was added")
                linkType = "link"
            else:
                show_dark_message(self, "You entered an invalid path!", 'Warning', wx.OK | wx.ICON_WARNING)
                return
    
            database[pieces[0]][pieces[1]][alias] = {}
            database[pieces[0]][pieces[1]][alias]["type"] = linkType
            database[pieces[0]][pieces[1]][alias]["path"] = item
            
        saveDataBase()

        self.m_treeCtrl2.DeleteAllItems()
        loadDataBase()
        
        # trigger searchbar event workaround
        # this is very hacky to update the databse through an empty append
        # but it's good enough... Cha Bu Duo
        self.search_bar.AppendText("")
        
    def OnPopupItemDelete(self, event):
        global database
        
        item = self.m_treeCtrl2.GetSelection() # selected/highlighted item

        # get all parents of hovered item organized in a list
        pieces = []
        while self.m_treeCtrl2.GetItemParent(item):
          piece = self.m_treeCtrl2.GetItemText(item)
          pieces.insert(0, piece)
          item = self.m_treeCtrl2.GetItemParent(item)
        
        # main folder
        if len(pieces) == 1:
            result = show_dark_message(self, "Are you sure deleting the main folder?", 'Warning', wx.OK | wx.CANCEL | wx.ICON_WARNING)
            if result != wx.OK:
                return
            del database[pieces[0]]
        # subfolder
        elif len(pieces) == 2:
            result = show_dark_message(self, "Are you sure deleting the subfolder?", 'Warning', wx.OK | wx.CANCEL | wx.ICON_WARNING)
            if result != wx.OK:
                return
            del database[pieces[0]][pieces[1]]
        # the links
        elif len(pieces) == 3:
            del database[pieces[0]][pieces[1]][pieces[2]]
        else:
            # shouldn't happen though...
            print("ERROR, NOT IMPLEMENTED")
            
        saveDataBase()

        # clear tree and reload the database
        self.m_treeCtrl2.DeleteAllItems()
        loadDataBase()
        
        # trigger searchbar event workaround
        # this is very hacky to update the databse through an empty append
        # but it's good enough... Cha Bu Duo
        self.search_bar.AppendText("")
        
    # Rename a link's alias or complete main or subfolders
    def OnPopupItemRename(self, event):
        global database
        
        item = self.m_treeCtrl2.GetSelection() # selected/highlighted item
        
        # get all parents of hovered item organized in a list
        pieces = []
        while self.m_treeCtrl2.GetItemParent(item):
          piece = self.m_treeCtrl2.GetItemText(item)
          pieces.insert(0, piece)
          item = self.m_treeCtrl2.GetItemParent(item)
          
        #print(pieces)
        
        # get the new name into renameItem variable
        result, renameItem = show_dark_text_dialog(self, 'Rename your favorite', 'Rename', pieces[-1])
        
        if result != wx.ID_OK:
            return
            
        # check for invalid characters: , and ;
        if "," in renameItem or ";" in renameItem:
            print(f"[WARN] , or ; is not allowed in the name!")
            show_dark_message(self, "Error: `,` or `;` is not allowed in the name due to imitations of the CSV file!", "Name error", wx.OK | wx.ICON_ERROR)
            return
            
        #database[newItem] = {}
        print(f"[INFO] Item was renamed from {pieces[-1]} to {renameItem}")
        
        # if len == 3, only the link's alias has changed
        if len(pieces) == 3:        
            database[pieces[0]][pieces[1]][renameItem] = database[pieces[0]][pieces[1]].pop(pieces[2])
            
        # Okay, this is ugly as fuck, good luck with debugging...
        # if len == 2, the subfolder name has changed, we have to copy everything to a temporary dictionary newDatabase while preserving the original order
        elif len(pieces) == 2:
            newDatabase = {}
            for key in database.keys():
                if key == pieces[0]:
                    newDatabase[key] = {}
                    for subkey in database[key].keys():
                        if subkey == pieces[-1]:
                            newDatabase[key][renameItem]=database[key][subkey]
                        else:
                            newDatabase[key][subkey]=database[key][subkey]
                else:
                    newDatabase[key]=database[key]
            
            database = newDatabase
            
        # if len == 1, the main folder name has changed, we have to copy everything to a temporary dictionary newDatabase while preserving the original order
        elif len(pieces) == 1:
            newDatabase = {}
            for key in database.keys():
                if key == pieces[-1]:
                    newDatabase[renameItem]=database[key]
                else:
                    newDatabase[key]=database[key]
            
            database = newDatabase
            
        else:
            # shouldn't happen though...
            print("ERROR, NOT IMPLEMENTED")
        
        saveDataBase()

        # clear tree and reload the database
        self.m_treeCtrl2.DeleteAllItems()
        loadDataBase()
        
        # trigger searchbar event workaround
        # this is very hacky to update the databse through an empty append
        # but it's good enough... Cha Bu Duo
        self.search_bar.AppendText("")
        
    # Editing a link has to check if link type has changed
    def OnPopupItemEdit(self, event):
        global database
        
        item = self.m_treeCtrl2.GetSelection() # selected/highlighted item
        
        # get all parents of hovered item organized in a list
        pieces = []
        while self.m_treeCtrl2.GetItemParent(item):
          piece = self.m_treeCtrl2.GetItemText(item)
          pieces.insert(0, piece)
          item = self.m_treeCtrl2.GetItemParent(item)
          
        #print(pieces)
        
        # get the new path into editItem variable
        oldPath = database[pieces[0]][pieces[1]][pieces[2]]["path"]
        oldType = database[pieces[0]][pieces[1]][pieces[2]]["type"]
        result, editItem = show_dark_text_dialog(self, 'Edit your link', 'Edit', oldPath)
        
        if result != wx.ID_OK:
            return
            
        # check for invalid characters: , and ;
        if "," in editItem or ";" in editItem:
            print(f"[WARN] , or ; is not allowed in the name!")
            show_dark_message(self, "Error: `,` or `;` is not allowed in the name due to imitations of the CSV file!", "Name error", wx.OK | wx.ICON_ERROR)
            return
            
        print(f"[INFO] Link change from {oldPath} to {editItem} was requested, validity check starts now:")
        
        if len(pieces) == 3:        
    
            # analyze link to decide the type
            if editItem[0:3].lower() in ["c:\\", "x:\\", "t:\\", "k:\\", "m:\\", "q:\\"]:
                if os.path.isfile(editItem):
                    linkType = "file"
                    print(f"[INFO] New file {editItem} was changed")
                else:
                    linkType = "folder"
                    print(f"[INFO] New folder {editItem} was changed")
            elif 'http://d1dapsvn01/svn/' in editItem:
                linkType = "svn"
                print(f"[INFO] New SVN path {editItem} was changed")
            elif "http://" in editItem or "https://" in editItem:
                print(f"[INFO] New website {editItem} was changed")
                linkType = "link"
            # storing passwords in this tool is not recommended and cannot be added via the tool
            # however if you hacked a password into the database manually, you can update it
            # through the GUI. This is useful for me for the SAP logon
            elif oldType == "password":
                print(f"[INFO] New password {editItem} was changed")
                linkType = "password"
            else:
                show_dark_message(self, "You entered an invalid path!", 'Warning', wx.OK | wx.ICON_WARNING)
                return
    
            # update the link and type
            database[pieces[0]][pieces[1]][pieces[2]]["type"] = linkType
            database[pieces[0]][pieces[1]][pieces[2]]["path"] = editItem

            
        else:
            # shouldn't happen though...
            print("ERROR, NOT IMPLEMENTED")
        
        saveDataBase()

        # clear tree and reload the database
        self.m_treeCtrl2.DeleteAllItems()
        loadDataBase()
        
        # trigger searchbar event workaround
        # this is very hacky to update the databse through an empty append
        # but it's good enough... Cha Bu Duo
        self.search_bar.AppendText("")
        
    # Copy link to clipboard
    def OnPopupItemCopy(self, event):
        global database
        
        item = self.m_treeCtrl2.GetSelection() # selected/highlighted item
        
        # get all parents of hovered item organized in a list
        pieces = []
        while self.m_treeCtrl2.GetItemParent(item):
          piece = self.m_treeCtrl2.GetItemText(item)
          pieces.insert(0, piece)
          item = self.m_treeCtrl2.GetItemParent(item)
          
        #print(pieces)
        #print(database[pieces[0]][pieces[1]][pieces[2]]["path"])
        
        pyperclip.copy(database[pieces[0]][pieces[1]][pieces[2]]["path"])

    def HelpWindow(self, event):
        helpText = "Features\n---------\nFavorites tree:\n\
        - You can organize your stuff in 3 levels of hierarchy, it cannot be less or more though\n\
        - Your favorites are stored in `links.csv` in the same folder, don't mess it up\n\
        - You can add, change or rename any favorite in the tree with a right click\n\
        - You can switch to a small sticky widget with the minimze button, double click to return\n\
        - You can set a branch default open - in any level - if you add `[-]` to the end of the name\n\
        - It's not allowed to use `,` or `;` in any name or path, entschuldigung\n\
        - When you add a new favorite, it will be automatically recognized as:\n\
              file/folder/web link or svn path\n\nSearch:\n\
        - Your search string will be split by spaces and used in AND relation\n\
        - Your search string will match non-visible metadata too\n\
              e.g. the type of the favorite (folder, svn, etc.)\n\nSupport:\n\
        david.dudas@variosystems.com"
        show_dark_message(self, helpText, "favorit3S.ai", wx.OK | wx.ICON_INFORMATION)
        event.Skip()

    def createMenu(self):
        self.menu = wx.Menu()
        self.addMenu = self.menu.Append(-1,'Add')
        self.Bind(wx.EVT_MENU, self.OnPopupItemAdd, self.addMenu)
        # Open menu is hidden
        #self.openMenu = self.menu.Append(-1,'Open')
        #self.Bind(wx.EVT_MENU, self.OnPopupItemSelected, self.openMenu)
        self.renameMenu = self.menu.Append(-1,'Rename')
        self.Bind(wx.EVT_MENU, self.OnPopupItemRename, self.renameMenu)
        self.copyMenu = self.menu.Append(-1,'Copy link')
        self.Bind(wx.EVT_MENU, self.OnPopupItemCopy, self.copyMenu)
        self.editMenu = self.menu.Append(-1,'Edit link')
        self.Bind(wx.EVT_MENU, self.OnPopupItemEdit, self.editMenu)
        # SEPARATOR -------
        self.menu.Append(wx.ID_SEPARATOR)
        self.deleteMenu = self.menu.Append(-1,'Remove')
        self.Bind(wx.EVT_MENU, self.OnPopupItemDelete, self.deleteMenu)

        apply_theme(self.menu)

    def __del__(self):
        pass

class SidePanel(wx.Frame):
    def __init__(self, parent, title, main_frame):
        super(SidePanel, self).__init__(parent, title=title, size=(10, 120),
                                        style=wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.FRAME_SHAPED)

        self.main_frame = main_frame
        self.new_position_confirmed = self.GetPosition()

        self.panel = wx.Panel(self, size=(10, 120))
        #self.panel.SetBackgroundColour('light grey')
        self.panel.SetBackgroundColour(wx.Colour(0, 0, 0, 100))  # Fully transparent background

        #self.show_button = wx.StaticText(self.panel, label='>', size=(10, 100), style=wx.ALIGN_CENTER)
        self.right_arrow = wx.Image('right_arrow.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.left_arrow = wx.Image('left_arrow.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()

        self.show_button = wx.StaticBitmap(self.panel, bitmap=self.right_arrow, pos=(0, 0))

        
        self.panel.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.panel.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.panel.Bind(wx.EVT_MOTION, self.on_motion)
        self.panel.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click)
        self.show_button.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.show_button.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.show_button.Bind(wx.EVT_MOTION, self.on_motion)
        self.show_button.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click)
        # Bind the activate event
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)
        self.Bind(wx.EVT_MAXIMIZE, self.on_activate)
        # Bind the focus events
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)

        # Center the side panel vertically on the primary screen
        primary_screen_geometry = wx.Display(0).GetGeometry()
        self.SetPosition((0, (primary_screen_geometry.GetHeight() - self.GetSize().GetHeight()) // 2))

        self.SetTransparent(100) 

        self.Hide()

        self.dragging = False
        self.last_position = (0, 0)

    def on_activate(self, event):
        if event.GetActive():
            print("Window activated\n")
        else:
            print("Window deactivated\n")
        event.Skip()  # Ensure the event is processed further

    def on_set_focus(self, event):
        print("Window gained focus\n")
        event.Skip()  # Ensure the event is processed further

    def on_kill_focus(self, event):
        print("Window lost focus\n")
        event.Skip()  # Ensure the event is processed further

    def on_show(self, event):
        self.main_frame.Show()
        self.Hide()

    def on_close(self, event):
        self.main_frame.Destroy()
        self.Destroy()

    def on_left_down(self, event):
        self.dragging = True
        self.last_position = event.GetPosition()
        self.panel.CaptureMouse()

    def on_left_up(self, event):
        self.dragging = False
        if self.panel.HasCapture():
            self.panel.ReleaseMouse()

    def on_motion(self, event):
        if self.dragging:
            current_position = event.GetPosition()
            delta = wx.Point(current_position.x - self.last_position.x,
                             current_position.y - self.last_position.y)
            new_position = self.GetPosition() + delta

            # Get the geometries of all screens
            screens = [wx.Display(i).GetGeometry() for i in range(wx.Display.GetCount())]

            # Check which screen the new position is in
            screen_found = False
            for screen in screens:
                if screen.Contains(new_position):
                    if new_position.x < screen.GetLeft() + screen.GetWidth() / 2:
                        new_position.x = screen.GetLeft()
                        #self.show_button.SetLabel('>')
                        self.show_button.SetBitmap(self.right_arrow)
                    else:
                        new_position.x = screen.GetRight() - self.GetSize().x + 1
                        #self.show_button.SetLabel('<')
                        self.show_button.SetBitmap(self.left_arrow)
                    new_position.y = max(screen.GetTop(), min(new_position.y, screen.GetBottom() - self.GetSize().y))
                    screen_found = True
                    break

            if screen_found == False:
                new_position = self.new_position_confirmed

            self.Move(new_position)
            self.new_position_confirmed = new_position

    def on_double_click(self, event):
        self.main_frame.Show()
        self.Hide()

def loadDataBase():
    global database
    
    # initial tree structure
    root = frame.m_treeCtrl2.AddRoot('My favorites')
    
    # read csv file's lines to rows[]
    if not os.path.exists('links.csv'):
        with open('links.csv', 'w', encoding='utf-8') as f:
            f.write(
                'Example folder 1\n'
                'Example folder 1;Subfolder 1\n'
                'Example folder 1;Subfolder 1;Google;link;https://google.com\n'
                'Example folder 1;Subfolder 1;YouTube;link;https://youtube.com\n'
                'Example folder 1;Subfolder 2\n'
                'Example folder 1;Subfolder 2;GitHub;link;https://github.com\n'
                'Example folder 2\n'
                'Example folder 2;Subfolder 3\n'
                'Example folder 2;Subfolder 3;Stack Overflow;link;https://stackoverflow.com\n'
            )
    file = open('links.csv', encoding="utf-8")
    csvReader = csv.reader(file) # unfortunately dialect='unix' or delimiter=";" doesn't help, you cannot use commas in the alias

    rows = []
    for row in csvReader:
        rows.append(row[0])
    file.close()

    # read the snapshot of open sections
    if not os.path.exists('open_sections.txt'):
        open('open_sections.txt', 'w', encoding='utf-8').close()
    section_file = open('open_sections.txt', encoding="utf-8")
    open_sections = section_file.readlines()
    open_sections = [line.rstrip('\n') for line in open_sections]
    section_file.close()

    # the global database instance
    database={}
    # instances of roots and subroots are only needed to expand them in the tree
    roots={}
    subroots={}
    
    # add main folder dictionaries to database, this could be done in a single loop
    for row in rows:
        rowData = row.split(";")
        if rowData[0] not in database.keys():
            database[rowData[0]] = {}
            roots[rowData[0]] = frame.m_treeCtrl2.AppendItem(root, rowData[0])
        else:
            #print(f"[INFO] Tree control: main folder {rowData[0]} already added")
            pass
           
    # add subfolders and links as nested dictionaries under main folder
    for row in rows:
        rowData = row.split(";")
        if len(rowData) == 1:
            continue
            
        if rowData[1] not in database[rowData[0]].keys():
            database[rowData[0]][rowData[1]] = {}
            # subroot's unique identifier is manfolder+subfolder to handle subfolders with the same name
            subroots[rowData[0]+rowData[1]] = frame.m_treeCtrl2.AppendItem(roots[rowData[0]], rowData[1])
        else:
            #print(f"[INFO] Tree control: subfolder {rowData[1]} already added")
            pass
            
        if len(rowData) == 2:
            continue
            
        # add links as nested dictionary with an alias, path and type
        #print(row)
        database[rowData[0]][rowData[1]][rowData[2]] = {}
        database[rowData[0]][rowData[1]][rowData[2]]["type"] = rowData[3]
        database[rowData[0]][rowData[1]][rowData[2]]["path"] = rowData[4]
        # add links under the subfolder in the tree, we don't need their unique instance ID
        frame.m_treeCtrl2.AppendItem(subroots[rowData[0]+rowData[1]], rowData[2])
    
    # go and expand any main folder or subfolder that has `[-]` in the end of its name
    frame.m_treeCtrl2.Expand(root)

    #print(open_sections)

    for keys in roots.keys():
        #print(keys)
        if keys[-3:] == "[-]" or keys in open_sections:
            frame.m_treeCtrl2.Expand(roots[keys])
            
    for keys in subroots.keys():
        #print(keys)
        if keys[-3:] == "[-]" or keys in open_sections:
            frame.m_treeCtrl2.Expand(subroots[keys])
            
    # automatically scroll to the top
    frame.m_treeCtrl2.SetScrollPos(wx.VERTICAL, 0)

    #print(roots.keys())
    #print("----")
    #print(subroots.keys())

# loadDatabase and loadSearch might be merged in the future, however it's important to work with a temporary database in loadSearch
# if we use the global database and e.g. we apply some filter text plus we rename an item it will overwrite the database with the filtered content!
def loadSearch(searchText):
    #global database
    # IMPORTANT! We are not using the global database instance here, because we don't want to accidentally modify anything in it!
    
    # split the search phrase by " " and remove empty strings (due to multiple spaces) --> searchTextListCleared
    searchTextList = searchText.split(" ")
    searchTextListCleared = []
    for item in searchTextList:
        if item != "":
            searchTextListCleared.append(item)
    
    # show the root text as "searchText" with search phrases + AND words
    searchText = ""
    for i, textItem in enumerate(searchTextListCleared):
        searchText += textItem
        if i < len(searchTextListCleared) - 1:
            searchText += " AND "
    
    # initial tree structure text
    root = frame.m_treeCtrl2.AddRoot(searchText)
    
    # ToDo: probably we shouldn't read the file again and again during typing search text...
    # filtering should be applied on global database instance instead of file reading
    # but filtering the database dictionary sucks compared to filtering file reading, so I don't want to do that :-(
    
    # read csv file's lines to rows[]
    if not os.path.exists('links.csv'):
        with open('links.csv', 'w', encoding='utf-8') as f:
            f.write(
                'Example folder 1\n'
                'Example folder 1;Subfolder 1\n'
                'Example folder 1;Subfolder 1;Google;link;https://google.com\n'
                'Example folder 1;Subfolder 1;YouTube;link;https://youtube.com\n'
                'Example folder 1;Subfolder 2\n'
                'Example folder 1;Subfolder 2;GitHub;link;https://github.com\n'
                'Example folder 2\n'
                'Example folder 2;Subfolder 3\n'
                'Example folder 2;Subfolder 3;Stack Overflow;link;https://stackoverflow.com\n'
            )
    file = open('links.csv', encoding="utf-8")
    csvReader = csv.reader(file)

    # read the snapshot of open sections
    if not os.path.exists('open_sections.txt'):
        open('open_sections.txt', 'w', encoding='utf-8').close()
    section_file = open('open_sections.txt', encoding="utf-8")
    open_sections = section_file.readlines()
    open_sections = [line.rstrip('\n') for line in open_sections]
    section_file.close()

    rows = []
    for row in csvReader:
        itemToShowList = []                      # this will store as many bools as many search phrases we have
        for searchItem in searchTextListCleared: # let's loop through the search phrases
            itemToShow = False                   # default search value, this will be overwritten if search term is found
            for item in row:                     # one row of the file is a list
                if searchItem.lower() in item.lower():
                    itemToShow = True            # set to True if search phrase was found in any fields of a line
            itemToShowList.append(itemToShow)
            
        if not False in itemToShowList:          # there is an AND relation, so if there is any False in the itemToShowList we won't add the item to the filter
            rows.append(row[0])
    file.close()

    # the search database local instance, NOT the global! See function's description!
    search_database={}
    # instances of roots and subroots are only needed to expand them in the tree
    roots={}
    subroots={}
    
    # add main folder dictionaries to database, this could be done in a single loop
    for row in rows:
        rowData = row.split(";")
        
        if rowData[0] not in search_database.keys():
            search_database[rowData[0]] = {}
            roots[rowData[0]] = frame.m_treeCtrl2.AppendItem(root, rowData[0])
        else:
            #print(f"[INFO] Tree control: main folder {rowData[0]} already added")
            pass
           
    numberOfResults = 0
    # add subfolders and links as nested dictionaries under main folder
    for row in rows:
        rowData = row.split(";")
        if len(rowData) == 1:
            continue
            
        if rowData[1] not in search_database[rowData[0]].keys():
            search_database[rowData[0]][rowData[1]] = {}
            # subroot's unique identifier is manfolder+subfolder to handle subfolders with the same name
            subroots[rowData[0]+rowData[1]] = frame.m_treeCtrl2.AppendItem(roots[rowData[0]], rowData[1])
        else:
            #print(f"[INFO] Tree control: subfolder {rowData[1]} already added")
            pass
            
        if len(rowData) == 2:
            continue
            
        # add links as nested dictionary with an alias, path and type
        search_database[rowData[0]][rowData[1]][rowData[2]] = {}
        search_database[rowData[0]][rowData[1]][rowData[2]]["type"] = rowData[3]
        search_database[rowData[0]][rowData[1]][rowData[2]]["path"] = rowData[4]
        # add links under the subfolder in the tree, we don't need their unique instance ID
        frame.m_treeCtrl2.AppendItem(subroots[rowData[0]+rowData[1]], rowData[2])
        numberOfResults += 1
    
    # go and expand any main folder or subfolder that has `[-]` in the end of its name
    frame.m_treeCtrl2.Expand(root)
    for keys in roots.keys():
        frame.m_treeCtrl2.Expand(roots[keys])
            
    for keys in subroots.keys():
        frame.m_treeCtrl2.Expand(subroots[keys])
        
    #print(numberOfResults)
    frame.m_treeCtrl2.SetItemText(root, searchText + " (" + str(numberOfResults) + " results)")
        
    # automatically scroll to the top
    frame.m_treeCtrl2.SetScrollPos(wx.VERTICAL, 0)

# Saves database dictionary as a csv
def saveDataBase():
    global database
    
    # add utf-8 to handle éáőíúű
    file = open('links.csv', "w", encoding="utf-8")
    
    # database is always maximum 3 level deep, this is my constraint
    for i in database:
        file.write(f"{i}\n")
        for j in database[i]:
            file.write(f"{i};{j}\n")
            for k in database[i][j]:
                file.write(f"{i};{j};{k};{database[i][j][k]['type']};{database[i][j][k]['path']}\n")

    file.close()

if __name__ == '__main__':
    '''
    app = wx.App(False)
    frame = HideableWidget(None, 'Hideable Widget')
    app.MainLoop()
    '''

##########################
### SCRIPT STARTS HERE ###
##########################

print(f"[INFO] Application started.")

parse_command_line()

database = {}
# we have to start the wxApp to show popups during lockfile check
application = wx.App(redirect=False)
locale = wx.Locale(wx.LANGUAGE_ENGLISH)

##############################
# LOCKFILE STUFF STARTS HERE #
##############################

# check whether lock file exists
lockExists = os.path.isfile("lockfile")
if lockExists:
    file = open("lockfile", 'r')
    lockPid = int(file.read()) # read pid from lock file
    file.close()

    print(f"[INFO] Lockfile exists, check active processes.")
    # check whether the locker python instance is still running
    # however this code works pretty well, it's slow as hell
    # pythonPids = []
    # for proc in psutil.process_iter(['pid','name']):
    #    if proc.name() == "python.exe":
    #        pythonPids.append(proc.pid)
    # So let's use something faster!
    pythonPids = []
    for pid in psutil.pids():                               # iterate through active PIDs
        if pid == lockPid:                                  # check if the locking PID is active in the system
            if psutil.Process(pid).name() in ["python.exe", "favorit3s.exe"]:  # check if the active PID is a python.exe and it's not just re-used.
                pythonPids.append(pid)
            
    # if the PID from lockfile is still running within the OS, bring it to the front
    if lockPid in pythonPids:
        # Switch to the already running app or give a warning message?
        # vbs cannot reposition the window, only activating it
        # e.g. switch_window.vbs 27076
        # subprocess.Popen(["cmd", "/c", "switch_window.vbs", f"{lockPid}"])
        # with Powershell we can even reposition the window!
        # e.g. powershell -executionpolicy remotesigned -File switch_window.ps1 27076
        print(f"[INFO] Application is already running with PID: {lockPid}. Switch to the application using powershell.")
        subprocess.Popen(["cmd", "/c", "powershell", "-executionpolicy", "remotesigned", "-File", "switch_window.ps1", f"{lockPid}"])
        
        # Don't show warning message, just exit after re-centering the window
        #wx.MessageBox("SVN bookmarks is already running!", 'Warning', wx.OK | wx.ICON_WARNING)
        exit()

# create a lock file with the current pid
file = open("lockfile", 'w')
file.write(str(os.getpid()))
file.close()

##############################
## LOCKFILE STUFF ENDS HERE ##
##############################

# start the gui and the app
frame = HideableWidget(None, 'Hideable Widget')

loadDataBase()

frame.Show()
#wx.lib.inspection.InspectionTool().Show() # Debug inspection tool
application.MainLoop()

# remove lockfile if gracefully exited
os.remove("lockfile")
