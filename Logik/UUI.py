import os, sys
import tkinter as tk

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

root = tk.Tk()

# --- ICON SETUP ---
icon_path = resource_path("data/icon.ico")
icon_path = os.path.normpath(icon_path)  # ✅ fix path slashes

if os.path.exists(icon_path):
    try:
        root.iconbitmap(icon_path)
    except Exception as e:
        print("Could not set icon:", e)
else:
    print("Icon file not found:", icon_path)

# (Optional) Taskbar icon fix
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('FoodSaver.GUI.1.0')
except Exception:
    pass

root.title("Food Saver")
root.mainloop()




# app_phone.py  —  lys, futuristisk, hamburger-menu m. ikoner + animationer
import tkinter as tk
from tkinter import ttk, messagebox
import DB_Handler as DB
import user_Login as UL

# Telefon-agtig størrelse
PHONE_W, PHONE_H = 390, 800

# Farver (lys tema)
BG       = "#f3f4f6"   # lys grå baggrund
CARD     = "#ffffff"   # kort/overflade
TEXT     = "#0f172a"   # mørk tekst
SUBTEXT  = "#334155"   # sekundær tekst
ACCENT_A = "#3b82f6"   # blå
ACCENT_B = "#06b6d4"   # cyan
DIM      = "#e5e7eb"   # divider/lys kant

def _hex_to_rgb(h): return tuple(int(h[i:i+2], 16) for i in (1,3,5))
def _rgb_to_hex(rgb): return "#%02x%02x%02x" % rgb
def _mix(c1, c2, t):
    a, b = _hex_to_rgb(c1), _hex_to_rgb(c2)
    m = (int(a[0]+(b[0]-a[0])*t), int(a[1]+(b[1]-a[1])*t), int(a[2]+(b[2]-a[2])*t))
    return _rgb_to_hex(m)

class GradientButton(tk.Canvas):
    """Knappen tegnes som en gradient på en Canvas + let hover-pulse."""
    def __init__(self, parent, text, command, w=200, h=40, r=14, from_c=ACCENT_A, to_c=ACCENT_B):
        super().__init__(parent, width=w, height=h, bg=CARD, highlightthickness=0, bd=0, cursor="hand2")
        self.cmd, self.text = command, text
        self.w, self.h, self.r = w, h, r
        self.from_c, self.to_c = from_c, to_c
        self._draw_grad()
        self.txt_id = self.create_text(w/2, h/2, text=text, fill="#ffffff", font=("Segoe UI Semibold", 10))
        self.bind("<Button-1>", lambda e: self.cmd())
        self.bind("<Enter>", self._hover_on)
        self.bind("<Leave>", self._hover_off)
        self.pulse = False

    def _draw_grad(self, lighten=0.0):
        self.delete("bg")
        steps = 40
        for i in range(steps):
            t = i/(steps-1)
            c = _mix(self.from_c, self.to_c, t)
            if lighten:
                base = _hex_to_rgb(c)
                c = _rgb_to_hex(tuple(min(255, int(v*(1+lighten))) for v in base))
            y0 = int(t*(self.h))
            self.create_rectangle(0, y0, self.w, y0+self.h/steps+1, fill=c, width=0, tags="bg")
        # pseudo- rounded: overlay hvidt hjørne-clip (enkel)
        self.create_rectangle(0,0,self.w,1, fill=self.from_c, width=0, tags="bg")

    def _hover_on(self, *_):
        self._draw_grad(lighten=0.08)

    def _hover_off(self, *_):
        self._draw_grad()

class MenuItem(tk.Frame):
    """En let ‘row’ med ikon (Canvas) + label – uden emojis."""
    def __init__(self, parent, text, icon, command):
        super().__init__(parent, bg=CARD)
        self.cmd = command
        self.configure(cursor="hand2", highlightthickness=1, highlightbackground=DIM)
        self.icon = tk.Canvas(self, width=22, height=22, bg=CARD, highlightthickness=0)
        self.icon.grid(row=0, column=0, padx=10, pady=10)
        self._draw_icon(self.icon, icon)
        self.lbl = tk.Label(self, text=text, bg=CARD, fg=TEXT, font=("Segoe UI", 10, "bold"))
        self.lbl.grid(row=0, column=1, sticky="w", padx=(2,10))
        self.grid_columnconfigure(1, weight=1)
        self.bind("<Button-1>", lambda e: self.cmd())
        self.icon.bind("<Button-1>", lambda e: self.cmd())
        self.lbl.bind("<Button-1>", lambda e: self.cmd())
        self.bind("<Enter>", self._hover)
        self.bind("<Leave>", self._unhover)

    def _hover(self, *_):
        self.configure(highlightbackground=ACCENT_A)

    def _unhover(self, *_):
        self.configure(highlightbackground=DIM)

    def _draw_icon(self, c: tk.Canvas, name: str):
        # alle ikoner tegnes med streger/former – ingen emojis
        if name == "home":
            c.create_polygon(3,12,11,4,19,12,19,20,13,20,13,14,9,14,9,20,3,20,
                             outline=ACCENT_A, fill="", width=2, joinstyle="round")
        elif name == "pantry":
            c.create_rectangle(4,6,18,18, outline=ACCENT_A, width=2)
            c.create_line(4,11,18,11, fill=ACCENT_A, width=2)
        elif name == "book":
            c.create_rectangle(4,5,18,19, outline=ACCENT_A, width=2)
            c.create_line(11,5,11,19, fill=ACCENT_A, width=2)
        elif name == "plus":
            c.create_line(11,5,11,19, fill=ACCENT_A, width=2)
            c.create_line(5,12,19,12, fill=ACCENT_A, width=2)
        elif name == "power":
            c.create_arc(4,4,18,18, start=45, extent=270, style="arc", outline=ACCENT_A, width=2)
            c.create_line(11,4,11,11, fill=ACCENT_A, width=2)
        elif name == "menu":
            c.create_line(3,7,19,7, fill=TEXT, width=3, capstyle="round")
            c.create_line(3,12,19,12, fill=TEXT, width=3, capstyle="round")
            c.create_line(3,17,19,17, fill=TEXT, width=3, capstyle="round")

class PhoneApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Food Saver")
        self.geometry(f"{PHONE_W}x{PHONE_H}")
        self.minsize(PHONE_W, PHONE_H)
        self.resizable(False, False)
        self.configure(bg=BG)

        self.bruger_data = None
        self._setup_style()

        # Shell
        self.shell = tk.Frame(self, bg=BG)
        self.shell.place(relx=0.5, rely=0.5, anchor="center", width=PHONE_W, height=PHONE_H)

        # Topbar
        self.topbar = tk.Frame(self.shell, bg=BG, height=56)
        self.topbar.pack(fill="x")
        self.menu_btn = tk.Canvas(self.topbar, width=36, height=36, bg=BG, highlightthickness=0, cursor="hand2")
        MenuItem(self.topbar, "", "menu", lambda: None)  # just to reuse icon lines
        # tegn hamburger på menu_btn
        MenuItem._draw_icon(MenuItem, self.menu_btn, "menu")  # hacky static call
        self.menu_btn.bind("<Button-1>", lambda e: self.toggle_menu())
        self.menu_btn.pack(side="left", padx=8, pady=10)

        self.title_lbl = tk.Label(self.topbar, text="Food Saver", fg=TEXT, bg=BG, font=("Segoe UI Semibold", 15))
        self.title_lbl.pack(side="left", padx=6)

        # Divider
        self._divider(self.shell)

        # Dropdown menu
        self.menu_panel = tk.Frame(self.shell, bg=CARD, highlightthickness=1, highlightbackground=DIM)
        self.menu_open = False
        self.menu_y = -200  # start uden for synsfelt
        self.menu_target_y = 56  # lige under topbar
        self.menu_panel.place(x=8, y=self.menu_y, width=PHONE_W-16, height=0)

        self.menu_inner = tk.Frame(self.menu_panel, bg=CARD)
        self.menu_inner.pack(fill="both", expand=True)
        self.backdrop = tk.Frame(self.shell, bg="#000000", width=PHONE_W, height=PHONE_H-56)
        self.backdrop.bind("<Button-1>", lambda e: self.hide_menu())

        # Content
        self.content = tk.Frame(self.shell, bg=BG)
        self.content.pack(fill="both", expand=True)

        # Pages
        self.pages = {}
        for Page in (LoginPage, HomePage, LagerPage, OpskrifterPage, TilfoejOpskriftPage):
            p = Page(self.content, self)
            self.pages[Page.__name__] = p
            p.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Start låst bag login
        self.show("LoginPage")

    # ---------- utils ----------
    def _divider(self, parent):
        c = tk.Canvas(parent, height=1, bg=BG, highlightthickness=0)
        c.pack(fill="x")
        c.create_line(0, 0, PHONE_W, 0, fill=DIM)

    def _setup_style(self):
        st = ttk.Style(self)
        if "clam" in st.theme_names():
            st.theme_use("clam")
        st.configure("Title.TLabel", foreground=TEXT, background=BG, font=("Segoe UI Semibold", 16))
        st.configure("Lbl.TLabel", foreground=SUBTEXT, background=BG, font=("Segoe UI", 10))
        st.configure("Card.TFrame", background=CARD)
        st.configure("Card.TLabel", foreground=TEXT, background=CARD, font=("Segoe UI", 10))
        st.configure("TEntry", fieldbackground="#ffffff")

    # ---------- menu ----------
    def build_menu(self):
        for w in self.menu_inner.winfo_children():
            w.destroy()
        items = []
        if self.bruger_data:
            items = [
                ("Hjem", "home", lambda: self.show("HomePage")),
                ("Lager", "pantry", lambda: self.show("LagerPage")),
                ("Opskrifter", "book", lambda: self.show("OpskrifterPage")),
                ("Tilføj opskrift", "plus", lambda: self.show("TilfoejOpskriftPage")),
            ]
        else:
            items = [("Login / Opret", "home", lambda: self.show("LoginPage"))]

        for text, icon, cmd in items:
            MenuItem(self.menu_inner, text, icon, lambda c=cmd: (self.hide_menu(), c())).pack(fill="x", padx=10, pady=6)

        if self.bruger_data:
            ttk.Separator(self.menu_inner, orient="horizontal").pack(fill="x", padx=10, pady=6)
            MenuItem(self.menu_inner, "Log ud", "power", self._logout_click).pack(fill="x", padx=10, pady=6)

    def toggle_menu(self):
        if self.menu_open: self.hide_menu()
        else: self.show_menu()

    def show_menu(self):
        self.build_menu()
        self.backdrop.place(x=0, y=56)
        self.backdrop.lift()
        self.menu_panel.lift()
        self.menu_open = True
        # animation: slide ned + height expand
        self.menu_y = -200
        self.menu_panel.place_configure(y=self.menu_y, height=0)
        self._animate_menu(opening=True)

    def hide_menu(self):
        if not self.menu_open: return
        self._animate_menu(opening=False)

    def _animate_menu(self, opening=True):
        if opening:
            if self.menu_y < self.menu_target_y:
                self.menu_y += 20
                h = min(220, (self.menu_y - 56) + 220)  # simple height expansion
                self.menu_panel.place_configure(y=self.menu_y, height=max(0, h))
                self.after(10, lambda: self._animate_menu(True))
            else:
                self.menu_panel.place_configure(y=self.menu_target_y)
        else:
            if self.menu_y > -200:
                self.menu_y -= 20
                h = max(0, (self.menu_y - 56) + 220)
                self.menu_panel.place_configure(y=self.menu_y, height=h)
                self.after(10, lambda: self._animate_menu(False))
            else:
                self.menu_open = False
                self.menu_panel.place_configure(height=0)
                self.menu_panel.place_forget()
                self.backdrop.place_forget()

    # ---------- app state ----------
    def show(self, name: str):
        page = self.pages[name]
        page.tkraise()
        self.title_lbl.config(text=getattr(page, "title_text", "Food Saver"))
        if hasattr(page, "on_show"):
            page.on_show()

    def after_login(self, bruger_data):
        self.bruger_data = bruger_data
        DB.lager = {k.lower(): v for k, v in bruger_data.get("lager", {}).items()}
        try:
            DB.load_opskrifter()
        except Exception as e:
            messagebox.showerror("Fejl", f"Kunne ikke indlæse opskrifter.\n{e}")
        # nulstil alle inputs ved login (så en ny bruger ikke arver felter)
        self.reset_all_inputs()
        self.hide_menu()
        self.show("HomePage")

    def autosave(self):
        if self.bruger_data:
            self.bruger_data["lager"] = DB.lager
            UL.gem_bruger(self.bruger_data)

    def _logout_click(self):
        self.autosave()
        self.bruger_data = None
        DB.lager = {}
        self.reset_all_inputs()
        self.hide_menu()
        self.show("LoginPage")

    def reset_all_inputs(self):
        # ryd loginfelter
        lp: LoginPage = self.pages["LoginPage"]
        lp.clear_inputs()
        # ryd sidefelter
        self.pages["LagerPage"].reset_inputs()
        self.pages["OpskrifterPage"].reset_inputs()
        self.pages["TilfoejOpskriftPage"].reset_inputs()


# ---------- sider ----------
class LoginPage(tk.Frame):
    title_text = "Login"
    def __init__(self, parent, app: PhoneApp):
        super().__init__(parent, bg=BG)
        self.app = app

        ttk.Label(self, text="Log ind eller opret konto", style="Title.TLabel").pack(pady=16)

        card = ttk.Frame(self, style="Card.TFrame")
        card.pack(padx=16, pady=8, fill="x")

        inner = tk.Frame(card, bg=CARD, highlightthickness=1, highlightbackground=DIM)
        inner.pack(padx=10, pady=10, fill="x")

        ttk.Label(inner, text="Brugernavn", style="Card.TLabel").pack(anchor="w", pady=(6,2))
        self.ent_user = ttk.Entry(inner)
        self.ent_user.pack(fill="x", padx=2)

        ttk.Label(inner, text="Password", style="Card.TLabel").pack(anchor="w", pady=(10,2))
        self.ent_pass = ttk.Entry(inner, show="*")
        self.ent_pass.pack(fill="x", padx=2, pady=(0,6))

        row = tk.Frame(self, bg=BG)
        row.pack(pady=12)
        GradientButton(row, "Login", self.login, w=150).pack(side="left", padx=6)
        GradientButton(row, "Opret konto", self.create, w=150).pack(side="left", padx=6)

        ttk.Label(self, text="Appen er låst, indtil du logger ind.", style="Lbl.TLabel").pack(pady=(4,0))

    def clear_inputs(self):
        self.ent_user.delete(0, "end")
        self.ent_pass.delete(0, "end")

    def on_show(self):
        # fokus i brugernavn
        self.ent_user.focus_set()

    def login(self):
        user = self.ent_user.get().strip()
        pwd = self.ent_pass.get()
        if not user or not pwd:
            messagebox.showinfo("Info", "Udfyld brugernavn og password.")
            return
        data = UL.load_bruger(user)
        if not data:
            messagebox.showerror("Fejl", "Bruger findes ikke.")
            return
        if data.get("password_hash") != UL.hash_password(pwd):
            messagebox.showerror("Fejl", "Forkert password.")
            return
        self.app.after_login(data)

    def create(self):
        user = self.ent_user.get().strip()
        pwd = self.ent_pass.get()
        if not user or not pwd:
            messagebox.showinfo("Info", "Udfyld brugernavn og password.")
            return
        if UL.load_bruger(user):
            messagebox.showerror("Fejl", "Brugernavn findes allerede.")
            return
        data = {"brugernavn": user, "password_hash": UL.hash_password(pwd), "lager": {}}
        UL.gem_bruger(data)
        messagebox.showinfo("OK", f"Konto '{user}' oprettet.")
        self.app.after_login(data)


class HomePage(tk.Frame):
    title_text = "Hjem"
    def __init__(self, parent, app: PhoneApp):
        super().__init__(parent, bg=BG)
        self.app = app
        ttk.Label(self, text="Velkommen", style="Title.TLabel").pack(pady=16)
        card = ttk.Frame(self, style="Card.TFrame")
        card.pack(padx=16, pady=8, fill="x")
        ttk.Label(card, text="Brug hamburger-menuen (☰) til at styre lager,\nfinde opskrifter eller tilføje nye.",
                  style="Card.TLabel", justify="center").pack(padx=16, pady=16)


class LagerPage(tk.Frame):
    title_text = "Lager"
    def __init__(self, parent, app: PhoneApp):
        super().__init__(parent, bg=BG)
        self.app = app

        ttk.Label(self, text="Lager", style="Title.TLabel").pack(pady=12)

        card = ttk.Frame(self, style="Card.TFrame")
        card.pack(padx=16, pady=8, fill="both", expand=True)

        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x", padx=12, pady=12)

        self.ent_ing = ttk.Entry(top)
        self.ent_ing.insert(0, "fx pasta")
        self.ent_amt = ttk.Entry(top, width=10)
        self.ent_amt.insert(0, "mængde")

        GradientButton(top, "Tilføj", self.add_item, w=110, h=36).pack(side="right")
        self.ent_amt.pack(side="right", padx=8)
        self.ent_ing.pack(side="right", padx=8, fill="x", expand=True)

        list_wrap = tk.Frame(card, bg=CARD)
        list_wrap.pack(fill="both", expand=True, padx=12, pady=(0,12))

        self.listbox = tk.Listbox(list_wrap, bg="#ffffff", fg=TEXT, bd=0,
                                  highlightthickness=1, highlightbackground=DIM,
                                  activestyle="none", selectbackground=ACCENT_A, selectforeground="#ffffff")
        self.listbox.pack(fill="both", expand=True, padx=8, pady=8)

        bottom = tk.Frame(card, bg=CARD)
        bottom.pack(fill="x", padx=12, pady=(0,12))
        GradientButton(bottom, "Slet valgt", self.del_selected, w=130, h=36).pack(side="left")
        GradientButton(bottom, "Opdater", self.refresh, w=110, h=36).pack(side="right")

    def reset_inputs(self):
        self.ent_ing.delete(0, "end"); self.ent_ing.insert(0, "fx pasta")
        self.ent_amt.delete(0, "end"); self.ent_amt.insert(0, "mængde")
        self.listbox.delete(0, "end")

    def on_show(self):
        self.refresh()

    def refresh(self):
        self.listbox.delete(0, "end")
        if not DB.lager:
            self.listbox.insert("end", "Lager er tomt.")
            return
        for ing, amt in sorted(DB.lager.items()):
            self.listbox.insert("end", f"{ing}: {amt}")

    def add_item(self):
        navn = self.ent_ing.get().strip().lower()
        try:
            amt = float(self.ent_amt.get().strip())
        except:
            messagebox.showerror("Fejl", "Mængde skal være et tal.")
            return
        if not navn:
            messagebox.showinfo("Info", "Skriv et navn.")
            return
        DB.tilføj_ingredient(navn, amt, self.app.bruger_data)
        self.app.autosave()
        self.refresh()

    def del_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Vælg en vare.")
            return
        line = self.listbox.get(sel[0])
        if ":" not in line: return
        navn = line.split(":", 1)[0].strip()
        DB.slet_ingredient(navn, self.app.bruger_data)
        self.app.autosave()
        self.refresh()


class OpskrifterPage(tk.Frame):
    title_text = "Opskrifter"
    def __init__(self, parent, app: PhoneApp):
        super().__init__(parent, bg=BG)
        self.app = app

        ttk.Label(self, text="Opskrifter", style="Title.TLabel").pack(pady=12)

        card = ttk.Frame(self, style="Card.TFrame")
        card.pack(padx=16, pady=8, fill="both", expand=True)

        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x", padx=12, pady=12)
        ttk.Label(top, text="Antal personer:", style="Card.TLabel").pack(side="left")
        self.ent_personer = ttk.Entry(top, width=6)
        self.ent_personer.insert(0, "2")
        self.ent_personer.pack(side="left", padx=8)
        GradientButton(top, "Find", self.find_ops, w=90, h=36).pack(side="left", padx=8)

        self.txt = tk.Text(card, bg="#ffffff", fg=TEXT, bd=0, highlightthickness=1,
                           highlightbackground=DIM, wrap="word")
        self.txt.pack(fill="both", expand=True, padx=12, pady=(0,12))

    def reset_inputs(self):
        self.ent_personer.delete(0, "end"); self.ent_personer.insert(0, "2")
        self.txt.delete("1.0", "end")

    def on_show(self):
        if not self.txt.get("1.0","end").strip():
            self.txt.insert("end", "Tryk Find for at se hvad du kan lave.")

    def find_ops(self):
        try:
            personer = int(self.ent_personer.get().strip())
        except:
            messagebox.showerror("Fejl", "Antal personer skal være et tal.")
            return

        try:
            DB.load_opskrifter()
        except Exception as e:
            messagebox.showerror("Fejl", f"Kunne ikke indlæse opskrifter.\n{e}")
            return

        self.txt.delete("1.0", "end")
        if not DB.lager:
            self.txt.insert("end", "Ingen ingredienser i lageret.\n")
            return

        found = False
        self.txt.insert("end", f"Opskrifter til {personer} person(er):\n\n")
        for navn, data in DB.opskrifter.items():
            ingreds = data.get("ingredienser", {})
            mangler = {}
            for ing, m in ingreds.items():
                try:
                    need = float(m) * float(personer)
                    have = float(DB.lager.get(ing, 0))
                except ValueError:
                    continue  # spring over hvis noget ikke kan konverteres til tal

                if have < need:
                    mangler[ing] = round(need - have, 2)
            if not mangler:
                self.txt.insert("end", f"• {navn}  —  klar\n")
                found = True
            elif 0 < len(mangler) < len(ingreds):
                parts = ", ".join(f"{k}: {v}" for k, v in mangler.items())
                self.txt.insert("end", f"• {navn}  —  mangler: {parts}\n")
                found = True


        if not found:
            self.txt.insert("end", "Ingen opskrifter kan laves med det lager, du har.\n")


class TilfoejOpskriftPage(tk.Frame):
    title_text = "Tilføj opskrift"
    def __init__(self, parent, app: PhoneApp):
        super().__init__(parent, bg=BG)
        self.app = app

        ttk.Label(self, text="Tilføj opskrift", style="Title.TLabel").pack(pady=12)

        card = ttk.Frame(self, style="Card.TFrame")
        card.pack(padx=16, pady=8, fill="both", expand=True)

        fields = tk.Frame(card, bg=CARD)
        fields.pack(fill="x", padx=12, pady=12)

        ttk.Label(fields, text="Navn:", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Label(fields, text="Ingredienser (pasta:100, tomat:2):", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(fields, text="Tid (min):", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Label(fields, text="Fremgangsmåde:", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=4)

        self.ent_navn = ttk.Entry(fields)
        self.ent_ing  = ttk.Entry(fields)
        self.ent_tid  = ttk.Entry(fields)
        self.txt_step = tk.Text(fields, height=8, bg="#ffffff", fg=TEXT, bd=0, highlightthickness=1, highlightbackground=DIM)

        self.ent_navn.grid(row=0, column=1, sticky="ew", padx=8)
        self.ent_ing.grid(row=1, column=1, sticky="ew", padx=8)
        self.ent_tid.grid(row=2, column=1, sticky="ew", padx=8)
        self.txt_step.grid(row=3, column=1, sticky="nsew", padx=8, pady=(4,0))
        fields.grid_columnconfigure(1, weight=1)

        GradientButton(card, "Gem opskrift", self.save_recipe, w=140, h=36).pack(padx=12, pady=12, anchor="e")

    def reset_inputs(self):
        self.ent_navn.delete(0, "end")
        self.ent_ing.delete(0, "end")
        self.ent_tid.delete(0, "end")
        self.txt_step.delete("1.0", "end")

    def save_recipe(self):
        navn = self.ent_navn.get().strip()
        ing_line = self.ent_ing.get().strip()
        tid = self.ent_tid.get().strip()
        steps = self.txt_step.get("1.0", "end").strip()

        if not navn or not ing_line:
            messagebox.showinfo("Info", "Udfyld mindst navn og ingredienser.")
            return
        try:
            ingreds = {}
            for part in ing_line.split(","):
                if not part.strip(): continue
                key, val = part.split(":")
                ingreds[key.strip().lower()] = float(val.strip())
        except Exception:
            messagebox.showerror("Fejl", "Ingredienser skal være på formen pasta:100, tomat:2")
            return

        data = {"ingredienser": ingreds, "tid": int(tid) if tid.isdigit() else tid, "opskrift": steps}
        try:
            import yaml, os
            filnavn = navn.replace(" ", "_") + ".yml"
            filsti = os.path.join(DB.opskrift_mappe, filnavn)
            with open(filsti, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True)
            DB.load_opskrifter()
            messagebox.showinfo("OK", f"Opskrift '{navn}' gemt.")
            self.reset_inputs()
        except Exception as e:
            messagebox.showerror("Fejl", f"Kunne ikke gemme opskrift.\n{e}")


if __name__ == "__main__":
    app = PhoneApp()
    app.mainloop()
