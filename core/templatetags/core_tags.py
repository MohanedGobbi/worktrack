from django import template

register = template.Library()

@register.filter(name='split_csv')
def split_csv(value):
    """Splits a comma-separated string into a list and trims whitespace."""
    if not value:
        return []
    return [item.strip() for item in str(value).split(',') if item.strip()]
@register.filter(name='get_item')
def get_item(dictionary, key):
    """Allows dictionary lookup in templates using a variable key."""
    return dictionary.get(key)

@register.filter(name='split')
def split(value, key):
    """
    Returns the value turned into a list.
    """
    return value.split(key)
@register.filter(name='multiply')
def multiply(value, arg):
    """Multiplies the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value

@register.filter(name='divide')
def divide(value, arg):
    """Divides the value by the argument."""
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return value

@register.filter(name='replace')
def replace(value, arg):
    """
    Replacing filter
    Use `{{ "aaa"|replace:"a,b" }}`
    """
    if len(arg.split(',')) != 2:
        return value

    what, to = arg.split(',')
    
    # allow stripping quotes from the what and to pieces.
    what = what.strip('\'"')
    to = to.strip('\'"')
    
    return value.replace(what, to)
