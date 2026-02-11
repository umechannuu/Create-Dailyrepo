"""Report data models for structured output"""
from typing import List, Optional
from pydantic import BaseModel, Field


class TopicDetail(BaseModel):
    """話題の詳細"""
    title: str = Field(description="話題のタイトル")
    items: List[str] = Field(description="箇条書き項目のリスト")


class TodoItem(BaseModel):
    """TODO項目"""
    title: str = Field(description="TODO項目のタイトル")
    priority: str = Field(description="優先度（高・中・低のいずれか）")
    estimated_time: Optional[str] = Field(
        description="想定所要時間（例: 1時間、30分）",
        default=None
    )
    related_topic: Optional[str] = Field(
        description="関連する話題・プロジェクト名",
        default=None
    )
    deadline: Optional[str] = Field(
        description="期限（YYYY-MM-DD形式、または「今週中」等）",
        default=None
    )


class DailyReport(BaseModel):
    """日報の構造化データモデル（TODO機能付き）"""
    work_content: List[TopicDetail] = Field(
        description="今日の作業内容。複数の話題に分けて記載"
    )
    insights: List[TopicDetail] = Field(
        description="得られた知見。複数の話題に分けて記載"
    )
    next_tasks: List[str] = Field(
        description="次回の予定候補のリスト（シンプルな箇条書き）"
    )
    suggested_todos: List[TodoItem] = Field(
        description="AIが提案する具体的なTODO項目（優先度・所要時間付き）"
    )
    unfinished_tasks: Optional[List[str]] = Field(
        description="今日完了しなかった作業（あれば）",
        default=None
    )

    def to_markdown(self) -> str:
        """Notion用のMarkdown形式に変換"""
        sections = []

        # 今日の作業内容
        sections.append("## 今日の作業内容")
        for topic in self.work_content:
            sections.append(f"### {topic.title}")
            for item in topic.items:
                sections.append(f"- {item}")

        # 得られた知見
        sections.append("\n## 得られた知見")
        for topic in self.insights:
            sections.append(f"### {topic.title}")
            for item in topic.items:
                sections.append(f"- {item}")

        # 次回の予定候補
        sections.append("\n## 次回の予定候補")
        for task in self.next_tasks:
            sections.append(f"- {task}")

        # AI提案TODO
        sections.append("\n## AI提案TODO")
        for todo in self.suggested_todos:
            line = f"- [{todo.priority}] **{todo.title}**"
            if todo.estimated_time:
                line += f" (所要時間: {todo.estimated_time})"
            if todo.deadline:
                line += f" 【期限: {todo.deadline}】"
            sections.append(line)

        # 未完了タスク
        if self.unfinished_tasks:
            sections.append("\n## 未完了タスク")
            for task in self.unfinished_tasks:
                sections.append(f"- {task}")

        return "\n".join(sections)

