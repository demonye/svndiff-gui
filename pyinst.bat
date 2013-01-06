python ..\pyinstaller-2.0\pyinstaller.py -y -w -i logo.ico svndiff-gui.py
python ..\pyinstaller-2.0\pyinstaller.py -c -F svndiff.py
python ..\pyinstaller-2.0\pyinstaller.py -c -F diff.py
copy *.png dist\svndiff-gui
copy *.gif dist\svndiff-gui
copy diff_template.html dist\svndiff-gui
copy settings dist\svndiff-gui
copy dist\*.exe dist\svndiff-gui
mkdir dist\svndiff-gui\imageformats
copy dist\imageformats\*.* dist\svndiff-gui\imageformats

