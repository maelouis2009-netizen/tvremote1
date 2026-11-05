Claude
Main · PY
import os
import shutil
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Ellipse, Triangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.metrics import dp
from adb_shell.adb_device import AdbDeviceTcp
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
        
        # RelativeLayout : les coordonnees du canvas sont relatives au widget (pos = 0,0)
        card_color = (0.15, 0.15, 0.18, 1) if image_path else color
        with self.canvas.before:
            Color(0.15, 0.15, 0.18, 0.3)
            self.shadow = RoundedRectangle(size=(self.size[0]-4, self.size[1]-4), pos=(2, -2), radius=[dp(16)])
            Color(*card_color)
            self.rect = RoundedRectangle(size=self.size, pos=(0, 0), radius=[dp(16)])
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
        self.shadow.pos = (2, -2)
        self.shadow.size = (instance.size[0]-4, instance.size[1]-4)
        self.rect.pos = (0, 0)
        self.rect.size = instance.size
 
    def on_press(self):
        self._long_fired = False
        self._long_event = Clock.schedule_once(self._fire_long, 0.8)
 
    def _fire_long(self, dt):
        self._long_fired = True
        if self.on_long_press:
            self.on_long_press(self.app_name)
 
    def on_release(self):
        if self._long_event is not None:
            self._long_event.cancel()
            self._long_event = None
        if not self._long_fired and self.on_launch:
            self.on_launch(self.pkg)
 
class KeyButton(Button):
    """Touche de telecommande arrondie qui remplit sa cellule"""
    def __init__(self, text, color, keycode, callback, **kwargs):
        super().__init__(
            text=text, font_size=dp(18), bold=True, color=(1, 1, 1, 1),
            background_normal='', background_down='', background_color=(0, 0, 0, 0),
            **kwargs
        )
        self.base_color = color
        self.keycode = keycode
        self.callback = callback
        with self.canvas.before:
            self._col = Color(*color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self.bind(pos=self._upd, size=self._upd, state=self._on_state)
        self.bind(on_press=lambda *_: self.callback(self.keycode))
 
    def _upd(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
 
    def _on_state(self, *args):
        r, g, b, a = self.base_color
        if self.state == 'down':
            self._col.rgba = (min(r + 0.25, 1), min(g + 0.25, 1), min(b + 0.25, 1), a)
        else:
            self._col.rgba = self.base_color
 
class DPad(Widget):
    """Croix directionnelle ronde, style telecommande (OK au centre)"""
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.active = None
        self.ok_label = Label(text="OK", bold=True, font_size=dp(22), color=(1, 1, 1, 1))
        self.add_widget(self.ok_label)
        self.bind(pos=self.redraw, size=self.redraw)
 
    def redraw(self, *args):
        self.canvas.before.clear()
        cx, cy = self.center_x, self.center_y
        r = min(self.width, self.height) / 2
        d = r * 0.70
        h = r * 0.12
        t = r * 0.14
        normal = (0.85, 0.86, 0.92, 1)
        lit = (0.35, 0.65, 1, 1)
        def col(name):
            return lit if self.active == name else normal
        with self.canvas.before:
            Color(0.18, 0.19, 0.25, 1)
            Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
            if self.active == 'ok':
                Color(0.25, 0.75, 0.35, 1)
            else:
                Color(0.1, 0.6, 0.2, 1)
            Ellipse(pos=(cx - r * 0.40, cy - r * 0.40), size=(r * 0.80, r * 0.80))
            Color(*col('up'))
            Triangle(points=[cx, cy + d + h, cx - t, cy + d - h, cx + t, cy + d - h])
            Color(*col('down'))
            Triangle(points=[cx, cy - d - h, cx - t, cy - d + h, cx + t, cy - d + h])
            Color(*col('left'))
            Triangle(points=[cx - d - h, cy, cx - d + h, cy - t, cx - d + h, cy + t])
            Color(*col('right'))
            Triangle(points=[cx + d + h, cy, cx + d - h, cy - t, cx + d - h, cy + t])
        self.ok_label.size = (r * 0.8, r * 0.8)
        self.ok_label.center = (cx, cy)
 
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        cx, cy = self.center_x, self.center_y
        r = min(self.width, self.height) / 2
        dx, dy = touch.x - cx, touch.y - cy
        dist = (dx * dx + dy * dy) ** 0.5
        if dist > r:
            return False
        if dist < r * 0.40:
            name, code = 'ok', 23
        elif abs(dx) > abs(dy):
            name, code = ('right', 22) if dx > 0 else ('left', 21)
        else:
            name, code = ('up', 19) if dy > 0 else ('down', 20)
        self.active = name
        self.redraw()
        Clock.schedule_once(self._release, 0.15)
        self.callback(code)
        return True
 
    def _release(self, dt):
        self.active = None
        self.redraw()
 
class TVRemoteApp(App):
    search_text = StringProperty("")
 
    def build(self):
        global USER_LOGO_DIR
        USER_LOGO_DIR = os.path.join(self.user_data_dir, "logos")
        os.makedirs(USER_LOGO_DIR, exist_ok=True)
        Window.clearcolor = (0.08, 0.08, 0.1, 1)
        
        w, h = Window.size
        is_portrait = h > w
        
        main_layout = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
 
        if is_portrait:
            # 1) Telecommande en haut
            controls = self.build_controls()
            controls.size_hint_y = None
            controls.height = dp(520)
            main_layout.add_widget(controls)
            # 2) Recherche + applis en dessous
            main_layout.add_widget(self.build_search_field())
            self.scroll = ScrollView()
            self.apps_grid = self.make_apps_grid(w)
            self.scroll.add_widget(self.apps_grid)
            main_layout.add_widget(self.scroll)
        else:
            h_layout = BoxLayout(orientation='horizontal', spacing=dp(15))
            controls = self.build_controls()
            controls.size_hint_x = 0.35
            h_layout.add_widget(controls)
            right = BoxLayout(orientation='vertical', spacing=dp(10))
            right.add_widget(self.build_search_field())
            self.scroll = ScrollView()
            self.apps_grid = self.make_apps_grid(w * 0.6)
            self.scroll.add_widget(self.apps_grid)
            right.add_widget(self.scroll)
            h_layout.add_widget(right)
            main_layout.add_widget(h_layout)
 
        self.status_label = Label(text="Chargement...", size_hint_y=None, height=dp(22), color=(0.5, 0.5, 0.5, 1), font_size='12sp')
        main_layout.add_widget(self.status_label)
 
        self.load_apps_async()
        return main_layout
 
    def build_search_field(self):
        self.search_field = TextInput(
            hint_text="  Rechercher une application...",
            size_hint_y=None, height=dp(46), font_size='16sp',
            background_color=(0.15, 0.15, 0.18, 1), foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.5, 0.5, 1), multiline=False
        )
        self.search_field.bind(text=self.on_search_text)
        return self.search_field
 
    def make_apps_grid(self, available_width):
        card_w = dp(100)
        gap = dp(12)
        usable = available_width - dp(24)
        cols = max(2, int(usable // (card_w + gap)))
        side = max(dp(4), (usable - cols * card_w - (cols - 1) * gap) / 2)
        grid = GridLayout(cols=cols, spacing=gap, size_hint_y=None,
                          padding=[side, dp(8), side, dp(8)])
        grid.bind(minimum_height=grid.setter('height'))
        return grid
 
    def build_controls(self):
        send = self.send_key_async
        DARK = (0.25, 0.26, 0.32, 1)
        box = BoxLayout(orientation='vertical', spacing=dp(10))
 
        # Ligne du haut : PWR a gauche, MUTE a droite
        top = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(52))
        top.add_widget(KeyButton("PWR", (0.85, 0.15, 0.15, 1), 26, send))
        top.add_widget(Widget())
        top.add_widget(KeyButton("MUTE", DARK, 164, send))
        box.add_widget(top)
 
        # Grande croix ronde au centre
        box.add_widget(DPad(send))
 
        # RET / HOME / MENU
        nav = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(52))
        nav.add_widget(KeyButton("RET", DARK, 4, send))
        nav.add_widget(KeyButton("HOME", (0.2, 0.4, 0.8, 1), 3, send))
        nav.add_widget(KeyButton("MENU", DARK, 82, send))
        box.add_widget(nav)
 
        # Volume a gauche, lecture au milieu, chaines a droite
        bottom = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(112))
        vol = BoxLayout(orientation='vertical', spacing=dp(8))
        vol.add_widget(KeyButton("VOL +", DARK, 24, send))
        vol.add_widget(KeyButton("VOL -", DARK, 25, send))
        mid = BoxLayout(orientation='vertical', spacing=dp(8))
        mid.add_widget(KeyButton("PLAY", DARK, 85, send))
        mid.add_widget(KeyButton("STOP", DARK, 86, send))
        ch = BoxLayout(orientation='vertical', spacing=dp(8))
        ch.add_widget(KeyButton("CH +", DARK, 166, send))
        ch.add_widget(KeyButton("CH -", DARK, 167, send))
        bottom.add_widget(vol)
        bottom.add_widget(mid)
        bottom.add_widget(ch)
        box.add_widget(bottom)
        return box
 
    def get_signer(self):
        key_path = os.path.join(self.user_data_dir, "tvremote_adb_key")
        bundled = os.path.join(BASE_DIR, "assets", "adbkey.txt")
        bundled_pub = os.path.join(BASE_DIR, "assets", "adbkey.pub.txt")
        if not os.path.exists(key_path) and os.path.exists(bundled):
            shutil.copyfile(bundled, key_path)
            if os.path.exists(bundled_pub):
                shutil.copyfile(bundled_pub, key_path + ".pub")
        if not os.path.exists(key_path):
            from adb_shell.auth.keygen import keygen
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
