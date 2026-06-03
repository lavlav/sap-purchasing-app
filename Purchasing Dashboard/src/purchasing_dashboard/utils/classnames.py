
def add_if_not_present(old_classname: str, classname:str) -> str:
    """
    Adds a css class to the existing classname string if it is not already present.
    
    :param old_classname: The existing classname string.
    :param classname: The class to add.
    :return: The updated class string.
    """
    if not old_classname:
        return classname
    classes = old_classname.split()
    if classname not in classes:
        classes.append(classname)
    return ' '.join(classes)

def remove_if_present(old_classname: str, classname: str) -> str:
    """
    Removes a css class from the existing classname string if it is present.
    
    :param old_classname: The existing classname string.
    :param classname: The class to remove.
    :return: The updated class string.
    """
    if not old_classname:
        return old_classname
    classes = old_classname.split()
    if classname in classes:
        classes.remove(classname)
    return ' '.join(classes)

def toggle_class(old_classname: str, classname: str, add: bool | None = None) -> str:
    """
    Adds or removes a css class from the existing classname string based on the add flag.
    
    :param old_classname: The existing classname string.
    :param classname: The class to add or remove.
    :param add: If True, adds the class; if False, removes it. If None, toggles the class.
    :return: The updated class string.
    """
    if add is None:
        add = classname not in old_classname
    if add:
        return add_if_not_present(old_classname, classname)
    else:
        return remove_if_present(old_classname, classname)
    
def toggle_hidden_class(old_classname: str, add: bool) -> str:
    """
    Adds or removes the 'hidden' class from the existing classname string based on the add flag.
    
    :param old_classname: The existing classname string.
    :param add: If True, adds the 'hidden' class; if False, removes it.
    :return: The updated class string.
    """
    return toggle_class(old_classname, "hidden", add)