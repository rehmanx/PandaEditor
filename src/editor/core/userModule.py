import editor.utils as EdUtils


class UserModule:
    def __init__(self, class_instance, sort_value):
        """ Class representing a Runtime User module or Editor plugin """
        self.class_instance = class_instance
        self.sort_value = sort_value
        self.saved_data = None

    def save_data(self):
        obj_data = EdUtils.ObjectData(self.class_instance._name)

        # get all attributes of module and add them to object data
        for name, val in self.class_instance.get_savable_atts():
            prop = EdUtils.EdProperty.Property(name, val)
            obj_data.add_property(prop)

        self.saved_data = obj_data

    def reload_data(self):
        properties = self.saved_data.properties

        for name, val in properties:
            if hasattr(self.class_instance, name):
                setattr(self.class_instance, name, val)
