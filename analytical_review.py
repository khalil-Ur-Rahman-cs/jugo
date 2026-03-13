import customtkinter as ctk
from datetime import datetime, timedelta

from database import db


class AnalyticsReview:
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self._range_days = 30
        self._grouping = "day"
        self._show_volume = True
        self._chart_container = None
        self._chart_canvas = None
        self.setup_ui()

    def setup_ui(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        container = ctk.CTkFrame(self.parent)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        self.setup_header(container)
        self.setup_candlestick_chart(container, volume=True)

    def setup_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(
            header,
            text="Analytics Review",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left", padx=5)

        buttons_frame = ctk.CTkFrame(header, fg_color="transparent")
        buttons_frame.pack(side="right")

        filters = [
            ("1D", 1, "day"),
            ("1W", 7, "day"),
            ("1M", 30, "day"),
            ("3M", 90, "week"),
            ("6M", 180, "week"),
            ("1Y", 365, "month"),
            ("ALL", None, "month"),
        ]

        for label, days, grouping in filters:
            ctk.CTkButton(
                buttons_frame,
                text=label,
                width=55,
                height=28,
                fg_color="#1f2a33",
                hover_color="#263340",
                command=lambda d=days, g=grouping: self.update_chart(d, g),
            ).pack(side="left", padx=4)

    def setup_candlestick_chart(self, parent, volume=True):
        self._show_volume = volume

        chart_frame = ctk.CTkFrame(parent, corner_radius=12)
        chart_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        self._chart_container = ctk.CTkFrame(chart_frame, fg_color="transparent")
        self._chart_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.render_candlestick_chart()

    def update_chart(self, limit_days, grouping=None):
        self._range_days = limit_days
        if grouping:
            self._grouping = grouping
        self.render_candlestick_chart()

    def render_candlestick_chart(self):
        if not self._chart_container:
            return

        for widget in self._chart_container.winfo_children():
            widget.destroy()

        try:
            data = self.get_candlestick_data(limit_days=self._range_days, grouping=self._grouping)
            if not data:
                ctk.CTkLabel(
                    self._chart_container,
                    text="No sales data to render chart.",
                    text_color="gray",
                ).pack(pady=20)
                return

            fig = self.build_candlestick_figure(data, volume=self._show_volume, figsize=(14, 8))
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            self._chart_canvas = FigureCanvasTkAgg(fig, master=self._chart_container)
            self._chart_canvas.draw()
            self._chart_canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as exc:
            ctk.CTkLabel(
                self._chart_container,
                text=f"Chart failed to load: {exc}",
                text_color="gray",
            ).pack(pady=20)

    def get_candlestick_data(self, limit_days=30, grouping="day"):
        """Build OHLCV data from sales totals per period."""
        try:
            params = []
            date_clause = ""
            if limit_days is not None:
                start_date = (datetime.now() - timedelta(days=limit_days - 1)).date().isoformat()
                date_clause = "AND DATE(created_at) >= ?"
                params.append(start_date)

            db.cursor.execute(
                """
                SELECT created_at, grand_total
                FROM sales
                WHERE grand_total > 0
                """ + date_clause + """
                ORDER BY created_at ASC
                """,
                params
            )
            rows = db.cursor.fetchall()
        except Exception:
            return []

        def parse_dt(value):
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value)
                except ValueError:
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                        try:
                            return datetime.strptime(value, fmt)
                        except ValueError:
                            continue
            return None

        def make_key(dt_value):
            if grouping == "week":
                iso = dt_value.isocalendar()
                return ("week", iso[0], iso[1])
            if grouping == "month":
                return ("month", dt_value.year, dt_value.month)
            return ("day", dt_value.date())

        def label_for(key):
            if key[0] == "week":
                return f"{key[1]}-W{key[2]:02d}"
            if key[0] == "month":
                return f"{key[1]}-{key[2]:02d}"
            return key[1].isoformat()

        data = []
        current_key = None
        open_price = close_price = high_price = low_price = None
        volume = 0

        for created_at, total in rows:
            dt_value = parse_dt(created_at)
            if not dt_value:
                continue
            amount = float(total or 0)
            key = make_key(dt_value)

            if current_key is None:
                current_key = key
                open_price = close_price = high_price = low_price = amount
                volume = 1
                continue

            if key != current_key:
                data.append((
                    label_for(current_key),
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume,
                ))
                current_key = key
                open_price = close_price = high_price = low_price = amount
                volume = 1
                continue

            close_price = amount
            high_price = max(high_price, amount)
            low_price = min(low_price, amount)
            volume += 1

        if current_key is not None:
            data.append((
                label_for(current_key),
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
            ))

        return data

    def build_candlestick_figure(self, data, volume=True, figsize=(14, 8)):
        """Render a Binance-style candlestick chart using matplotlib."""
        import sys
        import matplotlib
        if "matplotlib.pyplot" not in sys.modules:
            try:
                matplotlib.use("TkAgg")
            except Exception:
                pass
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle

        labels = [row[0] for row in data]
        ohlc = [(row[1], row[2], row[3], row[4]) for row in data]
        volumes = [row[5] for row in data]

        if volume:
            fig, (ax_price, ax_vol) = plt.subplots(
                2,
                1,
                figsize=figsize,
                dpi=100,
                sharex=True,
                gridspec_kw={"height_ratios": [3, 1]},
            )
        else:
            fig, ax_price = plt.subplots(figsize=figsize, dpi=100)
            ax_vol = None

        fig.patch.set_facecolor("#0b0f14")
        ax_price.set_facecolor("#0b0f14")
        if ax_vol:
            ax_vol.set_facecolor("#0b0f14")

        width = 0.6
        colors = []
        for i, (open_price, high_price, low_price, close_price) in enumerate(ohlc):
            color = "#2ECC71" if close_price >= open_price else "#E74C3C"
            colors.append(color)
            ax_price.vlines(i, low_price, high_price, color=color, linewidth=1.2)
            body_low = min(open_price, close_price)
            body_height = abs(close_price - open_price)
            min_body = max(0.5, (high_price - low_price) * 0.02)
            ax_price.add_patch(
                Rectangle(
                    (i - width / 2, body_low),
                    width,
                    body_height if body_height > 0 else min_body,
                    facecolor=color,
                    edgecolor=color,
                    linewidth=0.8,
                )
            )

        ax_price.grid(color="#1f2a33", linestyle="-", linewidth=0.6, alpha=0.6)
        ax_price.tick_params(colors="#9aa4ad", labelsize=8)
        for spine in ax_price.spines.values():
            spine.set_color("#1f2a33")

        if ax_vol:
            ax_vol.bar(range(len(volumes)), volumes, color=colors, width=0.6, alpha=0.8)
            ax_vol.grid(color="#1f2a33", linestyle="-", linewidth=0.6, alpha=0.4)
            ax_vol.tick_params(colors="#9aa4ad", labelsize=8)
            for spine in ax_vol.spines.values():
                spine.set_color("#1f2a33")

        step = max(1, len(labels) // 6)
        ticks = list(range(0, len(labels), step))
        tick_labels = [labels[i] for i in ticks]

        if ax_vol:
            ax_vol.set_xticks(ticks)
            ax_vol.set_xticklabels(tick_labels, rotation=0)
            ax_price.tick_params(labelbottom=False)
            ax_vol.set_ylabel("Volume", color="#9aa4ad", fontsize=9)
        else:
            ax_price.set_xticks(ticks)
            ax_price.set_xticklabels(tick_labels, rotation=0)

        ax_price.set_title("Sales Candlestick", color="#e5e7eb", fontsize=10, pad=10)
        ax_price.set_ylabel("Amount (Rs.)", color="#9aa4ad", fontsize=9)
        ax_price.set_xlim(-1, len(labels))

        fig.tight_layout()
        return fig
