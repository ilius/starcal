/*
 * StarCalendar Xfce panel applet
 *
 * A small Xfce4-panel plugin that replaces the StarCalendar tray/status icon.
 * It shows the status icon rendered by StarCalendar (a PNG written to
 * ~/.starcal3/xfce-applet/icon.png) and forwards click events to the
 * running StarCalendar process over a Unix socket
 * (~/.starcal3/xfce-applet/applet.sock).
 *
 * Run StarCalendar with `starcal --xfce-applet` (optionally with --hide) so it
 * serves the applet instead of the status icon.
 *
 * Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program; if not, see <http://www.gnu.org/licenses/agpl.txt>.
 */

#include <gtk/gtk.h>
#include <gio/gio.h>
#include <libxfce4panel/libxfce4panel.h>

#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#include "panel-plugin.h"

#define ICON_FILE_PREFIX "starcal3-indicator-"
#define TOOLTIP_FILE_NAME "tooltip.txt"
#define SOCKET_FILE_NAME "applet.sock"
#define LAUNCH_COMMAND_FILE "launch-command"
#define FALLBACK_ICON_NAME "starcal32"

typedef struct _StarcalAppletPlugin
{
    XfcePanelPlugin *plugin;

    GtkWidget *event_box;
    GtkWidget *image;

    GFileMonitor *dir_monitor;

    gchar *applet_dir;
    gchar *tooltip_path;
    gchar *socket_path;

    gint64 last_launch_time;
}
StarcalAppletPlugin;

static void
starcal_applet_construct (XfcePanelPlugin *plugin);

XFCE_PANEL_PLUGIN_REGISTER (starcal_applet_construct)

static gchar *
starcal_applet_build_dir (void)
{
    const gchar *env_dir = g_getenv ("STARCAL_XFCE_APPLET_DIR");
    if (env_dir != NULL && *env_dir != '\0')
        return g_strdup (env_dir);
    return g_build_filename (g_get_home_dir (), ".starcal3", "xfce-applet", NULL);
}

static gchar *
starcal_applet_find_icon_path (StarcalAppletPlugin *applet)
{
    GDir        *dir;
    const gchar *name;
    gchar       *newest = NULL;
    gint64       newest_mtime = -1;

    dir = g_dir_open (applet->applet_dir, 0, NULL);
    if (dir == NULL)
        return NULL;

    while ((name = g_dir_read_name (dir)) != NULL)
    {
        gchar     *path;
        GFile     *file;
        GFileInfo *info;
        gint64     mtime;

        if (!g_str_has_prefix (name, ICON_FILE_PREFIX)
            || !g_str_has_suffix (name, ".png"))
            continue;

        path = g_build_filename (applet->applet_dir, name, NULL);
        file = g_file_new_for_path (path);
        info = g_file_query_info (
            file, G_FILE_ATTRIBUTE_TIME_MODIFIED,
            G_FILE_QUERY_INFO_NONE, NULL, NULL);
        g_object_unref (file);

        if (info != NULL)
        {
            mtime = g_file_info_get_attribute_uint64 (
                info, G_FILE_ATTRIBUTE_TIME_MODIFIED);
            g_object_unref (info);
            if (mtime >= newest_mtime)
            {
                g_free (newest);
                newest = path;
                newest_mtime = mtime;
            }
            else
            {
                g_free (path);
            }
        }
        else
        {
            g_free (path);
        }
    }

    g_dir_close (dir);
    return newest;
}

static void
starcal_applet_update_icon (StarcalAppletPlugin *applet,
                            gint                 size)
{
    GdkPixbuf *pixbuf;
    gchar     *icon_path;

    if (size <= 0)
        return;

    icon_path = starcal_applet_find_icon_path (applet);
    pixbuf = icon_path != NULL
        ? gdk_pixbuf_new_from_file_at_size (icon_path, size, size, NULL)
        : NULL;
    g_free (icon_path);

    if (pixbuf == NULL)
    {
        gtk_image_set_from_icon_name (
            GTK_IMAGE (applet->image), FALLBACK_ICON_NAME, GTK_ICON_SIZE_MENU);
        gtk_image_set_pixel_size (GTK_IMAGE (applet->image), size);
        return;
    }

    gtk_image_set_from_pixbuf (GTK_IMAGE (applet->image), pixbuf);
    gtk_image_set_pixel_size (GTK_IMAGE (applet->image), 0);
    g_object_unref (pixbuf);
}

static void
starcal_applet_update_tooltip (StarcalAppletPlugin *applet)
{
    gchar *contents = NULL;

    if (g_file_get_contents (applet->tooltip_path, &contents, NULL, NULL)
        && contents != NULL && *contents != '\0')
    {
        gchar *tooltip = g_strstrip (contents);
        gtk_widget_set_tooltip_text (applet->event_box, tooltip);
    }
    else
    {
        gtk_widget_set_tooltip_text (applet->event_box, NULL);
    }

    g_free (contents);
}

static void
starcal_applet_file_changed (GFileMonitor        *monitor,
                             GFile               *file,
                             GFile               *other_file,
                             GFileMonitorEvent    event_type,
                             StarcalAppletPlugin *applet)
{
    gint size;

    (void) monitor;
    (void) file;
    (void) other_file;

    /* StarCalendar writes the files atomically (write to .tmp, then rename),
     * so the interesting event is usually RENAMED/MOVED; stay safe and also
     * accept the plain change events. Reloading both icon and tooltip on any
     * change keeps this simple. */
    switch (event_type)
    {
    case G_FILE_MONITOR_EVENT_CREATED:
    case G_FILE_MONITOR_EVENT_CHANGED:
    case G_FILE_MONITOR_EVENT_CHANGES_DONE_HINT:
    case G_FILE_MONITOR_EVENT_MOVED:
    case G_FILE_MONITOR_EVENT_RENAMED:
    case G_FILE_MONITOR_EVENT_DELETED:
        break;
    default:
        return;
    }

    size = xfce_panel_plugin_get_size (applet->plugin);
    starcal_applet_update_icon (applet, size);
    starcal_applet_update_tooltip (applet);
}

static void
starcal_applet_setup_monitor (StarcalAppletPlugin *applet)
{
    GFile   *dir_file;
    GError  *error = NULL;

    dir_file = g_file_new_for_path (applet->applet_dir);
    applet->dir_monitor = g_file_monitor_directory (
        dir_file, G_FILE_MONITOR_NONE, NULL, &error);
    g_object_unref (dir_file);

    if (applet->dir_monitor == NULL)
    {
        g_warning ("Failed to monitor %s: %s",
                   applet->applet_dir,
                   error != NULL ? error->message : "unknown error");
        g_clear_error (&error);
        return;
    }

    g_signal_connect (
        applet->dir_monitor, "changed",
        G_CALLBACK (starcal_applet_file_changed), applet);
}

static gchar *
starcal_applet_find_program (void)
{
    const gchar *app_cmd;
    gchar       *program;
    gchar       *path;
    const gchar *const dirs[] = {
        "/usr/bin",
        "/usr/local/bin",
        NULL,
    };
    const gchar *const *dir;

    /* allow overriding the starcal command via the environment */
    app_cmd = g_getenv ("STARCAL_APP");
    if (app_cmd != NULL && *app_cmd != '\0')
        return g_strdup (app_cmd);

    program = g_find_program_in_path ("starcal3");
    if (program != NULL)
        return program;

    /* the panel process may not inherit the full user PATH; fall back to
     * common locations, including ~/.local/bin */
    path = g_build_filename (g_get_home_dir (), ".local", "bin", "starcal3", NULL);
    if (g_file_test (path, G_FILE_TEST_IS_EXECUTABLE))
        return path;
    g_free (path);

    for (dir = dirs; *dir != NULL; dir++)
    {
        path = g_build_filename (*dir, "starcal3", NULL);
        if (g_file_test (path, G_FILE_TEST_IS_EXECUTABLE))
            return path;
        g_free (path);
    }

    return NULL;
}

static gboolean
starcal_applet_read_launch_command (StarcalAppletPlugin *applet,
                                    gchar             ***argv_out)
{
    gchar  *path;
    gchar  *contents = NULL;
    gchar **argv = NULL;
    gint    argc = 0;

    /* StarCalendar writes its own launch command to this file so the applet
     * can start it again even when it is not installed in PATH. */
    path = g_build_filename (applet->applet_dir, LAUNCH_COMMAND_FILE, NULL);
    if (!g_file_get_contents (path, &contents, NULL, NULL))
    {
        g_free (path);
        return FALSE;
    }
    g_free (path);

    if (!g_shell_parse_argv (contents, &argc, &argv, NULL) || argc < 1)
    {
        g_strfreev (argv);
        g_free (contents);
        return FALSE;
    }
    g_free (contents);

    *argv_out = argv;
    return TRUE;
}

static void
starcal_applet_launch_starcal (StarcalAppletPlugin *applet)
{
    gchar  **argv = NULL;
    GError  *error = NULL;
    gint64   now = g_get_monotonic_time ();

    /* avoid launching multiple instances on rapid clicks */
    if (now - applet->last_launch_time < 5 * G_TIME_SPAN_SECOND)
        return;
    applet->last_launch_time = now;

    if (starcal_applet_read_launch_command (applet, &argv))
    {
        guint len = g_strv_length (argv);
        argv = g_renew (gchar *, argv, len + 2);
        argv[len] = g_strdup ("--show");
        argv[len + 1] = NULL;
    }
    else
    {
        gchar *program = starcal_applet_find_program ();
        if (program == NULL)
        {
            g_message ("starcal3 command not found; set STARCAL_APP to launch it");
            return;
        }
        argv = g_new0 (gchar *, 3);
        argv[0] = program;
        argv[1] = g_strdup ("--show");
        argv[2] = NULL;
    }

    if (g_spawn_async (
        NULL, argv, NULL, G_SPAWN_SEARCH_PATH,
        NULL, NULL, NULL, &error) == FALSE)
    {
        g_warning ("Failed to launch starcal: %s",
                   error != NULL ? error->message : "unknown error");
        g_clear_error (&error);
    }
    else
    {
        gchar *cmdline = g_strjoinv (" ", argv);
        g_message ("Launching starcal: %s", cmdline);
        g_free (cmdline);
    }

    g_strfreev (argv);
}

static void
starcal_applet_send_command (StarcalAppletPlugin *applet,
                             const gchar         *command)
{
    struct sockaddr_un addr;
    gint               fd;

    fd = socket (AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0)
        return;

    memset (&addr, 0, sizeof (addr));
    addr.sun_family = AF_UNIX;
    g_strlcpy (addr.sun_path, applet->socket_path, sizeof (addr.sun_path));

    if (connect (fd, (struct sockaddr *) &addr, sizeof (addr)) == 0)
    {
        gchar   *msg = g_strconcat (command, "\n", NULL);
        gsize    msg_len = strlen (msg);
        gssize   written = write (fd, msg, msg_len);
        (void) written;
        g_free (msg);
    }
    else
    {
        /* StarCalendar is not running; launch it on any click. */
        starcal_applet_launch_starcal (applet);
    }

    close (fd);
}

static gboolean
starcal_applet_button_press (GtkWidget           *widget,
                             GdkEventButton      *event,
                             StarcalAppletPlugin *applet)
{
    (void) widget;

    if (event->button == 1)
        starcal_applet_send_command (applet, "left-click");
    else if (event->button == 2)
        starcal_applet_send_command (applet, "middle-click");

    /* always consume the press (button 3 included) so the panel's own
     * context menu does not appear */
    return TRUE;
}

static gboolean
starcal_applet_button_release (GtkWidget           *widget,
                               GdkEventButton      *event,
                               StarcalAppletPlugin *applet)
{
    (void) widget;

    /* send the popup command on button release: a popup opened on press
     * would grab the pointer and then be dismissed by the same click's
     * button-release event */
    if (event->button == 3)
        starcal_applet_send_command (applet, "popup");

    return TRUE;
}

static gboolean
starcal_applet_size_changed (XfcePanelPlugin      *plugin,
                             gint                  size,
                             StarcalAppletPlugin  *applet)
{
    GtkOrientation orientation;

    orientation = xfce_panel_plugin_get_orientation (plugin);
    if (orientation == GTK_ORIENTATION_HORIZONTAL)
        gtk_widget_set_size_request (GTK_WIDGET (plugin), -1, size);
    else
        gtk_widget_set_size_request (GTK_WIDGET (plugin), size, -1);

    starcal_applet_update_icon (applet, size);
    return TRUE;
}

static void
starcal_applet_free (XfcePanelPlugin      *plugin,
                     StarcalAppletPlugin  *applet)
{
    (void) plugin;

    if (applet->dir_monitor != NULL)
        g_object_unref (applet->dir_monitor);

    g_free (applet->applet_dir);
    g_free (applet->tooltip_path);
    g_free (applet->socket_path);

    g_slice_free (StarcalAppletPlugin, applet);
}

static void
starcal_applet_construct (XfcePanelPlugin *plugin)
{
    StarcalAppletPlugin *applet;

    applet = g_slice_new0 (StarcalAppletPlugin);
    applet->plugin = plugin;

    applet->applet_dir = starcal_applet_build_dir ();
    applet->tooltip_path = g_build_filename (
        applet->applet_dir, TOOLTIP_FILE_NAME, NULL);
    applet->socket_path = g_build_filename (
        applet->applet_dir, SOCKET_FILE_NAME, NULL);

    /* make sure the applet dir exists so the file monitor works even when
     * StarCalendar has not been started yet */
    g_mkdir_with_parents (applet->applet_dir, 0700);

    applet->event_box = gtk_event_box_new ();
    applet->image = gtk_image_new_from_icon_name (
        FALLBACK_ICON_NAME, GTK_ICON_SIZE_MENU);
    gtk_container_add (GTK_CONTAINER (applet->event_box), applet->image);
    gtk_widget_show_all (applet->event_box);

    gtk_container_add (GTK_CONTAINER (plugin), applet->event_box);

    g_signal_connect (
        applet->event_box, "button-press-event",
        G_CALLBACK (starcal_applet_button_press), applet);
    g_signal_connect (
        applet->event_box, "button-release-event",
        G_CALLBACK (starcal_applet_button_release), applet);

    g_signal_connect (
        G_OBJECT (plugin), "free-data",
        G_CALLBACK (starcal_applet_free), applet);
    g_signal_connect (
        G_OBJECT (plugin), "size-changed",
        G_CALLBACK (starcal_applet_size_changed), applet);

    starcal_applet_setup_monitor (applet);
    starcal_applet_update_icon (
        applet, xfce_panel_plugin_get_size (plugin));
    starcal_applet_update_tooltip (applet);
}