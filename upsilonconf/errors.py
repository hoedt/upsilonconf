class OptionalDependencyError(ImportError):
    """Raised when an attempt is made to import an optional dependency."""

    pass


class InvalidKeyError(ValueError):
    """Raised when a key can not be used in a configuration object."""

    pass
