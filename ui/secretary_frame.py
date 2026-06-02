import tkinter as tk
from tkinter import ttk, messagebox

from database import get_connection


class SecretaryFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        self.name_var = tk.StringVar()
        self.selected_secretary_id = None

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # \u65b0\u589e/\u7de8\u8f2f\u5340
        form_frame = ttk.LabelFrame(self, text="\u65b0\u589e\u6216\u7de8\u8f2f\u79d8\u66f8")
        form_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(form_frame, text="\u59d3\u540d").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, padx=8, pady=8, sticky="w")
        self.name_entry.bind("<Return>", lambda e: self.add_or_update_secretary())

        self.add_btn = ttk.Button(form_frame, text="\u65b0\u589e", command=self.add_or_update_secretary)
        self.add_btn.grid(row=0, column=2, padx=8, pady=8)

        self.update_btn = ttk.Button(form_frame, text="\u66f4\u65b0", command=self.add_or_update_secretary, state="disabled")
        self.update_btn.grid(row=0, column=3, padx=8, pady=8)

        ttk.Button(form_frame, text="\u6e05\u7a7a", command=self.clear_form).grid(row=0, column=4, padx=8, pady=8)
        ttk.Button(form_frame, text="\u91cd\u65b0\u6574\u7406", command=self.load_data).grid(row=0, column=5, padx=8, pady=8)

        # \u79d8\u66f8\u6e05\u55ae
        list_frame = ttk.LabelFrame(self, text="\u79d8\u66f8\u6e05\u55ae")
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("id", "name", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="\u59d3\u540d")
        self.tree.heading("status", text="\u72c0\u614b")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("name", width=220, anchor="w")
        self.tree.column("status", width=120, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # \u64cd\u4f5c\u6309\u9215\n        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))

        ttk.Button(btn_frame, text="\u7de8\u8f2f\u6240\u9078\u79d8\u66f8", command=self.edit_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="\u555f\u7528 / \u505c\u7528\u5207\u63db", command=self.toggle_active).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="\u522a\u9664\u6240\u9078\u79d8\u66f8", command=self.delete_selected).pack(side="left", padx=5)

    def set_status(self, message):
        root = self.winfo_toplevel()
        if hasattr(root, "set_status_message"):
            root.set_status_message(message)

    def sync_summary(self):
        root = self.winfo_toplevel()
        if hasattr(root, "sync_summary_views"):
            root.sync_summary_views()

    def load_data(self):
        """\u8f09\u5165\u79d8\u66f8\u6e05\u55ae"""
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, is_active
                FROM secretaries
                ORDER BY id ASC
            """)
            rows = cur.fetchall()
            conn.close()

            for row in rows:
                status = "\u555f\u7528" if row["is_active"] == 1 else "\u505c\u7528"
                self.tree.insert("", "end", values=(row["id"], row["name"], status))

            self.set_status(f"\u5df2\u8f09\u5165\u79d8\u66f8\u6e05\u55ae\uff0c\u5171 {len(rows)} \u7b46")
            self.sync_summary()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("\u8f09\u5165\u5931\u6557", f"\u7121\u6cd5\u8f09\u5165\u79d8\u66f8\u6e05\u55ae\uff1a{e}")

    def clear_form(self):
        """\u6e05\u7a7a\u8868\u55ae"""
        self.name_var.set("")
        self.selected_secretary_id = None
        self.add_btn.config(state="normal")
        self.update_btn.config(state="disabled")
        self.name_entry.focus()

    def on_tree_select(self, event=None):
        """Treeview \u9078\u64c7\u6642\u7684\u4e8b\u4ef6"""
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0])["values"]
        self.selected_secretary_id = values[0]

    def on_tree_double_click(self, event=None):
        """\u96d9\u64ca Treeview \u9805\u76ee\u6642\u7de8\u8f2f"""
        self.edit_selected()

    def get_selected_id(self):
        """\u53d6\u5f97\u76ee\u524d\u9078\u4e2d\u7684\u79d8\u66f8 ID"""
        selected = self.tree.selection()
        if not selected:
            return None
        values = self.tree.item(selected[0])["values"]
        return values[0]

    def edit_selected(self):
        """\u7de8\u8f2f\u6240\u9078\u79d8\u66f8"""
        secretary_id = self.get_selected_id()
        if not secretary_id:
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u5148\u9078\u64c7\u4e00\u7b46\u79d8\u66f8\u8cc7\u6599")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM secretaries WHERE id = ?", (secretary_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("\u9519\u8aa4", "\u627e\u4e0d\u5230\u79d8\u66f8\u8cc7\u6599")
            return

        self.selected_secretary_id = row["id"]
        self.name_var.set(row["name"])
        self.add_btn.config(state="disabled")
        self.update_btn.config(state="normal")
        self.name_entry.focus()
        self.name_entry.select_range(0, len(row["name"]))

    def add_or_update_secretary(self):
        """\u65b0\u589e\u6216\u66f4\u65b0\u79d8\u66f8"""
        name = self.name_var.get().strip()

        if not name:
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u8f38\u5165\u79d8\u66f8\u59d3\u540d")
            self.name_entry.focus()
            return

        if self.selected_secretary_id is not None:
            self.update_secretary_by_id(self.selected_secretary_id, name)
        else:
            self.add_secretary(name)

    def add_secretary(self, name):
        """\u65b0\u589e\u79d8\u66f8"""
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO secretaries (name, is_active)
                VALUES (?, 1)
            """, (name,))

            conn.commit()

            messagebox.showinfo("\u6210\u529f", f"\u5df2\u65b0\u589e\u79d8\u66f8\uff1a{name}")
            self.load_data()

            root = self.winfo_toplevel()
            if hasattr(root, "refresh_secretary_related_options"):
                root.refresh_secretary_related_options()

        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("\u9519\u8aa4", f"\u65b0\u589e\u5931\u6557\uff1a{e}")
        finally:
            if conn:
                conn.close()

    def update_secretary_by_id(self, secretary_id, new_name):
        """\u66f4\u65b0\u79d8\u66f8\u59d3\u540d"""
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("SELECT name FROM secretaries WHERE id = ?", (secretary_id,))
            row = cur.fetchone()
            if not row:
                messagebox.showerror("\u9519\u8aa4", "\u627e\u4e0d\u5230\u79d8\u66f8\u8cc7\u6599")
                return

            old_name = row["name"]
            if old_name == new_name:
                messagebox.showinfo("\u63d0\u793a", "\u59d3\u540d\u672a\u6539\u8b8a")
                return

            cur.execute("""
                UPDATE secretaries
                SET name = ?
                WHERE id = ?
            """, (new_name, secretary_id))

            conn.commit()

            messagebox.showinfo("\u6210\u529f", f"\u5df2\u66f4\u65b0\u79d8\u66f8\uff1a{old_name} \u2192 {new_name}")
            self.load_data()

            root = self.winfo_toplevel()
            if hasattr(root, "refresh_secretary_related_options"):
                root.refresh_secretary_related_options()

        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("\u9519\u8aa4", f"\u66f4\u65b0\u5931\u6557\uff1a{e}")
        finally:
            if conn:
                conn.close()

    def toggle_active(self):
        """\u555f\u7528/\u505c\u7528\u79d8\u66f8"""
        secretary_id = self.get_selected_id()
        if not secretary_id:
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u5148\u9078\u64c7\u4e00\u7b46\u79d8\u66f8\u8cc7\u6599")
            return

        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT is_active, name
                FROM secretaries
                WHERE id = ?
            """, (secretary_id,))
            row = cur.fetchone()
            if not row:
                messagebox.showerror("\u9519\u8aa4", "\u627e\u4e0d\u5230\u79d8\u66f8\u8cc7\u6599")
                return

            new_value = 0 if row["is_active"] == 1 else 1
            cur.execute("""
                UPDATE secretaries
                SET is_active = ?
                WHERE id = ?
            """, (new_value, secretary_id))
            conn.commit()

            status_text = "\u555f\u7528" if new_value == 1 else "\u505c\u7528"
            messagebox.showinfo("\u6210\u529f", f"\u5df2\u5c07 {row['name']} \u8a2d\u70ba{status_text}")
            self.load_data()

            root = self.winfo_toplevel()
            if hasattr(root, "refresh_secretary_related_options"):
                root.refresh_secretary_related_options()
        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("\u9519\u8aa4", f"\u66f4\u65b0\u5931\u6557\uff1a{e}")
        finally:
            if conn:
                conn.close()

    def delete_selected(self):
        """\u522a\u9664\u6240\u9078\u79d8\u66f8"""
        secretary_id = self.get_selected_id()
        if not secretary_id:
            messagebox.showwarning("\u63d0\u9190", "\u8acb\u5148\u9078\u64c7\u4e00\u7b46\u79d8\u66f8\u8cc7\u6599")
            return

        values = self.tree.item(self.tree.selection()[0])["values"]
        secretary_name = values[1]

        confirm = messagebox.askyesno(
            "\u78ba\u8a8d\u522a\u9664",
            f"\u662f\u5426\u78ba\u5b9a\u522a\u9664\u79d8\u66f8\uff1f\n\n\u59d3\u540d\uff1a{secretary_name}\n\n\u8b66\u544a\uff1a\u522a\u9664\u79d8\u66f8\u6703\u5f71\u97ff\u5176\u73ed\u8868\u3001\u8acb\u5047\u7b49\u76f8\u95dc\u7d00\u9304\uff01"
        )
        if not confirm:
            return

        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("DELETE FROM secretaries WHERE id = ?", (secretary_id,))
            conn.commit()

            messagebox.showinfo("\u6210\u529f", f"\u5df2\u522a\u9664\u79d8\u66f8\uff1a{secretary_name}")
            self.load_data()

            root = self.winfo_toplevel()
            if hasattr(root, "refresh_secretary_related_options"):
                root.refresh_secretary_related_options()
        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("\u9519\u8aa4", f"\u522a\u9664\u5931\u6557\uff1a{e}")
        finally:
            if conn:
                conn.close()