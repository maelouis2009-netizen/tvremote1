import os
import shutil
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.metrics import dp
from kivy.animation import Animation
from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.keygen import keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner

ANDROID = False
try:
    from jnius import autoclass
    from android import activity as android_activity
    ANDROID = True
except Exception:
    ANDROID = False

TV_IP = "192.168.8.7"
ADB_PORT = 5555
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUNDLED_LOGO_DIR = os.path.join(BASE_DIR, "assets", "logos")
EXTS = (".png", ".jpg", ".jpeg", ".webp")
USER_LOGO_DIR = None

BRAND_COLORS = {
    "Netflix": (0.89, 0.10, 0.11, 1), "SmartTube": (1.0, 0.8, 0.0, 1),
    "Nuvio": (0.2, 0.2, 0.6, 1), "Prime Video": (0.0, 0.65, 0.95, 1),
    "Canal+": (0.1, 0.1, 0.1, 1), "TF1+": (0.0, 0.4, 0.9, 1),
    "M6+": (0.9, 0.9, 0.1, 1), "Disney+": (0.05, 0.05, 0.3, 1),
    "France.tv": (0.9, 0.2, 0.2, 1), "Orange TV": (1.0, 0.45, 0.0, 1),
    "YouTube Music": (1.0, 0.0, 0.0, 1), "Roblox": (0.1, 0.1, 0.1, 1),
    "Steam Link": (0.1, 0.2, 0.4, 1), "Downloader": (1.0, 0.5, 0.0, 1),
    "Uptodown": (0.2, 0.6, 0.9, 1), "Retro": (0.5, 0.0, 0.0, 1),
    "NaviTV": (0.2, 0.2, 0.8, 1), "MagiConnect": (0.9, 0.2, 0.2, 1),
    "AutoStart Manager": (0.2, 0.2, 0.2, 1), "Button Mapper": (0.3, 0.6, 0.9, 1),
    "Media Player": (0.6, 0.3, 0.9, 1), "Navigateur": (0.1, 0.5, 0.9, 1),
    "T-solo": (0.5, 0.3, 0.9, 1), "Alexa": (0.0, 0.6, 0.9, 1)
}

QUICK_APPS = {
    "com.netflix.ninja": "Netflix", "org.smarttube.stable": "SmartTube",
    "com.nuvio.tv": "Nuvio", "com.amazon.amazonvideo.livingroom": "Prime Video"
}

ALLOWED_APPS = {
    "com.netflix.ninja": "Netflix", "org.smarttube.stable": "SmartTube",
    "com.nuvio.tv": "Nuvio", "com.amazon.amazonvideo.livingroom": "Prime Video",
    "com.canal.android.canal": "Canal+", "fr.tf1.mytf1": "TF1+",
    "fr.m6.m6replay": "M6+", "com.disney.disneyplus": "Disney+",
    "fr.francetv.pluzz": "France.tv", "com.orange.owtv.tv": "Orange TV",
    "com.google.android.youtube.tvmusic": "YouTube Music", "com.roblox.client": "Roblox",
    "com.valvesoftware.steamlink": "Steam Link", "com.esaba.downloader": "Downloader",
    "com.uptodown": "Uptodown", "io.github.udhaykumarbala.retro": "Retro",
    "com.tdpham.navitvbrowser": "NaviTV", "com.tcl.magiconnectfree": "MagiConnect",
    "com.sugarapps.autostartmanager": "AutoStart Manager", "flar2.homebutton": "Button Mapper",
    "com.tcl.ui_mediaCenter": "Media Player", "com.tcl.browser": "Navigateur",
    "com.tcl.t_solo": "T-solo", "com.tcl.smartalexa": "Alexa"
}

def get_slug(name):
    return name.lower().replace(" ", "-").replace("+", "-plus").replace(".", "-")

def find_logo(slug):
    dirs = []
    if USER_LOGO_DIR:
        dirs.append(USER_LOGO_DIR)
    dirs.append(BUNDLED_LOGO_DIR)
    for d in dirs:
        for e in EXTS:
            p = os.path.join(d, slug + e)
            if os.path.exists(p):
                return p
    return None

class AppCard(ButtonBehavior, RelativeLayout):
    def __init__(self, app_name, pkg, color, image_path=None, on_launch=None, on_long_press=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(100), dp(125))
        self.pkg = pkg
        self.app_name = app_name
        self.on_launch = on_launch
        self.on_long_press = on_long_press
        self._long_fired = False
        self._long_event = None
        
        with self.canvas.before:
            Color(0.15, 0.15, 0.18, 0.3)
            self.shadow = RoundedRectangle(size=(self.size[0]-4, self.size[1]-4), pos=(self.pos[0]+2, self.pos[1]-2), radius=[dp(16)])
            Color(*color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[dp(16)])
        self.bind(size=self._update_canvas, pos=self._update_canvas)
        
        if image_path:
            img = Image(source=image_path, size_hint=(0.75, 0.65), pos_hint={'center_x': 0.5, 'center_y': 0.68}, allow_stretch=True, keep_ratio=True)
            self.add_widget(img)
            label = Label(text=app_name, color=(1,1,1,1), font_size=dp(10), bold=True, size_hint=(1, 0.25), pos_hint={'center_x': 0.5, 'center_y': 0.12})
            self.add_widget(label)
        else:
            label = Label(text=app_name, color=(1,1,1,1), font_size=dp(12), bold=True, halign='center', valign='middle')
            label.text_size = self.size
            label.bind(size=lambda *args: setattr(label, 'text_size', self.size))
            self.add_widget(label)

    def _update_canvas(self, instance, value):
        self.shadow.pos = (instance.pos[0]+2, instance.pos[1]-2)
        self.shadow.size = (instance.size[0]-4, instance.size[1]-4)
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_press(self):
        self._long_fired = False
        self._long_event = Clock.schedule_once(self._fire_long, 0.8)
        Animation(scale=0.95, duration=0.1).start(self)

    def _fire_long(self, dt):
        self._long_fired = True
        if self.on_long_press:
            self.on_long_press(self.app_name)

    def on_release(self):
        if self._long_event is not None:
            self._long_event.cancel()
            self._long_event = None
        Animation(scale=1.0, duration=0.1).start(self)
        if not self._long_fired and self.on_launch:
            self.on_launch(self.pkg)

class RoundButton(Button):
    """Bouton rond avec couleur de fond"""
    def __init__(self, text, color, keycode, on_press_callback, btn_size=None, **kwargs):
        if btn_size is None:
            btn_size = dp(65)
        super().__init__(
            text=text,
            font_size=dp(20),
            bold=True,
            color=(1, 1, 1, 1),
            background_color=color,
            background_normal='',
            size_hint=(None, None),
            size=(btn_size, btn_size),
            **kwargs
        )
        self.keycode = keycode
        self.on_press_callback = on_press_callback
        self.bind(on_press=self._on_press)
    
    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.keycode)

class TVRemoteApp(App):
    search_text = StringProperty("")

    def build(self):
        global USER_LOGO_DIR
        USER_LOGO_DIR = os.path.join(self.user_data_dir, "logos")
        os.makedirs(USER_LOGO_DIR, exist_ok=True)
        Window.clearcolor = (0.08, 0.08, 0.1, 1)
        
        w, h = Window.size
        is_portrait = h > w
        
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=12)

        self.search_field = TextInput(
            hint_text="  Rechercher une application...",
            size_hint_y=None, height=50, font_size='16sp',
            background_color=(0.15, 0.15, 0.18, 1), foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.5, 0.5, 1), multiline=False
        )
        self.search_field.bind(text=self.on_search_text)
        main_layout.add_widget(self.search_field)

        if is_portrait:
            self.scroll = ScrollView(size_hint_y=0.58)
            self.apps_grid = GridLayout(cols=3, spacing=dp(12), size_hint_y=None, padding=dp(12))
            self.apps_grid.bind(minimum_height=self.apps_grid.setter('height'))
            self.scroll.add_widget(self.apps_grid)
            main_layout.add_widget(self.scroll)

            self.status_label = Label(text="Chargement...", size_hint_y=None, height=25, color=(0.5, 0.5, 0.5, 1), font_size='12sp')
            main_layout.add_widget(self.status_label)

            ctrl_layout = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=8)
            
            row1 = GridLayout(cols=3, spacing=10, size_hint_y=0.2)
            row1.add_widget(RoundButton("PWR", (0.9, 0.1, 0.1, 1), 26, self.send_key_async))
            row1.add_widget(RoundButton("HOME", (0.2, 0.4, 0.8, 1), 3, self.send_key_async))
            row1.add_widget(RoundButton("RET", (0.4, 0.4, 0.4, 1), 4, self.send_key_async))
            ctrl_layout.add_widget(row1)
            
            cross_layout = BoxLayout(orientation='vertical', spacing=6, size_hint_y=0.6)
            
            up_row = GridLayout(cols=3, spacing=10, size_hint_y=0.33)
            up_row.add_widget(Label(text=""))
            up_row.add_widget(RoundButton("^", (0.3, 0.3, 0.35, 1), 19, self.send_key_async))
            up_row.add_widget(Label(text=""))
            cross_layout.add_widget(up_row)
            
            mid_row = GridLayout(cols=3, spacing=10, size_hint_y=0.34)
            mid_row.add_widget(RoundButton("<", (0.3, 0.3, 0.35, 1), 21, self.send_key_async))
            mid_row.add_widget(RoundButton("OK", (0.1, 0.6, 0.2, 1), 23, self.send_key_async))
            mid_row.add_widget(RoundButton(">", (0.3, 0.3, 0.35, 1), 22, self.send_key_async))
            cross_layout.add_widget(mid_row)
            
            down_row = GridLayout(cols=3, spacing=10, size_hint_y=0.33)
            down_row.add_widget(Label(text=""))
            down_row.add_widget(RoundButton("v", (0.3, 0.3, 0.35, 1), 20, self.send_key_async))
            down_row.add_widget(Label(text=""))
            cross_layout.add_widget(down_row)
            
            ctrl_layout.add_widget(cross_layout)
            
            vol_row = GridLayout(cols=3, spacing=10, size_hint_y=0.2)
            vol_row.add_widget(RoundButton("-", (0.4, 0.4, 0.45, 1), 25, self.send_key_async))
            vol_row.add_widget(Label(text=""))
            vol_row.add_widget(RoundButton("+", (0.4, 0.4, 0.45, 1), 24, self.send_key_async))
            ctrl_layout.add_widget(vol_row)
            
            main_layout.add_widget(ctrl_layout)
        else:
            h_layout = BoxLayout(orientation='horizontal', spacing=15)
            
            ctrl_layout = BoxLayout(orientation='vertical', size_hint_x=0.28, spacing=8)
            
            row1 = GridLayout(cols=3, spacing=8, size_hint_y=0.15)
            row1.add_widget(RoundButton("PWR", (0.9, 0.1, 0.1, 1), 26, self.send_key_async, btn_size=dp(55)))
            row1.add_widget(RoundButton("HOME", (0.2, 0.4, 0.8, 1), 3, self.send_key_async, btn_size=dp(55)))
            row1.add_widget(RoundButton("RET", (0.4, 0.4, 0.4, 1), 4, self.send_key_async, btn_size=dp(55)))
            ctrl_layout.add_widget(row1)
            
            cross_layout = BoxLayout(orientation='vertical', spacing=6, size_hint_y=0.6)
            
            up_row = GridLayout(cols=3, spacing=8, size_hint_y=0.33)
            up_row.add_widget(Label(text=""))
            up_row.add_widget(RoundButton("^", (0.3, 0.3, 0.35, 1), 19, self.send_key_async, btn_size=dp(55)))
            up_row.add_widget(Label(text=""))
            cross_layout.add_widget(up_row)
            
            mid_row = GridLayout(cols=3, spacing=8, size_hint_y=0.34)
            mid_row.add_widget(RoundButton("<", (0.3, 0.3, 0.35, 1), 21, self.send_key_async, btn_size=dp(55)))
            mid_row.add_widget(RoundButton("OK", (0.1, 0.6, 0.2, 1), 23, self.send_key_async, btn_size=dp(55)))
            mid_row.add_widget(RoundButton(">", (0.3, 0.3, 0.35, 1), 22, self.send_key_async, btn_size=dp(55)))
            cross_layout.add_widget(mid_row)
            
            down_row = GridLayout(cols=3, spacing=8, size_hint_y=0.33)
            down_row.add_widget(Label(text=""))
            down_row.add_widget(RoundButton("v", (0.3, 0.3, 0.35, 1), 20, self.send_key_async, btn_size=dp(55)))
            down_row.add_widget(Label(text=""))
            cross_layout.add_widget(down_row)
            
            ctrl_layout.add_widget(cross_layout)
            
            vol_row = GridLayout(cols=3, spacing=8, size_hint_y=0.15)
            vol_row.add_widget(RoundButton("-", (0.4, 0.4, 0.45, 1), 25, self.send_key_async, btn_size=dp(55)))
            vol_row.add_widget(Label(text=""))
            vol_row.add_widget(RoundButton("+", (0.4, 0.4, 0.45, 1), 24, self.send_key_async, btn_size=dp(55)))
            ctrl_layout.add_widget(vol_row)
            
            h_layout.add_widget(ctrl_layout)
            
            right_layout = BoxLayout(orientation='vertical')
            self.scroll = ScrollView()
            self.apps_grid = GridLayout(cols=4, spacing=dp(12), size_hint_y=None, padding=dp(12))
            self.apps_grid.bind(minimum_height=self.apps_grid.setter('height'))
            self.scroll.add_widget(self.apps_grid)
            right_layout.add_widget(self.scroll)
            
            self.status_label = Label(text="Chargement...", size_hint_y=None, height=25, color=(0.5, 0.5, 0.5, 1), font_size='12sp')
            right_layout.add_widget(self.status_label)
            
            h_layout.add_widget(right_layout)
            main_layout.add_widget(h_layout)

        self.load_apps_async()
        return main_layout

    def get_signer(self):
        key_path = os.path.join(self.user_data_dir, "tvremote_adb_key")
        if not os.path.exists(key_path):
            keygen(key_path)
        try:
            return PythonRSASigner.FromFile(key_path)
        except AttributeError:
            with open(key_path, "r") as f:
                priv = f.read()
            pub = None
            pub_path = key_path + ".pub"
            if os.path.exists(pub_path):
                with open(pub_path, "r") as f:
                    pub = f.read()
            return PythonRSASigner(pub=pub, priv=priv)

    def get_device(self):
        try:
            dev = AdbDeviceTcp(TV_IP, ADB_PORT, default_transport_timeout_s=5)
            dev.connect(rsa_keys=[self.get_signer()], auth_timeout_s=10, read_timeout_s=10)
            return dev
        except Exception as e:
            print("ERREUR CONNEXION TV:", repr(e))
            return None

    def send_key_async(self, keycode):
        threading.Thread(target=self.send_key, args=(keycode,)).start()

    def launch_app_async(self, package_name):
        threading.Thread(target=self.launch_app, args=(package_name,)).start()

    def load_apps_async(self):
        threading.Thread(target=self.load_apps).start()

    def send_key(self, keycode):
        dev = self.get_device()
        if dev:
            dev.shell(f"input keyevent {keycode}")
            dev.close()
            Clock.schedule_once(lambda dt: self._update_status("Touche envoyée"), 0)
        else:
            Clock.schedule_once(lambda dt: self._update_status("TV non connectée"), 0)

    def launch_app(self, package_name):
        dev = self.get_device()
        if dev:
            dev.shell(f"monkey -p {package_name} -c android.intent.category.LEANBACK_LAUNCHER 1")
            Clock.schedule_once(lambda dt: self._update_status("Lancé !"), 0)
            dev.close()
        else:
            Clock.schedule_once(lambda dt: self._update_status("TV non connectée"), 0)

    def load_apps(self):
        app_list = sorted([(name, pkg) for pkg, name in ALLOWED_APPS.items() if pkg not in QUICK_APPS], key=lambda x: x[0])
        Clock.schedule_once(lambda dt: self._display_apps(app_list), 0)

    def on_search_text(self, instance, value):
        self.search_text = value.lower()
        self.load_apps_async()

    def _display_apps(self, app_list):
        self.apps_grid.clear_widgets()
        filtered_list = list(app_list)
        if self.search_text:
            filtered_list = [(name, pkg) for name, pkg in app_list if self.search_text in name.lower()]
            for pkg, name in QUICK_APPS.items():
                if self.search_text in name.lower():
                    if not any(p == pkg for _, p in filtered_list):
                        filtered_list.insert(0, (name, pkg))
        else:
            for pkg, name in QUICK_APPS.items():
                filtered_list.insert(0, (name, pkg))

        self.status_label.text = f"{len(filtered_list)} applications"

        for clean_name, pkg in filtered_list:
            color = BRAND_COLORS.get(clean_name, (0.2, 0.2, 0.25, 1))
            card = AppCard(
                clean_name, pkg, color,
                image_path=find_logo(get_slug(clean_name)),
                on_launch=lambda p: self.launch_app_async(p),
                on_long_press=self.import_icon
            )
            self.apps_grid.add_widget(card)

    def import_icon(self, app_name):
        self._pending_slug = get_slug(app_name)
        Clock.schedule_once(lambda dt: self._update_status(f"Choisis une image pour {app_name}..."), 0)
        if ANDROID:
            self._pick_android()
        else:
            self._pick_pc()

    def _pick_pc(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp")])
            root.destroy()
            if path:
                ext = os.path.splitext(path)[1].lower()
                if ext not in EXTS:
                    ext = ".png"
                self._save_import(path, ext)
        except Exception:
            Clock.schedule_once(lambda dt: self._update_status("Import impossible"), 0)

    def _pick_android(self):
        try:
            Intent = autoclass('android.content.Intent')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            intent = Intent(Intent.ACTION_GET_CONTENT)
            intent.setType("image/*")
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            android_activity.bind(on_activity_result=self._on_pick_result)
            PythonActivity.startActivityForResult(intent, 42)
        except Exception:
            Clock.schedule_once(lambda dt: self._update_status("Import impossible"), 0)

    def _on_pick_result(self, requestCode, resultCode, data):
        if requestCode != 42:
            return
        try:
            android_activity.unbind(on_activity_result=self._on_pick_result)
        except Exception:
            pass
        if resultCode != -1 or data is None:
            return
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            uri = data.getData()
            resolver = PythonActivity.getContentResolver()
            ins = resolver.openInputStream(uri)
            baos = autoclass('java.io.ByteArrayOutputStream')()
            jbyte = autoclass('java.lang.Byte').TYPE
            jarr = autoclass('java.lang.reflect.Array').newInstance(jbyte, 8192)
            n = ins.read(jarr)
            while n > 0:
                baos.write(jarr, 0, n)
                n = ins.read(jarr)
            ins.close()
            raw = bytes(baos.toByteArray())
            mime = resolver.getType(uri) or "image/png"
            ext = ".jpg" if "jpeg" in mime else (".webp" if "webp" in mime else ".png")
            dest = os.path.join(USER_LOGO_DIR, self._pending_slug + ext)
            with open(dest, "wb") as f:
                f.write(raw)
            Clock.schedule_once(lambda dt: self._refresh_after_import(), 0)
        except Exception:
            Clock.schedule_once(lambda dt: self._update_status("Erreur import"), 0)

    def _save_import(self, src, ext):
        dest = os.path.join(USER_LOGO_DIR, self._pending_slug + ext)
        shutil.copyfile(src, dest)
        self._refresh_after_import()

    def _refresh_after_import(self):
        self._update_status("Icône importée !")
        self.load_apps_async()

    def _update_status(self, text):
        self.status_label.text = text

if __name__ == '__main__':
    TVRemoteApp().run()