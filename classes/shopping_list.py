import time
from classes.item import Item


class ShoppingList(object):
    def __init__(self, title):
        self.title = title
        self.items = []

        # generate a random id for this item
        epoch_time = time.time()
        self.id = round(float(str(epoch_time)[8:]) * 10000000)

    def add_item(self, item_name):
        if item_name is None or len(item_name) < 1:
            return "Item must have a name"

        if not isinstance(item_name, str):
            return "Item name must be a string"

        for item in self.items:
            if item.name == item_name:
                return 'Item ' + item_name + ' already added'

        new_item = Item(item_name)
        self.items.append(new_item)

        return new_item.id

    def remove_item(self, item_id):
        if not isinstance(item_id, int):
            return "Item id must be an Integer"

        for item in self.items:
            if item.id == item_id:
                del item
                return True

        return "Item does not exist"

    def list_items(self):
        item_names = []
        for item in self.items:
            item_names.append(item.name)

        return item_names