REM Install Python 3.4 (because pygi-aio does not work with Python 3.6)
REM Add to environment variable: Python34/ and Python34/Scripts
REM Download latest pygi-aio from: https://sourceforge.net/projects/pygobjectwin32/files/
REM Run pygi-aio, check these packages:
REM - Base packages
REM - GDK-Pixbuf
REM - GTK+


REM Install other dependencies:
pip3 install python-dateutil
pip3 install psutil
pip3 install requests

