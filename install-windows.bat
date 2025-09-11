REM Install Python 3.8+
REM Add to PATH environment variable: Python3X/ and Python3X/Scripts

REM https://sourceforge.net/p/pygobjectwin32/tickets/58/
REM Author of pygobjectwin32(tumagonx) on 2021-01-11:
REM while newest mingw-w64 capable of targeting msvc 14 runtime (python 3.5-3.8)
REM and I just tried simple stuff. I dont think I will return to this project. So no.


REM Install other dependencies:
pip3 install pycairo
pip3 install psutil
pip3 install cachetools
pip3 install requests

