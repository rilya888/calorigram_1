
def test_imports():
    import importlib
    for mod in ["config", "constants", "database", "scheduler", "api_client"]:
        importlib.import_module(mod)
