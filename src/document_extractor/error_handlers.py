class UserFacingError(Exception):
    pass


def friendly_error(error: Exception) -> str:
    return str(error) if isinstance(error, UserFacingError) else "The document could not be processed. Check the file and configuration, then try again."
