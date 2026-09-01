from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from quack2tex.repository.menu_item_repository import MenuItemRepository
from quack2tex.repository.models import Base, MenuItem


def session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.registry.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_move_item_updates_parent_id() -> None:
    factory = session_factory()

    with factory() as session:
        root = session.query(MenuItem).filter(MenuItem.is_root == True).one()
        source = MenuItem(name="Source", icon=":/icons/gears.png", parent_id=root.id)
        target = MenuItem(name="Target", icon=":/icons/gears.png", parent_id=root.id)
        session.add_all([source, target])
        session.commit()

        moved = MenuItemRepository.move_item(session, source.id, target.id)

        assert moved.parent_id == target.id
        assert session.get(MenuItem, source.id).parent_id == target.id


def test_move_item_rejects_descendant_target() -> None:
    factory = session_factory()

    with factory() as session:
        root = session.query(MenuItem).filter(MenuItem.is_root == True).one()
        parent = MenuItem(name="Parent", icon=":/icons/gears.png", parent_id=root.id)
        child = MenuItem(name="Child", icon=":/icons/gears.png")
        parent.children.append(child)
        session.add(parent)
        session.commit()

        try:
            MenuItemRepository.move_item(session, parent.id, child.id)
        except ValueError as error:
            assert "children" in str(error)
        else:
            raise AssertionError("Expected moving an item under its child to fail.")

        assert session.get(MenuItem, parent.id).parent_id == root.id
