from utils import get_parent_dir
import gettext
import os

APP_NAME="deepin-ui"
LOCALE_DIR=os.path.join(get_parent_dir(__file__, 2), "locale")
if not os.path.exists(LOCALE_DIR):
    LOCALE_DIR="/usr/share/locale"
    
gettext.bindtextdomain(APP_NAME, LOCALE_DIR)
gettext.textdomain(APP_NAME)
_ = gettext.gettext
