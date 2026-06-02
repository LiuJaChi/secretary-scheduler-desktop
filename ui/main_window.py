import tkinter as tk
from tkinter import ttk
from datetime import datetime

from ui.secretary_frame import SecretaryFrame
from ui.schedule_frame import ScheduleFrame
from ui.leave_frame import LeaveFrame
from ui.holiday_frame import HolidayFrame
from ui.calendar_schedule_frame import CalendarScheduleFrame


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("排班管理系統")
        self.geometry("1400x900")
        self.minsize(1100, 700)

        self.status_var = tk.StringVar(value="系統就緒")
        self.summary_var = tk.StringVar(value="摘要載入中...")

        self._build_layout()
        self._build_tabs()
        self.sync_summary_views()
        self.set_status_message("系統已啟動")

    def _build_layout(self):
        """建立主視窗布局"""
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_label = ttk.Label(
            top_frame,
            text="排班管理系統",
            font=("Microsoft JhengHei", 16, "bold")
        )
        title_label.pack(side="left")

        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.datetime_label = ttk.Label(
            top_frame,
            text=f"啟動時間：{now_text}"
        )
        self.datetime_label.pack(side="right")

        summary_frame = ttk.LabelFrame(self, text="系統摘要")
        summary_frame.pack(fill="x", padx=10, pady=(0, 8))

        self.summary_label = ttk.Label(
            summary_frame,
            textvariable=self.summary_var,
            justify="left"
        )
        self.summary_label.pack(anchor="w", padx=10, pady=8)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",
            relief="sunken"
        )
        status_bar.pack(fill="x", side="bottom")

    def _build_tabs(self):
        """建立所有分頁"""
        print("[DEBUG] 開始建立分頁...")

        try:
            print("[DEBUG] 建立秘書管理分頁...")
            self.secretary_tab = SecretaryFrame(self.notebook)
            self.notebook.add(self.secretary_tab, text="秘書管理")
            print("[DEBUG] 秘書管理分頁建立成功")
        except Exception as e:
            print(f"[DEBUG] 秘書管理分頁建立失敗：{e}")

        try:
            print("[DEBUG] 建立月曆班表分頁...")
            self.calendar_tab = CalendarScheduleFrame(self.notebook)
            self.notebook.add(self.calendar_tab, text="月曆班表")
            print("[DEBUG] 月曆班表分頁建立成功")
        except Exception as e:
            print(f"[DEBUG] 月曆班表分頁建立失敗：{e}")

        try:
            print("[DEBUG] 建立班表管理分頁...")
            self.schedule_tab = ScheduleFrame(self.notebook)
            self.notebook.add(self.schedule_tab, text="班表管理")
            print("[DEBUG] 班表管理分頁建立成功")
        except Exception as e:
            print(f"[DEBUG] 班表管理分頁建立失敗：{e}")

        try:
            print("[DEBUG] 建立請假/補休分頁...")
            self.leave_tab = LeaveFrame(self.notebook)
            self.notebook.add(self.leave_tab, text="請假 / 補休")
            print("[DEBUG] 請假/補休分頁建立成功")
        except Exception as e:
            print(f"[DEBUG] 請假/補休分頁建立失敗：{e}")

        try:
            print("[DEBUG] 建立國定假日分頁...")
            self.holiday_tab = HolidayFrame(self.notebook)
            self.notebook.add(self.holiday_tab, text="國定假日")
            print("[DEBUG] 國定假日分頁建立成功")
        except Exception as e:
            print(f"[DEBUG] 國定假日分頁建立失敗：{e}")

        print("[DEBUG] 所有分頁建立完成")

    def set_status_message(self, message):
        """設定狀態列訊息"""
        self.status_var.set(message)

    def sync_summary_views(self):
        """更新主視窗摘要資訊"""
        parts = []

        try:
            if hasattr(self, "secretary_tab") and hasattr(self.secretary_tab, "tree"):
                secretary_count = len(self.secretary_tab.tree.get_children())
                parts.append(f"秘書筆數：{secretary_count}")
        except Exception:
            parts.append("秘書筆數：讀取失敗")

        try:
            if hasattr(self, "schedule_tab") and hasattr(self.schedule_tab, "tree"):
                schedule_count = len(self.schedule_tab.tree.get_children())
                parts.append(f"目前班表清單筆數：{schedule_count}")
        except Exception:
            parts.append("目前班表清單筆數：讀取失敗")

        try:
            if hasattr(self, "leave_tab") and hasattr(self.leave_tab, "tree"):
                leave_count = len(self.leave_tab.tree.get_children())
                parts.append(f"請假紀錄筆數：{leave_count}")
        except Exception:
            parts.append("請假紀錄筆數：讀取失敗")

        try:
            if hasattr(self, "leave_tab") and hasattr(self.leave_tab, "balance_tree"):
                comp_count = len(self.leave_tab.balance_tree.get_children())
                parts.append(f"補休餘額筆數：{comp_count}")
        except Exception:
            parts.append("補休餘額筆數：讀取失敗")

        try:
            if hasattr(self, "holiday_tab") and hasattr(self.holiday_tab, "tree"):
                holiday_count = len(self.holiday_tab.tree.get_children())
                parts.append(f"國定假日筆數：{holiday_count}")
        except Exception:
            parts.append("國定假日筆數：讀取失敗")

        if not parts:
            parts.append("目前沒有可顯示的摘要資料")

        self.summary_var.set(" ｜ ".join(parts))

    def open_schedule_for_date(self, date_str):
        """跳到班表管理頁，並以指定日期查詢"""
        self.notebook.select(self.schedule_tab)

        if hasattr(self.schedule_tab, "start_var"):
            self.schedule_tab.start_var.set(date_str)
        if hasattr(self.schedule_tab, "end_var"):
            self.schedule_tab.end_var.set(date_str)
        if hasattr(self.schedule_tab, "load_data"):
            self.schedule_tab.load_data()

        self.set_status_message(f"已切換到班表管理：{date_str}")

    def open_leave_for_date(self, date_str):
        """跳到請假/補休頁，並把日期帶入相關欄位"""
        self.notebook.select(self.leave_tab)

        if hasattr(self.leave_tab, "leave_date_var"):
            self.leave_tab.leave_date_var.set(date_str)
        if hasattr(self.leave_tab, "comp_date_var"):
            self.leave_tab.comp_date_var.set(date_str)

        self.set_status_message(f"已切換到請假 / 補休：{date_str}")

    def open_calendar_for_date(self, date_str):
        """跳回月曆頁，並顯示指定日期明細"""
        self.notebook.select(self.calendar_tab)

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if hasattr(self.calendar_tab, "year_var"):
                self.calendar_tab.year_var.set(dt.year)
            if hasattr(self.calendar_tab, "month_var"):
                self.calendar_tab.month_var.set(dt.month)
            if hasattr(self.calendar_tab, "load_calendar"):
                self.calendar_tab.load_calendar()
            if hasattr(self.calendar_tab, "show_day_detail"):
                self.calendar_tab.show_day_detail(date_str)
        except Exception:
            if hasattr(self.calendar_tab, "show_day_detail"):
                self.calendar_tab.show_day_detail(date_str)

        self.set_status_message(f"已切換到月曆：{date_str}")

    def refresh_schedule_tab_if_same_date(self, date_str):
        """如果班表管理頁目前查詢的認定就是該日期，則自動重新載入"""
        if not hasattr(self, "schedule_tab"):
            return

        try:
            start_date = self.schedule_tab.start_var.get().strip()
            end_date = self.schedule_tab.end_var.get().strip()
        except Exception:
            return

        if start_date == date_str and end_date == date_str:
            if hasattr(self.schedule_tab, "load_data"):
                self.schedule_tab.load_data()
            self.set_status_message(f"已同步更新班表管理頁：{date_str}")

    def refresh_all_tabs(self):
        """手動刷新所有分頁資料"""
        try:
            if hasattr(self.calendar_tab, "load_calendar"):
                self.calendar_tab.load_calendar()
        except Exception:
            pass

        try:
            if hasattr(self.schedule_tab, "load_data"):
                self.schedule_tab.load_data()
        except Exception:
            pass

        try:
            if hasattr(self.leave_tab, "load_data"):
                self.leave_tab.load_data()
            if hasattr(self.leave_tab, "load_comp_balances"):
                self.leave_tab.load_comp_balances()
        except Exception:
            pass

        try:
            if hasattr(self.holiday_tab, "load_data"):
                self.holiday_tab.load_data()
        except Exception:
            pass

        self.sync_summary_views()
        self.set_status_message("已重新整理所有分頁資料")

    def refresh_secretary_related_options(self):
        """更新秘書相關選項（在秘書新增/停用後調用）"""
        try:
            if hasattr(self, "schedule_tab") and hasattr(self.schedule_tab, "load_secretary_options"):
                self.schedule_tab.load_secretary_options()
        except Exception as e:
            print(f"[DEBUG] 刷新班表管理秘書選單失敗：{e}")

        try:
            if hasattr(self, "leave_tab") and hasattr(self.leave_tab, "load_secretary_options"):
                self.leave_tab.load_secretary_options()
        except Exception as e:
            print(f"[DEBUG] 刷新請假補休秘書選單失敗：{e}")
