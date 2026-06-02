import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from scheduler_service import (
    generate_schedule,
    get_schedule_by_range,
    update_schedule_one_click,
    SHIFT_LABELS,
)
from excel_service import export_schedule_to_excel
from ui.ui_data_helpers import get_active_secretary_options


class ScheduleFrame(ttk.Frame):
    SHIFT_OPTIONS = {
        "早班": "MORNING",
        "中晚班": "EVENING",
        "休息": "OFF",
        "補休": "COMP",
    }

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        today = datetime.now().strftime("%Y-%m-%d")

        self.start_var = tk.StringVar(value=today)
        self.end_var = tk.StringVar(value=today)
        self.secretary_var = tk.StringVar()
        self.reason_var = tk.StringVar()
        self.shift_var = tk.StringVar(value="早班")

        self.secretary_value_to_id = {}
        self.secretary_id_to_value = {}

        self._build_ui()
        self.load_secretary_options()
        self.load_data()

    def _build_ui(self):
        query_frame = ttk.LabelFrame(self, text="\u67e5\u8a62 / \u7522\u73ed")
        query_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(query_frame, text="\u958b\u59cb\u65e5\u671f").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        ttk.Entry(query_frame, textvariable=self.start_var, width=14).grid(row=0, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(query_frame, text="\u7d50\u675f\u65e5\u671f").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        ttk.Entry(query_frame, textvariable=self.end_var, width=14).grid(row=0, column=3, padx=8, pady=8, sticky="w")

        ttk.Label(query_frame, text="\u79d8\u66f8").grid(row=0, column=4, padx=8, pady=8, sticky="w")
        self.secretary_combo = ttk.Combobox(
            query_frame,
            textvariable=self.secretary_var,
            state="readonly",
            width=22
        )
        self.secretary_combo.grid(row=0, column=5, padx=8, pady=8, sticky="w")

        ttk.Button(query_frame, text="\u67e5\u8a62", command=self.load_data).grid(row=0, column=6, padx=8, pady=8)
        ttk.Button(query_frame, text="\u91cd\u65b0\u6574\u7406\u79d8\u66f8", command=self.load_secretary_options).grid(row=0, column=7, padx=8, pady=8)

        ttk.Button(query_frame, text="\u7522\u751f\u73ed\u8868", command=self.handle_generate_schedule).grid(row=1, column=0, padx=8, pady=8)
        ttk.Button(query_frame, text="\u5308\u51fa Excel", command=self.handle_export_excel).grid(row=1, column=1, padx=8, pady=8)

        edit_frame = ttk.LabelFrame(self, text="\u4e00\u9375\u8abf\u73ed")
        edit_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(edit_frame, text="\u65b0\u73ed\u5225").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.shift_combo = ttk.Combobox(
            edit_frame,
            textvariable=self.shift_var,
            state="readonly",
            width=18,
            values=list(self.SHIFT_OPTIONS.keys())
        )
        self.shift_combo.grid(row=0, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(edit_frame, text="\u539f\u56e0 / \u5099\u8a3b").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        ttk.Entry(edit_frame, textvariable=self.reason_var, width=40).grid(row=0, column=3, padx=8, pady=8, sticky="w")

        ttk.Button(edit_frame, text="\u5957\u7528\u5230\u6240\u9078\u73ed\u8868", command=self.handle_update_schedule).grid(row=0, column=4, padx=8, pady=8)

        list_frame = ttk.LabelFrame(self, text="\u73ed\u8868\u6e05\u55ae")
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = (
            "id", "work_date", "secretary_name", "shift_type",
            "time_range", "holiday", "source_type", "remark"
        )
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("work_date", text="\u65e5\u671f")
        self.tree.heading("secretary_name", text="\u79d8\u66f8")
        self.tree.heading("shift_type", text="\u73ed\u5225")
        self.tree.heading("time_range", text="\u6642\u9593")
        self.tree.heading("holiday", text="\u5047\u65e5\u73ed")
        self.tree.heading("source_type", text="\u4f86\u6e90")
        self.tree.heading("remark", text="\u5099\u8a3b")

        self.tree.column("id", width=70, anchor="center")
        self.tree.column("work_date", width=110, anchor="center")
        self.tree.column("secretary_name", width=120, anchor="w")
        self.tree.column("shift_type", width=90, anchor="center")
        self.tree.column("time_range", width=120, anchor="center")
        self.tree.column("holiday", width=80, anchor="center")
        self.tree.column("source_type", width=100, anchor="center")
        self.tree.column("remark", width=240, anchor="w")

        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

    def set_status(self, message):
        root = self.winfo_toplevel()
        if hasattr(root, "set_status_message"):
            root.set_status_message(message)

    def sync_summary(self):
        root = self.winfo_toplevel()
        if hasattr(root, "sync_summary_views"):
            root.sync_summary_views()

    def load_secretary_options(self):
        values, value_to_id, id_to_value = get_active_secretary_options()

        self.secretary_value_to_id = value_to_id
        self.secretary_id_to_value = id_to_value

        combo_values = ["\u5168\u90e8"] + values
        self.secretary_combo["values"] = combo_values

        current = self.secretary_var.get().strip()
        if current not in combo_values:
            self.secretary_var.set("\u5168\u90e8")

        self.set_status(f"\u5df2\u8f09\u5165\u79d8\u66f8\u9078\u55ae\uff0c\u5171 {len(values)} \u4f4d\u555f\u7528\u4e2d\u79d8\u66f8")

    def get_selected_secretary_id(self):
        text = self.secretary_var.get().strip()
        if not text or text == "\u5168\u90e8":
            return None
        return self.secretary_value_to_id.get(text)

    def validate_date(self, date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def load_data(self):
        start_date = self.start_var.get().strip()
        end_date = self.end_var.get().strip()

        if not self.validate_date(start_date):
            messagebox.showwarning("\u63d0\u9190", "\u958b\u59cb\u65e5\u671f\u683c\u5f0f\u932f\u8aa4\uff0c\u8acb\u4f7f\u7528 YYYY-MM-DD")
            return

        if not self.validate_date(end_date):
            messagebox.showwarning("\u63d0\u9190", "\u7d50\u675f\u65e5\u671f\u683c\u5f0f\u932f\u8aa4\uff0c\u8acb\u4f7f\u7528 YYYY-MM-DD")
            return

        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            rows = get_schedule_by_range(start_date, end_date)
            selected_secretary_id = self.get_selected_secretary_id()

            if selected_secretary_id is not None:
                rows = [r for r in rows if r["secretary_id"] == selected_secretary_id]

            for row in rows:
                shift_label = SHIFT_LABELS.get(row["shift_type"], row["shift_type"])
                start_time = row["start_time"] or ""
                end_time = row["end_time"] or ""
                time_range = f"{start_time}-{end_time}" if start_time or end_time else ""
                holiday_text = "\u662f" if row["is_holiday_shift"] == 1 else "\u5426"

                self.tree.insert("", "end", values=(
                    row["id"],
                    row["work_date"],
                    row["secretary_name"],
                    shift_label,
                    time_range,
                    holiday_text,
                    row["source_type"] or "",
                    row["remark"] or "",
                ))

            self.set_status(f"\u5df2\u8f09\u5165\u73ed\u8868\uff0c\u5171 {len(rows)} \u7b46")
            self.sync_summary()
        except Exception as e:
            messagebox.showerror("\u9519\u8aa4", f"\u8f09\u5165\u73ed\u8868\u5931\u6557\uff1a{e}")

    def handle_generate_schedule(self):
        start_date = self.start_var.get().strip()
        end_date = self.end_var.get().strip()

        if not self.validate_date(start_date):
            messagebox.showwarning("\u63d0\u9190", "\u958b\u59cb\u65e5\u671f\u683c\u5f0f\u932f\u8aa4\uff0c\u8acb\u4f7f\u7528 YYYY-MM-DD")
            return

        if not self.validate_date(end_date):
            messagebox.showwarning("\u63d0\u9190", "\u7d50\u675f\u65e5\u671f\u683c\u5f0f\u932f\u8aa4\uff0c\u8acb\u4f7f\u7528 YYYY-MM-DD")
            return

        confirm = messagebox.askyesno(
            "\u78ba\u8a8d\u7522\u73ed",
            "\u662f\u5426\u8981\u91cd\u65b0\u7522\u751f\u6307\u5b9a\u65e5\u671f\u5340\u9593\u7684\u73ed\u8868\uff1f\n\u82e5\u8a72\u5340\u9593\u5df2\u6709\u73ed\u8868\uff0c\u5c07\u6703\u5148\u6e05\u9664\u518d\u91cd\u5efa\u3002"
        )
        if not confirm:
            return

        try:
            generate_schedule(start_date, end_date, clear_existing=True)
            self.load_data()
            self.set_status(f"\u5df2\u5b8c\u6210\u7522\u73ed\uff1a{start_date} ~ {end_date}")

            root = self.winfo_toplevel()
            if hasattr(root, "calendar_tab") and hasattr(root.calendar_tab, "load_calendar"):
                root.calendar_tab.load_calendar()
        except Exception as e:
            messagebox.showerror("\u9519\u8aa4", f"\u7522\u73ed\u5931\u6557\uff1a{e}")

    def get_selected_schedule_id(self):
        selected = self.tree.selection()
        if not selected:
            return None
        values = self.tree.item(selected[0])["values"]
        return values[0]

    def handle_update_schedule(self):
        schedule_id = self.get_selected_schedule_id()
        if not schedule_id:
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u5148\u9078\u64c7\u4e00\u7b46\u73ed\u8868\u8cc7\u6599")
            return

        shift_label = self.shift_var.get().strip()
        if not shift_label:
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u9078\u64c7\u65b0\u73ed\u5225")
            return

        new_shift = self.SHIFT_OPTIONS[shift_label]
        reason = self.reason_var.get().strip()

        ok, msg, payload = update_schedule_one_click(schedule_id, new_shift, reason)
        if ok:
            messagebox.showinfo("\u6210\u529f", msg)
            self.load_data()
            self.reason_var.set("")

            if payload and "work_date" in payload:
                root = self.winfo_toplevel()
                if hasattr(root, "calendar_tab") and hasattr(root.calendar_tab, "load_calendar"):
                    root.calendar_tab.load_calendar()
                if hasattr(root, "calendar_tab") and hasattr(root.calendar_tab, "show_day_detail"):
                    root.calendar_tab.show_day_detail(payload["work_date"])

            self.set_status(msg)
        else:
            messagebox.showerror("\u9519\u8aa4", msg)

    def handle_export_excel(self):
        start_date = self.start_var.get().strip()
        end_date = self.end_var.get().strip()

        if not self.validate_date(start_date):
            messagebox.showwarning("\u63d0\u9190", "\u958b\u59cb\u65e5\u671f\u683c\u5f0f\u932f\u8aa4\uff0c\u8acb\u4f7f\u7528 YYYY-MM-DD")
            return

        if not self.validate_date(end_date):
            messagebox.showwarning("\u63d0\u9190", "\u7d50\u675f\u65e5\u671f\u683c\u5f0f\u932f\u8aa4\uff0c\u8acb\u4f7f\u7528 YYYY-MM-DD")
            return

        file_path = filedialog.asksaveasfilename(
            title="\u5308\u51fa\u73ed\u8868 Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel \u6a94\u6848", "*.xlsx")]
        )
        if not file_path:
            return

        try:
            rows = get_schedule_by_range(start_date, end_date)
            selected_secretary_id = self.get_selected_secretary_id()

            if selected_secretary_id is not None:
                rows = [r for r in rows if r["secretary_id"] == selected_secretary_id]

            export_schedule_to_excel(rows, file_path)
            messagebox.showinfo("\u6210\u529f", f"\u5df2\u5308\u51fa Excel\uff1a\n{file_path}")
            self.set_status(f"\u5df2\u5308\u51fa\u73ed\u8868 Excel\uff1a{file_path}")
        except Exception as e:
            messagebox.showerror("\u9519\u8aa4", f"\u5308\u51fa\u5931\u6557\uff1a{e}")