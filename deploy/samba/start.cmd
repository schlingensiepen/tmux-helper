@echo off
REM Open-TmuxTabs v2.0.0 -- Starter fuer die Samba-Freigabe
REM Startet tmux-helper via pipx aus dem Wheel neben dieser Datei.
REM Voraussetzungen: Python 3.10+, pipx, Windows Terminal, OpenSSH-Client

pipx run --spec "%~dp0open_tmux_tabs-2.0.0-py3-none-any.whl" open-tmux-tabs
