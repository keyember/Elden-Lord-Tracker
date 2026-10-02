
"""Diagnostic Windows 64 bits, sans injection ni ecriture dans le jeu.
Ne lit que l'en-tete PE (2 octets) pour verifier l'acces memoire.
Ne fournit PAS encore le timer ou les etats de chargement.
"""
from tracker.i18n import tr, translate_status
import ctypes as C
from ctypes import wintypes as W
import json
import os
import struct
import sys
from pathlib import Path
from datetime import datetime, timezone

class PROCESSENTRY32W(C.Structure):
    _fields_ = [('dwSize', W.DWORD), ('cntUsage', W.DWORD), ('th32ProcessID', W.DWORD), ('th32DefaultHeapID', C.c_size_t), ('th32ModuleID', W.DWORD), ('cntThreads', W.DWORD), ('th32ParentProcessID', W.DWORD), ('pcPriClassBase', W.LONG), ('dwFlags', W.DWORD), ('szExeFile', W.WCHAR * 260)]

class MODULEENTRY32W(C.Structure):
    _fields_ = [('dwSize', W.DWORD), ('th32ModuleID', W.DWORD), ('th32ProcessID', W.DWORD), ('GlblcntUsage', W.DWORD), ('ProccntUsage', W.DWORD), ('modBaseAddr', C.c_void_p), ('modBaseSize', W.DWORD), ('hModule', W.HMODULE), ('szModule', W.WCHAR * 256), ('szExePath', W.WCHAR * 260)]

def api():
    k = C.WinDLL('kernel32', use_last_error=True)
    declarations = {'CreateToolhelp32Snapshot': ([W.DWORD, W.DWORD], W.HANDLE), 'Process32FirstW': ([W.HANDLE, C.POINTER(PROCESSENTRY32W)], W.BOOL), 'Process32NextW': ([W.HANDLE, C.POINTER(PROCESSENTRY32W)], W.BOOL), 'Module32FirstW': ([W.HANDLE, C.POINTER(MODULEENTRY32W)], W.BOOL), 'Module32NextW': ([W.HANDLE, C.POINTER(MODULEENTRY32W)], W.BOOL), 'OpenProcess': ([W.DWORD, W.BOOL, W.DWORD], W.HANDLE), 'ReadProcessMemory': ([W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)], W.BOOL), 'CloseHandle': ([W.HANDLE], W.BOOL)}
    for name, (args, ret) in declarations.items():
        f = getattr(k, name)
        f.argtypes = args
        f.restype = ret
    return k

def processes(k):
    h = k.CreateToolhelp32Snapshot(2, 0)
    if h == C.c_void_p(-1).value:
        raise C.WinError(C.get_last_error())
    result = []
    try:
        e = PROCESSENTRY32W()
        e.dwSize = C.sizeof(e)
        ok = k.Process32FirstW(h, C.byref(e))
        if not ok:
            raise C.WinError(C.get_last_error())
        while ok:
            result.append((e.th32ProcessID, e.szExeFile))
            ok = k.Process32NextW(h, C.byref(e))
    finally:
        k.CloseHandle(h)
    return result

def module(k, pid):
    h = k.CreateToolhelp32Snapshot(8 | 16, pid)
    if h == C.c_void_p(-1).value:
        raise C.WinError(C.get_last_error())
    try:
        e = MODULEENTRY32W()
        e.dwSize = C.sizeof(e)
        ok = k.Module32FirstW(h, C.byref(e))
        if not ok:
            raise C.WinError(C.get_last_error())
        while ok:
            if e.szModule.lower() == 'eldenring.exe':
                return (e.szExePath, e.modBaseAddr, e.modBaseSize)
            ok = k.Module32NextW(h, C.byref(e))
        raise ValueError('Module eldenring.exe introuvable')
    finally:
        k.CloseHandle(h)

def version(path):
    v = C.WinDLL('version', use_last_error=True)
    v.GetFileVersionInfoSizeW.argtypes = [W.LPCWSTR, C.POINTER(W.DWORD)]
    v.GetFileVersionInfoSizeW.restype = W.DWORD
    v.GetFileVersionInfoW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p]
    v.GetFileVersionInfoW.restype = W.BOOL
    v.VerQueryValueW.argtypes = [C.c_void_p, W.LPCWSTR, C.POINTER(C.c_void_p), C.POINTER(W.UINT)]
    v.VerQueryValueW.restype = W.BOOL
    handle = W.DWORD()
    size = v.GetFileVersionInfoSizeW(path, C.byref(handle))
    if not size:
        return None
    buffer = C.create_string_buffer(size)
    if not v.GetFileVersionInfoW(path, 0, size, buffer):
        return None
    ptr = C.c_void_p()
    length = W.UINT()
    if not v.VerQueryValueW(buffer, '\\', C.byref(ptr), C.byref(length)) or length.value < 16:
        return None
    values = struct.unpack('<4I', C.string_at(ptr, 16))
    if values[0] != 4277077181:
        return None
    ms, ls = values[2:4]
    return f'{ms >> 16}.{ms & 65535}.{ls >> 16}.{ls & 65535}'

def diagnose():
    if os.name != 'nt':
        raise ValueError('Diagnostic reserve a Windows')
    if C.sizeof(C.c_void_p) != 8:
        raise ValueError('Python 64 bits requis')
    k = api()
    items = processes(k)
    protected = [name for _, name in items if 'easyanticheat' in name.lower() or name.lower() == 'start_protected_game.exe']
    if protected:
        raise ValueError('Processus EAC detecte : diagnostic arrete. Aucun contournement effectue.')
    games = [pid for pid, name in items if name.lower() == 'eldenring.exe']
    if len(games) != 1:
        raise ValueError("Lance une seule instance d'Elden Ring avec EAC desactive")
    pid = games[0]
    path, base, size = module(k, pid)
    h = k.OpenProcess(1024 | 16, False, pid)
    if not h:
        raise C.WinError(C.get_last_error())
    try:
        buffer = C.create_string_buffer(2)
        n = C.c_size_t()
        if not k.ReadProcessMemory(h, base, buffer, 2, C.byref(n)):
            raise C.WinError(C.get_last_error())
        if n.value != 2 or buffer.raw != b'MZ':
            raise ValueError('En-tete executable inattendu')
    finally:
        k.CloseHandle(h)
    return {'status': 'memory_read_access_ok', 'pid': pid, 'executable_path': path, 'file_version': version(path), 'module_base': hex(base), 'module_size': size, 'read_only': True, 'bytes_read': 2, 'timer_implemented': False, 'note': "Absence de processus EAC connus ne prouve pas a elle seule la desactivation d'EAC."}
if __name__ == '__main__':
    report = {'time': datetime.now(timezone.utc).isoformat()}
    try:
        report.update(diagnose())
    except (OSError, ValueError) as exc:
        report.update(status='error', error=str(exc))
    folder = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'EldenRingTracker'
    try:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / 'memory_probe.json'
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print('Rapport :', path)
    except OSError as exc:
        print("Impossible d'ecrire le rapport :", exc)
    sys.exit(1 if report.get('status') == 'error' else 0)
