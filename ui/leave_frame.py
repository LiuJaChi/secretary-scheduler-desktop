import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database import get_connection
from scheduler_service import (
    approve_leave_request_one_click,
    use_comp_leave_one_click,
    get_comp_leave_balances,
)
from ui.ui_data_helpers import get_active_secretary_options


class LeaveFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        today = datetime.now().strftime("%Y-%m-%d")

        self.secretary_var = tk.StringVar()
        self.leave_date_var = tk.StringVar(value=today)
        self.reason_var = tk.StringVar()
        self.comp_date_var = tk.StringVar(value=today)
        self.comp_note_var = tk.StringVar()

        self.secretary_value_to_id = {}
        self.secretary_id_to_value = {}

        self._build_ui()
        self.load_secretary_options()
        self.load_data()
        self.load_comp_balances()

    def _build_ui(self):
        top_pane = ttk.PanedWindow(self, orient="vertical")
        top_pane.pack(fill="both", expand=True, padx=10, pady=10)

        upper_frame = ttk.Frame(top_pane)
        lower_frame = ttk.Frame(top_pane)
        top_pane.add(upper_frame, weight=2)
        top_pane.add(lower_frame, weight=3)

        # \u8acb\u5047\u7533\u8acb\u5340
        leave_form = ttk.LabelFrame(upper_frame, text="\u8acb\u5047\u7533\u8acb / \u6838\u51c6")
        leave_form.pack(fill="x", padx=0, pady=(0, 10))

        ttk.Label(leave_form, text="\u79d8\u66f8").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.secretary_combo = ttk.Combobox(
            leave_form,
            textvariable=self.secretary_var,
            state="readonly",
            width=24
        )
        self.secretary_combo.grid(row=0, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(leave_form, text="\u8acb\u5047\u65e5\u671f").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        ttk.Entry(leave_form, textvariable=self.leave_date_var, width=14).grid(
            row=0, column=3, padx=8, pady=8, sticky="w"
        )

        ttk.Label(leave_form, text="\u539f\u56e0").grid(row=0, column=4, padx=8, pady=8, sticky="w")
        ttk.Entry(leave_form, textvariable=self.reason_var, width=28).grid(
            row=0, column=5, padx=8, pady=8, sticky="w"
        )

        ttk.Button(leave_form, text="\u65b0\u589e\u8acb\u5047\u7533\u8acb", command=self.add_leave_request).grid(
            row=0, column=6, padx=8, pady=8
        )
        ttk.Button(leave_form, text="\u6838\u51c6\u6240\u9078\u8acb\u5047", command=self.approve_selected_leave).grid(
            row=0, column=7, padx=8, pady=8
        )

        # \u88dc\u4f11\u4f7f\u7528\u5340
        comp_form = ttk.LabelFrame(upper_frame, text="\u88dc\u4f11\u4f7f\u7528")
        comp_form.pack(fill="x", padx=0, pady=(0, 10))

        ttk.Label(comp_form, text="\u88dc\u4f11\u65e5\u671f").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        ttk.Entry(comp_form, textvariable=self.comp_date_var, width=14).grid(
            row=0, column=1, padx=8, pady=8, sticky="w"
        )

        ttk.Label(comp_form, text="\u8aaa\u660e").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        ttk.Entry(comp_form, textvariable=self.comp_note_var, width=40).grid(
            row=0, column=3, padx=8, pady=8, sticky="w"
        )

        ttk.Button(comp_form, text="\u4f7f\u7528\u88dc\u4f11", command=self.use_comp_leave).grid(
            row=0, column=4, padx=8, pady=8
        )
        ttk.Button(comp_form, text="\u91cd\u65b0\u6574\u7406", command=self.reload_all).grid(
            row=0, column=5, padx=8, pady=8
        )

        # \u8acb\u5047\u6e05\u55ae
        leave_list_frame = ttk.LabelFrame(lower_frame, text="\u8acb\u5047\u7533\u8acb\u6e05\u55ae")
        leave_list_frame.pack(fill="both", expand=True, pady=(0, 10))

        leave_columns = ("id", "secretary_name", "leave_date", "reason", "status")
        self.tree = ttk.Treeview(leave_list_frame, columns=leave_columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("secretary_name", text="\u79d8\u66f8")
        self.tree.heading("leave_date", text="\u8acb\u5047\u65e5\u671f")
        self.tree.heading("reason", text="\u539f\u56e0")
        self.tree.heading("status", text="\u72c0\u614b")

        self.tree.column("id", width=70, anchor="center")
        self.tree.column("secretary_name", width=120, anchor="w")
        self.tree.column("leave_date", width=120, anchor="center")
        self.tree.column("reason", width=220, anchor="w")
        self.tree.column("status", width=100, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        # \u88dc\u4f11\u9918\u984d\u6e05\u55ae
        balance_frame = ttk.LabelFrame(lower_frame, text="\u88dc\u4f11\u9918\u984d")
        balance_frame.pack(fill="both", expand=True)

        balance_columns = ("secretary_name", "balance")
        self.balance_tree = ttk.Treeview(balance_frame, columns=balance_columns, show="headings")
        self.balance_tree.heading("secretary_name", text="\u79d8\u66f8")
        self.balance_tree.heading("balance", text="\u88dc\u4f11\u9918\u984d")

        self.balance_tree.column("secretary_name", width=180, anchor="w")
        self.balance_tree.column("balance", width=120, anchor="center")

        self.balance_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def set_status(self, message):
        root = self.winfo_toplevel()
        if hasattr(root, "set_status_message"):
            root.set_status_message(message)

    def sync_summary(self):
        root = self.winfo_toplevel()
        if hasattr(root, "sync_summary_views"):
            root.sync_summary_views()

    def validate_date(self, date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def load_secretary_options(self):
        values, value_to_id, id_to_value = get_active_secretary_options()

        self.secretary_value_to_id = value_to_id
        self.secretary_id_to_value = id_to_value

        self.secretary_combo["values"] = values

        current = self.secretary_var.get().strip()
        if values:
            if current not in values:
                self.secretary_var.set(values[0])
        else:
            self.secretary_var.set("")

        self.set_status(f"\u5df2\u8f09\u5165\u8acb\u5047\u9801\u79d8\u66f8\u9078\u55ae\uff0c\u5171 {len(values)} \u4f4d\u555f\u7528\u4e2d\u79d8\u66f8")

    def get_selected_secretary_id(self):
        text = self.secretary_var.get().strip()
        if not text:
            return None
        return self.secretary_value_to_id.get(text)

    def get_selected_secretary_name(self):
        text = self.secretary_var.get().strip()
        if not text:
            return ""
        if " - " in text:
            return text.split(" - ", 1)[1]
        return text

    def add_leave_request(self):
        secretary_id = self.get_selected_secretary_id()
        leave_date = self.leave_date_var.get().strip()
        reason = self.reason_var.get().strip()

        if not secretary_id:
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u5148\u9078\u64c7\u79d8\u66f8")
            return

        if not self.validate_date(leave_date):
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u5047\u65e5\u671f\u683c\u5f0f\u932f\u8aa4\uff0c\u8acb\u4f7f\u7528 YYYY-MM-DD")
            return

        if not reason:
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u8f38\u5165\u8acb\u5047\u539f\u56e0")
            return

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO leave_requests (secretary_id, leave_date, reason, status)
                VALUES (?, ?, ?, 'pending')
            """, (secretary_id, leave_date, reason))
            conn.commit()

            messagebox.showinfo("\u6210\u529f", "\u8acb\u5047\u7533\u8acb\u5df2\u65b0\u589e")
            self.reason_var.set("")
            self.load_data()
            self.sync_summary()
            self.set_status(f"\u5df2\u65b0\u589e\u8acb\u5047\u7533\u8acb\uff1a{leave_date}")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("\u9519\u8aa4", f"\u65b0\u589e\u8acb\u5047\u7533\u8acb\u5931\u6557\uff1a{e}")
        finally:
            conn.close()

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                lr.id,
                lr.secretary_id,
                lr.leave_date,
                lr.reason,
                lr.status,
                s.name AS secretary_name
            FROM leave_requests lr
            JOIN secretaries s ON s.id = lr.secretary_id
            ORDER BY lr.leave_date DESC, lr.id DESC
        """)
        rows = cur.fetchall()
        conn.close()

        status_map = {
            "pending": "\u5f85\u6838\u51c6",
            "approved": "\u5df2\u6838\u51c6",
            "rejected": "\u5df2\u62d2\u7d55",
        }

        for row in rows:
            self.tree.insert("", "end", values=(
                row["id"],
                row["secretary_name"],
                row["leave_date"],
                row["reason"],
                status_map.get(row["status"], row["status"]),
            ))

        self.set_status(f"\u5df2\u8f09\u5165\u8acb\u5047\u7533\u8acb\uff0c\u5171 {len(rows)} \u7b46")

    def get_selected_leave_id(self):
        selected = self.tree.selection()
        if not selected:
            return None

        values = self.tree.item(selected[0])["values"]
        return values[0]

    def approve_selected_leave(self):
        leave_id = self.get_selected_leave_id()
        if not leave_id:
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u5148\u9078\u64c7\u4e00\u7b46\u8acb\u5047\u7533\u8acb")
            return

        ok, msg, payload = approve_leave_request_one_click(leave_id)
        if ok:
            messagebox.showinfo("\u6210\u529f", msg)
            self.load_data()
            self.sync_summary()

            if payload and "leave_date" in payload:
                root = self.winfo_toplevel()
                if hasattr(root, "calendar_tab") and hasattr(root.calendar_tab, "load_calendar"):
                    root.calendar_tab.load_calendar()
                if hasattr(root, "calendar_tab") and hasattr(root.calendar_tab, "show_day_detail"):
                    root.calendar_tab.show_day_detail(payload["leave_date"])
                if hasattr(root, "refresh_schedule_tab_if_same_date"):
                    root.refresh_schedule_tab_if_same_date(payload["leave_date"])

            self.set_status(msg)
        else:
            messagebox.showerror("\u9519\u8aa4", msg)

    def use_comp_leave(self):
        secretary_id = self.get_selected_secretary_id()
        use_date = self.comp_date_var.get().strip()
        note = self.comp_note_var.get().strip()

        if not secretary_id:
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u5148\u9078\u64c7\u79d8\u66f8")
            return

        if not self.validate_date(use_date):
            messagebox.showwarning("\u63d0\u9190", "\u88dc\u4f11\u65e5\u671f\u683c\u5f0f\u932f\u8aa4\uff0c\u8acb\u4f7f\u7528 YYYY-MM-DD")
            return

        ok, msg = use_comp_leave_one_click(secretary_id, use_date, note)
        if ok:
            messagebox.showinfo("\u6210\u529f", msg)
            self.comp_note_var.set("")
            self.load_comp_balances()
            self.sync_summary()

            root = self.winfo_toplevel()
            if hasattr(root, "calendar_tab") and hasattr(root.calendar_tab, "load_calendar"):
                root.calendar_tab.load_calendar()
            if hasattr(root, "calendar_tab") and hasattr(root.calendar_tab, "show_day_detail"):
                root.calendar_tab.show_day_detail(use_date)
            if hasattr(root, "refresh_schedule_tab_if_same_date"):
                root.refresh_schedule_tab_if_same_date(use_date)

            self.set_status(msg)
        else:
            messagebox.showerror("\u9519\u8aa4", msg)

    def load_comp_balances(self):
        for row in self.balance_tree.get_children():
            self.balance_tree.delete(row)

        try:
            rows = get_comp_leave_balances()
            for row in rows:
                self.balance_tree.insert("", "end", values=(
                    row["secretary_name"],
                    row["balance"],
                ))

            self.set_status(f"\u5df2\u8f09\u5165\u88dc\u4f11\u9918\u984d\uff0c\u5171 {len(rows)} \u7b46")
        except Exception as e:
            messagebox.showerror("\u9519\u8aa4", f"\u8f09\u5165\u88dc\u4f11\u9918\u984d\u5931\u6557\uff1a{e}")

    def reload_all(self):
        self.load_secretary_options()
        self.load_data()
        self.load_comp_balances()
        self.sync_summary()
        self.set_status("\u5df2\u91cd\u65b0\u6574\u7406\u8acb\u5047 / \u88dc\u4f11\u8cc7\u6599")