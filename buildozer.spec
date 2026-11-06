[app]
title = TV Remote Louis
package.name = tvremote
package.domain = org.louis
source.dir = .
source.include_exts = py,png,jpg,jpeg,webp,txt
source.exclude_dirs = bin,.buildozer,.git,.github,apk_build,__pycache__
version = 1.0

requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.1,sdl2,pyjnius,pillow,requests,adb-shell,cryptography,pycryptodome,filetype

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.enable_androidx = True

p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 0
