from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, event
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import MappedAsDataclass
from sqlalchemy.orm import mapped_column

from .db.registry import mapper_registry as reg


class Base(MappedAsDataclass, DeclarativeBase):
    registry = reg


class MenuItem(Base):
    """
    Block model.
    """

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(init=False, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    icon: Mapped[str] = mapped_column(nullable=False)
    system_instruction: Mapped[str] = mapped_column(nullable=True, default=None)
    guidance_prompt: Mapped[str] = mapped_column(nullable=True, default=None)
    models: Mapped[str] = mapped_column(nullable=True, default=None)
    capture_mode: Mapped[str] = mapped_column(nullable=True, default=None)
    parent_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=True, default=None)

    # Define relationships between parent and children
    if TYPE_CHECKING:
        parent: "MenuItem"
        children: List["MenuItem"] = []
    else:
        # Avoid using the same name 'parent' in backref
        parent = relationship("MenuItem", remote_side=[id])
        children = relationship('MenuItem', remote_side=[parent_id], uselist=True, back_populates='parent', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.id}, {self.name})>"

@event.listens_for(MenuItem, 'after_delete')
def receive_after_delete(mapper, connection, target):
    """
    Event listener for after delete
    :param mapper:
    :param connection:
    :param target:
    :return:
    """
    # remove logo file
    print(f"Deleting logo file: {target.icon}")
    logo_path = Path(target.icon)
    if logo_path.exists():
        os.remove(logo_path)