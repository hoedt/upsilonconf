class OptionalDependencyError(ImportError):
    """Raised when an attempt is made to import an optional dependency."""

    pass


def optional_dependency_to(feature: str = None, package: str = None) -> callable:
    """
    Decorator factory for functions that provide optional features.

    The decorators produced by this decorator factory aim
    to capture any import errors that might occur
    as a result of optional dependencies not being installed.
    If the import statement fails, an `OptionalDependencyError` is raised
    with a (hopefully) more meaningful error message.

    Parameters
    ----------
    feature : str, optional
        A description of the optional feature that could fail.
        This description should complete the sentence
        "You have to install a package to ...".
        If no description is provided, a generic description is used.
    package : str, optional
        The name of the package that needs to be installed
        to make use of the optional features.
        By default, the module name is used to identify the package.
        However, sometimes there might be a (slight) difference.

    Returns
    -------
    _decorator : callable
        A decorator for wrapping functions with imports of optional dependencies.
        This wrapper will raise an `OptionalDependencyError` if the import fails.
    """
    if feature is None:
        feature = "make use of this feature"

    def _decorator(func: callable):
        def _wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ImportError as err:
                pkg = err.name if package is None else package
                msg = f"You have to install '{pkg}' to {feature}"
                raise OptionalDependencyError(
                    msg, name=err.name, path=err.path
                ) from err

        return _wrapper

    return _decorator


optional_dependency = optional_dependency_to(None)
