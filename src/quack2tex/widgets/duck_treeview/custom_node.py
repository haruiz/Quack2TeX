from __future__ import annotations


class CustomNode:
    """
    Treeview model item
    """
    def __init__(self, data: list, icon=None, parent: CustomNode = None):
        """
        Initialize a TreeItem instance.

        :param data: List of data associated with the item.
        :param icon: Optional icon for the item.
        :param parent: Optional parent TreeItem.
        """
        self.item_data = data
        self.parent_item = parent
        self._enabled = True
        self.tag = None
        self._checked = False
        self.tooltip_attr = None
        self.level = -1
        self.icon = icon
        self.child_items = []

    @property
    def checked(self):
        """
        Get the checked status of the item.

        :return: Boolean indicating if the item is checked.
        """
        return self._checked

    @checked.setter
    def checked(self, value):
        """
        Set the checked status of the item and update its children and siblings.

        :param value: Boolean indicating the new checked status.
        """
        self._checked = value
        if self.child_items:
            for child in self.child_items:
                child.checked = value
        self._update_checked_status_siblings()

    def _update_checked_status_siblings(self):
        """
        Update the checked status of the item's siblings.
        """
        parent = self.parent()
        while parent:
            all_siblings_are_checked = all([sibling.checked for sibling in self.siblings])
            parent._checked = all_siblings_are_checked
            parent = parent.parent()

    @property
    def enabled(self):
        """
        Get the enabled status of the item.

        :return: Boolean indicating if the item is enabled.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        """
        Set the enabled status of the item and update its children.

        :param value: Boolean indicating the new enabled status.
        """
        self._enabled = value

        if self.child_items:
            for child in self.child_items:
                child.enabled = value

    def _update_enabled_status_siblings(self):
        """
        Update the enabled status of the item's siblings.
        """
        parent = self.parent()
        while parent:
            all_siblings_are_disabled = all([not sibling.enabled for sibling in self.siblings])
            parent._enabled = not all_siblings_are_disabled
            parent = parent.parent()

    @property
    def siblings(self):
        """
        Get the siblings of the item.

        :return: List of sibling TreeItems.
        """
        parent = self.parent()
        if parent:
            return parent.child_items
        return []

    def child(self, number: int) -> 'CustomNode':
        """
        Get the child item at the specified position.

        :param number: Position of the child item.
        :return: TreeItem at the specified position or None if out of range.
        """
        if number < 0 or number >= len(self.child_items):
            return None
        return self.child_items[number]

    def last_child(self):
        """
        Get the last child item.

        :return: Last TreeItem or None if there are no children.
        """
        return self.child_items[-1] if self.child_items else None

    def child_count(self) -> int:
        """
        Get the number of child items.

        :return: Number of child items.
        """
        return len(self.child_items)

    def child_number(self) -> int:
        """
        Get the position of this item among its siblings.

        :return: Position of the item.
        """
        if self.parent_item:
            return self.parent_item.child_items.index(self)
        return 0

    def column_count(self) -> int:
        """
        Get the number of columns in the item data.

        :return: Number of columns.
        """
        return len(self.item_data)


    def data(self, column: int):
        """
        Get the data at the specified column.

        :param column: Column index.
        :return: Data at the specified column or None if out of range.
        """
        if column < 0 or column >= len(self.item_data):
            return None
        return self.item_data[column]

    def add_child(self, child: CustomNode):
        """
        Add a child item.

        :param child: TreeItem to add as a child.
        """
        self.child_items.append(child)
        child.parent_item = self

    def insert_children(self, position: int, count: int, columns: int) -> bool:
        """
        Insert multiple child items at the specified position.

        :param position: Position to insert the children.
        :param count: Number of children to insert.
        :param columns: Number of columns for each child.
        :return: Boolean indicating if the insertion was successful.
        """
        if position < 0 or position > len(self.child_items):
            return False

        for row in range(count):
            data = [None] * columns
            item = CustomNode(data.copy(), self)
            self.child_items.insert(position, item)

        return True

    def insert_columns(self, position: int, columns: int) -> bool:
        """
        Insert columns into the item data.

        :param position: Position to insert the columns.
        :param columns: Number of columns to insert.
        :return: Boolean indicating if the insertion was successful.
        """
        if position < 0 or position > len(self.item_data):
            return False

        for column in range(columns):
            self.item_data.insert(position, None)

        for child in self.child_items:
            child.insert_columns(position, columns)

        return True

    def parent(self):
        """
        Get the parent item.

        :return: Parent TreeItem or None if there is no parent.
        """
        return self.parent_item

    def child_at(self, position: int) -> CustomNode | None:
        """
        Get the child item at the specified position.

        :param position: Position of the child item.
        :return: TreeItem at the specified position or None if out of range.
        """
        if position < 0 or position >= len(self.child_items):
            return None

        return self.child_items[position]

    def child_index(self, child: CustomNode) -> int:
        """
        Get the index of the specified child item.

        :param child: Child TreeItem.
        :return: Index of the child item.
        """
        return self.child_items.index(child)

    def remove_child(self, position: int) -> bool:
        """
        Remove the child item at the specified position.

        :param position: Position of the child item to remove.
        :return: Boolean indicating if the removal was successful.
        """
        if position < 0 or position >= len(self.child_items):
            return False

        self.child_items.pop(position)
        return True

    def remove_children(self, position: int, count: int) -> bool:
        """
        Remove multiple child items starting from the specified position.

        :param position: Starting position of the children to remove.
        :param count: Number of children to remove.
        :return: Boolean indicating if the removal was successful.
        """
        if position < 0 or position + count > len(self.child_items):
            return False

        for row in range(count):
            self.child_items.pop(position)

        return True

    def remove_columns(self, position: int, columns: int) -> bool:
        """
        Remove columns from the item data.

        :param position: Starting position of the columns to remove.
        :param columns: Number of columns to remove.
        :return: Boolean indicating if the removal was successful.
        """
        if position < 0 or position + columns > len(self.item_data):
            return False

        for column in range(columns):
            self.item_data.pop(position)

        for child in self.child_items:
            child.remove_columns(position, columns)

        return True

    def set_data(self, column: int, value):
        """
        Set the data at the specified column.

        :param column: Column index.
        :param value: New value to set.
        :return: Boolean indicating if the data was set successfully.
        """
        if column < 0 or column >= len(self.item_data):
            return False

        self.item_data[column] = value
        return True

    def __repr__(self) -> str:
        """
        Get a string representation of the TreeItem.

        :return: String representation of the TreeItem.
        """
        result = f"<treeitem.TreeItem at 0x{id(self):x}"
        for d in self.item_data:
            result += f' "{d}"' if d else " <None>"
        result += f", {len(self.child_items)} children>"
        return result