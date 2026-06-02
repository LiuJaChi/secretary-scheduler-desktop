import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import calendar

from database import get_connection
from scheduler_service import SHIFT_LABELS, update_schedule_one_click


class QuickScheduleEditDialog(tk.Toplevel):
    SHIFT_OPTIONS = {
        "早班": "MORNING",
        "中晚班": "EVENING",
        "休息": "OFF",
        "補休": "COMP",
    }
    SHIFT_OPTIONS_REVERSE = {v: k for k, v in SHIFT_OPTIONS.items()}

    def __init__(self, master, schedule_row, on_saved=None):
        super().__init__(master)
        self.title("快速調班")
        self.geometry("420x240")
        self.resizable(False, False)

        self.schedule_row = schedule_row
        self.on_saved = on_saved

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Label(container, text=f"日期：{self.schedule_row['work_date']}").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=5
        )
        ttk.Label(container, text=f"秘書：{self.schedule_row['secretary_name']}").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=5
        )

        ttk.Label(container, text="班別").grid(row=2, column=0, sticky="w", pady=5)
        self.shift_var = tk.StringVar()
        self.shift_combo = ttk.Combobox(
            container,
            textvariable=self.shift_var,
            state="readonly",
            values=list(self.SHIFT_OPTIONS.keys()),
            width=18
        )
        self.shift_combo.grid(row=2, column=1, sticky="w", pady=5)

        current_shift = self.schedule_row["shift_type"]
        self.shift_var.set(self.SHIFT_OPTIONS_REVERSE.get(current_shift, "休息"))

        ttk.Label(container, text="原因 / 備註").grid(row=3, column=0, sticky="nw", pady=5)
        self.reason_text = tk.Text(container, width=28, height=5)
        self.reason_text.grid(row=3, column=1, sticky="w", pady=5)
        self.reason_text.insert("1.0", self.schedule_row.get("remark", "") or "")

        btn_frame = ttk.Frame(container)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="e", pady=(10, 0))

        ttk.Button(btn_frame, text="儲存", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side="left", padx=5)

    def save(self):
        shift_label = self.shift_var.get().strip()
        reason = self.reason_text.get("1.0", "end").strip()

        if not shift_label:
            messagebox.showwarning("提醒", "請選擇班別")
            return

        new_shift = self.SHIFT_OPTIONS[shift_label]
        schedule_id = self.schedule_row["id"]

        ok, msg, _ = update_schedule_one_click(schedule_id, new_shift, reason)
        if ok:
            messagebox.showinfo("成功", msg)
            if self.on_saved:
                self.on_saved(self.schedule_row["work_date"])
            self.destroy()
        else:
            messagebox.showerror("錯誤", msg)


class CalendarScheduleFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        now = datetime.now()
        self.year_var = tk.IntVar(value=now.year)
        self.month_var = tk.IntVar(value=now.month)
        self.selected_date_var = tk.StringVar(value="")

        self._day_button_refs = {}
        self._build_ui()
        self.load_calendar()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="年份").pack(side="left", padx=(0, 5))
        self.year_combo = ttk.Combobox(
            top,
            textvariable=self.year_var,
            state="readonly",
            width=8,
            values=[y for y in range(2020, 2036)]
        )
        self.year_combo.pack(side="left", padx=5)

        ttk.Label(top, text="月份").pack(side="left", padx=(10, 5))
        self.month_combo = ttk.Combobox(
            top,
            textvariable=self.month_var,
            state="readonly",
            width=6,
            values=[m for m in range(1, 13)]
        )
        self.month_combo.pack(side="left", padx=5)

        ttk.Button(top, text="載入月曆", command=self.load_calendar).pack(side="left", padx=10)
        ttk.Button(top, text="今天", command=self.go_today).pack(side="left", padx=5)

        self.selected_label = ttk.Label(top, textvariable=self.selected_date_var, foreground="blue")
        self.selected_label.pack(side="right")

        main_pane = ttk.PanedWindow(self, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left_frame = ttk.LabelFrame(main_pane, text="月曆")
        right_frame = ttk.LabelFrame(main_pane, text="日期明細")

        main_pane.add(left_frame, weight=3)
        main_pane.add(right_frame, weight=2)

        self.calendar_container = ttk.Frame(left_frame)
        self.calendar_container.pack(fill="both", expand=True, padx=8, pady=8)

        self.detail_tree = ttk.Treeview(
            right_frame,
            columns=("id", "name", "shift", "time", "source", "remark"),
            show="headings"
        )
        self.detail_tree.heading("id", text="ID")
        self.detail_tree.heading("name", text="秘書")
        self.detail_tree.heading("shift", text="班別")
        self.detail_tree.heading("time", text="時間")
        self.detail_tree.heading("source", text="來源")
        self.detail_tree.heading("remark", text="備註")

        self.detail_tree.column("id", width=60, anchor="center")
        self.detail_tree.column("name", width=100, anchor="w")
        self.detail_tree.column("shift", width=90, anchor="center")
        self.detail_tree.column("time", width=120, anchor="center")
        self.detail_tree.column("source", width=90, anchor="center")
        self.detail_tree.column("remark", width=180, anchor="w")

        self.detail_tree.pack(fill="both", expand=True, padx=8, pady=8)

        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))

        ttk.Button(btn_frame, text="重新整理日期明細", command=self.reload_selected_day).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="快速調班", command=self.open_quick_edit).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="前往班表管理", command=self.jump_to_schedule).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="前往請假 / 補休", command=self.jump_to_leave).pack(side="left", padx=5)

    def set_status(self, message):
        root = self.winfo_toplevel()
        if hasattr(root, "set_status_message"):
            root.set_status_message(message)

    def sync_summary(self):
        root = self.winfo_toplevel()
        if hasattr(root, "sync_summary_views"):
            root.sync_summary_views()

    def go_today(self):
        now = datetime.now()
        self.year_var.set(now.year)
        self.month_var.set(now.month)
        self.load_calendar()

    def load_calendar(self):
        for widget in self.calendar_container.winfo_children():
            widget.destroy()

        self._day_button_refs = {}

        year = int(self.year_var.get())
        month = int(self.month_var.get())

        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        for col, name in enumerate(weekdays):
            lbl = ttk.Label(self.calendar_container, text=name, anchor="center")
            lbl.grid(row=0, column=col, padx=3, pady=3, sticky="nsew")

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)

        for row_index, week in enumerate(month_days, start=1):
            for col_index, day in enumerate(week):
                if day == 0:
                    frame = ttk.Frame(self.calendar_container)
                    frame.grid(row=row_index, column=col_index, padx=3, pady=3, sticky="nsew")
                    continue

                date_str = f"{year:04d}-{month:02d}-{day:02d}"
                summary = self.get_day_summary(date_str)

                text = f"{day}\n{summary}"
                btn = tk.Button(
                    self.calendar_container,
                    text=text,
                    justify="left",
                    anchor="nw",
                    width=14,
                    height=5,
                    command=lambda d=date_str: self.show_day_detail(d)
                )
                btn.grid(row=row_index, column=col_index, padx=3, pady=3, sticky="nsew")
                self._day_button_refs[date_str] = btn

        for i in range(7):
            self.calendar_container.columnconfigure(i, weight=1)
        for i in range(len(month_days) + 1):
            self.calendar_container.rowconfigure(i, weight=1)

        self.set_status(f"已載入月曆：{year}-{month:02d}")

    def get_day_summary(self, date_str):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT shift_type, COUNT(*) AS cnt
            FROM schedules
            WHERE work_date = ?
            GROUP BY shift_type
            ORDER BY shift_type
        """, (date_str,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return "無班表"

        parts = []
        for row in rows:
            label = SHIFT_LABELS.get(row["shift_type"], row["shift_type"])
            parts.append(f"{label}:{row['cnt']}")
        return "\n".join(parts)

    def get_day_schedule_rows(self, date_str):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                sc.id,
                sc.work_date,
                sc.shift_type,
                sc.start_time,
                sc.end_time,
                sc.source_type,
                sc.remark,
                s.name AS secretary_name
            FROM schedules sc
            JOIN secretaries s ON s.id = sc.secretary_id
            WHERE sc.work_date = ?
            ORDER BY sc.id ASC
        """, (date_str,))
        rows = cur.fetchall()
        conn.close()
        return rows

    def show_day_detail(self, date_str):
        self.selected_date_var.set(f"目前日期：{date_str}")

        for row in self.detail_tree.get_children():
            self.detail_tree.delete(row)

        rows = self.get_day_schedule_rows(date_str)
        for row in rows:
            shift_label = SHIFT_LABELS.get(row["shift_type"], row["shift_type"])
            start_time = row["start_time"] or ""
            end_time = row["end_time"] or ""
            time_text = f"{start_time}-{end_time}" if start_time or end_time else ""

            self.detail_tree.insert("", "end", values=(
                row["id"],
                row["secretary_name"],
                shift_label,
                time_text,
                row["source_type"] or "",
                row["remark"] or ""
            ))

        self.selected_date_var.set(f"目前日期：{date_str}（共 {len(rows)} 筆）")
        self.set_status(f"已顯示日期明細：{date_str}")

    def reload_selected_day(self):
        text = self.selected_date_var.get().strip()
        if not text.startswith("目前日期："):
            messagebox.showwarning("提醒", "請先從月曆選擇日期")
            return

        date_str = text.replace("目前日期：", "").split("（")[0].strip()
        self.show_day_detail(date_str)
        self.load_calendar()
        self.sync_summary()

    def get_selected_schedule_id(self):
        selected = self.detail_tree.selection()
        if not selected:
            return None
        values = self.detail_tree.item(selected[0])["values"]
        return values[0]

    def get_schedule_row_by_id(self, schedule_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                sc.id,
                sc.work_date,
                sc.shift_type,
                sc.start_time,
                sc.end_time,
                sc.source_type,
                sc.remark,
                s.name AS secretary_name
            FROM schedules sc
            JOIN secretaries s ON s.id = sc.secretary_id
            WHERE sc.id = ?
        """, (schedule_id,))
        row = cur.fetchone()
        conn.close()
        return row

    def open_quick_edit(self):
        schedule_id = self.get_selected_schedule_id()
        if not schedule_id:
            messagebox.showwarning("提醒", "請先選擇要調整的班表")
            return

        schedule_row = self.get_schedule_row_by_id(schedule_id)
        if not schedule_row:
            messagebox.showerror("錯誤", "找不到班表資料")
            return

        def on_saved(date_str):
            self.show_day_detail(date_str)
            self.load_calendar()
            self.sync_summary()

            root = self.winfo_toplevel()
            if hasattr(root, "refresh_schedule_tab_if_same_date"):
                root.refresh_schedule_tab_if_same_date(date_str)

        dialog = QuickScheduleEditDialog(self, schedule_row, on_saved=on_saved)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

    def _get_selected_date(self):
        text = self.selected_date_var.get().strip()
        if not text.startswith("目前日期："):
            return None
        return text.replace("目前日期：", "").split("（")[0].strip()

    def jump_to_schedule(self):
        date_str = self._get_selected_date()
        if not date_str:
            messagebox.showwarning("提醒", "請先從月曆選擇日期")
            return

        root = self.winfo_toplevel()
        if hasattr(root, "open_schedule_for_date"):
            root.open_schedule_for_date(date_str)

    def jump_to_leave(self):
        date_str = self._get_selected_date()
        if not date_str:
            messagebox.showwarning("提醒", "請先從月曆選擇日期")
            return

        root = self.winfo_toplevel()
        if hasattr(root, "open_leave_for_date"):
            root.open_leave_for_date(date_str)