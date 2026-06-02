import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database import get_connection


class HolidayFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        self.date_var = tk.StringVar()
        self.name_var = tk.StringVar()

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        form_frame = ttk.LabelFrame(self, text="\u65b0\u589e\u570b\u5b9a\u5047\u65e5")
        form_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(form_frame, text="\u65e5\u671f").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        ttk.Entry(form_frame, textvariable=self.date_var, width=16).grid(
            row=0, column=1, padx=8, pady=8, sticky="w"
        )

        ttk.Label(form_frame, text="\u540d\u7a31").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        ttk.Entry(form_frame, textvariable=self.name_var, width=28).grid(
            row=0, column=3, padx=8, pady=8, sticky="w"
        )

        ttk.Button(form_frame, text="\u65b0\u589e", command=self.add_holiday).grid(
            row=0, column=4, padx=8, pady=8
        )
        ttk.Button(form_frame, text="\u6e05\u7a7a", command=self.clear_form).grid(
            row=0, column=5, padx=8, pady=8
        )
        ttk.Button(form_frame, text="\u91cd\u65b0\u6574\u7406", command=self.load_data).grid(
            row=0, column=6, padx=8, pady=8
        )

        list_frame = ttk.LabelFrame(self, text="\u570b\u5b9a\u5047\u65e5\u6e05\u55ae")
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("id", "date", "name")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="\u65e5\u671f")
        self.tree.heading("name", text="\u540d\u7a31")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("date", width=140, anchor="center")
        self.tree.column("name", width=240, anchor="w")

        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))

        ttk.Button(btn_frame, text="\u522a\u9664\u6240\u9078\u5047\u65e5", command=self.delete_selected).pack(side="left", padx=5)

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

    def clear_form(self):
        self.date_var.set("")
        self.name_var.set("")

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, date, name
            FROM holidays
            ORDER BY date ASC, id ASC
        """)
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert("", "end", values=(
                row["id"],
                row["date"],
                row["name"],
            ))

        self.set_status(f"\u5df2\u8f09\u5165\u570b\u5b9a\u5047\u65e5\uff0c\u5171 {len(rows)} \u7b46")
        self.sync_summary()

    def find_holiday_by_date(self, date_str):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, date, name
            FROM holidays
            WHERE date = ?
            ORDER BY id ASC
            LIMIT 1
        """, (date_str,))
        row = cur.fetchone()
        conn.close()
        return row

    def add_holiday(self):
        date_str = self.date_var.get().strip()
        name = self.name_var.get().strip()

        if not self.validate_date(date_str):
            messagebox.showwarning("\u63d0\u9190", "\u65e5\u671f\u683c\u5f0f\u932f\u8aa4\uff0c\u8acb\u4f7f\u7528 YYYY-MM-DD")
            return

        if not name:
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u8f38\u5165\u5047\u65e5\u540d\u7a31")
            return

        existing = self.find_holiday_by_date(date_str)
        if existing:
            if existing["name"] == name:
                messagebox.showinfo(
                    "\u63d0\u793a",
                    f"\u8a72\u65e5\u671f\u5df2\u5b58\u5728\u76f8\u540c\u5047\u65e5\u8cc7\u6599\uff1a\n{date_str} {name}"
                )
                return

            confirm_update = messagebox.askyesno(
                "\u65e5\u671f\u5df2\u5b58\u5728",
                (
                    f"\u65e5\u671f {date_str} \u5df2\u5b58\u5728\u5047\u65e5\u8cc7\u6599\uff1a\n"
                    f"\u76ee\u524d\u540d\u7a31\uff1a{existing['name']}\n"
                    f"\u65b0\u540d\u7a31\uff1a{name}\n\n"
                    f"\u662f\u5426\u8981\u66f4\u65b0\u6210\u65b0\u540d\u7a31\uff1f"
                )
            )

            if not confirm_update:
                return

            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE holidays
                    SET name = ?
                    WHERE id = ?
                """, (name, existing["id"]))
                conn.commit()

                messagebox.showinfo("\u6210\u529f", f"\u5df2\u66f4\u65b0\u5047\u65e5\u540d\u7a31\uff1a{date_str} {name}")
                self.clear_form()
                self.load_data()

                root = self.winfo_toplevel()
                if hasattr(root, "calendar_tab") and hasattr(root.calendar_tab, "load_calendar"):
                    root.calendar_tab.load_calendar()
            except Exception as e:
                conn.rollback()
                messagebox.showerror("\u9519\u8aa4", f"\u66f4\u65b0\u5931\u6557\uff1a{e}")
            finally:
                conn.close()
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO holidays (date, name)
                VALUES (?, ?)
            """, (date_str, name))
            conn.commit()

            messagebox.showinfo("\u6210\u529f", f"\u5df2\u65b0\u589e\u570b\u5b9a\u5047\u65e5\uff1a{date_str} {name}")
            self.clear_form()
            self.load_data()

            root = self.winfo_toplevel()
            if hasattr(root, "calendar_tab") and hasattr(root.calendar_tab, "load_calendar"):
                root.calendar_tab.load_calendar()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("\u9519\u8aa4", f"\u65b0\u589e\u5931\u6557\uff1a{e}")
        finally:
            conn.close()

    def get_selected_holiday_id(self):
        selected = self.tree.selection()
        if not selected:
            return None

        values = self.tree.item(selected[0])["values"]
        return values[0]

    def delete_selected(self):
        holiday_id = self.get_selected_holiday_id()
        if not holiday_id:
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u5148\u9078\u64c7\u4e00\u7b46\u570b\u5b9a\u5047\u65e5\u8cc7\u6599")
            return

        values = self.tree.item(self.tree.selection()[0])["values"]
        date_str = values[1]
        holiday_name = values[2]

        confirm = messagebox.askyesno(
            "\u78ba\u8a8d\u522a\u9664",
            f"\u662f\u5426\u78ba\u5b9a\u522a\u9664\u570b\u5b9a\u5047\u65e5\uff1f\n\n\u65e5\u671f\uff1a{date_str}\n\u540d\u7a31\uff1a{holiday_name}"
        )
        if not confirm:
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                DELETE FROM holidays
                WHERE id = ?
            """, (holiday_id,))
            conn.commit()

            messagebox.showinfo("\u6210\u529f", "\u5df2\u522a\u9664\u570b\u5b9a\u5047\u65e5")
            self.load_data()

            root = self.winfo_toplevel()
            if hasattr(root, "calendar_tab") and hasattr(root.calendar_tab, "load_calendar"):
                root.calendar_tab.load_calendar()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("\u9519\u8aa4", f"\u522a\u9664\u5931\u6557\uff1a{e}")
        finally:
            conn.close()