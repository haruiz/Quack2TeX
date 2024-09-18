from quack2tex.repository.models import MenuItem
from quack2tex.repository.db.sync_session import get_db_session
from sqlalchemy.orm import Session
from typing import List, Optional


class MenuItemRepository:
    """
    Repository class for handling operations related to MenuItems.
    """

    @staticmethod
    def populate_item_children(session: Session, parent_item: MenuItem) -> None:
        """
        Recursively populates the children of a given menu item.

        Args:
            session (Session): The active database session.
            parent_item (MenuItem): The menu item whose children are to be populated.
        """
        for child in parent_item.children:
            MenuItemRepository.populate_item_children(session, child)

    @classmethod
    def build_tree(cls, session: Session) -> List[MenuItem]:
        """
        Constructs a tree structure of menu items with parent-child relationships.

        This method retrieves all root menu items (items without a parent) and
        recursively appends their children to form a hierarchical structure.

        Args:
            session (Session): The active database session.

        Returns:
            List[MenuItem]: A list of root menu items, each containing its nested children.
        """
        tree: List[MenuItem] = []
        root_items: List[MenuItem] = session.query(MenuItem).filter(MenuItem.parent_id == None).all()

        for root_item in root_items:
            cls.populate_item_children(session, root_item)
            tree.append(root_item)

        return tree

    @classmethod
    def add_item(cls, session: Session, item: MenuItem) -> MenuItem:
        """
        Adds a new menu item to the database.

        Args:
            session (Session): The active database session.
            item (MenuItem): The menu item to add.
            parent_id (Optional[int]): The ID of the parent item, if any.
        """
        if item.parent_id:
            parent_item = session.query(MenuItem).get(item.parent_id)
            parent_item.children.append(item)
        else:
            session.add(item)
        session.commit()
        # Refresh the item to populate its children
        session.refresh(item)
        return item


    @classmethod
    def delete_items(cls, session: Session, item_ids: List[int]) -> None:
        """
        Deletes multiple menu items from the database.

        Args:
            session (Session): The active database session.
            item_ids (List[int]): The IDs of the items to delete.
        """
        items = session.query(MenuItem).filter(MenuItem.id.in_(item_ids)).all()
        for item in items:
            session.delete(item)
        session.commit()

    @classmethod
    def update_item(cls, session: Session, item: MenuItem) -> MenuItem:
        """
        Updates a menu item in the database.

        Args:
            session (Session): The active database session.
            item (MenuItem): The menu item to update.
        """
        item = session.merge(item)
        session.commit()
        return item


if __name__ == '__main__':
    with get_db_session() as session:
        menu_tree = MenuItemRepository.build_tree(session)
        # Optionally, print or use the tree as needed
        print(menu_tree)
