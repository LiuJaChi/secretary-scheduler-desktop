import tkinter as tk
from tkinter import messagebox

from database import init_db
from migration_runner import run_migrations
from duplicate_cleanup_tool import DuplicateCleanupWindow
from ui.main_window import MainWindow


def main():
    init_db()

    result = run_migrations()
    if not result["ok"]:
        root = tk.Tk()
        root.withdraw()

        messagebox.showerror("資料庫 Migration 錯誤", result["message"])

        if result.get("has_duplicates"):
            open_tool = messagebox.askyesno(
                "開啟清理工具",
                "偵測到重複資料，是否立即開啟「重複資料清理工具」？"
            )
            if open_tool:
                root.deiconify()
                root.title("資料修復工具啟動中")
                cleanup_window = DuplicateCleanupWindow(root)
                cleanup_window.protocol("WM_DELETE_WINDOW", root.destroy)
                root.mainloop()
                return

        root.destroy()
        return

    app = MainWindow()
    if result["applied"]:
        app.set_status_message(f"已自動套用 migration：{', '.join(result['applied'])}")
    app.mainloop()


if __name__ == "__main__":
    main()