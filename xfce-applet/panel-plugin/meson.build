plugin_sources = [
  'panel-plugin.c',
  'panel-plugin.h',
]

plugin_install_subdir = 'xfce4' / 'panel' / 'plugins'

plugin_lib = shared_module(
  'starcal-applet',
  plugin_sources,
  gnu_symbol_visibility: 'hidden',
  c_args: [
    '-DG_LOG_DOMAIN="starcal-applet"',
  ],
  dependencies: [
    glib,
    gtk,
    libxfce4panel,
  ],
  install: true,
  install_dir: get_option('prefix') / get_option('libdir') / plugin_install_subdir,
)

install_data(
  'starcal-applet.desktop',
  install_dir: get_option('prefix') / get_option('datadir') / plugin_install_subdir,
)

# install the app icon into the hicolor theme so the panel item and the
# "Add New Items" dialog show it
install_data(
  '../../images/starcal-48.png',
  install_dir: get_option('prefix') / get_option('datadir') / 'icons' / 'hicolor' / '48x48' / 'apps',
)