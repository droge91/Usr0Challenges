def validate(string):
    hasnum = any(char.isdigit() for char in string)
    hasq = any(char == "q" for char in string.lower())
    haslength = True if len(string) < 10 and len(string) > 5 else False

    if hasnum and hasq and haslength:
        return True
    return False