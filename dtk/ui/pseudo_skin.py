from skin_config import skin_config
from theme import Theme, ui_theme
from utils import get_parent_dir
import os

# Init skin config.
skin_config.init_skin(
    "01",
    os.path.join(get_parent_dir(__file__, 3), "skin"),
    os.path.expanduser("~/.config/deepin-demo/skin"),
    os.path.expanduser("~/.config/deepin-demo/skin_config.ini"),
    )

# Create application theme.
app_theme = Theme(
    os.path.join(get_parent_dir(__file__, 3), "app_theme"),
    os.path.expanduser("~/.config/deepin-demo/theme")
    )

# Set theme.
skin_config.load_themes(ui_theme, app_theme)
