# -*- mode: python -*-
a = Analysis(['uploadfiles.py'],
             pathex=['F:\\Ye_Projects\\svndiff-gui'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'uploadfiles.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=True )
