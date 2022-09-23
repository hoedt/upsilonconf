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


def _lazy_imports(
    pkg_name: str, submodules: dict, base_dir: list, aliases: dict = None
):
    """
    Function for lazily importing submodules in a package.

    Parameters
    ----------
    pkg_name : str
        The package name. Typically ``__package__``.
        This is necessary for building the fully qualified module name.
    submodules : dict
        Dictionary mapping module names to a list of attributes.
    base_dir : list
        List of already known names. Typically the output of ``dir()``.
    aliases : dict, optional
        Aliases for imported modules or attributes.

    Returns
    -------
    __getattr__
        Function to access sub-modules and attributes for a module.
    __dir__
        Function to list available names for a module.
    """
    # inspired by https://github.com/scientific-python/lazy_loader
    import importlib

    attr_to_module = {attr: m for m, attrs in submodules.items() for attr in attrs}
    if aliases is None:
        aliases = {}

    def lazy_getattr(name: str):
        name = aliases.get(name, name)
        if name in submodules.keys():
            return importlib.import_module(f"{pkg_name}.{name}")

        if name in attr_to_module.keys():
            m = importlib.import_module(f"{pkg_name}.{attr_to_module[name]}")
            return getattr(m, name)

        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    def lazy_dir():
        return list(attr_to_module.keys()) + base_dir + list(submodules.keys())

    return lazy_getattr, lazy_dir
