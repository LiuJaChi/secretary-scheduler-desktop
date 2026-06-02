from datetime import datetime, timedelta

from database import get_connection


SHIFT_LABELS = {
    "MORNING": "早班",
    "EVENING": "中晚班",
    "OFF": "休息",
    "COMP": "補休",
}


def _parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _daterange(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def _get_active_secretaries():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name
        FROM secretaries
        WHERE is_active = 1
        ORDER BY id ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def _get_leave_request_by_id(leave_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, secretary_id, leave_date, reason, status
        FROM leave_requests
        WHERE id = ?
    """, (leave_id,))
    row = cur.fetchone()
    conn.close()
    return row


def _get_schedule_by_id(schedule_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, secretary_id, work_date, shift_type, source_type, remark
        FROM schedules
        WHERE id = ?
    """, (schedule_id,))
    row = cur.fetchone()
    conn.close()
    return row


def _find_used_comp_record(secretary_id, target_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, use_date, status, note
        FROM comp_leave_records
        WHERE secretary_id = ?
          AND use_date = ?
          AND status = 'used'
        ORDER BY id DESC
        LIMIT 1
    """, (secretary_id, target_date))
    row = cur.fetchone()
    conn.close()
    return row


def _find_leave_request_on_date(secretary_id, target_date, exclude_leave_id=None):
    conn = get_connection()
    cur = conn.cursor()

    if exclude_leave_id is None:
        cur.execute("""
            SELECT id, leave_date, status, reason
            FROM leave_requests
            WHERE secretary_id = ?
              AND leave_date = ?
            ORDER BY id DESC
            LIMIT 1
        """, (secretary_id, target_date))
    else:
        cur.execute("""
            SELECT id, leave_date, status, reason
            FROM leave_requests
            WHERE secretary_id = ?
              AND leave_date = ?
              AND id <> ?
            ORDER BY id DESC
            LIMIT 1
        """, (secretary_id, target_date, exclude_leave_id))

    row = cur.fetchone()
    conn.close()
    return row


def _find_schedule_on_date(secretary_id, target_date, exclude_schedule_id=None):
    conn = get_connection()
    cur = conn.cursor()

    if exclude_schedule_id is None:
        cur.execute("""
            SELECT id, work_date, shift_type, source_type, remark
            FROM schedules
            WHERE secretary_id = ?
              AND work_date = ?
            ORDER BY id DESC
            LIMIT 1
        """, (secretary_id, target_date))
    else:
        cur.execute("""
            SELECT id, work_date, shift_type, source_type, remark
            FROM schedules
            WHERE secretary_id = ?
              AND work_date = ?
              AND id <> ?
            ORDER BY id DESC
            LIMIT 1
        """, (secretary_id, target_date, exclude_schedule_id))

    row = cur.fetchone()
    conn.close()
    return row


def _is_holiday(date_str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM holidays WHERE date = ? LIMIT 1", (date_str,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def generate_schedule(start_date, end_date, clear_existing=True):
    """
    簡化版排班產生器：
    - 有核准請假：排 OFF
    - 有已使用補休：排 COMP
    - 國定假日：排 OFF
    - 其他平日：依秘書順序輪流 MORNING / EVENING
    """
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)
    secretaries = _get_active_secretaries()

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN")

        if clear_existing:
            cur.execute("""
                DELETE FROM schedules
                WHERE work_date BETWEEN ? AND ?
            """, (start_date, end_date))

        for day_index, d in enumerate(_daterange(start_dt, end_dt)):
            work_date = d.strftime("%Y-%m-%d")
            is_holiday = _is_holiday(work_date)

            for sec_index, sec in enumerate(secretaries):
                secretary_id = sec["id"]

                approved_leave = _find_leave_request_on_date(secretary_id, work_date)
                comp_used = _find_used_comp_record(secretary_id, work_date)

                if approved_leave and approved_leave["status"] == "approved":
                    shift_type = "OFF"
                    source_type = "leave"
                    remark = f"請假：{approved_leave['reason']}"
                elif comp_used:
                    shift_type = "COMP"
                    source_type = "comp_leave"
                    remark = comp_used["note"] or "使用補休"
                elif is_holiday:
                    shift_type = "OFF"
                    source_type = "holiday"
                    remark = "國定假日"
                else:
                    # 簡易輪排：依日期 + 秘書順序交替
                    shift_type = "MORNING" if (day_index + sec_index) % 2 == 0 else "EVENING"
                    source_type = "auto"
                    remark = "系統自動排班"

                start_time = None
                end_time = None
                if shift_type == "MORNING":
                    start_time = "08:00"
                    end_time = "12:00"
                elif shift_type == "EVENING":
                    start_time = "13:00"
                    end_time = "17:00"

                cur.execute("""
                    INSERT INTO schedules (
                        secretary_id,
                        work_date,
                        shift_type,
                        start_time,
                        end_time,
                        is_holiday_shift,
                        source_type,
                        remark
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    secretary_id,
                    work_date,
                    shift_type,
                    start_time,
                    end_time,
                    1 if is_holiday else 0,
                    source_type,
                    remark
                ))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_schedule_by_range(start_date, end_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            sc.id,
            sc.secretary_id,
            sc.work_date,
            sc.shift_type,
            sc.start_time,
            sc.end_time,
            sc.is_holiday_shift,
            sc.source_type,
            sc.remark,
            s.name AS secretary_name
        FROM schedules sc
        JOIN secretaries s ON s.id = sc.secretary_id
        WHERE sc.work_date BETWEEN ? AND ?
        ORDER BY sc.work_date ASC, sc.id ASC
    """, (start_date, end_date))
    rows = cur.fetchall()
    conn.close()
    return rows


def approve_leave_request_one_click(leave_id):
    leave_row = _get_leave_request_by_id(leave_id)
    if not leave_row:
        return False, "找不到請假申請資料", None

    secretary_id = leave_row["secretary_id"]
    leave_date = leave_row["leave_date"]

    if leave_row["status"] == "approved":
        return False, "此請假申請已核准，無需重複操作", None

    comp_conflict = _find_used_comp_record(secretary_id, leave_date)
    if comp_conflict:
        note_text = comp_conflict["note"] if comp_conflict["note"] else "無"
        return False, f"核准失敗：當日已有補休使用紀錄（{note_text}）", None

    schedule_conflict = _find_schedule_on_date(secretary_id, leave_date)
    if schedule_conflict and schedule_conflict["shift_type"] not in ("OFF", "COMP"):
        shift_label = SHIFT_LABELS.get(schedule_conflict["shift_type"], schedule_conflict["shift_type"])
        return False, f"核准失敗：當日已有班表（{shift_label}），請先調整班表", None

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE leave_requests
            SET status = 'approved'
            WHERE id = ?
        """, (leave_id,))
        conn.commit()

        return True, "請假已核准", {
            "leave_id": leave_id,
            "leave_date": leave_date,
            "secretary_id": secretary_id
        }
    except Exception as e:
        conn.rollback()
        return False, f"核准失敗：{e}", None
    finally:
        conn.close()


def use_comp_leave_one_click(secretary_id, use_date, note):
    leave_conflict = _find_leave_request_on_date(secretary_id, use_date)
    if leave_conflict:
        return False, f"使用補休失敗：當日已有請假申請（狀態：{leave_conflict['status']}）"

    schedule_conflict = _find_schedule_on_date(secretary_id, use_date)
    if schedule_conflict and schedule_conflict["shift_type"] not in ("OFF", "COMP"):
        shift_label = SHIFT_LABELS.get(schedule_conflict["shift_type"], schedule_conflict["shift_type"])
        return False, f"使用補休失敗：當日已有班表（{shift_label}），請先調整班表"

    existing_comp = _find_used_comp_record(secretary_id, use_date)
    if existing_comp:
        return False, "使用補休失敗：當日已有補休使用紀錄"

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO comp_leave_records (secretary_id, use_date, status, note)
            VALUES (?, ?, 'used', ?)
        """, (secretary_id, use_date, note))
        conn.commit()
        return True, "補休使用成功"
    except Exception as e:
        conn.rollback()
        return False, f"補休使用失敗：{e}"
    finally:
        conn.close()


def get_comp_leave_balances():
    """
    簡化版補休餘額：
    以 used 筆數顯示已使用量，先回傳負值邏輯避免畫面出錯。
    若你之後有 earned 紀錄規則，再改這裡。
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            s.name AS secretary_name,
            COALESCE(SUM(CASE WHEN clr.status = 'earned' THEN 1 ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN clr.status = 'used' THEN 1 ELSE 0 END), 0) AS balance
        FROM secretaries s
        LEFT JOIN comp_leave_records clr ON clr.secretary_id = s.id
        WHERE s.is_active = 1
        GROUP BY s.id, s.name
        ORDER BY s.id ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def update_schedule_one_click(schedule_id, new_shift, reason):
    schedule_row = _get_schedule_by_id(schedule_id)
    if not schedule_row:
        return False, "找不到班表資料", None

    secretary_id = schedule_row["secretary_id"]
    work_date = schedule_row["work_date"]
    old_shift = schedule_row["shift_type"]

    if new_shift in ("MORNING", "EVENING"):
        leave_conflict = _find_leave_request_on_date(secretary_id, work_date)
        if leave_conflict and leave_conflict["status"] in ("pending", "approved"):
            return False, f"調班失敗：當日已有請假申請（狀態：{leave_conflict['status']}）", None

        comp_conflict = _find_used_comp_record(secretary_id, work_date)
        if comp_conflict:
            note_text = comp_conflict["note"] if comp_conflict["note"] else "無"
            return False, f"調班失敗：當日已有補休使用紀錄（{note_text}）", None

    conn = get_connection()
    cur = conn.cursor()

    try:
        start_time = None
        end_time = None
        if new_shift == "MORNING":
            start_time = "08:00"
            end_time = "12:00"
        elif new_shift == "EVENING":
            start_time = "13:00"
            end_time = "17:00"

        cur.execute("""
            UPDATE schedules
            SET shift_type = ?, start_time = ?, end_time = ?, remark = ?
            WHERE id = ?
        """, (new_shift, start_time, end_time, reason, schedule_id))

        conn.commit()
        return True, f"調班成功：{old_shift} → {new_shift}", {
            "schedule_id": schedule_id,
            "work_date": work_date,
            "secretary_id": secretary_id,
            "old_shift": old_shift,
            "new_shift": new_shift,
        }
    except Exception as e:
        conn.rollback()
        return False, f"調班失敗：{e}", None
    finally:
        conn.close()
