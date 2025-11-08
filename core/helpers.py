def handle_serializer_exception(val, custom_message="-"):
    print("val.errors", val.errors)
    if "error" in val.errors:
        error = val.errors["error"][0]
    else:
        key = next(iter(val.errors))
        error = key + ", " + val.errors[key][0]
        error = error.replace("non_field_errors, ", "")

    if custom_message != "-":
        if "unique" in str(error).lower():
            error = custom_message
    return error
