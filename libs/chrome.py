import os
import signal
import time
from dataclasses import dataclass
from pathlib import Path
from subprocess import Popen, TimeoutExpired

user_data_dir_path = Path(__file__).parent.parent / 'user_data'
user_data_dir_path.mkdir(exist_ok=True)


@dataclass
class Chrome:
    proc = None

    @classmethod
    def run_background(cls):
        """ 開啟背景執行除錯模式的 chrome
        """
        for chrom_exe_path_str in [
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
        ]:
            if Path(chrom_exe_path_str).exists():
                break
        else:
            raise FileNotFoundError('找不到 chrome.exe')

        cls.proc = Popen([
            chrom_exe_path_str,
            "--remote-debugging-port=9222",
            f'--user-data-dir={user_data_dir_path}',
        ])

    @classmethod
    def close(cls):
        cls.proc.kill()
