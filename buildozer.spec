[app]
title = TV Remote
package.name = tvremote
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,webp,json,txt
source.include_patterns = assets/logos/*.png, assets/logos/*.jpg, assets/logos/*.jpeg, assets/logos/*.webp, assets/adbkey.txt, assets/adbkey.pub.txt
version = 0.1

requirements = python3,kivy==2.3.0,adb-shell,cryptography,pyjnius,pillow
orientation = all
fullscreen = 0

android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
