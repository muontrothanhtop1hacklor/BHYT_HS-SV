# -*- coding: utf-8 -*-
"""
src/utils/resource_monitor.py
Module giám sát tài nguyên bộ nhớ chuẩn:
- Đo RAM nền của hệ điều hành trước khi chạy.
- Đo RSS đỉnh (Resident Set Size) của TOÀN BỘ CÂY TIẾN TRÌNH (Tiến trình cha + tất cả tiến trình con).
- Tách biệt rõ ràng giữa RAM hệ thống và RAM thực tế của tiến trình.
"""

import os
import time
import threading
import psutil


class ProcessTreeMemoryMonitor:
    def __init__(self, interval_sec: float = 0.1):
        self.interval_sec = interval_sec
        self.parent_proc = psutil.Process(os.getpid())
        self.stop_event = threading.Event()
        self.thread = None

        self.baseline_sys_used_bytes = 0
        self.baseline_sys_total_bytes = 0
        self.peak_sys_used_bytes = 0

        self.peak_process_tree_rss_bytes = 0
        self.samples = []

    def start(self):
        # Ghi nhận RAM nền hệ thống
        vm = psutil.virtual_memory()
        self.baseline_sys_used_bytes = vm.used
        self.baseline_sys_total_bytes = vm.total
        self.peak_sys_used_bytes = vm.used
        self.peak_process_tree_rss_bytes = self._get_tree_rss()

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def _get_tree_rss(self) -> int:
        total_rss = 0
        try:
            procs = [self.parent_proc] + self.parent_proc.children(recursive=True)
            for p in procs:
                try:
                    if p.is_running():
                        total_rss += p.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
        return total_rss

    def _monitor_loop(self):
        while not self.stop_event.is_set():
            # Lấy RSS cây tiến trình
            rss = self._get_tree_rss()
            if rss > self.peak_process_tree_rss_bytes:
                self.peak_process_tree_rss_bytes = rss

            # Lấy RAM hệ thống
            try:
                vm_used = psutil.virtual_memory().used
                if vm_used > self.peak_sys_used_bytes:
                    self.peak_sys_used_bytes = vm_used
            except Exception:
                pass

            time.sleep(self.interval_sec)

    def stop(self) -> dict:
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

        # Đo lần cuối
        final_rss = self._get_tree_rss()
        if final_rss > self.peak_process_tree_rss_bytes:
            self.peak_process_tree_rss_bytes = final_rss

        return {
            "baseline_sys_used_gb": round(self.baseline_sys_used_bytes / (1024**3), 2),
            "baseline_sys_total_gb": round(self.baseline_sys_total_bytes / (1024**3), 2),
            "peak_sys_used_gb": round(self.peak_sys_used_bytes / (1024**3), 2),
            "peak_process_tree_rss_mb": round(self.peak_process_tree_rss_bytes / (1024**2), 2),
            "peak_process_tree_rss_gb": round(self.peak_process_tree_rss_bytes / (1024**3), 3),
        }
