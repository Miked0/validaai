"""
Design System Components - Reusable UI components built on design tokens.
Each component encapsulates token-based styling and consistent behavior.
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List, Any
from dataclasses import dataclass
from enum import Enum

# Import token constants
try:
    from design.tokens import (
        COLOR_BG_PRIMARY, COLOR_BG_CARD, COLOR_BG_INPUT, COLOR_BG_HOVER,
        COLOR_FG_PRIMARY, COLOR_FG_MUTED, COLOR_FG_DISABLED,
        COLOR_ACCENT_PRIMARY, COLOR_ACCENT_HOVER, COLOR_ACCENT_PRESS,
        COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_INFO,
        COLOR_BORDER_DEFAULT, COLOR_BORDER_FOCUS, COLOR_BORDER_ERROR,
        SPACING_NONE, SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL, SPACING_2XL,
        FONT_FAMILY_PRIMARY, FONT_FAMILY_MONO,
        FONT_WEIGHT_NORMAL, FONT_WEIGHT_MEDIUM, FONT_WEIGHT_SEMIBOLD, FONT_WEIGHT_BOLD,
        FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_LG, FONT_SIZE_XL, FONT_SIZE_2XL,
        LINE_HEIGHT_NORMAL,
        RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL, RADIUS_FULL,
        SHADOW_SM, SHADOW_MD, SHADOW_LG,
        TRANSITION_FAST, TRANSITION_NORMAL
    )
except ImportError:
    # Fallback values if tokens not available
    COLOR_BG_PRIMARY = "#2C2F33"
    COLOR_BG_CARD = "#23272A"
    COLOR_BG_INPUT = "#1E1F22"
    COLOR_BG_HOVER = "#2C2F33"
    COLOR_FG_PRIMARY = "#FFFFFF"
    COLOR_FG_MUTED = "#CCCCCC"
    COLOR_FG_DISABLED = "#888888"
    COLOR_ACCENT_PRIMARY = "#5865F2"
    COLOR_ACCENT_HOVER = "#4752C4"
    COLOR_ACCENT_PRESS = "#3C45A5"
    COLOR_SUCCESS = "#3BA55C"
    COLOR_ERROR = "#ED4245"
    COLOR_WARNING = "#FAA61A"
    COLOR_INFO = "#5865F2"
    COLOR_BORDER_DEFAULT = "#40444B"
    COLOR_BORDER_FOCUS = "#5865F2"
    COLOR_BORDER_ERROR = "#ED4245"
    SPACING_NONE = 0
    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 12
    SPACING_LG = 16
    SPACING_XL = 24
    SPACING_2XL = 32
    FONT_FAMILY_PRIMARY = "Segoe UI"
    FONT_FAMILY_MONO = "Consolas"
    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_MEDIUM = 500
    FONT_WEIGHT_SEMIBOLD = 600
    FONT_WEIGHT_BOLD = 700
    FONT_SIZE_XS = 10
    FONT_SIZE_SM = 11
    FONT_SIZE_BASE = 12
    FONT_SIZE_LG = 14
    FONT_SIZE_XL = 18
    FONT_SIZE_2XL = 22
    LINE_HEIGHT_NORMAL = 1.5
    RADIUS_SM = 4
    RADIUS_MD = 6
    RADIUS_LG = 8
    RADIUS_XL = 12
    RADIUS_FULL = 9999
    SHADOW_SM = "0 1px 2px rgba(0,0,0,0.3)"
    SHADOW_MD = "0 4px 8px rgba(0,0,0,0.4)"
    SHADOW_LG = "0 8px 16px rgba(0,0,0,0.5)"
    TRANSITION_FAST = "150ms"
    TRANSITION_NORMAL = "200ms"


# ════════════════════════════════════════════════════════════
# Style Configuration Helpers
# ════════════════════════════════════════════════════════════

def configure_component_styles(style: ttk.Style) -> None:
    """Configure ttk styles for all design system components."""
    # Card
    style.configure("DS.Card.TFrame", background=COLOR_BG_CARD)
    style.configure("DS.Card.TLabelframe", background=COLOR_BG_CARD, foreground=COLOR_FG_PRIMARY,
                    borderwidth=1, relief="solid")
    style.configure("DS.Card.TLabelframe.Label", background=COLOR_BG_CARD, 
                    foreground=COLOR_ACCENT_PRIMARY, font=(FONT_FAMILY_PRIMARY, FONT_SIZE_BASE, "bold"))
    
    # Field Row
    style.configure("DS.FieldRow.TFrame", background=COLOR_BG_PRIMARY)
    
    # Input
    style.configure("DS.TEntry",
        fieldbackground=COLOR_BG_INPUT,
        foreground=COLOR_FG_PRIMARY,
        bordercolor=COLOR_BORDER_DEFAULT,
        lightcolor=COLOR_BORDER_DEFAULT,
        darkcolor=COLOR_BORDER_DEFAULT,
        insertcolor=COLOR_FG_PRIMARY,
        padding=SPACING_SM)
    style.map("DS.TEntry",
        foreground=[("disabled", COLOR_FG_DISABLED)],
        bordercolor=[("focus", COLOR_BORDER_FOCUS), ("invalid", COLOR_BORDER_ERROR)])
    
    # Button variants
    style.configure("DS.Primary.TButton",
        background=COLOR_ACCENT_PRIMARY,
        foreground=COLOR_FG_PRIMARY,
        borderwidth=0,
        focuscolor=COLOR_ACCENT_PRIMARY,
        padding=(SPACING_LG, SPACING_SM),
        font=(FONT_FAMILY_PRIMARY, FONT_SIZE_BASE, "bold"))
    style.map("DS.Primary.TButton",
        background=[("active", COLOR_ACCENT_HOVER), ("pressed", COLOR_ACCENT_PRESS), ("disabled", COLOR_BORDER_DEFAULT)],
        foreground=[("disabled", COLOR_FG_MUTED)])
    
    style.configure("DS.Secondary.TButton",
        background=COLOR_BG_CARD,
        foreground=COLOR_FG_PRIMARY,
        borderwidth=1,
        bordercolor=COLOR_BORDER_DEFAULT,
        padding=(SPACING_LG, SPACING_SM))
    style.map("DS.Secondary.TButton",
        background=[("active", COLOR_BORDER_DEFAULT), ("pressed", COLOR_BG_HOVER), ("disabled", COLOR_BORDER_DEFAULT)],
        foreground=[("disabled", COLOR_FG_MUTED)])
    
    style.configure("DS.Success.TButton",
        background=COLOR_SUCCESS,
        foreground=COLOR_FG_PRIMARY,
        borderwidth=0,
        focuscolor=COLOR_SUCCESS,
        padding=(SPACING_LG, SPACING_SM),
        font=(FONT_FAMILY_PRIMARY, FONT_SIZE_BASE, "bold"))
    style.map("DS.Success.TButton",
        background=[("active", "#2E8B4E"), ("pressed", "#277642")])
    
    style.configure("DS.Danger.TButton",
        background=COLOR_ERROR,
        foreground=COLOR_FG_PRIMARY,
        borderwidth=0,
        focuscolor=COLOR_ERROR,
        padding=(SPACING_LG, SPACING_SM))
    style.map("DS.Danger.TButton",
        background=[("active", "#C03537"), ("pressed", "#A02C2E")])
    
    style.configure("DS.Ghost.TButton",
        background=COLOR_BG_PRIMARY,
        foreground=COLOR_ACCENT_PRIMARY,
        borderwidth=0,
        padding=(SPACING_MD, SPACING_SM))
    style.map("DS.Ghost.TButton",
        background=[("active", COLOR_BG_HOVER)],
        foreground=[("disabled", COLOR_FG_MUTED)])
    
    # Progressbar
    style.configure("DS.TProgressbar",
        background=COLOR_ACCENT_PRIMARY,
        troughcolor=COLOR_BG_INPUT,
        borderwidth=0,
        thickness=8)
    
    # Status Badge
    style.configure("DS.Badge.TLabel",
        background=COLOR_BG_CARD,
        foreground=COLOR_FG_PRIMARY,
        padding=(SPACING_SM, SPACING_XS),
        font=(FONT_FAMILY_PRIMARY, FONT_SIZE_XS, "bold"))
    
    # Combobox
    style.configure("DS.TCombobox",
        fieldbackground=COLOR_BG_INPUT,
        foreground=COLOR_FG_PRIMARY,
        background=COLOR_BG_CARD,
        bordercolor=COLOR_BORDER_DEFAULT,
        arrowcolor=COLOR_FG_PRIMARY,
        padding=SPACING_SM)
    style.map("DS.TCombobox",
        background=[("readonly", COLOR_BG_CARD)],
        foreground=[("disabled", COLOR_FG_MUTED)])
    
    # Separator
    style.configure("DS.TSeparator", background=COLOR_BORDER_DEFAULT)
    
    # Treeview (for tables)
    style.configure("DS.Treeview",
        background=COLOR_BG_INPUT,
        foreground=COLOR_FG_PRIMARY,
        fieldbackground=COLOR_BG_INPUT,
        borderwidth=0,
        rowheight=28,
        font=(FONT_FAMILY_PRIMARY, FONT_SIZE_SM))
    style.configure("DS.Treeview.Heading",
        background=COLOR_BG_CARD,
        foreground=COLOR_ACCENT_PRIMARY,
        font=(FONT_FAMILY_PRIMARY, FONT_SIZE_SM, "bold"),
        borderwidth=1,
        relief="flat")
    style.map("DS.Treeview",
        background=[("selected", COLOR_ACCENT_PRIMARY)],
        foreground=[("selected", COLOR_FG_PRIMARY)])


# ════════════════════════════════════════════════════════════
# Base Component Class
# ════════════════════════════════════════════════════════════

class DSComponent:
    """Base class for design system components."""
    
    def __init__(self, parent: tk.Widget, **kwargs):
        self.parent = parent
        self._widget: Optional[tk.Widget] = None
        self._build(**kwargs)
    
    def _build(self, **kwargs) -> None:
        """Override in subclasses to build the widget."""
        raise NotImplementedError
    
    @property
    def widget(self) -> tk.Widget:
        """Return the underlying tkinter widget."""
        if self._widget is None:
            raise RuntimeError("Component not built")
        return self._widget
    
    def pack(self, **kwargs) -> 'DSComponent':
        self.widget.pack(**kwargs)
        return self
    
    def grid(self, **kwargs) -> 'DSComponent':
        self.widget.grid(**kwargs)
        return self
    
    def place(self, **kwargs) -> 'DSComponent':
        self.widget.place(**kwargs)
        return self


# ════════════════════════════════════════════════════════════
# Card Component
# ════════════════════════════════════════════════════════════

class Card(ttk.Frame, DSComponent):
    """Elevated card container with padding."""
    
    def __init__(
        self, 
        parent: tk.Widget, 
        title: Optional[str] = None,
        padding: int = SPACING_MD,
        **kwargs
    ):
        self.title = title
        self.padding = padding
        super().__init__(parent, style="DS.Card.TFrame", padding=padding, **kwargs)
        self._widget = self
        
        # Content frame for children
        self.content = ttk.Frame(self, style="DS.Card.TFrame")
        self.content.pack(fill=tk.BOTH, expand=True)
        
        if title:
            header = ttk.Label(
                self.content,
                text=title,
                style="Title.TLabel",
                font=(FONT_FAMILY_PRIMARY, FONT_SIZE_LG, "bold"),
                foreground=COLOR_ACCENT_PRIMARY
            )
            header.pack(anchor=tk.W, pady=(0, SPACING_SM))
            ttk.Separator(self.content, style="DS.TSeparator").pack(fill=tk.X, pady=(0, SPACING_MD))
    
    def add(self, widget: tk.Widget, **pack_kwargs) -> 'Card':
        """Add a widget to the card content area."""
        default_pack = {"fill": tk.X, "pady": SPACING_XS}
        default_pack.update(pack_kwargs)
        widget.pack(in_=self.content, **default_pack)
        return self


class CardSection(ttk.Labelframe, DSComponent):
    """Card-style labelframe with consistent styling."""
    
    def __init__(
        self, 
        parent: tk.Widget, 
        title: str = "",
        text: Optional[str] = None,
        padding: int = SPACING_MD,
        **kwargs
    ):
        # Accept both 'title' (our param) and 'text' (ttk.Labelframe standard)
        label_text = title if title else (text if text is not None else "")
        # Call ttk.Labelframe.__init__ directly to avoid MRO issues
        ttk.Labelframe.__init__(self, parent, text=label_text, style="DS.Card.TLabelframe", padding=padding, **kwargs)
        self._widget = self
        self._content = self  # Labelframe itself is the content container
    
    @property
    def content(self):
        """Return self as content container (for Card-like interface)."""
        return self._content

# ════════════════════════════════════════════════════════════
# Field Row Component (Label + Input + Optional Button)
# ════════════════════════════════════════════════════════════

class FieldRow(ttk.Frame, DSComponent):
    """Standardized row: Label + Entry + optional Browse button."""
    
    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        browse_cmd: Optional[Callable] = None,
        browse_text: str = "Selecionar",
        entry_width: int = 50,
        entry_state: str = "normal",
        required: bool = False,
        help_text: Optional[str] = None,
        **kwargs
    ):
        self.label_text = label
        self.variable = variable
        self.browse_cmd = browse_cmd
        self.required = required
        self.help_text = help_text
        
        # Filter kwargs for ttk.Frame (remove FieldRow-specific args)
        frame_kwargs = {k: v for k, v in kwargs.items() if k not in 
                       ('filetypes', 'browse_text', 'entry_width', 'entry_state')}
        
        super().__init__(parent, style="DS.FieldRow.TFrame", **frame_kwargs)
        self._widget = self
        self._build()
    
    def _build(self):
        # Label
        label_text = f"{self.label_text} *" if self.required else self.label_text
        self.label = ttk.Label(
            self,
            text=label_text,
            font=(FONT_FAMILY_PRIMARY, FONT_SIZE_BASE),
            foreground=COLOR_FG_PRIMARY
        )
        self.label.pack(anchor=tk.W, pady=(0, SPACING_XS))
        
        # Input row
        input_frame = ttk.Frame(self, style="DS.FieldRow.TFrame")
        input_frame.pack(fill=tk.X, expand=True)
        
        self.entry = ttk.Entry(
            input_frame,
            textvariable=self.variable,
            width=50,
            state=self.variable.get() and "normal" or "normal",  # Will be overridden by state
            style="DS.TEntry"
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        if self.browse_cmd:
            self.browse_btn = ttk.Button(
                input_frame,
                text="Selecionar",
                command=self.browse_cmd,
                style="DS.Secondary.TButton"
            )
            self.browse_btn.pack(side=tk.LEFT, padx=(SPACING_SM, 0))
        
        # Help text
        if self.help_text:
            self.help_label = ttk.Label(
                self,
                text=self.help_text,
                font=(FONT_FAMILY_PRIMARY, FONT_SIZE_XS),
                foreground=COLOR_FG_MUTED
            )
            self.help_label.pack(anchor=tk.W, pady=(SPACING_XS, 0))
        
        # Validation state
        self._error_msg: Optional[str] = None
    
    def set_error(self, message: Optional[str]) -> None:
        """Show/hide validation error."""
        self._error_msg = message
        if message:
            self.entry.configure(style="DS.TEntry")  # Will show error border via style map
            if not hasattr(self, 'error_label'):
                self.error_label = ttk.Label(
                    self,
                    text=message,
                    font=(FONT_FAMILY_PRIMARY, FONT_SIZE_XS),
                    foreground=COLOR_ERROR
                )
                self.error_label.pack(anchor=tk.W, pady=(SPACING_XS, 0))
            else:
                self.error_label.config(text=message)
        elif hasattr(self, 'error_label'):
            self.error_label.destroy()
            delattr(self, 'error_label')
    
    def set_state(self, state: str) -> None:
        """Set entry state (normal, disabled, readonly)."""
        self.entry.configure(state=state)


# ════════════════════════════════════════════════════════════
# Button Components
# ════════════════════════════════════════════════════════════

class Button(ttk.Button, DSComponent):
    """Enhanced button with variant support."""
    
    VARIANT_STYLES = {
        "primary": "DS.Primary.TButton",
        "secondary": "DS.Secondary.TButton",
        "success": "DS.Success.TButton",
        "danger": "DS.Danger.TButton",
        "ghost": "DS.Ghost.TButton",
    }
    
    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Optional[Callable] = None,
        variant: str = "primary",
        width: Optional[int] = None,
        **kwargs
    ):
        style_name = self.VARIANT_STYLES.get(variant, "DS.Primary.TButton")
        super().__init__(
            parent,
            text=text,
            command=command,
            style=style_name,
            width=width or 0,
            **kwargs
        )
        self._widget = self
        self.variant = variant
    
    def set_loading(self, loading: bool) -> None:
        """Show loading state."""
        if loading:
            self.config(state=tk.DISABLED)
            self._original_text = self.cget("text")
            self.config(text="⏳ Processando...")
        else:
            self.config(state=tk.NORMAL)
            if hasattr(self, '_original_text'):
                self.config(text=self._original_text)


class ButtonGroup(ttk.Frame, DSComponent):
    """Horizontal group of buttons with consistent spacing."""
    
    def __init__(self, parent: tk.Widget, spacing: int = SPACING_SM, **kwargs):
        super().__init__(parent, style="DS.FieldRow.TFrame", **kwargs)
        self._widget = self
        self.spacing = spacing
        self.buttons: List[Button] = []
    
    def add_button(self, *args, **kwargs) -> Button:
        btn = Button(self, *args, **kwargs)
        btn.pack(side=tk.LEFT, padx=(0, self.spacing))
        self.buttons.append(btn)
        return btn
    
    def clear(self) -> None:
        for btn in self.buttons:
            btn.destroy()
        self.buttons.clear()


# ════════════════════════════════════════════════════════════
# Status Badge
# ════════════════════════════════════════════════════════════

class Status(Enum):
    OK = "OK"
    REVISAO = "REVISAO"
    ERRO = "ERRO"
    ERRO_PAGAMENTO = "ERRO_PAGAMENTO"
    NOT_RUN = "NOT_RUN"
    UNKNOWN = "UNKNOWN"


class StatusBadge(ttk.Label, DSComponent):
    """Colored status badge."""
    
    STATUS_COLORS = {
        Status.OK: COLOR_SUCCESS,
        Status.REVISAO: COLOR_WARNING,
        Status.ERRO: COLOR_ERROR,
        Status.ERRO_PAGAMENTO: COLOR_ERROR,
        Status.NOT_RUN: COLOR_FG_MUTED,
        Status.UNKNOWN: COLOR_BORDER_DEFAULT,
    }
    
    STATUS_LABELS = {
        Status.OK: "✓ OK",
        Status.REVISAO: "⚠ REVISAO",
        Status.ERRO: "✗ ERRO",
        Status.ERRO_PAGAMENTO: "✗ ERRO_PAG",
        Status.NOT_RUN: "○ NOT_RUN",
        Status.UNKNOWN: "? UNKNOWN",
    }
    
    def __init__(
        self,
        parent: tk.Widget,
        status: Status = Status.UNKNOWN,
        size: str = "sm",
        **kwargs
    ):
        self.status = status
        self.size = size
        
        font_size = FONT_SIZE_XS if size == "sm" else FONT_SIZE_SM
        padding_x = SPACING_SM if size == "sm" else SPACING_MD
        padding_y = SPACING_XS if size == "sm" else SPACING_SM
        
        super().__init__(
            parent,
            text=self.STATUS_LABELS[status],
            style="DS.Badge.TLabel",
            font=(FONT_FAMILY_PRIMARY, font_size, "bold"),
            foreground=COLOR_FG_PRIMARY,
            background=self.STATUS_COLORS[status],
            padding=(padding_x, padding_y),
            **kwargs
        )
        self._widget = self
    
    def set_status(self, status: Status) -> None:
        """Update badge status."""
        self.status = status
        self.config(
            text=self.STATUS_LABELS[status],
            background=self.STATUS_COLORS[status]
        )


# ════════════════════════════════════════════════════════════
# Progress Ring (Circular Progress)
# ════════════════════════════════════════════════════════════

class ProgressRing(tk.Canvas, DSComponent):
    """Circular progress indicator with percentage."""
    
    def __init__(
        self,
        parent: tk.Widget,
        size: int = 60,
        stroke_width: int = 6,
        variant: str = "primary",
        **kwargs
    ):
        self.size = size
        self.stroke_width = stroke_width
        self.variant = variant
        self._progress = 0.0
        self._message = ""
        
        color_map = {
            "primary": COLOR_ACCENT_PRIMARY,
            "success": COLOR_SUCCESS,
            "warning": COLOR_WARNING,
            "error": COLOR_ERROR,
        }
        self.color = color_map.get(variant, COLOR_ACCENT_PRIMARY)
        
        super().__init__(
            parent,
            width=size,
            height=size,
            background=COLOR_BG_PRIMARY,
            highlightthickness=0,
            **kwargs
        )
        self._widget = self
        self._draw()
    
    @property
    def progress(self) -> float:
        return self._progress
    
    @progress.setter
    def progress(self, value: float) -> None:
        self._progress = max(0.0, min(1.0, value))
        self._draw()
    
    @property
    def message(self) -> str:
        return self._message
    
    @message.setter
    def message(self, value: str) -> None:
        self._message = value
        self._draw()
    
    def _draw(self) -> None:
        self.delete("all")
        
        # Background circle
        r = (self.size - self.stroke_width) // 2
        cx = cy = self.size // 2
        
        self.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=COLOR_BORDER_DEFAULT,
            width=self.stroke_width
        )
        
        # Progress arc
        if self._progress > 0:
            extent = 360 * self._progress
            self.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=90,
                extent=-extent,
                outline=self.color,
                width=self.stroke_width,
                style=tk.ARC
            )
        
        # Center text
        percent = int(self._progress * 100)
        text = f"{percent}%" if not self._message else self._message
        self.create_text(
            cx, cy,
            text=text,
            fill=COLOR_FG_PRIMARY,
            font=(FONT_FAMILY_PRIMARY, FONT_SIZE_SM, "bold")
        )


# ════════════════════════════════════════════════════════════
# File Drop Zone
# ════════════════════════════════════════════════════════════

class FileDropZone(ttk.Frame, DSComponent):
    """Drag-and-drop file zone with visual feedback."""
    
    def __init__(
        self,
        parent: tk.Widget,
        label: str = "Arraste arquivos aqui",
        accept: Optional[List[str]] = None,
        on_drop: Optional[Callable[[List[str]], None]] = None,
        **kwargs
    ):
        self.label_text = label
        self.accept = accept or [".pdf", ".jpg", ".jpeg", ".png"]
        self.on_drop = on_drop
        self._dragging = False
        
        super().__init__(parent, style="DS.Card.TFrame", **kwargs)
        self._widget = self
        self._build()
        self._bind_events()
    
    def _build(self):
        self.config(padding=SPACING_XL)
        
        self.icon_label = ttk.Label(
            self,
            text="📁",
            font=(FONT_FAMILY_PRIMARY, FONT_SIZE_2XL),
            foreground=COLOR_FG_MUTED
        )
        self.icon_label.pack(pady=(0, SPACING_SM))
        
        self.text_label = ttk.Label(
            self,
            text=self.label_text,
            font=(FONT_FAMILY_PRIMARY, FONT_SIZE_BASE),
            foreground=COLOR_FG_MUTED
        )
        self.text_label.pack()
        
        self.hint_label = ttk.Label(
            self,
            text=f"Formatos: {', '.join(self.accept)}",
            font=(FONT_FAMILY_PRIMARY, FONT_SIZE_XS),
            foreground=COLOR_FG_DISABLED
        )
        self.hint_label.pack(pady=(SPACING_SM, 0))
    
    def _bind_events(self):
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        
        # Drag and drop (requires tkdnd on Windows, fallback to click)
        try:
            self.drop_target_register(tk.DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
            self.dnd_bind("<<DragEnter>>", lambda e: self._set_drag(True))
            self.dnd_bind("<<DragLeave>>", lambda e: self._set_drag(False))
        except tk.TclError:
            # tkdnd not available
            pass
    
    def _on_enter(self, event):
        if not self._dragging:
            self.config(style="DS.Card.TFrame")
            self.icon_label.config(foreground=COLOR_ACCENT_PRIMARY)
            self.text_label.config(foreground=COLOR_FG_PRIMARY)
    
    def _on_leave(self, event):
        if not self._dragging:
            self.icon_label.config(foreground=COLOR_FG_MUTED)
            self.text_label.config(foreground=COLOR_FG_MUTED)
    
    def _on_click(self, event):
        from tkinter import filedialog
        files = filedialog.askopenfilenames(
            title="Selecionar arquivos",
            filetypes=[("Todos", "*.*")] + [(ext.upper(), f"*{ext}") for ext in self.accept]
        )
        if files and self.on_drop:
            self.on_drop(list(files))
    
    def _set_drag(self, dragging: bool):
        self._dragging = dragging
        if dragging:
            self.config(style="DS.Card.TFrame")
            self.icon_label.config(foreground=COLOR_ACCENT_PRIMARY)
            self.text_label.config(text="Solte para upload", foreground=COLOR_ACCENT_PRIMARY)
        else:
            self.icon_label.config(foreground=COLOR_FG_MUTED)
            self.text_label.config(text=self.label_text, foreground=COLOR_FG_MUTED)
    
    def _on_drop(self, event):
        self._set_drag(False)
        files = self.tk.splitlist(event.data)
        if files and self.on_drop:
            # Filter by accepted extensions
            filtered = [f for f in files if any(f.lower().endswith(ext) for ext in self.accept)]
            if filtered:
                self.on_drop(filtered)


# ════════════════════════════════════════════════════════════
# Log Viewer Component
# ════════════════════════════════════════════════════════════

class LogViewer(ttk.Frame, DSComponent):
    """Styled log viewer with colored levels."""
    
    LEVEL_TAGS = {
        "error": ("❌", COLOR_ERROR),
        "warning": ("⚠", COLOR_WARNING),
        "success": ("✅", COLOR_SUCCESS),
        "info": ("ℹ", COLOR_FG_MUTED),
        "process": ("🔄", COLOR_ACCENT_PRIMARY),
        "debug": ("🐛", COLOR_FG_DISABLED),
    }
    
    def __init__(
        self,
        parent: tk.Widget,
        height: int = 10,
        max_lines: int = 1000,
        **kwargs
    ):
        self.max_lines = max_lines
        self._line_count = 0
        
        super().__init__(parent, **kwargs)
        self._widget = self
        self._build()
    
    def _build(self):
        # Text widget with scrollbar
        text_frame = ttk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text = tk.Text(
            text_frame,
            height=10,
            state=tk.DISABLED,
            bg=COLOR_BG_INPUT,
            fg=COLOR_FG_PRIMARY,
            insertbackground=COLOR_FG_PRIMARY,
            selectbackground=COLOR_ACCENT_PRIMARY,
            selectforeground=COLOR_FG_PRIMARY,
            borderwidth=SPACING_NONE,
            relief="flat",
            font=(FONT_FAMILY_MONO, FONT_SIZE_SM),
            wrap=tk.WORD
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.configure(yscrollcommand=scrollbar.set)
        
        # Configure tags
        for level, (icon, color) in self.LEVEL_TAGS.items():
            self.text.tag_configure(level, foreground=color)
            self.text.tag_configure(f"{level}_icon", foreground=color)
    
    def log(self, message: str, level: str = "info") -> None:
        """Add a log message with level."""
        self.text.configure(state=tk.NORMAL)
        
        if self._line_count >= self.max_lines:
            # Remove oldest lines
            self.text.delete("1.0", "2.0")
        else:
            self._line_count += 1
        
        icon, color = self.LEVEL_TAGS.get(level, self.LEVEL_TAGS["info"])
        
        self.text.insert(tk.END, f"{icon} ", f"{level}_icon")
        self.text.insert(tk.END, f"{message}\n", level)
        
        self.text.see(tk.END)
        self.text.configure(state=tk.DISABLED)
    
    def clear(self) -> None:
        """Clear all log messages."""
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.configure(state=tk.DISABLED)
        self._line_count = 0
    
    def save(self, path: str) -> None:
        """Save log to file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.text.get("1.0", tk.END))


# ════════════════════════════════════════════════════════════
# Table Component (Treeview wrapper)
# ════════════════════════════════════════════════════════════

@dataclass
class Column:
    """Table column definition."""
    key: str
    title: str
    width: int = 100
    min_width: int = 50
    anchor: str = "w"
    stretch: bool = False


class DataTable(ttk.Frame, DSComponent):
    """Sortable, filterable data table."""
    
    def __init__(
        self,
        parent: tk.Widget,
        columns: List[Column],
        on_select: Optional[Callable[[dict], None]] = None,
        **kwargs
    ):
        self.columns = columns
        self.on_select = on_select
        self._data: List[dict] = []
        self._sort_column: Optional[str] = None
        self._sort_reverse = False
        
        super().__init__(parent, **kwargs)
        self._widget = self
        self._build()
    
    def _build(self):
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=(0, SPACING_SM))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        
        ttk.Label(toolbar, text="🔍", font=(FONT_FAMILY_PRIMARY, FONT_SIZE_BASE)).pack(side=tk.LEFT)
        ttk.Entry(toolbar, textvariable=self.search_var, style="DS.TEntry").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=SPACING_SM)
        
        # Treeview
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        col_keys = [c.key for c in self.columns]
        self.tree = ttk.Treeview(
            tree_frame,
            columns=col_keys,
            show="headings",
            style="DS.Treeview",
            selectmode="browse"
        )
        
        # Configure columns
        for col in self.columns:
            self.tree.heading(col.key, text=col.title, command=lambda k=col.key: self._on_sort(k))
            self.tree.column(
                col.key,
                width=col.width,
                minwidth=col.min_width,
                anchor=col.anchor,
                stretch=col.stretch
            )
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._on_select(e))
    
    def set_data(self, data: List[dict]) -> None:
        """Set table data."""
        self._data = data
        self._refresh()
    
    def _refresh(self) -> None:
        # Clear
        self.tree.delete(*self.tree.get_children())
        
        # Filter
        search = self.search_var.get().lower()
        filtered = [
            row for row in self._data
            if not search or any(search in str(v).lower() for v in row.values())
        ]
        
        # Sort
        if self._sort_column:
            filtered.sort(
                key=lambda r: str(r.get(self._sort_column, "")),
                reverse=self._sort_reverse
            )
        
        # Insert
        for row in filtered:
            values = [row.get(c.key, "") for c in self.columns]
            self.tree.insert("", tk.END, values=values, tags=(str(row),))
    
    def _on_search(self, *args) -> None:
        self._refresh()
    
    def _on_sort(self, column: str) -> None:
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = False
        self._refresh()
    
    def _on_select(self, event) -> None:
        selection = self.tree.selection()
        if selection and self.on_select:
            item = self.tree.item(selection[0])
            # Find matching data row
            for row in self._data:
                if all(str(row.get(c.key, "")) == str(v) for c, v in zip(self.columns, item["values"])):
                    self.on_select(row)
                    break


# ════════════════════════════════════════════════════════════
# Factory Functions for Common UI Patterns
# ════════════════════════════════════════════════════════════

def create_labeled_entry(parent, label, variable, **kwargs) -> FieldRow:
    """Quick factory for labeled entry row."""
    return FieldRow(parent, label, variable, **kwargs)


def create_file_field(parent, label, variable, **kwargs) -> FieldRow:
    """Quick factory for file selection field."""
    def browse():
        from tkinter import filedialog
        filetypes = kwargs.pop("filetypes", [("Todos", "*.*")])
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            variable.set(path)
    
    return FieldRow(
        parent,
        label,
        variable,
        browse_cmd=browse,
        browse_text="Selecionar",
        **kwargs
    )


def create_folder_field(parent, label, variable, **kwargs) -> FieldRow:
    """Quick factory for folder selection field."""
    def browse():
        from tkinter import filedialog
        path = filedialog.askdirectory()
        if path:
            variable.set(path)
    
    return FieldRow(
        parent,
        label,
        variable,
        browse_cmd=browse,
        browse_text="Selecionar pasta",
        **kwargs
    )


def create_primary_button(parent, text, command, **kwargs) -> Button:
    return Button(parent, text, command, variant="primary", **kwargs)


def create_success_button(parent, text, command, **kwargs) -> Button:
    return Button(parent, text, command, variant="success", **kwargs)


def create_danger_button(parent, text, command, **kwargs) -> Button:
    return Button(parent, text, command, variant="danger", **kwargs)


def create_secondary_button(parent, text, command, **kwargs) -> Button:
    return Button(parent, text, command, variant="secondary", **kwargs)


def create_ghost_button(parent, text, command, **kwargs) -> Button:
    return Button(parent, text, command, variant="ghost", **kwargs)


# ════════════════════════════════════════════════════════════
# Theme Application
# ════════════════════════════════════════════════════════════

def apply_design_system(root: tk.Tk) -> ttk.Style:
    """Apply complete design system to root window."""
    style = ttk.Style(root)
    
    # Use 'clam' as base for better customization
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    
    # Root
    root.configure(bg=COLOR_BG_PRIMARY)
    
    # Base
    style.configure(".",
        background=COLOR_BG_PRIMARY,
        foreground=COLOR_FG_PRIMARY,
        font=(FONT_FAMILY_PRIMARY, FONT_SIZE_BASE),
    )
    
    # Frames
    style.configure("TFrame", background=COLOR_BG_PRIMARY)
    style.configure("DS.Card.TFrame", background=COLOR_BG_CARD)
    
    # Labelframe
    style.configure("TLabelframe", background=COLOR_BG_CARD, foreground=COLOR_FG_PRIMARY,
                    borderwidth=1, relief="solid")
    style.configure("TLabelframe.Label", background=COLOR_BG_CARD, 
                    foreground=COLOR_ACCENT_PRIMARY, font=(FONT_FAMILY_PRIMARY, FONT_SIZE_BASE, "bold"))
    
    # Labels
    style.configure("TLabel", background=COLOR_BG_CARD, foreground=COLOR_FG_PRIMARY)
    style.configure("Title.TLabel", background=COLOR_BG_PRIMARY, foreground=COLOR_FG_PRIMARY,
                    font=(FONT_FAMILY_PRIMARY, FONT_SIZE_2XL, "bold"))
    style.configure("Subtitle.TLabel", background=COLOR_BG_PRIMARY, foreground=COLOR_FG_MUTED,
                    font=(FONT_FAMILY_PRIMARY, FONT_SIZE_SM))
    style.configure("Muted.TLabel", background=COLOR_BG_CARD, foreground=COLOR_FG_MUTED)
    style.configure("Status.TLabel", background=COLOR_BG_PRIMARY, foreground=COLOR_FG_MUTED)
    
    # Entry
    style.configure("TEntry",
        fieldbackground=COLOR_BG_INPUT,
        foreground=COLOR_FG_PRIMARY,
        bordercolor=COLOR_BORDER_DEFAULT,
        lightcolor=COLOR_BORDER_DEFAULT,
        darkcolor=COLOR_BORDER_DEFAULT,
        insertcolor=COLOR_FG_PRIMARY,
        padding=SPACING_SM)
    style.map("TEntry",
        foreground=[("disabled", COLOR_FG_DISABLED)])
    
    # Combobox
    style.configure("TCombobox",
        fieldbackground=COLOR_BG_INPUT,
        foreground=COLOR_FG_PRIMARY,
        background=COLOR_BG_CARD,
        bordercolor=COLOR_BORDER_DEFAULT,
        arrowcolor=COLOR_FG_PRIMARY,
        padding=SPACING_SM)
    style.map("TCombobox",
        background=[("readonly", COLOR_BG_CARD)],
        foreground=[("disabled", COLOR_FG_MUTED)])
    
    # Buttons
    style.configure("TButton",
        background=COLOR_ACCENT_PRIMARY,
        foreground=COLOR_FG_PRIMARY,
        borderwidth=0,
        focuscolor=COLOR_ACCENT_PRIMARY,
        padding=(SPACING_LG, SPACING_SM),
        font=(FONT_FAMILY_PRIMARY, FONT_SIZE_BASE, "bold"))
    style.map("TButton",
        background=[("active", COLOR_ACCENT_HOVER), ("pressed", COLOR_ACCENT_PRESS), ("disabled", COLOR_BORDER_DEFAULT)],
        foreground=[("disabled", COLOR_FG_MUTED)])
    
    # Secondary button style
    style.configure("Secondary.TButton",
        background=COLOR_BG_CARD,
        foreground=COLOR_FG_PRIMARY,
        borderwidth=1,
        bordercolor=COLOR_BORDER_DEFAULT,
        padding=(SPACING_LG, SPACING_SM))
    style.map("Secondary.TButton",
        background=[("active", COLOR_BORDER_DEFAULT), ("pressed", COLOR_BG_HOVER), ("disabled", COLOR_BORDER_DEFAULT)],
        foreground=[("disabled", COLOR_FG_MUTED)])
    
    # Success button style
    style.configure("Success.TButton",
        background=COLOR_SUCCESS,
        foreground=COLOR_FG_PRIMARY,
        borderwidth=0,
        focuscolor=COLOR_SUCCESS,
        padding=(SPACING_LG, SPACING_SM),
        font=(FONT_FAMILY_PRIMARY, FONT_SIZE_BASE, "bold"))
    style.map("Success.TButton",
        background=[("active", "#2E8B4E"), ("pressed", "#277642")])
    
    # Danger button style
    style.configure("Danger.TButton",
        background=COLOR_ERROR,
        foreground=COLOR_FG_PRIMARY,
        borderwidth=0,
        focuscolor=COLOR_ERROR,
        padding=(SPACING_LG, SPACING_SM))
    style.map("Danger.TButton",
        background=[("active", "#C03537"), ("pressed", "#A02C2E")])
    
    # Progressbar
    style.configure("TProgressbar",
        background=COLOR_ACCENT_PRIMARY,
        troughcolor=COLOR_BG_INPUT,
        borderwidth=0,
        thickness=8)
    
    # Notebook
    style.configure("TNotebook", background=COLOR_BG_PRIMARY, borderwidth=0)
    style.configure("TNotebook.Tab",
        background=COLOR_BG_CARD,
        foreground=COLOR_FG_MUTED,
        padding=(SPACING_LG, SPACING_SM),
        font=(FONT_FAMILY_PRIMARY, FONT_SIZE_BASE))
    style.map("TNotebook.Tab",
        background=[("selected", COLOR_ACCENT_PRIMARY), ("active", COLOR_BORDER_DEFAULT)],
        foreground=[("selected", COLOR_FG_PRIMARY)])
    
    # Scrollbar
    style.configure("Vertical.TScrollbar",
        background=COLOR_BG_CARD,
        troughcolor=COLOR_BG_PRIMARY,
        bordercolor=COLOR_BG_PRIMARY,
        arrowcolor=COLOR_FG_MUTED,
        width=10)
    style.map("Vertical.TScrollbar",
        background=[("active", COLOR_ACCENT_PRIMARY)])
    
    # Separator
    style.configure("TSeparator", background=COLOR_BORDER_DEFAULT)
    
    # Treeview
    style.configure("Treeview",
        background=COLOR_BG_INPUT,
        foreground=COLOR_FG_PRIMARY,
        fieldbackground=COLOR_BG_INPUT,
        borderwidth=0,
        rowheight=28,
        font=(FONT_FAMILY_PRIMARY, FONT_SIZE_SM))
    style.configure("Treeview.Heading",
        background=COLOR_BG_CARD,
        foreground=COLOR_ACCENT_PRIMARY,
        font=(FONT_FAMILY_PRIMARY, FONT_SIZE_SM, "bold"),
        borderwidth=1,
        relief="flat")
    style.map("Treeview",
        background=[("selected", COLOR_ACCENT_PRIMARY)],
        foreground=[("selected", COLOR_FG_PRIMARY)])
    
    # Configure component-specific styles
    configure_component_styles(style)
    
    return style


if __name__ == "__main__":
    # Demo
    root = tk.Tk()
    root.title("Design System Demo")
    root.geometry("800x600")
    
    apply_design_system(root)
    
    # Demo layout
    main = ttk.Frame(root, padding=SPACING_XL, style="TFrame")
    main.pack(fill=tk.BOTH, expand=True)
    
    # Card
    card = Card(main, title="Exemplo de Card")
    card.add(ttk.Label(card.content, text="Conteúdo do card com padding padrão"))
    card.pack(fill=tk.X, pady=SPACING_MD)
    
    # Field Row
    var = tk.StringVar()
    field = FieldRow(main, "Caminho do arquivo", var, browse_cmd=lambda: var.set("test"))
    field.pack(fill=tk.X, pady=SPACING_MD)
    
    # Buttons
    btn_group = ButtonGroup(main)
    btn_group.add_button("Primário", lambda: None, variant="primary")
    btn_group.add_button("Sucesso", lambda: None, variant="success")
    btn_group.add_button("Perigo", lambda: None, variant="danger")
    btn_group.add_button("Secundário", lambda: None, variant="secondary")
    btn_group.pack(fill=tk.X, pady=SPACING_MD)
    
    # Status Badges
    badge_frame = ttk.Frame(main)
    badge_frame.pack(fill=tk.X, pady=SPACING_MD)
    for status in Status:
        StatusBadge(badge_frame, status).pack(side=tk.LEFT, padx=SPACING_SM)
    
    # Progress Ring
    progress = ProgressRing(main, size=80)
    progress.progress = 0.65
    progress.message = "65%"
    progress.pack(pady=SPACING_MD)
    
    # Log Viewer
    log = LogViewer(main, height=6)
    log.pack(fill=tk.BOTH, expand=True, pady=SPACING_MD)
    log.log("Sistema iniciado", "success")
    log.log("Carregando configurações...", "process")
    log.log("Aviso: arquivo não encontrado", "warning")
    log.log("Erro ao conectar", "error")
    log.log("Processo concluído", "success")
    
    root.mainloop()