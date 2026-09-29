# daily_planner/core.py (重构优化版)


class ScheduleManager:

    def __init__(self, schedule):
        # 保证日程永远按时间升序排列
        self.schedule = sorted(schedule, key=lambda x: x[0])

    def get_current_and_next_task(self, now_hm: str):
        """根据当前时间 (例如 "07:00")，计算当前任务和下一个任务"""
        if not self.schedule:
            return "无任务", "无下一个任务"

        # 规则 1：如果当前时间比今天第一个任务还要早
        if now_hm < self.schedule[0][0]:
            first_time, first_task = self.schedule[0]
            return "自由时间", f"NEXT ({first_time}): {first_task}"

        curr_task = "自由时间"
        next_task = "今日已完成"

        # 规则 2：遍历找当前时间落在哪个区间
        for i, (t, task) in enumerate(self.schedule):
            if now_hm >= t:
                curr_task = task
                if i + 1 < len(self.schedule):
                    next_t, next_item = self.schedule[i + 1]
                    next_task = f"NEXT ({next_t}): {next_item}"

        return curr_task, next_task