#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
#
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from deepin_utils.file import get_parent_dir
from skin_config import skin_config
from theme import Theme, ui_theme
import os

def init_skin(project_name,
              project_version,
              skin_name,
              application_skin_dir,
              application_theme_dir=None,
              ):
    '''
    Initialize skin easily.

    @param project_name: Project name.
    @param project_version: Project version.
    @param skin_name: Default skin name.
    @param application_skin_dir: Application's skin directory in system level, user space skin directory at ~/.config/project_name/skin .
    @param application_skin_dir: Application's theme directory in system level, user space theme directory at ~/.config/project_name/theme, set as None if don't you just want use theme of deepin-ui.
    @return: Return application theme, return None if application_theme_dir is None.

    >>> from dtk.ui.init_skin import init_skin
    >>> from deepin_utils.file import get_parent_dir
    >>> import os
    >>>
    >>> app_theme = init_skin(
    >>>     "deepin-ui-demo",
    >>>     "1.0",
    >>>     "01",
    >>>     os.path.join(get_parent_dir(__file__), "skin"),
    >>>     os.path.join(get_parent_dir(__file__), "app_theme"),
    >>>     )

    Equal to below code:

    >>> from dtk.ui.skin_config import skin_config
    >>> from dtk.ui.theme import Theme, ui_theme
    >>> from deepin_utils.file import get_parent_dir
    >>> import os
    >>>
    >>> # Init skin config.
    >>> skin_config.init_skin(
    >>>     "01",
    >>>     os.path.join(get_parent_dir(__file__), "skin"),
    >>>     os.path.expanduser("~/.config/deepin-ui-demo/skin"),
    >>>     os.path.expanduser("~/.config/deepin-ui-demo/skin_config.ini"),
    >>>     "deepin-ui-demo",
    >>>     "1.0"
    >>>     )
    >>>
    >>> # Create application theme.
    >>> app_theme = Theme(
    >>>     os.path.join(get_parent_dir(__file__), "app_theme"),
    >>>     os.path.expanduser("~/.config/deepin-ui-demo/theme")
    >>>     )
    >>>
    >>> # Set theme.
    >>> skin_config.load_themes(ui_theme, app_theme)
    '''
    # Init skin config.
    skin_config.init_skin(
        skin_name,
        application_skin_dir,
        os.path.expanduser("~/.config/%s/skin" % (project_name)),
        os.path.expanduser("~/.config/%s/skin_config.ini" % (project_name)),
        project_name,
        project_version,
        )

    # Create application theme.
    if application_theme_dir != None:
        app_theme = Theme(
            application_theme_dir,
            os.path.expanduser("~/.config/%s/theme" % (project_name))
            )
    else:
        app_theme = None

    # Set theme.
    skin_config.load_themes(ui_theme, app_theme)

    return app_theme

def init_theme():
    '''
    Use deepin-ui's default theme.
    '''
    init_skin(
        "deepin-ui",
        "1.0",
        "default",
        os.path.join(get_parent_dir(__file__, 2), "skin"),
        )
