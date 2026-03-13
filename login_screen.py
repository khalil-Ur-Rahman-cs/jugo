import os
import tkinter as tk

import customtkinter as ctk
from tkinter import font as tkfont, messagebox
from PIL import Image, ImageDraw, ImageTk

from database import db


class LoginWindow:
    def __init__(self):
        self.root = ctk.CTk()
        self.window = self.root
        self.root.title("JUGO SWAT - Login")
        self.root.geometry("500x600")
        self.root.minsize(500, 600)
        self.root.resizable(True, True)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 600) // 2
        self.root.geometry(f"500x600+{x}+{y}")

        self.card_width = 380
        self.card_height = 520
        self.card_corner_radius = 40
        self.background_photo = None
        self.card_photo = None
        self.title_logo_photo = None
        self.form_watermark_source = None
        self.background_image_source = None
        self._resize_job = None
        self.brand_logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo1.png")

        self.setup_background()

        container = ctk.CTkFrame(
            self.root,
            width=self.card_width,
            height=self.card_height,
            corner_radius=self.card_corner_radius,
            fg_color="transparent",
            border_width=0,
        )
        container.place(relx=0.5, rely=0.5, anchor="center")
        container.pack_propagate(False)
        self.container = container

        title_frame = ctk.CTkFrame(
            container,
            fg_color="transparent",
            corner_radius=self.card_corner_radius,
        )
        title_frame.pack(pady=(40, 10))
        self.title_frame = title_frame

        self.title_logo_label = ctk.CTkLabel(title_frame, text="")
        self.title_logo_label.pack(side="left", padx=(0, 10))

        # --- Color Section ---
        self.text_container = ctk.CTkFrame(title_frame, fg_color="transparent")
        self.text_container.pack(side="left")

        # "JUGO" - Pink/Magenta Color
        self.jugo_label = ctk.CTkLabel(
            self.text_container,
            text="JUGO ",
            font=ctk.CTkFont(size=27, weight="bold"),
            text_color="#D63366"  
        )
        self.jugo_label.pack(side="left")

        # "SWAT" - Orange Color
        self.swat_label = ctk.CTkLabel(
            self.text_container,
            text="SWAT",
            font=ctk.CTkFont(size=27, weight="bold"),
            text_color="#F58220"   
        )
        self.swat_label.pack(side="left")

        subtitle = ctk.CTkLabel(
            container,
            text="Management System",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        subtitle.pack(pady=(0, 40))

        ctk.CTkLabel(
            container,
            text="Username",
            font=ctk.CTkFont(size=14),
        ).pack(anchor="w", padx=40)

        self.username_entry = ctk.CTkEntry(
            container,
            placeholder_text="Enter username",
            width=320,
            height=40,
            font=ctk.CTkFont(size=14),
        )
        self.username_entry.pack(pady=(5, 20))
        self.username_entry.insert(0, "admin")

        ctk.CTkLabel(
            container,
            text="Password",
            font=ctk.CTkFont(size=14),
        ).pack(anchor="w", padx=40)

        self.password_entry = ctk.CTkEntry(
            container,
            placeholder_text="Enter password",
            show="\u2022",
            width=320,
            height=40,
            font=ctk.CTkFont(size=14),
        )
        self.password_entry.pack(pady=(5, 30))

        login_button = ctk.CTkButton(
            container,
            text="LOGIN",
            command=self.login,
            width=320,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            fg_color="#2ECC71",
            hover_color="#27AE60",
            text_color="#E4E4E4",
        )
        login_button.pack(pady=10)

        hint = ctk.CTkLabel(
            container,
            text="Default: admin / admin123",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        hint.pack(pady=(20, 10))

        footer = ctk.CTkLabel(
            container,
            text="© 2025 JUGO SWAT - Swat, Pakistan",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        footer.pack(side="bottom", pady=20)

        self.password_entry.bind("<Return>", lambda e: self.login())
        self.root.bind("<Configure>", self.on_window_resize)
        self.root.after(0, self.load_title_logo)
        self.root.after(0, self.maximize_window)

    def setup_background(self):
        image_path = os.path.join(os.path.dirname(__file__), "assets", "jugo.jpeg")

        self.background_label = tk.Label(self.root, bd=0, highlightthickness=0)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.background_label.lower()

        self.card_bg_label = tk.Label(self.root, bd=0, highlightthickness=0)
        self.card_bg_label.place(relx=0.5, rely=0.5, anchor="center")

        try:
            self.background_image_source = Image.open(image_path).convert("RGB")
        except Exception:
            self.root.configure(fg_color="#EAF6EA")
            self.background_image_source = None

        try:
            self.form_watermark_source = self.load_cropped_brand_logo()
        except Exception:
            self.form_watermark_source = None

    def on_window_resize(self, event):
        if event.widget is not self.root:
            return

        if self._resize_job is not None:
            self.root.after_cancel(self._resize_job)

        self._resize_job = self.root.after(30, self.refresh_background)

    def maximize_window(self):
        self.root.update_idletasks()
        windowing_system = self.root.tk.call("tk", "windowingsystem")

        try:
            if windowing_system == "win32":
                self.root.state("zoomed")
            else:
                self.root.attributes("-zoomed", True)
        except tk.TclError:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        self.refresh_background()

    def refresh_background(self):
        self._resize_job = None

        window_width = max(self.root.winfo_width(), 1)
        window_height = max(self.root.winfo_height(), 1)

        if self.background_image_source is None:
            fallback_card = Image.new("RGB", (self.card_width, self.card_height), (250, 250, 250))
            self.card_photo = ImageTk.PhotoImage(fallback_card)
            self.card_bg_label.configure(image=self.card_photo)
            self.card_bg_label.image = self.card_photo
            self.container.lift()
            return

        cover_image = self.build_cover_image(self.background_image_source, window_width, window_height)
        self.background_photo = ImageTk.PhotoImage(cover_image)
        self.background_label.configure(image=self.background_photo)
        self.background_label.image = self.background_photo
        self.background_label.lower()

        card_image = self.build_card_image(cover_image)
        self.card_photo = ImageTk.PhotoImage(card_image)
        self.card_bg_label.configure(image=self.card_photo)
        self.card_bg_label.image = self.card_photo
        self.card_bg_label.place(relx=0.5, rely=0.5, anchor="center")
        self.card_bg_label.lift(self.background_label)
        self.container.lift(self.card_bg_label)

    def build_cover_image(self, image, width, height):
        image_width, image_height = image.size
        scale = max(width / image_width, height / image_height)
        resized_width = max(1, int(image_width * scale))
        resized_height = max(1, int(image_height * scale))

        resized = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
        left = max(0, (resized_width - width) // 2)
        top = max(0, (resized_height - height) // 2)
        return resized.crop((left, top, left + width, top + height))

    def build_card_image(self, background_image):
        left = max(0, (background_image.width - self.card_width) // 2)
        top = max(0, (background_image.height - self.card_height) // 2)
        base = background_image.crop(
            (left, top, left + self.card_width, top + self.card_height)
        ).convert("RGBA")

        overlay = Image.new("RGBA", (self.card_width, self.card_height), (255, 255, 255, 0))
        mask = Image.new("L", (self.card_width, self.card_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            (0, 0, self.card_width - 1, self.card_height - 1),
            radius=self.card_corner_radius,
            fill=255,
        )

        white_panel = Image.new("RGBA", (self.card_width, self.card_height), (255, 255, 255, 188))
        overlay.paste(white_panel, (0, 0), mask)
        card = Image.alpha_composite(base, overlay)

        if self.form_watermark_source is not None:
            target_width = int(self.card_width * 1.2)
            target_height = max(1, int(self.form_watermark_source.height * (target_width / self.form_watermark_source.width)))
            watermark = self.form_watermark_source.resize((target_width, target_height), Image.Resampling.LANCZOS)
            alpha_channel = watermark.getchannel("A").point(lambda value: int(value * 0.55))
            watermark.putalpha(alpha_channel)

            watermark_layer = Image.new("RGBA", (self.card_width, self.card_height), (0, 0, 0, 0))
            position_x = (self.card_width - target_width) // 2
            position_y = (self.card_height - target_height) // 2
            watermark_layer.paste(watermark, (position_x, position_y), watermark)
            card = Image.alpha_composite(card, watermark_layer)

        border = Image.new("RGBA", (self.card_width, self.card_height), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border)
        border_draw.rounded_rectangle(
            (1, 1, self.card_width - 2, self.card_height - 2),
            radius=self.card_corner_radius,
            outline=(255, 255, 255, 240),
            width=1,
        )

        return Image.alpha_composite(card, border)

    def load_cropped_brand_logo(self):
        logo_image = Image.open(self.brand_logo_path).convert("RGBA")
        alpha_channel = logo_image.getchannel("A")
        visible_bounds = alpha_channel.getbbox()

        if visible_bounds:
            logo_image = logo_image.crop(visible_bounds)

        return logo_image

    def load_title_logo(self):
        try:
            target_height = max(
                int(max(self.jugo_label.winfo_reqheight(), self.swat_label.winfo_reqheight()) * 1.08),
                tkfont.Font(size=27, weight="bold").metrics("linespace"),
            )

            logo_image = self.load_cropped_brand_logo()
            logo_width = max(1, int(logo_image.width * (target_height / logo_image.height)))
            resized_logo = logo_image.resize((logo_width, target_height), Image.Resampling.LANCZOS)

            self.title_logo_photo = ImageTk.PhotoImage(resized_logo)
            self.title_logo_label.configure(image=self.title_logo_photo)
            self.title_logo_label.image = self.title_logo_photo
        except Exception:
            self.title_logo_label.configure(text="")

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password!")
            return

        try:
            result = db.verify_login(username, password)

            if result:
                self.window.destroy()
                from dashboard import Dashboard
                dashboard = Dashboard()
                dashboard.run()
            else:
                messagebox.showerror("Error", "Invalid username or password!")
                self.password_entry.delete(0, "end")
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")
            print(f"Error: {e}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = LoginWindow()
    app.run()
