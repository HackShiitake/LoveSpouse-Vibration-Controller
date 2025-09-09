"""
Bluetooth Vibration Toy Controller
==================================

This application provides both a GUI interface and HTTP API for controlling Bluetooth vibration toys.
It uses Bluetooth LE advertising to send commands and supports pattern playback from .vibepattern files.

API SPECIFICATION
================

HTTP Server runs on port 4545 by default.

Endpoints:
----------

1. GET /API/{strength}-{duration}{unit}
   
   Controls vibration with specified strength and duration.
   
   Parameters:
   - strength: Integer 0-9 (0 = stop, 9 = maximum intensity)
   - duration: Float/Integer duration value
   - unit: "ms" (milliseconds) or "s" (seconds)
   
   Examples:
   - GET /API/5-1000ms    # Strength 5 for 1000 milliseconds
   - GET /API/3-2.5s      # Strength 3 for 2.5 seconds
   - GET /API/0-100ms     # Stop vibration (strength 0)
   
   Response (JSON):
   - Success: {"status": "ok", "strength": 5, "duration": "1000ms"}
   - Error: {"error": "error_message"}

2. GET / (any other path)
   
   Returns API information and usage.
   
   Response: {"status": "ready", "usage": "GET /API/{strength}-{duration}{unit}"}

PATTERN FILE FORMAT (.vibepattern)
=================================

Pattern files should be placed in the "pattern/" directory.

Format:
Line 1: JSON header with metadata
        {"name": "Pattern Name", "author": "Author Name"}

Line 2+: Sequence commands in format: {strength}-{duration}{unit}
         - strength: 0-9
         - duration: number
         - unit: "ms" or "s"

Example pattern file:
{"name": "Pulse Wave", "author": "Developer"}
3-500ms
0-250ms
5-750ms
0-500ms
7-1s
0-250ms

BLUETOOTH COMMANDS
=================

The application uses predefined hex commands for different strength levels:
- Level 0: F41D7C (stop)
- Level 1: F7864E
- Level 2: F60F5F
- Level 3: F1B02B
- Level 4: F0393A
- Level 5: F3A208
- Level 6: F22B19
- Level 7: FDDCE1
- Level 8: FC55F0
- Level 9: C5175C (maximum)

Commands are sent via Bluetooth LE advertising with manufacturer data.
"""

import os
import re
import json
import threading
import time
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import tkinter as tk
from tkinter import ttk

import winsdk.windows.devices.bluetooth.advertisement as wwda
from winsdk.windows.devices.bluetooth.advertisement import BluetoothLEAdvertisementPublisherStatus
import winsdk.windows.storage.streams as wwss


class ToyController:
    """
    Bluetooth toy intensity control class
    
    Handles communication with Bluetooth vibration toys using LE advertising.
    Supports both single commands and continuous operation modes.
    """
    
    # Predefined hex commands for different intensity levels (0-9)
    COMMANDS = [
        "F41D7C",  # Level 0 - Stop
        "F7864E",  # Level 1
        "F60F5F",  # Level 2
        "F1B02B",  # Level 3
        "F0393A",  # Level 4
        "F3A208",  # Level 5
        "F22B19",  # Level 6
        "FDDCE1",  # Level 7
        "FC55F0",  # Level 8
        "C5175C"   # Level 9 - Maximum
    ]

    def __init__(self):
        self.is_running = False
        self.current_thread = None

    def get_command(self, strength: int) -> str:
        """
        Get hex command for specified strength level
        
        Args:
            strength (int): Intensity level 0-9
            
        Returns:
            str: Hex command string
        """
        strength = max(0, min(len(self.COMMANDS) - 1, strength))
        return self.COMMANDS[strength]

    async def send_command_async(self, command: str, duration: float):
        """
        Send command asynchronously via Bluetooth LE advertising
        
        Args:
            command (str): Hex command to send
            duration (float): Duration in seconds
        """
        # Create Bluetooth LE advertisement publisher
        adv = wwda.BluetoothLEAdvertisementPublisher()
        mdata = wwda.BluetoothLEManufacturerData()
        mdata.company_id = 0xFF

        # Create data writer and write the command with header
        writer = wwss.DataWriter()
        writer.write_bytes(bytearray.fromhex("0000006db643ce97fe427c" + command))
        mdata.data = writer.detach_buffer()

        # Start advertising
        adv.advertisement.manufacturer_data.append(mdata)
        adv.start()
        
        # Wait for advertising to start
        while adv.status != BluetoothLEAdvertisementPublisherStatus.STARTED:
            time.sleep(0.01)
        
        # Keep advertising for specified duration
        time.sleep(duration)
        adv.stop()

    def send_command(self, strength: int, duration: float):
        """
        Send command synchronously
        
        Args:
            strength (int): Intensity level 0-9
            duration (float): Duration in seconds
        """
        command = self.get_command(strength)
        asyncio.run(self.send_command_async(command, duration))

    def start_continuous(self, strength: int):
        """
        Start continuous vibration at specified strength
        
        Args:
            strength (int): Intensity level 1-9 (0 stops continuous mode)
        """
        self.stop_continuous()
        if strength > 0:
            self.is_running = True

            def continuous_send():
                """Continuous sending loop running in separate thread"""
                while self.is_running:
                    self.send_command(strength, 0.1)
                    time.sleep(0.1)

            self.current_thread = threading.Thread(target=continuous_send, daemon=True)
            self.current_thread.start()

    def stop_continuous(self):
        """Stop continuous operation and send stop command"""
        self.is_running = False
        if self.current_thread:
            self.current_thread = None
        # Send stop command (strength 0 for short duration)
        self.send_command(0, 0.05)


# Global controller instance
controller = ToyController()


class PatternManager:
    """
    Manager for loading and handling .vibepattern files from pattern/ directory
    
    Pattern files contain sequences of vibration commands with timing information.
    """
    
    def __init__(self, folder="pattern"):
        self.folder = folder
        self.patterns = self.load_patterns()

    def load_patterns(self):
        """
        Load all .vibepattern files from the specified folder
        
        Returns:
            dict: Dictionary of pattern_name -> sequence_list
        """
        patterns = {}
        if not os.path.isdir(self.folder):
            return patterns

        for file in os.listdir(self.folder):
            if file.endswith(".vibepattern"):
                path = os.path.join(self.folder, file)
                with open(path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]

                if not lines:
                    continue

                # First line should be JSON format with metadata
                try:
                    header = json.loads(lines[0])
                    name = header.get("name", file)
                    author = header.get("author", "")
                except json.JSONDecodeError:
                    name, author = file, ""

                # Create display name with author if available
                display_name = f"{name} by {author}" if author else name

                # Parse remaining lines: strength-duration(ms|s) format
                sequence = []
                for line in lines[1:]:
                    match = re.match(r'(\d+)-(\d+)(ms|s)', line)
                    if match:
                        strength = int(match.group(1))
                        duration_val = int(match.group(2))
                        duration_unit = match.group(3)
                        # Convert to seconds
                        duration = duration_val / 1000.0 if duration_unit == "ms" else duration_val
                        sequence.append((strength, duration))

                if sequence:
                    patterns[display_name] = sequence

        return patterns


# Global pattern manager instance
pattern_manager = PatternManager()


class ModernStyle:
    """
    Discord-inspired color palette and styling for the GUI
    
    Provides a modern dark theme with Discord-like colors and styling methods.
    """
    
    # Discord Dark Theme Colors
    BG_PRIMARY = "#36393F"      # Main background
    BG_SECONDARY = "#2F3136"    # Secondary background
    BG_TERTIARY = "#202225"     # Tertiary background
    ACCENT = "#5865F2"          # Discord Blurple
    ACCENT_HOVER = "#4752C4"    # Hover state
    SUCCESS = "#57F287"         # Success color
    WARNING = "#FEE75C"         # Warning color
    DANGER = "#ED4245"          # Danger color
    TEXT_PRIMARY = "#FFFFFF"    # Main text
    TEXT_SECONDARY = "#B9BBBE"  # Secondary text
    TEXT_MUTED = "#72767D"      # Muted text
    BORDER = "#40444B"          # Border color
    
    @staticmethod
    def configure_style():
        """
        Customize ttk styles with modern Discord-inspired theme
        """
        style = ttk.Style()
        
        # Set main theme
        style.theme_use('clam')
        
        # Frame styling
        style.configure('Modern.TFrame', 
                       background=ModernStyle.BG_PRIMARY,
                       relief='flat')
        
        # Label styling
        style.configure('Title.TLabel',
                       background=ModernStyle.BG_PRIMARY,
                       foreground=ModernStyle.TEXT_PRIMARY,
                       font=('Segoe UI', 16, 'bold'))
        
        style.configure('Modern.TLabel',
                       background=ModernStyle.BG_PRIMARY,
                       foreground=ModernStyle.TEXT_SECONDARY,
                       font=('Segoe UI', 10))
        
        style.configure('Value.TLabel',
                       background=ModernStyle.BG_PRIMARY,
                       foreground=ModernStyle.ACCENT,
                       font=('Segoe UI', 14, 'bold'))
        
        # Scale/Slider styling
        style.configure('Modern.Horizontal.TScale',
                       background=ModernStyle.BG_PRIMARY,
                       troughcolor=ModernStyle.BG_TERTIARY,
                       slidercolor=ModernStyle.ACCENT,
                       lightcolor=ModernStyle.ACCENT,
                       darkcolor=ModernStyle.ACCENT_HOVER,
                       focuscolor=ModernStyle.ACCENT)
        
        # Button styling
        style.configure('Modern.TButton',
                       background=ModernStyle.BG_SECONDARY,
                       foreground=ModernStyle.TEXT_PRIMARY,
                       borderwidth=1,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       relief='flat')
        
        style.map('Modern.TButton',
                  background=[('active', ModernStyle.ACCENT),
                             ('pressed', ModernStyle.ACCENT_HOVER)],
                  foreground=[('active', ModernStyle.TEXT_PRIMARY),
                             ('pressed', ModernStyle.TEXT_PRIMARY)])
        
        # Stop button styling (danger color)
        style.configure('Stop.TButton',
                       background=ModernStyle.DANGER,
                       foreground=ModernStyle.TEXT_PRIMARY,
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 11, 'bold'),
                       relief='flat')
        
        style.map('Stop.TButton',
                  background=[('active', '#C73E3E'),
                             ('pressed', '#B32F2F')])


class TkinterGUI:
    """
    Modern GUI interface for vibration control
    
    Provides intensity control via slider and pattern playback functionality.
    Features a Discord-inspired dark theme design.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎮 Vibration Controller")
        self.root.geometry("420x650")
        self.root.configure(bg=ModernStyle.BG_PRIMARY)
        self.root.resizable(False, False)
        
        # Set icon if available
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # Apply modern styling
        ModernStyle.configure_style()
        
        self.create_widgets()
        
        # Pattern playback control flags
        self.pattern_running = False
        self.pattern_thread = None

    def create_widgets(self):
        """Create and layout all GUI widgets"""
        # Main container frame
        main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Application title
        title_label = ttk.Label(main_frame, text="Vibration Controller", style='Title.TLabel')
        title_label.pack(pady=(0, 30))
        
        # Create main sections
        self.create_intensity_section(main_frame)
        self.create_pattern_section(main_frame)
        self.create_status_section(main_frame)

    def create_intensity_section(self, parent):
        """Create intensity control section with slider and controls"""
        intensity_frame = ttk.Frame(parent, style='Modern.TFrame')
        intensity_frame.pack(fill='x', pady=(0, 30))
        
        # Section title
        title = ttk.Label(intensity_frame, text="💪 Intensity Control", 
                         style='Modern.TLabel', font=('Segoe UI', 12, 'bold'))
        title.pack(anchor='w', pady=(0, 15))
        
        # Slider container
        slider_container = ttk.Frame(intensity_frame, style='Modern.TFrame')
        slider_container.pack(fill='x')
        
        # Current intensity value display
        value_frame = ttk.Frame(slider_container, style='Modern.TFrame')
        value_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(value_frame, text="Current Level:", style='Modern.TLabel').pack(side='left')
        
        self.strength_var = tk.IntVar(value=0)
        self.strength_label = ttk.Label(value_frame, text="0", style='Value.TLabel')
        self.strength_label.pack(side='right')
        
        # Intensity slider
        self.strength_scale = ttk.Scale(
            slider_container,
            from_=0,
            to=9,
            orient="horizontal",
            variable=self.strength_var,
            command=self.on_strength_change,
            style='Modern.Horizontal.TScale',
            length=300
        )
        self.strength_scale.pack(pady=10)
        
        # Level indicators (0-9)
        levels_frame = ttk.Frame(slider_container, style='Modern.TFrame')
        levels_frame.pack(fill='x', pady=(5, 20))
        
        for i in range(10):
            label = ttk.Label(levels_frame, text=str(i), style='Modern.TLabel')
            label.pack(side='left', expand=True)
        
        # Emergency stop button
        self.stop_button = ttk.Button(
            intensity_frame, 
            text="🛑 STOP", 
            command=self.stop_action,
            style='Stop.TButton'
        )
        self.stop_button.pack(pady=10)

    def create_pattern_section(self, parent):
        """Create pattern playback section with file list and controls"""
        pattern_frame = ttk.Frame(parent, style='Modern.TFrame')
        pattern_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Section title
        title = ttk.Label(pattern_frame, text="🎵 Pattern Playback", 
                         style='Modern.TLabel', font=('Segoe UI', 12, 'bold'))
        title.pack(anchor='w', pady=(0, 15))
        
        # Listbox container with scrollbar
        list_container = ttk.Frame(pattern_frame, style='Modern.TFrame')
        list_container.pack(fill='both', expand=True)
        
        # Custom styled listbox for pattern selection
        self.pattern_listbox = tk.Listbox(
            list_container,
            bg=ModernStyle.BG_SECONDARY,
            fg=ModernStyle.TEXT_PRIMARY,
            selectbackground=ModernStyle.ACCENT,
            selectforeground=ModernStyle.TEXT_PRIMARY,
            font=('Segoe UI', 10),
            borderwidth=0,
            highlightthickness=0,
            activestyle='none',
            height=8
        )
        
        # Scrollbar for pattern list
        scrollbar = tk.Scrollbar(list_container, bg=ModernStyle.BG_TERTIARY,
                                troughcolor=ModernStyle.BG_TERTIARY,
                                activebackground=ModernStyle.ACCENT)
        
        self.pattern_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.pattern_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.pattern_listbox.yview)
        
        # Load patterns into listbox
        for name in pattern_manager.patterns.keys():
            self.pattern_listbox.insert(tk.END, name)
        
        # Bind events for pattern selection
        self.pattern_listbox.bind("<Double-1>", self.play_selected_pattern)
        self.pattern_listbox.bind("<Return>", self.play_selected_pattern)
        
        # Play button
        play_button = ttk.Button(
            pattern_frame, 
            text="▶️ Play Selected", 
            command=lambda: self.play_selected_pattern(),
            style='Modern.TButton'
        )
        play_button.pack(pady=(10, 0))

    def create_status_section(self, parent):
        """Create status display section"""
        status_frame = ttk.Frame(parent, style='Modern.TFrame')
        status_frame.pack(fill='x')
        
        # Status indicator label
        self.status_label = ttk.Label(
            status_frame, 
            text="🟢 Ready", 
            style='Modern.TLabel',
            font=('Segoe UI', 10)
        )
        self.status_label.pack()

    def on_strength_change(self, value):
        """
        Handle intensity slider changes
        
        Args:
            value (str): Slider value as string
        """
        strength = int(float(value))
        self.strength_label.config(text=str(strength))
        
        # Update status and start/stop continuous operation
        if strength == 0:
            controller.stop_continuous()
            self.status_label.config(text="🟢 Ready")
        else:
            controller.start_continuous(strength)
            self.status_label.config(text=f"🔵 Running - Level {strength}")

    def stop_action(self):
        """Emergency stop action - stops all operations"""
        # Stop intensity control
        self.strength_var.set(0)
        self.strength_label.config(text="0")
        controller.stop_continuous()
        
        # Stop pattern playback
        self.pattern_running = False
        
        # Update status
        self.status_label.config(text="🛑 Stopped")
        
        # Reset to ready after short delay
        self.root.after(1000, lambda: self.status_label.config(text="🟢 Ready"))

    def play_selected_pattern(self, event=None):
        """
        Play the selected pattern from the listbox
        
        Args:
            event: Optional event parameter (for event binding)
        """
        selection = self.pattern_listbox.curselection()
        if not selection:
            return
        
        name = self.pattern_listbox.get(selection[0])
        sequence = pattern_manager.patterns.get(name, [])
        
        # Stop any currently running pattern
        self.pattern_running = False
        if self.pattern_thread and self.pattern_thread.is_alive():
            time.sleep(0.1)
        
        def run_pattern():
            """Pattern execution function running in separate thread"""
            self.pattern_running = True
            self.root.after(0, lambda: self.status_label.config(text="🎵 Playing Pattern"))
            
            # Loop through pattern sequence while pattern is active
            while self.pattern_running:
                for strength, duration in sequence:
                    if not self.pattern_running:
                        break
                    controller.send_command(strength, duration)
            
            # Send stop command when pattern ends
            controller.send_command(0, 0.05)
            self.root.after(0, lambda: self.status_label.config(text="🟢 Ready"))
        
        # Start pattern in separate thread
        self.pattern_thread = threading.Thread(target=run_pattern, daemon=True)
        self.pattern_thread.start()

    def run(self):
        """Start the GUI main loop"""
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self.root.mainloop()


class RequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the vibration control API
    
    Handles GET requests to control vibration toys via HTTP endpoints.
    """
    
    def _set_headers(self, status=200):
        """Set standard HTTP response headers"""
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # Match API endpoint pattern: /API/{strength}-{duration}{unit}
        api_match = re.match(r'/API/(\d+)-(\d+(?:\.\d+)?)(ms|s)', path)
        if api_match:
            strength = int(api_match.group(1))
            duration_val = float(api_match.group(2))
            duration_unit = api_match.group(3)

            # Convert duration to seconds
            duration = duration_val if duration_unit == 's' else duration_val / 1000.0
            # Clamp strength to valid range (0-9)
            strength = max(0, min(9, strength))

            try:
                # Send command to controller
                controller.send_command(strength, duration)
                self._set_headers()
                response = {"status": "ok", "strength": strength, "duration": f"{duration_val}{duration_unit}"}
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return
            except Exception as e:
                # Return error response
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        # Default response with API usage information
        self._set_headers()
        response = {"status": "ready", "usage": "GET /API/{strength}-{duration}{unit}"}
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress default HTTP server logging"""
        pass


def run_server(port=4545):
    """
    Run HTTP server in background thread
    
    Args:
        port (int): Port number to listen on (default: 4545)
    """
    server_address = ("", port)
    httpd = HTTPServer(server_address, RequestHandler)
    try:
        httpd.serve_forever()
    except:
        pass
    httpd.server_close()


def main():
    """
    Main application entry point
    
    Starts the HTTP server in background and launches the GUI.
    """
    # Start HTTP server in daemon thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Launch GUI (main thread)
    gui = TkinterGUI()
    gui.run()


if __name__ == "__main__":
    main()