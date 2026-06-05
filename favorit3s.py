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


def apply_theme(window):
    if window is None:
        return

    if is_dark_theme():
        enable_windows_dark_widgets(window)

    if isinstance(window, (wx.TextCtrl, wx.SearchCtrl)):
        window.SetBackgroundColour(get_theme_color(DARK_FIELD, LIGHT_FIELD))
        window.SetForegroundColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))
    elif isinstance(window, wx.TreeCtrl):
        window.SetBackgroundColour(get_theme_color(DARK_FIELD, LIGHT_FIELD))
        window.SetForegroundColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))
    elif isinstance(window, wx.Button):
        window.SetBackgroundColour(get_theme_color(DARK_PANEL, LIGHT_PANEL))
        window.SetForegroundColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))
    elif isinstance(window, (wx.Frame, wx.Dialog, wx.Panel)):
        window.SetBackgroundColour(get_theme_color(DARK_BG, LIGHT_BG))
        window.SetForegroundColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))
    elif isinstance(window, wx.StaticText):
        window.SetForegroundColour(get_theme_color(DARK_TEXT, LIGHT_TEXT))

    for child in window.GetChildren():
        apply_theme(child)

    window.Refresh()


def show_dark_text_dialog(parent, message, caption, value=""):
    dlg = wx.TextEntryDialog(parent, message, caption, value)
    apply_theme(dlg)
    result = dlg.ShowModal()
    text = dlg.GetValue()
    dlg.Destroy()
    return result, text


def show_dark_message(parent, message, caption, style=wx.OK):
    dlg = wx.MessageDialog(parent, message, caption, style)
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


main_icon_old = PyEmbeddedImage(
    b'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAABHNCSVQICAgIfAhkiAAAIABJ'
    b'REFUeJztnX9oVOeX/1/nmclkMiYziZt18xFXRESKiIiIFBGRUsRPkW4pWlzXqrUipYiISBER'
    b'EZEiUoqIlBKs1ej6KUZKKdIWKSJFpBQpRYqISBHXdbN+8k1mJnE6mdz7nO8f92bunfycSWai'
    b'n20PtJg7c5975t5zn+c857zP+4iqCn/KH1bM81bgT3m+8qcB/MHlTwP4g8ufBvAHlz8N4A8u'
    b'fxrAH1yiz1uBWop0Ysh2J0jEEzhOAhtNIDaJaCOuJkHiRChgpR+VLBGnH2v6iURz5Ao58i15'
    b'3UPhef+OWor8X4sDSCeG/ux8IroM1aUo8xHmoDIXdBYisbHPVovSjchj4BHoIwx3GKy7zV9m'
    b'3NO//t8zhv8TBiAd2Zlg52JlPbAWYT5KEtEEyBSXOc0DaVSeIlwH/ZpY9C7Rxm7diK2G/s9T'
    b'/qENQM7nZsPgetDXUVYg0lr7q2oe5EdUbxI1F3VL8n7tr1k7+YczAGknSl3vSxjzGsr7oG2j'
    b'TuuqDiJPgafetM5vqN5H5AnW9hOJZnFtDkwco42IJlFmAgtRXQC0IdKK1TaMxEcfn26Q77B8'
    b'QvT3u/p2W67mN6DK8g9lAHK2r5WI3YnqdoQFo07vymOE74GfsOZX6swDcjO6dRdO2dfpxPB7'
    b'thlX5yPyEmKXo7IG0cWjLynahcpVhOO6LfXbVH7jdMs/hAHIpUwzDmtRPYyyEJHS3YvqA4Tb'
    b'GL2ERm6RTvZX03uXdqI0dMVw6pdhZAMqryC6AMIzg1qQLoRPMNGzumVGV7WuX0t54Q3AX+eP'
    b'obyJkCz9VLtQuUjEXqS1Zdq8dPk8uwCjr6K6D5EFpSqpA1wnYg7r28mfpkOfqcgLawByihjN'
    b'veuwcgKRhSUfem/8JcScoiGZfl7euHzW3Uhd3WsoB1BdXDozaQ9wjAE9q7tass9Dv3LkhTQA'
    b'6STO7+n3UfaDtAWfaB7kO+AYA6k7lazrtRS5lF1AwW5HZC+QKH6g9CNcwjWHdEdT9/PTcGx5'
    b'4QxAzva1YtzDiOwOjqoF7iN6gIaWqy/q/lvOZ5ahegThtcBZVAvyA2Le161N956vhiPlhTIA'
    b'6cjOxOrHiL5VdLC87dY1hEM0NN95UR/+kMjnPXMQcwBkK0Jj6KPruHaf7mi589yUG0VeGAOQ'
    b'i8/acJ3TwJvFg0o/Rk+Sck7ov7X2Pz/tKhPpxPAsswnhBDA7+ETv4eqmF8kIXohsoHzW3Yjr'
    b'fIjq+uJBJYvRowz+Yz18AN2IpZC6jNj3gVBcQF4iYj6Wjr6Xnptyw+S5zwDS3pskbg55Dt+Q'
    b'aA9q9vIvycv/6AkYOde3EuynwGKG7rTyA9HophchVvD8Z4B62YHlvdCRNMghCskv/tEfPgAz'
    b'mn7EmN1IaCYQVmOdI9LZmxznzGmR52oA0pF9GZUjgbOkedCjJLLnXpQt3lRFN2J1a9MPWLsX'
    b'1cfBB2zhmex6jqoBz3EJkIvZhTh6BmEVMBRB+5QZfR/oxn/N1+y67USJZ5OoNiMmhg4anKiD'
    b'cXJYm9Z3a+NveNft3Yw1p4oRTSWLkXW6NfljLa5Zll7PzQDOpz8BdhX3y6rXkNgO3ZZ4UpPr'
    b'fUuM/+1bjrjrgaUgC0GbQeKo9iPyBPQuyA/Y2Df6TsPjCQetVIdODM/SJxHeD3433yN122v1'
    b'uyfU6XkYgJxLvwLyVWif/AQia3Vb492qX6vzv+Lkk6twdQ/CSqB5fJCI5kGeoJwjohf17eaH'
    b'VdXn8545GPMpyGve5bQAcky3p45V8zpl6zPdBiB/659FwTkHrAPxboCYA7otebIm1xpw94Nu'
    b'rxwsohaVW4h8yEDy+2r6JPJ5ZjnC9ZDv00WdWa2bkw+qdY1yZfqdQMfdgPIqQ3sikW9w5WI1'
    b'LyGdGLmQXUHB+RJ0b8nDV7Iod4BzwBGQfcAJ0O+A3/ywM/4ssQrVL6jP7Jf2KnrsjamfET2N'
    b'Wt+opI1BPSAXQnmEaZJpnQHkAgnczC2EJQCodYhEVlUzbSqdGPKZV3D5GGFx8QMvpHybiJxC'
    b'7C39j5ZHw86Lk8ssQtk0yoyRAz2DyR+sFupHzmfmA5eBZf6hJ1je0HdSt6sxftl6TJcBSCeG'
    b'XGYnqqdCEK6zui21s6rXGMiuw7FnEZkFgALwGDhOJHVO32bcB+iPsQDHfgSsDXS1FswZRA7q'
    b'1mRPVfQ9l92CaEfxgNLBjNSO6cx3TN8S4PS3omwo3lDVpxi+qOo1cunVOPbj4sP3LnSfCDso'
    b'pNonevjg79u3JO9TH92JyCfBkmAMsAWrB+UU40DLKxC38BVKaCbSdWSzC8Y+ofoyfQYw6C5F'
    b'dFXxb5Gr9KZ+qNbwcrZ3CSodAXhELcoPxMx6fTtVsROn/974lET2IMoHKEOAjgTCPlKZvdUw'
    b'Aj/mcMLbCQAwk6jdLJ3T91ymzwCsvj4MQ3exWrg9+c/euUTkQ4Q5oaN3MOa9qXjWuvFf88xo'
    b'/gSjp/xA1dAne0n1vTYVnYsi7g0ET0eRKMgqnP5pgLd7Mi0GIBeftYG8Xjyg3CHRV5Xol3xL'
    b'DEeOF/fVQ+NHI1urAcDQjeQZdE6AnAzeVGlD3U/l8ypM14mZ94DQTKgrybtLpjxumTI9M4B1'
    b'VgPN3h9qEfkK/nXKb790Yvh79i00jCHQbgwfEKteUEnfbe3HyHGQ4EGJzMLYI15V0hTG3ogl'
    b'Er2CFrefcYS1U1K4Aqm5AUg7UZSXQ1G/p4h7vSqe7rO+l1E9GjiW9IMc1a2pa9X2pHVrsoc6'
    b'u88LFxflTVSnntCpb7yFyMPi38Ir0j49hbu1nwGifc1AMKUpjzGxKZdTySliiHsIdK4/sEW4'
    b'TMF2jH/mFCTWcheVI56hgZ9H2CcXswvHP3EC6cVBuVn8W3UO8b5p2Q1MgwHQCrq0+LfIr1MF'
    b'Qkgnhub0VmBtKK5/H+seqSUEWzdidXvqCvBFcXsotOLaw3Ip0zzpcXfhgN4MHE1pxNUV1dB5'
    b'Iqm9AajOAwmtkzr1rV++dzHK3tDDT4Mc1XdmVj2DN6qIexLlZ/8PUHkdR9aPf9IEEo3c82sZ'
    b'QTSO0UXTsR2cBifQDsO/ydQBka7ZDbKo+LdyBWfw6pTHLVN028y7iHwcmgUaUXtgKrMA6j5G'
    b'8WsHxIDOIdtd89zANDgaEjaAHIORkrdUOonT19dInduIo41INOlV6mojaBKRGCL9qO3HSD+W'
    b'VuCtYATtIsKHun2agaOJ1FfkMj8Aazw1WEhBj8m57I+e3jSiRBHbj0b7idgsrvZ4EVCTwzVZ'
    b'/tKUDWBvzU8hkw5+lsxB4wmgpr9rOjzNkIOkD7GDeekkzrO+ZWCXISwjom1Y5mKkDay3XEjx'
    b'f6Dq/XvIry/NXvTg6krp6IvT0HS/lnF0L0/wbBbO4EowS0EbkWJWMwq8D/p+cAKAAbGe7iIg'
    b'kgbtwriP+HvmkZzTHxH5hYHUHer1cZAlZQ51biPwtFa/B2qcDPISQOk7wXStd1F+RWQ5MBOr'
    b'Ccx4lC1lSw7VHCKPQK8h5msceVCNciy50JXAaZyPcVcCm1BdhEgjaHx8YEm5onmQPKiPCCre'
    b'qx4ksqrW1US1NYALJHDTP48o7qy5aA/KbcR8RyTyxWR2HfItMZ6mX/OqkmWVt92sxgMvU1QL'
    b'GLOm1njBmhiAtPcmiclyRN5Hdf04xEw50Ece/44+Bh6gch+RHo+1y/SjtoBrGxE2ge4OZRPv'
    b'A2lEZqE6ZwRngPcdB6QLtAOrl+lvuTdR/kHO52YjzitYu9vDLYzCDjJEJgWPgC5EGlFd5emg'
    b'FqQDU3+UqJPDcRKgSZxokoidjeoilPkgc0Fne/mL0a4BoF3AOYTLpJvv1oKxrOoGIJ/3L8Y4'
    b'B1FeHRWGpdYB+QXDd1h+QaL3SAw+1o1j7999aNdFhFf9Q2kMu4hGfiDvzsXoYmAFKq8hzB11'
    b'EM9gLhOTj3VzKj38Yw+wmV0H+gGiK0Z9KErWI4rimkc3E7vHQOIp8fRiLJeLXAGqD1Dzmr4z'
    b'diJKLmWace1crFmEsgzhTdB5I2YZBdAHGPMFUR1V96lI1QxALqTn4cr7CDspxv2Hi97CRt9j'
    b'sPEeLdhyHTY5l9nsASeKSNoruIM7whBuDwnUFYeGlVg2g74MLCy9oX6VsYl8RNy5ohtbstJO'
    b'lPrMEpTDiK4tefDeze8GfgS+ZkbkK2jqGa63RymTPoLKodB5H+r25kNl/T5vvx8jl/kAODL6'
    b't3zd4QQJ/XK8F6YSmbIBeD8+8yqWg16+f/gND/2tepEZzbt0I2Xj/r21OPMN8EpxTCPr9O3U'
    b'92Oec4oYTb0LMeZNYBdo27A3Kwdcpp5j5FkHumekn6J5VK5iOEPe/jhRhNGHeN0mSHrdI1L3'
    b'SiX+h5zL7EY4VfydKrkRVHdeGPoLXHtM3y2FtU1GpuTUyNm+VnKZD7B6FWF18IZqAbiB8hal'
    b'xZFJ8l2VXfN/M6+jLC/+rXKVeOrmOGegeyjoOy2/6rbUUUSWoOaAvwQMSQLYzgB3EE6XPHwl'
    b'C3oJG13BjNQm3Zq6VlZ4eSD1COVMMTikzMd1N1UYzQsBTyUPZh1qPijRXWhE2EnU3JDz2XVT'
    b'BaZM2gDkb/2zMPYMcChwwNR6e1wOYd2tur35yyBxAghJCtGyr+khcXVDSSWN8EUlM4huTfYw'
    b'I/kxKltQOqAEFhZi81DHz/TtJKHv6zuNv1YSU9BdOBhz1XM6AZEYqm9UCO4Ilk7VHK52MyN5'
    b'0tNdLw7TfR7Ys6Qye6eSOZzUifJ5ZjlGTyKyMqSwg3AF7DHdOjNImYo+BhnKBs6joa78a8Yj'
    b'i7AaAD2E29TxXaX6eg8ydRvYLuczPaB7Rm7p5B5ENun2KeAI8k23qE/fANnsDamrKOhK4Kuy'
    b'zhcWhP79FNx8SPetciHzNS6HA7SztIF+SH1mpnTIicmAVSuaAaQT4xc1nAVeDj7RHjDHEbNb'
    b't80cdgMlmL6szmawrqz4tnRisHZLqHjCItIxWS9Y2onKhcwGlA2j7udFF4BzaCoAD92Fg3I2'
    b'lNUzYLeW84b6s10AZlV5gkRLQazx1JdIZBOq10LoJAO6B6sfT6bauLIl4Pe+VYheBALCROUx'
    b'mC0UkkfHsMAgkmUkhrjl5blz/S9BKMOmcheYfMKnPr0Fq5+W4gb1XuhGxoG3UD3jQdgmKQW9'
    b'jYSQQ+jLxLPLxz7Bl0SkDQiMT3hEU1NJHkA3YnVb411isgnheMjQ4ohu4ZmclrN9FeEJyzIA'
    b'783vX4y1pxBZGIrF/4yyQ7clvxsbdav3A2g1oO6y0b8Xul47UXDXe9473vJiuEw+WfHWR9qJ'
    b'yrnsa6gcDdLSakG/QdgMHEI1yMKprsdxjk+6dr+lpR/Dl16IF1BasayfcBYY1LkorYF+PBrL'
    b'19HNqTQmfwLkqDf7+rrDW0Tco3Khq+wsYnkzQH92Psb5tFjRA3jlVZGt+s7Y2zFfsUeohDKA'
    b'snrCm+GhiDYVo34ij3EjX02qPi/euxLR08GbrxblG9zIdt3a/AuF5pOI7ClCv71o3iZy5oh8'
    b'1t04zsijirdm6zfAw2A8u4HEszHfTOnEILoE8WcAlRyYcdPm+nZbjmzqBKL7isYmEkPZgY1/'
    b'UK4RTGgA0tmbxOhxStZ8fsbIe2VV89bRA/wSaM4C6jOjR+uK5zgvoxoq6+J7BhsrTorI+cx8'
    b'rHwEzAuN9Q0R9gwlinQXDgOpKwgHijOBSAz0PSJ12yflYcebH+HxGfqKsMAHxo4u/0MUJNhG'
    b'C1ns4IQlYrqHAvmWSwiHgXRRd5V92Phb5WxBx/2CnCLGM7Mb9LWSNV/NnrKTFHWpLKK/hMAT'
    b'czAhMMfwa7YTxZUtxa2l1TxR01Hp2y+fdTeiegQI4GiqPyGyd3jJt+7CYVbqLGKOla6rHKA+'
    b'vYoKRTdisVyiuG0Tg7JJvh1jz96aSYCuDB25Xy66SXfhIPlPUD4qIouFRpDDDGQmXG7Ht5Dm'
    b'vnUI+wk4+54SYR8zmsrOUOlGLCK3UPEcGqUZ164b882qyywFCWYbkZtYrWhrJu1EiUR3AW+F'
    b'YhR3iZg9Y7F5618pYHJnEDkdqtSZjXLCj/JVJvU8QPV6cAGW051dOup3B1k3LG9yrZJL6dtt'
    b'OdzBU4icCwxY5+JyXD7vmTPeuWMagJzPzca6BymJ68tpelNfVwy6GBy85Wf7PLyDyBu09I5Y'
    b'o6QTg+FVUI9bT7WAyFUakpVt/eozSxAJModeWPfDiaqQvcpf5yNEgkijh13YXTE+ry6Vxci1'
    b'4vqMtmH1leHjSCfxkXUNcp0Kxc+LfAhFrKIBXYNEto933qg/ygsvFnZTLF1WC3xJjNOTSUl6'
    b'ysnl0KHZ5MzI0qrBTJLwWyvyGLQialjfcTvIEFzcY+A4xYzUl2Xpuu2fnmCi+xhy4rwxNtOf'
    b'fa0SI9CNeM4m8sT/LVFgA/SWOpa/Z5cCAQJY5CYRnRRsXrelfsOYvaj6KCIxwC652DfmMjb6'
    b'D0plFqPsLD4IlScYOTGlVKTINYYcFQDVzSNAlAWzaJjzd7PiBgyR6FqPcHLIoZK72NjpSsLH'
    b'/D7jLuipkHc9C9E99PZWtCvQbanfUL0VHNAl9JvSpJO16xGd439eQPl+Svc5n7yNob24FIjO'
    b'xnF3j7WjGWEA/vbhULAmqUX0Y+LJqREXNLh38Vg4hq60GicogfJ8Ars9tGbnIVQ7X4b4AZwD'
    b'JZVCxh6ulPBJd+HgOGeAYCoWfYWYvDX2WWMNJh1Fn0IkitEtQzOJXzO5O2SsT6iPXKn4GsN1'
    b'r4ueBvH9NDEIG6irf2W074+cAWx8hZ9L90fkNsQuTxVsqRtbskjkC4Y8YyGJJSCH8LaGwVSo'
    b'3EFilW39bGEtEtphiFzl93DhZQX6vtvaj/JxqArIgGypNNIG7j0vzzA0MCvJ5dqkE4PrbC9p'
    b'gqF6Uf+9ccogUP33xqeIfhyioDFYd6d0MgLkMppD8h5DHP1KPyInq0VhplubvkY15GDxqpzP'
    b'eClTNWtAPQi5qoORqyQS5efS23uTXrGIn+HzCChOTqlSKJL/0Qt9D22vdAUR+2ZFDuHgzC5E'
    b'vwmiofISMrjKq2sMMaQqv+Ka6nElDeh1MEESSmQVzzIjildKf0h//wLCZdbovclk3yaQ9pIU'
    b'MbqbgewCcEN0LKQRqazAs4HVoawjID/we/LnqSjq8wFdRhkKt8ZRtnjIozLH2IWDyA0QP9JI'
    b'I6prwO4N4GtqQb/CTVat4ZTuaskS4XKI3KIZeEs6/6tE91IDEDfguPfarlUdg4brXEO4FHoj'
    b'VuLoQSSU+BH5tRKfQzqJY82OUJYvDeZkNajddFvzDb8LmX8xVuHOGH0/P5b8c+oG4V0FsgnR'
    b'N0PfuMcM/ajq9Ljx1FUg2PqKrmcgVRKFLRqA15xJ14SUvEvU3qLKou+29hORj4O3CkA3EQZn'
    b'IF9V9Pb/nn6JcAUyeguj1cPTq7kYCg6BuGWFWYun/5UCqt+EDgVklUo/oieqhfErue5G8oiG'
    b'X7Y4rr4R/k7wI8zgSoplXGoRvuNZS03oS/1um8dLkhjFD3kMzgQJphHyCug873wtgFytFpOX'
    b'p1/0F4RgRlJZQy4zr6IxjLkamo5DY3OZQbesGMWkxHADDcPy9PWwI+ttR9qJ4uqaAHwhWVSv'
    b'1ZSx20Y6UL4ecVz4iQEpe9vmEVBIkKsQejBaXb9lIPEU5UYorT0ftDIaF9WnJZTxnjwkGjta'
    b'K4JqAOLNXcMii/OJuMVYi3fTWv4rivhFjuC9hf/SPC7wcqqiO5q60fr9QOkso0SJR8rPwDVm'
    b'GglnKpXb1eb31V04RCPfFfMZXrLl5XKXAf97G1BKg0DCx/ofDVNG9o4nfgDsesjxngW6ZEh3'
    b'7wcMpuaUKCd6czqaNeg7DY9RLTUA0bVYW34u3mEFYf9BqDiOXpZo089IyG9RXUNvGen0b4nx'
    b'LL0D9AOkpKUcWJ2e1jGiPyEaxDNUVg7p7hsAq0pKqyaRjJiUXn/rn0WJ8wZ+GnYnkbojZdXb'
    b'K6+E/t2PRmrSrdMjmdRwFnSpD1wZU6QTw9PMduBDSkgywK9+Xj8tnIDx5kcwrGNJQ1cMhgxA'
    b'bQizpl1gp6cl+qDzeihjZ0u8VXQ3BU6Oh8/zA1fBWyTcJ+LWkHdfbgT/lFh4LR3xzc+6G71K'
    b'H/2wJKwe3g6KzqF/4pz9VMXfUYUiotKGbWgDMPItMaQEMfOIAtXd+48icqErgZWADk3lCXA5'
    b'SGJIDHQzzmC7fDYGCVMuNxMJI2l5TERqqLveLyWMlFGncK/Led1h0MOEcYjKN4gcCVLEYjBU'
    b'h3ByIlH5dZiWCwEMT3OtARgRLyHRYGrf61bjCxEC6xd+IlK3D0qgWVHgNaL2K+nIvDUilm0G'
    b'humuT6hL1U53oz0MFX54P6LEADzoeXYFxl4B3VsE0ngcAGdwoju9ULiEYxSrK88vTEZ3+a0k'
    b'lqF2EYDBDLQShiOjXfSnpoFuRZegNhQKlZu6ZUYX2ebTGA4SYNwMyEson/IsfdD3GzyxMjMA'
    b'UqoD8qi2TNuS9Qo2in/PHSrNkm+JUZ/ZiWs7EFaXZDWVM9RxQHc2PiWReoJyx2cxB3iJOq0c'
    b'cVSpqJMFAuP1i1CMx8kjvneqFpUn09KxS80biBnCG+Qw9ivABzo2n0PYhOrt0N67GTjAgPOD'
    b'nM9s8tvMNhLsAGwp+rgGMhjpDyDkACT55/5mOZ9dx/9mrqJ6clid4WNU9vMvzfuHQupedI7v'
    b'oLiUzMbaMB6wNmJMDpFQcMxjVDc4bgzVofy5Ba1KQ4TxRC6QQEPM4ei98N5dd+Ho1tQ1VHeA'
    b'fB3yC6KILERpx9pziFkDPtBSsIjUduZynAJIACxRnUPBPY7aDoRXhxFh/AK6nUKqfcSWOhK9'
    b'UTIORd6D2oljncD3ANC4tBM1iIlBUXELo4Qrqy3a+yrhSliRUUOh+k7Lr8xKbUJ0v1chG0K9'
    b'iqxHNMwVCNbW1gAaWkpvove2by9tSaNPET4iFlmn25uvjzabeiXjYaSQrJoq5/CEEo8VQIKX'
    b'WyVGAzEDNo5o8BaFv1QD8Wr+zGqkiApOYxgz86d/pcBAyydYfQtvlxB6m0rq5qNE2CIXsiuk'
    b'nWi19tfSifGcu/Q83MxeREZn8FR1UH4As4N06tCEwA4JbSnROLak7qL6MjhsBhCiRDKxKFYd'
    b'jAkcJ2NrSx3X3zMbY14OHp7excbGhX17b1HLHWlnK/XpdlT3ecRNIcSySBRlK2q3UJ95xDO9'
    b'Kef4AeEBEukCfUpDMj2RkyidvUlyphU1bWDnIbqCmKzBZVHIaEPKqQNyC5FLDKTOlu0/ib2F'
    b'Sg/ITG9cu1baqV3+xRGDIRoq67PUWRslYgooBSCBYsDUlp1S6uaCG2yflF8oJMqCQXk3p/mG'
    b'dGTvgC5HOQChHIZ3AQPMQ2QeqpuAbtTtAdLkMk/lPE+9FCxZRHJYjXuxfU2izATTBjSDnYlo'
    b'qx+ZBEYjUtEuxByH6BUSiS7dVsEOJMJDBnmAsMLXeYlXPlajhtIxE8Wx4YYdBWgpRMHmUSn4'
    b'hIeGEpaKGojY1SVhUTFXK27n4qV6r0lHXxzrBmFsD8QSvKXev9v8/0I6DA2koecqozzjYQc8'
    b'Z9QGoFO5j5VLuiNROR9hrOUxTvpnhnCQqotRdy7hrVo1RQoxkETxN6kUdCN5A5ECiI9axaBa'
    b'MwPw1+VQ9I9+mguTzzp6uX+/ClcdkHOofojqTz42PlcauatocOutmdqD8ivQjshuIFS0qXma'
    b'nEklzfyKqRvFA8JMrNYuLFyIxEI9GxhKDkVB0ojNepYhBmG2fEusJtnAXK7Ny6MX36zr+m9T'
    b'yIULaZQ00IhggB7d1nwIOCT/2TuXQZZ7nrrORWU2aJuHRtY4IgmfxsU3Is0jkvNyIfIEzGPE'
    b'/Q237mcGG+/pLhz5PLsAo3tC1++BlinsPOR7sHkvYigGZR3w6eTHG0cithGVYCZULycRxaEb'
    b'Iz2haXE2/9OXhKnTrI4QHVwZpETVIjq1rKNLt5+inYPPsC2dxHUjeb8x5CPwQSONmUYGbCMS'
    b'iWFNlKgTxYrBqMWJOkRxcKyDRHM0pftH72CuzYSXE+XBVCKPujXZI+fTvzCEZxCWy2c06rs1'
    b'IIj2nNpk8PKZewBRmpp6eJYJrTsym4hNAlU1AGknSoyXGQrcKN3IFKnj67WbwbCeMpuBZ83D'
    b'HSnPx0ilodwkV9Poh0Vm+UYwdGDquEPlOuIbgJKkvncptNQAjOMu9HsfehLhPoDxCQ3C6d95'
    b'lDRerJI09c9EWBrauz/E1k+tWXJdKuthCH1R5jNYqF1iRXR5SezBVFa1PPqY3KZYRq5xHKlR'
    b'PCAUv/BK0B5AEQ9gAqCD0FgTZ+T3wbaSuj+RuzQ2TCl37zlShHS3czBSy147a0JX70HyU8dN'
    b'2OgDdKhyWqIISyuheClHPK4EwgGsX0gn+2HIACLcGsbnV/3YdDSyFEKpW+X7qmTuInI9SBgZ'
    b'U4IQqqLI+f83uyT9q3KTeFv5Badjic0/LAGLqiyGeHVn4PrI0mLWFAD5gb94W2/PADxrCKpo'
    b'lGVVz1GrrvFSu3hbtjpbnXUul/wNJASslDVjMnFMRTTyMkiYyfNmNQzYRwQHFDrCAtzI7KmO'
    b'WxyuE4OVl70OLADkMNwe0t17IJ41fB9KtrRidF3VlPDoWsI16r8Qa6lOJ4wWLCVVx8zl75k1'
    b'VRnbF7nQlfArl4Z2MF2IrV6bdw1VHikJcKvnB/T1zURlnZf0A9BHYQIqA0Nrqd4kaE+SAH11'
    b'MixZo0pdbHHJFOQxcFQlzuATMXwfsHzZRixrq9bhG8BJzC4xYJUHyPgsXhWJMb8Ul2CPQaVi'
    b'XqIxpU7nj1j/801F5zvk0eZ/omQq0rXEItVCqqxCCaYg5VZVkTvRuluI+pg3YxB9jabs+Exk'
    b'lYjRV4u9AADEXqlq5ZG3BAfOrLKsaulhHcG2ei4cei8agL7dlkMlVL8mbVhTUkc2GfHAn3ZJ'
    b'qNPHE4xObfs3THxK9jAPwEKMVsWRlQskQLeGrpYHU90WdX/BAQ0VcZLJy9bCAAAJpElEQVQE'
    b'GRNxXK54NHmElnJ5CFKydJXmzOsjl1ECh0rZMeW2qJ5HG56CfqOhufqNkAztFAM9Hn9uCX5w'
    b'EuLxFqQ3U1p2/gWZVFWhZ7oRi9GfisuYaiNqV04F0yDfEvMQVT7i28NRnBlOuFV6gb7GHggR'
    b'IqBtOLphSo2MJTKnqIQnP1XE11Ou9DY/QQnTq8yj4FZG5jBc+vpmYtlAmHQCuVyL3j24db95'
    b'eQh8bIMumlLjyJ7eNkpo8ngEkREMbyU3x6uBMx14rUlAJIbwPvH05Kcj175SipWLVJtwAvDB'
    b'pBE5E8xgEkd1r0c+MUmps2+VxESE75mVrE3VVGPjA0qKRlhGPDIpP0DaiTIo+0v9Fi6Nxuw6'
    b'8u2oTz5A+TKExp2Nlb2j8ctMqIj39oUpUp9gqV3VUWvyFw9xO6SALMTV9yYzg8ln2YVYfT8U'
    b'+s0hkZEAzyqJPyuGStCnEA+IpVcjbAiN9Qg7Ov3MCAPQjViidacp7fH7Br9nN1Q8nebTc9FQ'
    b'EwTl1nAK9GqKx/apx8GG6+G30pBdV4nucqErQVQ/AALOItEzNDTVpO6wKNFoiJVMYpOBi8vZ'
    b'vlZEDkEx9ZvD8BGDyYejfX/0m1I/4yliTwZ7a5KoPVj5dKqLAxYstX7io7ZVx783PwZOEfD0'
    b'zsS1h8mny9oWeuxdDW94/Y6KnAP3IfJpTXyXsET4lSL9O5R0ZClD5BQxIu7uYUG3H0EujYW6'
    b'GtUAdCOWhpbLiIa2O/ISjp4oN0Ts3UizFIoIozQqFfXhmYx4PHmmo4SnV2Q5rhwtqwfA79kV'
    b'CMdCXEkF4KNat3AFIJfPgYSY1XVxuR3JpRNDMrMB2B2CyHUjZqxGHsA4XMFeBUvkmNcXwK9j'
    b'El1LxO4vK1vlebBLCLhwupEq8vaMI15DBQ5TWhL9Js/M7vF8Gfm8Zw5WTxDQzDqIXCShtaNw'
    b'CYvbmkdDORloxhm9ADUs0omhr3cxwrEQ3jKHyMf88/jE3uOviw1N90EOQpgmTfeiDTsmDLVG'
    b'E0nQMJvWQwZSNWXDKJGG5jsoh1EdKnRJIBwkn948mlMoF//ehpiPEFaFpv7bRO3RWhA4jSZe'
    b'5zH7axG/LySxduIdWH//Ioy0U9IXQa/iDJ6eyGkd1wB0I5ZC8hrIR6hfMubh6I6QzOwa17s2'
    b'zhyEIJQs/DgtNYe+6EYs2dQVhE9CBREJLMeoz24J6y4d2Zk4dScgxKClPEL0gA8tm0aJ3Edl'
    b'qIVNHJFF471s8kXPHMQ5gwz1VlQL+iMmcqQc7qEJPWOvo4b9BDgboh6dCRwjnt08dup1GHpG'
    b'pOqUcxOJ7qGAmI9Avgg1gmhD7QnqMxuknaj8rX8WlqOIbAkyZqQxfEC+Zdp1Bu4jIZibspjm'
    b'7KhJOenoe4kB0+5VKw3da3mIMXvL9VnK2hrprpYsrnMQzKWA+Jgkqid5mj04qk9gS4o/exi0'
    b'07L+Dxfdmuyhjn0gX4WKTFtBTxPLHGDA6QC7K3RKGjX7yae+nM4Zq0Tfkk6huphBt8QApBMj'
    b'5zPLUPcKYZg9/Ibqron6IoSlfLLDd1v7kbqDiFxFbVCyrfYAtuFweHfg9cCTMHrmLnWRaeAc'
    b'GF10cypNRD9AuBYEuGQmYo8gsnYYQ/lRZjSNuW2aFhEJO4KziERLu348S7+Bx6S+KHCytRuV'
    b'PRSaKyLHriiwo9sST3AGtyPmHEXWb4mhug/jXh0qzKQh8lIpcwe3hzBoz0v07eaH1MkWwjQ0'
    b'QyhZr9t3D8heBpor6y1QC4mEGVrFYDyAiFx81iYd6WMg50AWFSHeyh1gEzPGa983ulScKPFm'
    b'AvkAOB0giCSKyAqsXiKW2YVlUYi5owDcq0kCpVKx0TgqI/Xw7mOBcOv45ymD+rAkIKQsk45n'
    b'S3EHz2DZX1Lho/oAYQczmm9MJsYy6fbx0okhl9kF7Aff2/feJAcRr9jUO9iFRjbo9qbn4VAB'
    b'IGf6Z1E3uAk1+ynpHDpMvPKyH0GOMyN5/XnNBHIp08wgV8AHuHrVS4VhD76AyCWMHp0KMeak'
    b'U6W6EctA6gxqtnq1c2p9OFOUkq7c9CORSSs4FZFTxORc+k2iTgfI8ZKH793AK6D3SmcyVoE9'
    b'Sy5zWj7PLJ8WHr/hUpfKAwFoxsvKhhxB7cFwgjr2TZUVddIzQMkgZ/taMe5eYOfIohLNg3yD'
    b'teeoi9320Ts1E+nE8HvfQtSuBt7Dq0UMPUS1wD2QY8xKfcl/9zcTdfaMqrvaApjvED0HsZ9I'
    b'JLpqGcqWCyRw+5aCuw5hZyihM6RQHo+L4FDZfRsnumY1DAD8RERzZg2W/aCrh/Hl4K9p91H5'
    b'hrrIV+TzD3nWWpiqb+C/oTF6e2M0mBUoG/xkyPzSNV0tKjmEMxA5E86NT6i7kgW9D+Yaol/i'
    b'DN6viu7tRGnoiiFNSVzndb/Z1VJEZ480WulCOI6JXqnmS1Q1AygO2EmcXHoTyBbQlaM7VmpR'
    b'+dXLDspNsA9xzBMa9OlEDSqkE8PAs1loYRZuZA5iF4KsRlk+5vqu2g3yDZh2ZjT9ONZbLKeI'
    b'kcpuRnUzoqvGdAo9x+snkJuoPMLYJ5i6LnIzusfywj1D7W0kG2mjTtqwOhfRxX69xGJK+iWE'
    b'7xO/IeYKxrZXmwQbamAAxYEvPmvDddagvA8sQbSx1Kp9US34Fb5pn7njqd9MIotIv+8AJYos'
    b'Hh692UwgiVeo2TzGuA6QBvkGY84yOPBzubTscvFZG9ZZjfIeyrJxdHcQsiBpIIuS9evus6j0'
    b'I+qgNCLSCCT94oxm72+dOc6uIwd0efA8e5nMzAe12kXVzACKFzhFjFR6JcjrwGpUl5SweFRb'
    b'lH7QW4hcR8zXNDTdn+y6LaeIMbN3Ba5Z7/X5YVmNdX8MegPMNWbId7qxBiX6w6TmBlC80Cli'
    b'/FNvGzayBFdXg65BZDZKEjQ+qRvrefI5vNnjAeg1jLmJIw9oauqplsMm7USp62mDyEsYXYXK'
    b'K3iZtyHdyy9CUUB8fwTNgTz1gTLXIHIH0//Qb1Y1LTJtBjDiwu1ESWTn4+oyYC6qc0HmgLb5'
    b'U34CNIESZYjBw6OwyyL62CeXfojKQ+LmJ6KN3bUGmxR178RQ6J2DG12K2Dm4zPMdtzbQhJ82'
    b'T/jMZd6DFsn5zuQjxNfdyG/Ek3eeZ+TxuRnAcJFTxGjNJLDROG7e4JgoUZ9K1qiloJaodRis'
    b'd5B8Drc1/1zj9SHxupV3x5H6OFYMdSaKzZsiA0ldvUPBOsStQ3cq90JERX15YQzgT3k+Mv1R'
    b'rj/lhZI/DeAPLn8awB9c/jSAP7j8aQB/cPnTAP7g8v8BFVz1HKZ+pCMAAAAASUVORK5CYII=')

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
        self.m_treeCtrl2 = wx.TreeCtrl(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(self.size[0] - 15, self.size[1] - 80), wx.TR_DEFAULT_STYLE)
        self.search_bar = wx.SearchCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(self.size[0] - 45,-1), wx.TE_LEFT)
        self.search_bar.ShowCancelButton(True)
        #self.search_bar.SetHint("You can search your favorites here!")
        self.search_bar.SetDescriptiveText("Find your favorites here!")
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
        helpText = "Features\n\nFavorites tree:\n\
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
        david.dudas@thyssenkrupp.com"
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
    file = open('links.csv', encoding="utf-8")
    csvReader = csv.reader(file) # unfortunately dialect='unix' or delimiter=";" doesn't help, you cannot use commas in the alias

    rows = []
    for row in csvReader:
        rows.append(row[0])
    file.close()

    # read the snapshot of open sections
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
    file = open('links.csv', encoding="utf-8")
    csvReader = csv.reader(file)

    # read the snapshot of open sections
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
            if psutil.Process(pid).name() == "python.exe":  # check if the active PID is a python.exe and it's not just re-used.
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
