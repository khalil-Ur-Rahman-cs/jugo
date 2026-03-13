import customtkinter as ctk
from login_screen import LoginWindow
from PIL import Image, ImageTk
import os
import sys

# CustomTkinter settings
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# Assets ka path set karna (EXE ke liye bhi kaam karega)
def get_asset_path(filename):
    if hasattr(sys, '_MEIPASS'):
        # EXE run ho raha hai
        return os.path.join(sys._MEIPASS, "assets", filename)
    else:
        # Normal Python run ho raha hai
        return os.path.join("assets", filename)

def main():
    app = LoginWindow()
    window = getattr(app, "window", None) or getattr(app, "root", None) or app
    
    # ========== WINDOW TITLE & ICON ==========
    
    # 1. Window Title (Title bar mein dikhega)
    window.title("SM ENTERPRISES")
    
    # 2. Window Icon (Taskbar + Title bar ke liye)
    try:
        icon_path = get_asset_path("sm_logo.ico")
        window.iconbitmap(icon_path)
    except Exception as e:
        print(f"Icon load nahi hua: {e}")
    
    # 3. Window Icon Alternative (agar upar wala fail ho)
    try:
        icon_path = get_asset_path("sm_logo.ico")
        window.iconphoto(False, ImageTk.PhotoImage(file=icon_path))
    except:
        pass
    
    # ==========================================
    
    app.run()

if __name__ == "__main__":
    main()