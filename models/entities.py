
class Clazz:
    def __init__(self, 
                 name, 
                 full_qualified_name, 
                 absolute_path, 
                 start_line, 
                 end_line, content, 
                 class_type,
                 parent_classes):
        self.name = name
        self.full_qualified_name = full_qualified_name
        self.absolute_path = absolute_path
        self.start_line = start_line
        self.end_line = end_line
        self.content = content
        self.class_type = class_type
        self.parent_class = parent_classes

class Method:
    def __init__(self, 
                 name, 
                 full_qualified_name, 
                 absolute_path, start_line, 
                 end_line, 
                 content, 
                 params, 
                 modifiers, 
                 signature, type):
        self.name = name
        self.full_qualified_name = full_qualified_name
        self.absolute_path = absolute_path
        self.start_line = start_line
        self.end_line = end_line
        self.content = content
        self.params = params
        self.modifiers = modifiers
        self.signature = signature
        self.type = type

class Variable:
    def __init__(self, 
                 name, 
                 full_qualified_name, 
                 absolute_path, 
                 start_line, 
                 end_line, 
                 content,  
                 modifiers, 
                 data_type):
        self.name = name
        self.full_qualified_name = full_qualified_name
        self.absolute_path = absolute_path
        self.start_line = start_line
        self.end_line = end_line
        self.content = content
        self.modifiers = modifiers
        self.data_type = data_type