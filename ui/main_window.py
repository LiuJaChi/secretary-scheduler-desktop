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
        """\u5efa立主視\u7a97\u4f48局"""
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
        """\u5efa立所有分頁"""
        print("[DEBUG] \u958b始\u5efa\u7acb分頁...")

        try:
            print("[DEBUG] \u5efa\u7acb秘\u66f8管理分頁...")
            self.secretary_tab = SecretaryFrame(self.notebook)
            self.notebook.add(self.secretary_tab, text="秘\u66f8管理")
            print("[DEBUG] 秘書管理分頁建立成功")
        except Exception as e:
            print(f"[DEBUG] 秘書管理分頁建立失敗：{e}")

        try:
            print("[DEBUG] 建\u7acb月曆班表分頁...")
            self.calendar_tab = CalendarScheduleFrame(self.notebook)
            self.notebook.add(self.calendar_tab, text="月曆班表")
            print("[DEBUG] 月曆班表分頁建立成功")
        except Exception as e:
            print(f"[DEBUG] 月曆班表分頁建立失敗：{e}")

        try:
            print("[DEBUG] 建\u7acb班表管理分頁...")
            self.schedule_tab = ScheduleFrame(self.notebook)
            self.notebook.add(self.schedule_tab, text="班表管理")
            print("[DEBUG] 班表管理分頁建立成功")
        except Exception as e:
            print(f"[DEBUG] 班表管理分頁建立失敗：{e}")

        try:
            print("[DEBUG] 建\u7acb請假/補休分頁...")
            self.leave_tab = LeaveFrame(self.notebook)
            self.notebook.add(self.leave_tab, text="請假 / 補休")
            print("[DEBUG] 請假/補休分頁建立成功")
        except Exception as e:
            print(f"[DEBUG] 請假/補休分頁建立失敗：{e}")

        try:
            print("[DEBUG] 建\u7acb國定假日分頁...")
            self.holiday_tab = HolidayFrame(self.notebook)
            self.notebook.add(self.holiday_tab, text="國定假日")
            print("[DEBUG] 國定假日分頁建立成功")
        except Exception as e:
            print(f"[DEBUG] 國定假日分頁建立失敗：{e}")

        print("[DEBUG] 所有分頁建立完成")

    def set_status_message(self, message):
        """\u8a2d\u5b9a狀態\u5217訊\u606f"""
        self.status_var.set(message)

    def sync_summary_views(self):
        """\u66f4\u65b0主視\u7a97\u6458\u8981資\u8a0a"""
        parts = []

        try:
            if hasattr(self, "secretary_tab") and hasattr(self.secretary_tab, "tree"):
                secretary_count = len(self.secretary_tab.tree.get_children())
                parts.append(f"秘\u66f8\u7b46\u6578：{secretary_count}")
        except Exception:
            parts.append("秘\u66f8\u7b46\u6578：讀\u53d6失敗")

        try:
            if hasattr(self, "schedule_tab") and hasattr(self.schedule_tab, "tree"):
                schedule_count = len(self.schedule_tab.tree.get_children())
                parts.append(f"目前班表清\u55ae\u7b46\u6578：{schedule_count}")
        except Exception:
            parts.append("目前班表清\u55ae\u7b46\u6578：讀\u53d6失敗")

        try:
            if hasattr(self, "leave_tab") and hasattr(self.leave_tab, "tree"):
                leave_count = len(self.leave_tab.tree.get_children())
                parts.append(f"請假紀\u9304\u7b46\u6578：{leave_count}")
        except Exception:
            parts.append("請假紀\u9304\u7b46\u6578：讀\u53d6失敗")

        try:
            if hasattr(self, "leave_tab") and hasattr(self.leave_tab, "balance_tree"):
                comp_count = len(self.leave_tab.balance_tree.get_children())
                parts.append(f"補休餘額\u7b46\u6578：{comp_count}")
        except Exception:
            parts.append("補休餘額\u7b46\u6578：讀\u53d6失敗")

        try:
            if hasattr(self, "holiday_tab") and hasattr(self.holiday_tab, "tree"):
                holiday_count = len(self.holiday_tab.tree.get_children())
                parts.append(f"國定假日\u7b46\u6578：{holiday_count}")
        except Exception:
            parts.append("國定假日\u7b46\u6578：讀\u53d6失敗")

        if not parts:
            parts.append("目前沒有可顯示的摘要資\u6599")

        self.summary_var.set(" ｜ ".join(parts))

    def open_schedule_for_date(self, date_str):
        """\u8df3\u5230班表\u7ba1\u7406\u9801，\u4e26\u4ee5\u6307\u5b9a\u65e5\u671f\u67e5\u8a62"""
        self.notebook.select(self.schedule_tab)

        if hasattr(self.schedule_tab, "start_var"):
            self.schedule_tab.start_var.set(date_str)
        if hasattr(self.schedule_tab, "end_var"):
            self.schedule_tab.end_var.set(date_str)
        if hasattr(self.schedule_tab, "load_data"):
            self.schedule_tab.load_data()

        self.set_status_message(f"\u5df2\u5207\u63db\u5230\u73ed\u8868\u7ba1\u7406：{date_str}")

    def open_leave_for_date(self, date_str):
        """\u8df3\u5230\u8acb\u5047/\u88dc\u4f11\u9801\uff0c\u4e26\u628a\u65e5\u671f\u5e36\u5165\u76f8\u95dc\u6b04\u4f4d"""
        self.notebook.select(self.leave_tab)

        if hasattr(self.leave_tab, "leave_date_var"):
            self.leave_tab.leave_date_var.set(date_str)
        if hasattr(self.leave_tab, "comp_date_var"):
            self.leave_tab.comp_date_var.set(date_str)

        self.set_status_message(f"\u5df2\u5207\u63db\u5230\u8acb\u5047 / \u88dc\u4f11：{date_str}")

    def open_calendar_for_date(self, date_str):
        """\u8df3\u56de\u6708\u66c6\u9801\uff0c\u4e26\u986f\u793a\u6307\u5b9a\u65e5\u671f\u660e\u7d30"""
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

        self.set_status_message(f"\u5df2\u5207\u63db\u5230\u6708\u66c6：{date_str}")

    def refresh_schedule_tab_if_same_date(self, date_str):
        """\u5982\u679c\u73ed\u8868\u7ba1\u7406\u9801\u76ee\u524d\u67e5\u8a62\u7684\u5254\u597d\u5c31\u662f\u8a72\u65e5\u671f\uff0c\u5247\u81ea\u52d5\u91cd\u65b0\u8f09\u5165"""
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
            self.set_status_message(f"\u5df2\u540c\u6b65\u66f4\u65b0\u73ed\u8868\u7ba1\u7406\u9801：{date_str}")

    def refresh_all_tabs(self):
        """\u624b\u52d5\u5237\u65b0\u6240\u6709\u5206\u9801\u8cc7\u6599"""
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
        self.set_status_message("已\u91cd\u65b0\u6574\u7406\u6240\u6709\u5206\u9801\u8cc7\u6599")

    def refresh_secretary_related_options(self):
        """\u66f4\u65b0\u79d8\u66f8\u76f8\u95dc\u9078\u9805（\u5728\u79d8\u66f8\u65b0\u589e/\u505c\u7528\u5f8c\u8abf\u7528）"""
        try:
            if hasattr(self, "schedule_tab") and hasattr(self.schedule_tab, "load_secretary_options"):
                self.schedule_tab.load_secretary_options()
        except Exception as e:
            print(f"[DEBUG] \u5237\u65b0\u73ed\u8868\u7ba1\u7406\u79d8\u66f8\u9078\u55ae\u5931\u6557：{e}")

        try:
            if hasattr(self, "leave_tab") and hasattr(self.leave_tab, "load_secretary_options"):
                self.leave_tab.load_secretary_options()
        except Exception as e:
            print(f"[DEBUG] \u5237\u65b0\u8acb\u5047\u88dc\u4f11\u79d8\u66f8\u9078\u55ae\u5931\u6557：{e}")