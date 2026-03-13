# Utility functions for UI behavior.

def center_window(window, width, height):
    """Center a window on the screen with a fixed size."""
    width = int(width)
    height = int(height)
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = max((screen_width - width) // 2, 0)
    y = max((screen_height - height) // 2, 0)
    window.geometry(f"{width}x{height}+{x}+{y}")
