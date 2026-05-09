from calculator_engine.app.main import app
from settings.app_settings import settings
from settings.paths import APP_ROOT, PROJECT_ROOT, SRC_ROOT


def test_imports_and_paths():
    assert app is not None
    assert PROJECT_ROOT.exists()
    assert SRC_ROOT.exists()
    assert APP_ROOT.exists()
    assert settings.app_name == "Calculator Engine"
