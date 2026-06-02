from database import get_connection


def get_active_secretary_options():
    """
    回傳給 Combobox 用的顯示清單與映射資料。

    returns:
        display_values: ["1 - 王小美", "2 - 李佳蓉"]
        value_to_id: {"1 - 王小美": 1, ...}
        id_to_value: {1: "1 - 王小美", ...}
    """
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

    display_values = []
    value_to_id = {}
    id_to_value = {}

    for row in rows:
        text = f"{row['id']} - {row['name']}"
        display_values.append(text)
        value_to_id[text] = row["id"]
        id_to_value[row["id"]] = text

    return display_values, value_to_id, id_to_value