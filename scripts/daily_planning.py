#!/usr/bin/env python3
"""
Daily Planning Script for Personal Agent
每晚自动规划第二天的开发任务
"""
import sys
sys.path.append('/Users/fufu/clawd/personal-agent/backend')

from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


class PlanningService:
    """任务规划服务"""

    def __init__(self):
        self.connection_string = settings.mongodb_connection_string
        self.client = None
        self._db = None
        self._plans = None

    async def _get_collections(self):
        """初始化 MongoDB 连接"""
        if self._plans is None:
            self.client = AsyncIOMotorClient(self.connection_string)
            self._db = self.client["agent_planning"]
            self._plans = self._db["development_plans"]

            await self._plans.create_index([("date", -1)])

        return self._plans

    async def save_daily_plan(self, date: str, tasks: list[str], priorities: list[str]):
        """保存每日计划"""
        try:
            plans = await self._get_collections()

            doc = {
                "date": date,
                "tasks": tasks,
                "priorities": priorities,
                "created_at": datetime.utcnow(),
                "status": "pending"
            }

            await plans.insert_one(doc)
            return True
        except Exception as e:
            print(f"Error saving plan: {e}")
            return False

    async def get_today_plan(self):
        """获取今天的计划"""
        try:
            plans = await self._get_collections()

            today = datetime.now().strftime("%Y-%m-%d")
            doc = await plans.find_one({"date": today})

            if doc:
                return {
                    "date": doc["date"],
                    "tasks": doc["tasks"],
                    "priorities": doc["priorities"],
                    "status": doc["status"],
                    "created_at": doc.get("created_at"),
                    "completed_at": doc.get("completed_at")
                }
            return None
        except Exception as e:
            print(f"Error getting plan: {e}")
            return None

    async def mark_plan_completed(self, date: str, completed_tasks: list[str]):
        """标记任务完成"""
        try:
            plans = await self._get_collections()

            doc = await plans.find_one_and_update(
                {"date": date},
                {"$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "completed_tasks": completed_tasks
                }}
            )
            return True
        except Exception as e:
            print(f"Error marking completed: {e}")
            return False

    async def get_plan_history(self, limit: int = 7) -> list[dict]:
        """获取历史计划"""
        try:
            plans = await self._get_collections()

            cursor = plans.find().sort("date", -1).limit(limit)
            docs = await cursor.to_list(length=limit)

            return docs
        except Exception as e:
            print(f"Error getting history: {e}")
            return []

    async def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()
            self._plans = None


async def generate_daily_plan() -> str:
    """生成每日计划"""

    today = datetime.now().strftime("%Y-%m-%d")
    weekday = datetime.now().strftime("%A")  # Monday, Tuesday, etc.

    # 根据星期几生成不同的计划模板
    if weekday == "Monday":
        tasks = [
            "代码审查：检查当前架构和代码质量",
            "性能分析：测量响应时间和数据库查询次数",
            "任务规划：定义本周的开发目标",
            "文档更新：更新 README 和架构文档"
        ]
        priorities = ["high", "medium", "high", "medium"]

    elif weekday == "Tuesday":
        tasks = [
            "功能开发 1：性能优化（缓存机制）",
            "功能开发 2：记忆分类扩展",
            "测试验证：测试所有边界情况",
            "代码提交：提交到 GitHub"
        ]
        priorities = ["high", "high", "medium", "low"]

    elif weekday == "Wednesday":
        tasks = [
            "功能开发 1：更多工具集成（日历、邮件）",
            "功能开发 2：批量记忆操作功能",
            "错误处理：改进错误日志和用户提示",
            "性能测试：对比优化前后的性能"
        ]
        priorities = ["high", "medium", "medium", "low"]

    elif weekday == "Thursday":
        tasks = [
            "功能开发 1：向量数据库集成准备",
            "功能开发 2：本地 LLM 集成调研",
            "代码重构：优化模块间的依赖关系",
            "文档编写：编写 API 文档和开发指南"
        ]
        priorities = ["medium", "high", "medium", "low"]

    elif weekday == "Friday":
        tasks = [
            "代码审查：周终代码审查和优化",
            "测试周：执行完整的测试套件",
            "部署准备：准备生产环境部署",
            "下周规划：制定下一周的开发计划"
        ]
        priorities = ["medium", "medium", "high", "high"]

    else:  # Saturday and Sunday
        tasks = [
            "技术调研：调研新框架和技术",
            "代码优化：重构和性能优化",
            "文档整理：整理和归档文档",
            "社区参与：参与开源社区讨论"
        ]
        priorities = ["low", "medium", "medium", "low"]

    return f"""
# 📋 {today} 开发计划
## 任务清单
{chr(10).join([f"{i+1}. {task}" for i, task in enumerate(tasks)])}

## 优先级
{chr(10).join([f"- [{priority}] {task}" for i, (task, priority) in zip(tasks, priorities)])}

---
今天的工作：{datetime.now().strftime("%H:%M")} 自动生成
"""


async def main():
    """主函数：保存每日计划"""

    # 创建规划服务
    planning = PlanningService()

    try:
        # 生成今天的日期
        today = datetime.now().strftime("%Y-%m-%d")
        weekday = datetime.now().strftime("%A")
        weekday_zh = {
            "Monday": "星期一",
            "Tuesday": "星期二",
            "Wednesday": "星期三",
            "Thursday": "星期四",
            "Friday": "星期五",
            "Saturday": "星期六",
            "Sunday": "星期日"
        }[weekday]

        # 生成计划
        plan_text = await generate_daily_plan()
        today_tasks = [
            "代码审查：检查当前架构和代码质量",
            "性能分析：测量响应时间和数据库查询次数",
            "任务规划：定义本周的开发目标",
            "文档更新：更新 README 和架构文档"
        ] if weekday == "Monday" else [
            "功能开发 1：性能优化（缓存机制）",
            "功能开发 2：记忆分类扩展",
            "测试验证：测试所有边界情况",
            "代码提交：提交到 GitHub"
        ]

        today_priorities = ["high", "medium", "high", "medium"] if weekday == "Monday" else ["high", "high", "medium", "low"]

        # 保存到 MongoDB
        success = await planning.save_daily_plan(today, today_tasks, today_priorities)

        if success:
            print(f"✅ 成功保存 {today} 的开发计划")
            print(f"📝 计划已保存到 MongoDB agent_planning.development_plans 集合")
            print(f"🚀 明天早上老大可以查验进度")
        else:
            print(f"❌ 保存计划失败")

        # 关闭连接
        await planning.close()

    except Exception as e:
        print(f"❌ 计划生成失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
