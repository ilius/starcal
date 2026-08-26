#!/bin/bash

gtk_profile_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
gtk_profile_root=$(cd "$gtk_profile_dir/../.." && pwd)

gtk_version=${STARCAL_GTK_VERSION:-}
if [ -z "$gtk_version" ]; then
	gtk_version=$(<"$gtk_profile_root/.gtk-version")
fi

case "$gtk_version" in
	3 | 3.0)
		gtk_version=3
		gi_stub_profile="Gtk3,Gdk3,Soup2"

		almalinux_gtk_dependencies=()
		almalinux_gtksource_dependencies=('gtksourceview4')
		almalinux_appindicator_dependencies=('libappindicator-gtk3')

		archlinux_gtk_dependencies=()
		archlinux_gtksource_dependencies=('gtksourceview4')
		archlinux_appindicator_dependencies=('libappindicator-gtk3')

		debian_gtk_dependencies=('gir1.2-gtk-3.0')
		debian_gtksource_dependencies=('gir1.2-gtksource-4')
		debian_appindicator_dependencies=()

		fedora_gtk_dependencies=()
		fedora_gtksource_dependencies=('gtksourceview4')
		fedora_appindicator_dependencies=('libappindicator-gtk3')

		suse_gtk_dependencies=('typelib(Gtk) = 3.0' 'typelib(Gdk) = 3.0')
		suse_gtksource_dependencies=('typelib-1_0-GtkSource-4')
		suse_appindicator_dependencies=('typelib(AppIndicator3)')
		;;
	4 | 4.0)
		gtk_version=4
		gi_stub_profile="Gtk4,Gdk4,Soup3"

		almalinux_gtk_dependencies=('gtk4')
		almalinux_gtksource_dependencies=('gtksourceview5')
		almalinux_appindicator_dependencies=('libappindicator-gtk3')

		archlinux_gtk_dependencies=('gtk4')
		archlinux_gtksource_dependencies=('gtksourceview5')
		archlinux_appindicator_dependencies=('libappindicator-gtk3')

		debian_gtk_dependencies=('gir1.2-gtk-4.0')
		debian_gtksource_dependencies=('gir1.2-gtksource-5')
		debian_appindicator_dependencies=()

		fedora_gtk_dependencies=('gtk4')
		fedora_gtksource_dependencies=('gtksourceview5')
		fedora_appindicator_dependencies=('libappindicator-gtk3')

		suse_gtk_dependencies=('typelib(Gtk) = 4.0' 'typelib(Gdk) = 4.0')
		suse_gtksource_dependencies=('typelib-1_0-GtkSource-5')
		suse_appindicator_dependencies=('typelib(AppIndicator3)')
		;;
	*)
		echo "Unsupported GTK version: $gtk_version (expected 3 or 4)" >&2
		return 1
		;;
esac

gtk_name="Gtk$gtk_version"
