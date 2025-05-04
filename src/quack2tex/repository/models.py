from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, List
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, event, LargeBinary, Text, func, DateTime
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship
)

from .db.registry import mapper_registry as reg



# -----------------------
# Base Class
# -----------------------

class Base(MappedAsDataclass, DeclarativeBase):
    registry = reg


# -----------------------
# MenuItem Model
# -----------------------

class MenuItem(Base):
    """
    Menu item model representing items with potential parent-child hierarchy.
    """
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(init=False, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    icon: Mapped[str] = mapped_column(nullable=False)
    is_root: Mapped[bool] = mapped_column(nullable=False, default=False)
    system_instruction: Mapped[str] = mapped_column(nullable=True, default=None)
    guidance_prompt: Mapped[str] = mapped_column(nullable=True, default=None)
    models: Mapped[str] = mapped_column(nullable=True, default=None)
    capture_mode: Mapped[str] = mapped_column(nullable=True, default=None)
    parent_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=True, default=None)

    if TYPE_CHECKING:
        parent: MenuItem
        children: List[MenuItem] = []
    else:
        parent = relationship("MenuItem", remote_side=[id])
        children = relationship(
            "MenuItem",
            remote_side=[parent_id],
            uselist=True,
            back_populates="parent",
            cascade="all, delete-orphan"
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.id}, {self.name})>"


class Prompt(Base):
    """
    Represents a prompt entry with a name and a list of associated responses.
    """
    __tablename__ = "prompt"

    id: Mapped[int] = mapped_column(init=False, primary_key=True, autoincrement=True)
    system_instruction: Mapped[str] = mapped_column(Text, nullable=True)
    guidance_prompt: Mapped[str] = mapped_column(Text, nullable=True)
    prompt_input: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    capture_mode: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(tz=timezone.utc),  # Python-side default for dataclass
        server_default=func.now(),  # DB-side default
        nullable=False
    )
    if TYPE_CHECKING:
        responses: List[Response]
    else:
        responses = relationship(
            "Response",
            back_populates="prompt",
            cascade="all, delete-orphan"
        )


class Response(Base):
    """
    Represents the output of a model associated with a prompt.
    """
    __tablename__ = "response"

    id: Mapped[int] = mapped_column(init=False, primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompt.id"), nullable=False)
    model: Mapped[str] = mapped_column(nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False)

    if TYPE_CHECKING:
        prompt: Prompt
    else:
        prompt = relationship("Prompt", back_populates="responses")



# -----------------------
# Event Listeners
# -----------------------

@event.listens_for(MenuItem, "after_delete")
def receive_after_delete(mapper, connection, target: MenuItem):
    """
    Deletes associated logo file after a MenuItem is removed.
    """
    # print(f"Deleting logo file: {target.icon}")
    if not target.icon:
        return

    logo_path = Path(target.icon)
    if logo_path.exists():
        os.remove(logo_path)


@event.listens_for(MenuItem.__table__, "after_create")
def after_menuitem_created(target, connection, **kw):
    # print("🧱 MenuItem table was created!")
    # Maybe insert initial rows here
    connection.execute(
        MenuItem.__table__.insert(),[{
                "name": "Duck",
                "icon": ":icons/rubber-duck.png",
                "is_root": True
        }]
    )

