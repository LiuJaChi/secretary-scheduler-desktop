import tkinter as tk
from tkinter import ttk, messagebox

from database import get_connection


class CleanupPreviewDialog(tk.Toplevel):
    def __init__(self, master, preview_text, on_confirm):
        super().__init__(master)
        self.title("清理前預覽摘要")
        self.geometry("900x620")
        self.resizable(True, True)
        self.on_confirm = on_confirm

        self.transient(master)
        self.grab_set()

        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(
            top,
            text="請先確認以下刪除摘要，確認後才會正式執行清理。",
            foreground="blue"
        ).pack(anchor="w")

        text_frame = ttk.Frame(self)
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.text = tk.Text(text_frame, wrap="word")
        self.text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar.set)

        self.text.insert("1.0", preview_text)
        self.text.config(state="disabled")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="確認執行清理", command=self.confirm).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side="left", padx=5)

    def confirm(self):
        self.destroy()
        if self.on_confirm:
            self.on_confirm()


class DuplicateCleanupWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("重複資料清理工具")
        self.geometry("1220x800")
        self.resizable(True, True)

        self.duplicate_groups = []
        self.group_keep_overrides = {}

        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Button(top, text="重新掃描", command=self.scan_duplicates).pack(side="left", padx=5)
        ttk.Button(top, text="指定保留所選資料", command=self.set_selected_detail_as_keep).pack(side="left", padx=5)
        ttk.Button(top, text="清除此群組手動保留設定", command=self.clear_group_keep_override).pack(side="left", padx=5)
        ttk.Button(top, text="一鍵清理重複資料", command=self.cleanup_duplicates).pack(side="left", padx=5)
        ttk.Button(top, text="關閉", command=self.destroy).pack(side="right", padx=5)

        self.summary_var = tk.StringVar(value="尚未掃描")
        ttk.Label(top, textvariable=self.summary_var, foreground="blue").pack(side="left", padx=15)

        group_frame = ttk.LabelFrame(self, text="重複群組")
        group_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        group_columns = ("table", "group_key", "count", "keep_id", "delete_ids")
        self.group_tree = ttk.Treeview(group_frame, columns=group_columns, show="headings", height=12)
        self.group_tree.heading("table", text="資料表")
        self.group_tree.heading("group_key", text="重複鍵值")
        self.group_tree.heading("count", text="重複筆數")
        self.group_tree.heading("keep_id", text="保留 ID")
        self.group_tree.heading("delete_ids", text="刪除 ID 清單")

        self.group_tree.column("table", width=180, anchor="center")
        self.group_tree.column("group_key", width=360, anchor="w")
        self.group_tree.column("count", width=100, anchor="center")
        self.group_tree.column("keep_id", width=100, anchor="center")
        self.group_tree.column("delete_ids", width=260, anchor="w")

        self.group_tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.group_tree.bind("<<TreeviewSelect>>", self.on_group_select)

        detail_frame = ttk.LabelFrame(self, text="所選群組明細")
        detail_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        detail_top = ttk.Frame(detail_frame)
        detail_top.pack(fill="x", padx=8, pady=(8, 0))

        self.detail_hint_var = tk.StringVar(value="請先選擇上方重複群組")
        ttk.Label(detail_top, textvariable=self.detail_hint_var, foreground="green").pack(anchor="w")

        detail_columns = ("id", "field1", "field2", "field3", "field4", "field5", "action")
        self.detail_tree = ttk.Treeview(detail_frame, columns=detail_columns, show="headings", height=12)

        self.detail_tree.heading("id", text="ID")
        self.detail_tree.heading("field1", text="欄位1")
        self.detail_tree.heading("field2", text="欄位2")
        self.detail_tree.heading("field3", text="欄位3")
        self.detail_tree.heading("field4", text="欄位4")
        self.detail_tree.heading("field5", text="欄位5")
        self.detail_tree.heading("action", text="處理結果")

        self.detail_tree.column("id", width=80, anchor="center")
        self.detail_tree.column("field1", width=180, anchor="w")
        self.detail_tree.column("field2", width=180, anchor="w")
        self.detail_tree.column("field3", width=180, anchor="w")
        self.detail_tree.column("field4", width=180, anchor="w")
        self.detail_tree.column("field5", width=180, anchor="w")
        self.detail_tree.column("action", width=140, anchor="center")

        self.detail_tree.pack(fill="both", expand=True, padx=8, pady=8)

        note_frame = ttk.LabelFrame(self, text="說明")
        note_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(
            note_frame,
            text=(
                "預設策略：每組重複資料保留最小 ID。\n"
                "你可以在下方明細先選一筆，再按「指定保留所選資料」，手動改變保留對象。\n"
                "正式清理前，系統會先顯示預覽摘要確認視窗。"
            ),
            justify="left"
        ).pack(anchor="w", padx=10, pady=10)

        self.scan_duplicates()

    def clear_group_tree(self):
        for row in self.group_tree.get_children():
            self.group_tree.delete(row)

    def clear_detail_tree(self):
        for row in self.detail_tree.get_children():
            self.detail_tree.delete(row)

    def scan_duplicates(self):
        self.clear_group_tree()
        self.clear_detail_tree()
        self.duplicate_groups = []
        self.group_keep_overrides = {}

        all_groups = []
        all_groups.extend(self._scan_holidays())
        all_groups.extend(self._scan_leave_requests())
        all_groups.extend(self._scan_schedules())
        all_groups.extend(self._scan_comp_used())

        self.duplicate_groups = all_groups

        for index, item in enumerate(all_groups):
            self.group_tree.insert("", "end", iid=str(index), values=(
                item["table"],
                item["group_key"],
                item["count"],
                item["keep_id"],
                ",".join(str(x) for x in item["delete_ids"])
            ))

        if all_groups:
            self.summary_var.set(f"掃描完成：共找到 {len(all_groups)} 組重複資料")
            first_iid = self.group_tree.get_children()[0]
            self.group_tree.selection_set(first_iid)
            self.group_tree.focus(first_iid)
            self.on_group_select()
        else:
            self.summary_var.set("掃描完成：未發現重複資料")
            self.detail_hint_var.set("未發現重複資料")

    def _fetch_rows(self, sql, params=()):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()
        return rows

    def _group_duplicate_result(self, rows, table_name, key_builder):
        groups = {}
        for row in rows:
            key = key_builder(row)
            groups.setdefault(key, []).append(row)

        result = []
        for group_key, items in groups.items():
            ids = sorted([item["id"] for item in items])
            keep_id = ids[0]
            delete_ids = ids[1:]
            result.append({
                "table": table_name,
                "group_key": group_key,
                "count": len(ids),
                "keep_id": keep_id,
                "delete_ids": delete_ids,
                "rows": items,
            })
        return result

    def _scan_holidays(self):
        rows = self._fetch_rows("""
            SELECT *
            FROM holidays
            WHERE date IN (
                SELECT date
                FROM holidays
                GROUP BY date
                HAVING COUNT(*) > 1
            )
            ORDER BY date, id
        """)
        return self._group_duplicate_result(
            rows,
            "holidays",
            lambda row: f"date={row['date']}"
        )

    def _scan_leave_requests(self):
        rows = self._fetch_rows("""
            SELECT *
            FROM leave_requests
            WHERE (secretary_id, leave_date) IN (
                SELECT secretary_id, leave_date
                FROM leave_requests
                GROUP BY secretary_id, leave_date
                HAVING COUNT(*) > 1
            )
            ORDER BY secretary_id, leave_date, id
        """)
        return self._group_duplicate_result(
            rows,
            "leave_requests",
            lambda row: f"secretary_id={row['secretary_id']}, leave_date={row['leave_date']}"
        )

    def _scan_schedules(self):
        rows = self._fetch_rows("""
            SELECT *
            FROM schedules
            WHERE (secretary_id, work_date) IN (
                SELECT secretary_id, work_date
                FROM schedules
                GROUP BY secretary_id, work_date
                HAVING COUNT(*) > 1
            )
            ORDER BY secretary_id, work_date, id
        """)
        return self._group_duplicate_result(
            rows,
            "schedules",
            lambda row: f"secretary_id={row['secretary_id']}, work_date={row['work_date']}"
        )

    def _scan_comp_used(self):
        rows = self._fetch_rows("""
            SELECT *
            FROM comp_leave_records
            WHERE status = 'used'
              AND use_date IS NOT NULL
              AND (secretary_id, use_date) IN (
                  SELECT secretary_id, use_date
                  FROM comp_leave_records
                  WHERE status = 'used' AND use_date IS NOT NULL
                  GROUP BY secretary_id, use_date
                  HAVING COUNT(*) > 1
              )
            ORDER BY secretary_id, use_date, id
        """)
        return self._group_duplicate_result(
            rows,
            "comp_leave_records",
            lambda row: f"secretary_id={row['secretary_id']}, use_date={row['use_date']}"
        )

    def get_selected_group_index(self):
        selected = self.group_tree.selection()
        if not selected:
            return None
        return int(selected[0])

    def get_effective_keep_id(self, group_index):
        group = self.duplicate_groups[group_index]
        return self.group_keep_overrides.get(group_index, group["keep_id"])

    def refresh_group_row(self, group_index):
        group = self.duplicate_groups[group_index]
        keep_id = self.get_effective_keep_id(group_index)
        all_ids = sorted([row["id"] for row in group["rows"]])
        delete_ids = [x for x in all_ids if x != keep_id]

        self.group_tree.item(str(group_index), values=(
            group["table"],
            group["group_key"],
            group["count"],
            keep_id,
            ",".join(str(x) for x in delete_ids)
        ))

    def on_group_select(self, event=None):
        self.clear_detail_tree()

        group_index = self.get_selected_group_index()
        if group_index is None or group_index >= len(self.duplicate_groups):
            self.detail_hint_var.set("請先選擇上方重複群組")
            return

        group = self.duplicate_groups[group_index]
        rows = group["rows"]
        keep_id = self.get_effective_keep_id(group_index)

        self.configure_detail_columns(group["table"])
        self.detail_hint_var.set(
            f"目前群組保留 ID：{keep_id}（可在下方選一筆後按「指定保留所選資料」）"
        )

        for row in rows:
            values = self.build_detail_row_values(group_index, group["table"], row, keep_id)
            self.detail_tree.insert("", "end", iid=str(row["id"]), values=values)

    def configure_detail_columns(self, table_name):
        if table_name == "holidays":
            headers = ["ID", "日期", "名稱", "", "", "", "處理結果"]
        elif table_name == "leave_requests":
            headers = ["ID", "秘書ID", "請假日期", "原因", "狀態", "", "處理結果"]
        elif table_name == "schedules":
            headers = ["ID", "秘書ID", "班表日期", "班別", "來源", "備註", "處理結果"]
        elif table_name == "comp_leave_records":
            headers = ["ID", "秘書ID", "使用日期", "狀態", "說明", "", "處理結果"]
        else:
            headers = ["ID", "欄位1", "欄位2", "欄位3", "欄位4", "欄位5", "處理結果"]

        self.detail_tree.heading("id", text=headers[0])
        self.detail_tree.heading("field1", text=headers[1])
        self.detail_tree.heading("field2", text=headers[2])
        self.detail_tree.heading("field3", text=headers[3])
        self.detail_tree.heading("field4", text=headers[4])
        self.detail_tree.heading("field5", text=headers[5])
        self.detail_tree.heading("action", text=headers[6])

    def build_detail_row_values(self, group_index, table_name, row, keep_id):
        default_keep_id = self.duplicate_groups[group_index]["keep_id"]

        if row["id"] == keep_id:
            action = "手動保留" if keep_id != default_keep_id else "保留"
        else:
            action = "刪除"

        if table_name == "holidays":
            return (row["id"], row["date"], row["name"], "", "", "", action)

        if table_name == "leave_requests":
            return (
                row["id"],
                row["secretary_id"],
                row["leave_date"],
                row["reason"],
                row["status"],
                "",
                action
            )

        if table_name == "schedules":
            return (
                row["id"],
                row["secretary_id"],
                row["work_date"],
                row["shift_type"],
                row["source_type"] if "source_type" in row.keys() else "",
                row["remark"] if "remark" in row.keys() else "",
                action
            )

        if table_name == "comp_leave_records":
            return (
                row["id"],
                row["secretary_id"],
                row["use_date"],
                row["status"],
                row["note"] if "note" in row.keys() else "",
                "",
                action
            )

        return (row["id"], "", "", "", "", "", action)

    def set_selected_detail_as_keep(self):
        group_index = self.get_selected_group_index()
        if group_index is None:
            messagebox.showwarning("提醒", "請先選擇上方重複群組")
            return

        detail_selected = self.detail_tree.selection()
        if not detail_selected:
            messagebox.showwarning("提醒", "請先在下方明細選擇一筆資料")
            return

        keep_id = int(detail_selected[0])
        self.group_keep_overrides[group_index] = keep_id
        self.refresh_group_row(group_index)
        self.on_group_select()
        messagebox.showinfo("成功", f"已指定保留 ID：{keep_id}")

    def clear_group_keep_override(self):
        group_index = self.get_selected_group_index()
        if group_index is None:
            messagebox.showwarning("提醒", "請先選擇上方重複群組")
            return

        if group_index in self.group_keep_overrides:
            del self.group_keep_overrides[group_index]
            self.refresh_group_row(group_index)
            self.on_group_select()
            messagebox.showinfo("成功", "已恢復此群組的預設保留規則（保留最小 ID）")
        else:
            messagebox.showinfo("提示", "此群組目前沒有手動保留設定")

    def build_cleanup_preview(self):
        lines = []
        total_groups = len(self.duplicate_groups)
        total_delete_count = 0
        table_delete_counts = {}

        lines.append("")
        lines.append("")

        for group_index, group in enumerate(self.duplicate_groups):
            keep_id = self.get_effective_keep_id(group_index)
            delete_ids = [row["id"] for row in group["rows"] if row["id"] != keep_id]
            delete_count = len(delete_ids)

            total_delete_count += delete_count
            table_delete_counts[group["table"]] = table_delete_counts.get(group["table"], 0) + delete_count

        lines.append(f"重複群組總數：{total_groups}")
        lines.append(f"預計刪除總筆數：{total_delete_count}")
        lines.append("")

        lines.append("")
        for table_name in sorted(table_delete_counts.keys()):
            lines.append(f"- {table_name}：刪除 {table_delete_counts[table_name]} 筆")
        lines.append("")

        lines.append("")
        for group_index, group in enumerate(self.duplicate_groups, start=1):
            effective_keep_id = self.get_effective_keep_id(group_index - 1)
            delete_ids = [row["id"] for row in group["rows"] if row["id"] != effective_keep_id]

            lines.append(
                f"{group_index}. [{group['table']}] {group['group_key']}"
            )
            lines.append(f"   - 保留 ID：{effective_keep_id}")
            lines.append(f"   - 刪除 ID：{', '.join(str(x) for x in delete_ids) if delete_ids else '無'}")

        lines.append("")
        lines.append("確認後將正式刪除上述刪除 ID 資料，且此操作不可回復。")
        return "\n".join(lines)

    def cleanup_duplicates(self):
        if not self.group_tree.get_children():
            messagebox.showinfo("提示", "目前沒有重複資料可清理")
            return

        preview_text = self.build_cleanup_preview()

        CleanupPreviewDialog(
            self,
            preview_text=preview_text,
            on_confirm=self.execute_cleanup_duplicates
        )

    def execute_cleanup_duplicates(self):
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("BEGIN")

            for group_index, group in enumerate(self.duplicate_groups):
                keep_id = self.get_effective_keep_id(group_index)
                delete_ids = [row["id"] for row in group["rows"] if row["id"] != keep_id]

                if not delete_ids:
                    continue

                placeholders = ",".join("?" for _ in delete_ids)
                sql = f"DELETE FROM {group['table']} WHERE id IN ({placeholders})"
                cur.execute(sql, delete_ids)

            conn.commit()
            self.scan_duplicates()
            messagebox.showinfo("成功", "重複資料清理完成，請重新啟動程式後再套用 migration")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("錯誤", f"清理失敗：{e}")
        finally:
            conn.close()