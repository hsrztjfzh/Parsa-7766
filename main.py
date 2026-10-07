import threading
import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.core.window import Window

Window.clearcolor = (0.035, 0.035, 0.035, 1)
DEFAULT_API_URL = "http://10.0.2.2:8000"  # Real phone: http://10.37.218.59:8000

class LoginScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs); self.app_ref = app_ref
        root = BoxLayout(orientation="vertical", padding=dp(28), spacing=dp(14))
        root.add_widget(Label(text="[b]VGR STORE[/b]", markup=True, font_size="34sp", color=(.9,.03,.15,1), size_hint_y=None, height=dp(55)))
        root.add_widget(Label(text="ADMIN PANEL", font_size="15sp", color=(.65,.65,.65,1), size_hint_y=None, height=dp(28)))
        self.url = TextInput(text=DEFAULT_API_URL, hint_text="API URL", multiline=False, size_hint_y=None, height=dp(50), background_color=(.09,.09,.09,1), foreground_color=(1,1,1,1))
        self.user = TextInput(hint_text="Username", multiline=False, size_hint_y=None, height=dp(50), background_color=(.09,.09,.09,1), foreground_color=(1,1,1,1))
        self.pw = TextInput(hint_text="Password", password=True, multiline=False, size_hint_y=None, height=dp(50), background_color=(.09,.09,.09,1), foreground_color=(1,1,1,1))
        for w in (self.url,self.user,self.pw): root.add_widget(w)
        self.btn = Button(text="LOGIN", size_hint_y=None, height=dp(52), background_normal="", background_color=(.85,.02,.12,1)); self.btn.bind(on_press=self.login); root.add_widget(self.btn)
        self.status = Label(text="", font_size="13sp", color=(.75,.75,.75,1)); root.add_widget(self.status); root.add_widget(Label())
        self.add_widget(root)
    def login(self, *_):
        url,u,p=self.url.text.strip().rstrip("/"),self.user.text.strip(),self.pw.text
        if not url or not u or not p: self.status.text="Please fill in all fields."; return
        self.btn.disabled=True; self.status.text="Connecting..."
        threading.Thread(target=self._req,args=(url,u,p),daemon=True).start()
    def _req(self,url,u,p):
        try:
            r=requests.post(url+"/auth/login",json={"username":u,"password":p},timeout=8); d=r.json()
            if r.ok and d.get("token"): Clock.schedule_once(lambda dt:self._ok(url,d["token"]),0)
            else: Clock.schedule_once(lambda dt:self._fail(str(d.get("detail","Login failed."))),0)
        except Exception as e: Clock.schedule_once(lambda dt:self._fail("Connection error: "+str(e)),0)
    def _ok(self,url,token): self.app_ref.api_url=url; self.app_ref.token=token; self.btn.disabled=False; self.manager.current="dashboard"; self.app_ref.dashboard.load()
    def _fail(self,msg): self.status.text=msg; self.btn.disabled=False

class DashboardScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs); self.app_ref=app_ref
        root=BoxLayout(orientation="vertical",padding=dp(18),spacing=dp(10))
        head=BoxLayout(size_hint_y=None,height=dp(55)); head.add_widget(Label(text="[b]VGR STORE ADMIN[/b]",markup=True,font_size="23sp",color=(1,1,1,1)))
        out=Button(text="LOGOUT",size_hint_x=None,width=dp(95),background_normal="",background_color=(.16,.16,.16,1)); out.bind(on_press=self.logout); head.add_widget(out); root.add_widget(head)
        self.status=Label(text="Dashboard",size_hint_y=None,height=dp(26),color=(.65,.65,.65,1)); root.add_widget(self.status)
        cards=GridLayout(cols=2,spacing=dp(10),size_hint_y=None,height=dp(250)); self.values={}
        for key,title in [("users","USERS"),("active_ads","ACTIVE ADS"),("pending_ads","PENDING ADS"),("active_subscriptions","ACTIVE SUBSCRIPTIONS")]:
            box=BoxLayout(orientation="vertical",padding=dp(10)); box.add_widget(Label(text=title,font_size="13sp",color=(.62,.62,.62,1))); v=Label(text="—",font_size="28sp",color=(.9,.03,.15,1)); box.add_widget(v); self.values[key]=v; cards.add_widget(box)
        root.add_widget(cards)
        refresh=Button(text="REFRESH DASHBOARD",size_hint_y=None,height=dp(52),background_normal="",background_color=(.85,.02,.12,1)); refresh.bind(on_press=lambda *_:self.load()); root.add_widget(refresh)
        self.message=Label(text="",font_size="13sp",color=(.7,.7,.7,1)); root.add_widget(self.message); self.add_widget(root)
    def load(self):
        if not self.app_ref.token:return
        self.status.text="Loading..."; threading.Thread(target=self._req,daemon=True).start()
    def _req(self):
        try:
            r=requests.get(self.app_ref.api_url+"/dashboard",headers={"Authorization":"Bearer "+self.app_ref.token},timeout=8); d=r.json()
            if r.ok: Clock.schedule_once(lambda dt:self._update(d),0)
            else: Clock.schedule_once(lambda dt:self._fail("Access denied or session expired."),0)
        except Exception as e: Clock.schedule_once(lambda dt:self._fail("Connection error: "+str(e)),0)
    def _update(self,d):
        for k,v in self.values.items():v.text=str(d.get(k,0))
        self.status.text="Dashboard • Connected"; self.message.text="Data updated successfully."
    def _fail(self,m):self.message.text=m;self.status.text="Dashboard"
    def logout(self,*_):self.app_ref.token=None;self.manager.current="login"

class VGRAdminApp(App):
    def build(self):
        self.api_url=DEFAULT_API_URL; self.token=None; sm=ScreenManager(); sm.add_widget(LoginScreen(self,name="login")); self.dashboard=DashboardScreen(self,name="dashboard"); sm.add_widget(self.dashboard); return sm

if __name__=="__main__": VGRAdminApp().run()
