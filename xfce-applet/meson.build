project(
  'starcal-applet',
  'c',
  version: '0.1.0',
  meson_version: '>= 0.54.0',
  default_options: [
    'c_std=gnu11',
    'buildtype=debugoptimized',
    'warning_level=2',
  ]
)

glib = dependency('glib-2.0', version: '>= 2.66.0')
gtk = dependency('gtk+-3.0', version: '>= 3.22.0')
libxfce4panel = dependency('libxfce4panel-2.0', version: '>= 4.16.0')

subdir('panel-plugin')