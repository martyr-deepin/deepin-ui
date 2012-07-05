/* Copyright (C) 2012 Deepin, Inc.
 *               2012 Wang Yong
 *               2012 Xia Bin
 *
 * Author:     Xia Bin <xiabin@linuxdeepin.com>
 * Maintainer: Wang Yong <lazycat.manatee@gmail.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <stdlib.h>
#include <string.h>
#include <glib.h>
#include <gtk/gtk.h>
#include <webkit/webkit.h>
#include <libsoup/soup.h>
#include <Python.h>
#include "pygobject.h"

static void add_cookie(char *cookie_file)
{
     SoupSession *session = webkit_get_default_session();
     SoupCookieJar *jar = soup_cookie_jar_text_new(cookie_file, false);
     soup_session_add_feature(session, SOUP_SESSION_FEATURE(jar));
}

static PyObject* dtk_webkit_cookie_add_cookie(PyObject* self, PyObject* args);

static PyMethodDef webkit_cookie_methods[] = {
     {"add_cookie", (PyCFunction)dtk_webkit_cookie_add_cookie, METH_VARARGS,
      "Add cookie support for webkit webview."},
     {NULL, NULL, 0, NULL}
};


static PyObject* dtk_webkit_cookie_add_cookie(PyObject* self, PyObject* args) {
     char *cookie_file;
     
     if (!PyArg_ParseTuple(args, "s", &cookie_file)) {
          return NULL;
     }

     add_cookie(cookie_file);

     Py_RETURN_NONE;
}

PyMODINIT_FUNC initdtk_webkit_cookie(void) {
     PyObject *m;

     /* This is necessary step for Python binding, otherwise got sefault error */
     init_pygobject();
     
     m = Py_InitModule("dtk_webkit_cookie", webkit_cookie_methods);

     if (!m) {
          return;
     }
}
