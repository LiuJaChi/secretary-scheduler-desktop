-- 目的：
-- 1. 防止 holidays 同日期重複
-- 2. 防止 leave_requests 同秘書同日期重複
-- 3. 防止 schedules 同秘書同日期重複
-- 4. 防止 comp_leave_records 在 status='used' 且 use_date 不為空時，
--    同秘書同日期重複

BEGIN;

-- holidays: 同一天只能一筆
CREATE UNIQUE INDEX IF NOT EXISTS idx_holidays_unique_date
ON holidays(date);

-- leave_requests: 同一位秘書同一天只能有一筆請假申請
CREATE UNIQUE INDEX IF NOT EXISTS idx_leave_requests_unique_secretary_date
ON leave_requests(secretary_id, leave_date);

-- schedules: 同一位秘書同一天只能有一筆班表
CREATE UNIQUE INDEX IF NOT EXISTS idx_schedules_unique_secretary_date
ON schedules(secretary_id, work_date);

-- comp_leave_records:
-- 只限制「已使用補休」且 use_date 有值的資料
CREATE UNIQUE INDEX IF NOT EXISTS idx_comp_leave_records_unique_used_secretary_date
ON comp_leave_records(secretary_id, use_date)
WHERE status = 'used' AND use_date IS NOT NULL;

COMMIT;