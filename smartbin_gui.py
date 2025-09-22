#!/usr/bin/env python3
"""
SmartBin Modern GUI Application
A modern CustomTkinter interface for the SmartBin PySerial Bluetooth protocol
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext, simpledialog
import threading
import queue
import time
import base64
import io
import json
import os
from datetime import datetime, timedelta
from PIL import Image, ImageTk
from typing import Optional, Dict, Any, Tuple
import serial
import subprocess

# Import our existing protocol
from smartbin_pyserial_protocol import SmartBinPySerialProtocol

class SmartBinGUI:
    def __init__(self):
        # Set appearance and theme
        ctk.set_appearance_mode("dark")  # "dark" or "light"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        # Main window
        self.root = ctk.CTk()
        self.root.title("🤖 SmartBin Control Center")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Communication protocol
        self.protocol = None
        self.protocol_thread = None
        self.running = False
        self.connected = False
        self.reconnect_attempts = 0
        self.auto_reconnect = True  # Enable automatic reconnection
        self.max_reconnect_interval = 30  # Max delay between attempts (seconds)
        self.sudo_password = None  # Stored sudo password for session
        
        # GUI state
        self.current_image = None
        self.classification_data = {}
        self.message_queue = queue.Queue()
        
        # Persistent stats
        self.session_start_time = datetime.now()
        self.total_items_processed = 0
        self.connection_uptime = timedelta()
        self.last_connection_time = None
        
        # Bin stats (persistent across sessions) - Updated for 9-class binary system
        self.bin_stats = {
            0: {"count": 0, "weight": 0.0, "last_updated": None},  # Recyclable bin
            1: {"count": 0, "weight": 0.0, "last_updated": None},  # Non-recyclable bin
        }
        
        # System stats
        self.system_stats = {
            "coins_dispensed": 0,
            "total_classifications": 0,
            "successful_connections": 0,
            "connection_failures": 0,
            "last_maintenance": None
        }
        
        # Load persistent stats
        self._load_persistent_stats()
        
        # Initialize GUI
        self._setup_gui()
        
        # Request sudo password at startup (mandatory)
        if not self._request_startup_sudo_password():
            print("❌ Sudo password required for SmartBin operation")
            self.root.destroy()
            return
        
        self._setup_protocol_integration()
        
        # Start GUI update loop
        self._start_gui_updates()
        
        # Start stats update loop
        self._start_stats_updates()
    
    def _setup_gui(self):
        """Setup the main GUI layout"""
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=2)  # Top section (image + classification)
        self.root.grid_rowconfigure(1, weight=3)  # Middle section (message log) - resizable
        self.root.grid_rowconfigure(2, weight=0)  # Bottom section (controls)
        
        # Top section: Image and Classification
        self._create_top_section()
        
        # Create a resizable splitter for message section
        self.main_paned = tk.PanedWindow(
            self.root, 
            orient=tk.VERTICAL, 
            sashwidth=8,
            sashrelief=tk.RAISED,
            bg="#2b2b2b"
        )
        self.main_paned.grid(row=1, column=0, sticky="nsew", padx=10)
        
        # Dummy frame for the splitter (we'll add the message section to this)
        self.splitter_top = ctk.CTkFrame(self.main_paned)
        self.splitter_bottom = ctk.CTkFrame(self.main_paned)
        
        # Add frames to the paned window
        self.main_paned.add(self.splitter_top, height=100)  # Minimum height
        self.main_paned.add(self.splitter_bottom, height=300)  # Message log area
        
        # Middle section: Message log (in the bottom part of splitter)
        self._create_message_section()
        
        # Bottom section: Controls
        self._create_control_section()
    
    def _create_top_section(self):
        """Create the top section with image, classification, and bin status"""
        # Main top frame
        self.top_frame = ctk.CTkFrame(self.root)
        self.top_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")
        
        # Configure top frame grid
        self.top_frame.grid_columnconfigure(0, weight=2)  # Image area
        self.top_frame.grid_columnconfigure(1, weight=1)  # Classification area
        self.top_frame.grid_columnconfigure(2, weight=1)  # Bin status area
        
        # Left: Image preview
        self._create_image_section()
        
        # Middle: Classification results
        self._create_classification_section()
        
        # Right: Bin status visualization
        self._create_bin_status_section()
    
    def _create_image_section(self):
        """Create the image preview section"""
        self.image_frame = ctk.CTkFrame(self.top_frame)
        self.image_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        
        # Image title
        self.image_title = ctk.CTkLabel(
            self.image_frame, 
            text="🖼️ Last Captured Image",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.image_title.pack(pady=(10, 5))
        
        # Image display
        self.image_label = ctk.CTkLabel(
            self.image_frame,
            text="No image captured yet",
            width=400,
            height=300,
            fg_color=("gray75", "gray25")
        )
        self.image_label.pack(pady=10, padx=10)
        
        # Image info
        self.image_info = ctk.CTkLabel(
            self.image_frame,
            text="Size: - | Format: - | Timestamp: -",
            font=ctk.CTkFont(size=12)
        )
        self.image_info.pack(pady=(0, 10))
    
    def _create_classification_section(self):
        """Create the classification results section"""
        self.classification_frame = ctk.CTkFrame(self.top_frame)
        self.classification_frame.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")
        
        # Classification title
        self.classification_title = ctk.CTkLabel(
            self.classification_frame,
            text="📊 Classification Results",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.classification_title.pack(pady=(10, 5))
        
        # Classification results area
        self.classification_results = ctk.CTkFrame(self.classification_frame)
        self.classification_results.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Default classification display
        self.no_classification_label = ctk.CTkLabel(
            self.classification_results,
            text="No classification data\nyet available",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray60")
        )
        self.no_classification_label.pack(expand=True)
    
    def _create_bin_status_section(self):
        """Create the bin status visualization section"""
        self.bin_status_frame = ctk.CTkFrame(self.top_frame)
        self.bin_status_frame.grid(row=0, column=2, padx=(5, 10), pady=10, sticky="nsew")
        
        # Bin status title
        self.bin_status_title = ctk.CTkLabel(
            self.bin_status_frame,
            text="🗂️ Bin Status",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.bin_status_title.pack(pady=(10, 5))
        
        # Bin status grid
        self.bin_grid = ctk.CTkFrame(self.bin_status_frame)
        self.bin_grid.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Initialize bin counts for 9-class system with binary mapping
        self.bin_counts = {
            # Recyclable materials
            "aluminium": 0,
            "carton": 0,
            "glass": 0,
            "paper_and_cardboard": 0,
            "plastic": 0,
            # Non-recyclable materials  
            "ewaste": 0,
            "organic_waste": 0,
            "textile": 0,
            "wood": 0
        }
        self.bin_capacity = 10
        self.coin_count = 7
        self.coin_capacity = 10
        
        self._create_bin_visualizations()
    
    def _create_bin_visualizations(self):
        """Create the bin and coin visualizations for 9-class system"""
        # Recyclable bin info
        recyclable_info = {
            "aluminium": {"emoji": "🥤", "color": "#C0C0C0"},
            "carton": {"emoji": "📦", "color": "#8D6E63"},
            "glass": {"emoji": "🍾", "color": "#4CAF50"}, 
            "paper_and_cardboard": {"emoji": "📄", "color": "#FF9800"},
            "plastic": {"emoji": "🥤", "color": "#2196F3"}
        }
        
        # Non-recyclable bin info
        non_recyclable_info = {
            "ewaste": {"emoji": "💻", "color": "#9C27B0"},
            "organic_waste": {"emoji": "🍎", "color": "#795548"},
            "textile": {"emoji": "�", "color": "#E91E63"},
            "wood": {"emoji": "🪵", "color": "#6D4C41"}
        }
        
        # Create recyclable section
        recyclable_frame = ctk.CTkFrame(self.bin_grid)
        recyclable_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        recyclable_title = ctk.CTkLabel(
            recyclable_frame,
            text="♻️ Recyclable Materials",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4CAF50"
        )
        recyclable_title.pack(pady=(5, 2))
        
        # Recyclable items grid
        recyclable_grid = ctk.CTkFrame(recyclable_frame)
        recyclable_grid.pack(fill="x", padx=5, pady=5)
        
        for i, (waste_type, info) in enumerate(recyclable_info.items()):
            row = i // 3
            col = i % 3
            
            item_frame = ctk.CTkFrame(recyclable_grid, width=80, height=60)
            item_frame.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            item_frame.grid_propagate(False)
            
            # Configure grid weights
            recyclable_grid.grid_rowconfigure(row, weight=1)
            recyclable_grid.grid_columnconfigure(col, weight=1)
            
            # Item emoji and label
            item_label = ctk.CTkLabel(
                item_frame,
                text=f"{info['emoji']}\n{waste_type.replace('_', ' ').title()[:8]}",
                font=ctk.CTkFont(size=10, weight="bold")
            )
            item_label.pack(pady=2)
            
            # Count label
            count_label = ctk.CTkLabel(
                item_frame,
                text=f"{self.bin_counts[waste_type]}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=info['color']
            )
            count_label.pack(pady=2)
            
            # Store references for updates
            setattr(self, f"{waste_type}_count_label", count_label)
        
        # Create non-recyclable section
        non_recyclable_frame = ctk.CTkFrame(self.bin_grid)
        non_recyclable_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        non_recyclable_title = ctk.CTkLabel(
            non_recyclable_frame,
            text="🗑️ Non-Recyclable Materials",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F44336"
        )
        non_recyclable_title.pack(pady=(5, 2))
        
        # Non-recyclable items grid
        non_recyclable_grid = ctk.CTkFrame(non_recyclable_frame)
        non_recyclable_grid.pack(fill="x", padx=5, pady=5)
        
        for i, (waste_type, info) in enumerate(non_recyclable_info.items()):
            row = i // 2
            col = i % 2
            
            item_frame = ctk.CTkFrame(non_recyclable_grid, width=120, height=60)
            item_frame.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            item_frame.grid_propagate(False)
            
            # Configure grid weights
            non_recyclable_grid.grid_rowconfigure(row, weight=1)
            non_recyclable_grid.grid_columnconfigure(col, weight=1)
            
            # Item emoji and label
            item_label = ctk.CTkLabel(
                item_frame,
                text=f"{info['emoji']}\n{waste_type.replace('_', ' ').title()}",
                font=ctk.CTkFont(size=10, weight="bold")
            )
            item_label.pack(pady=2)
            
            # Count label
            count_label = ctk.CTkLabel(
                item_frame,
                text=f"{self.bin_counts[waste_type]}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=info['color']
            )
            count_label.pack(pady=2)
            
            # Store references for updates
            setattr(self, f"{waste_type}_count_label", count_label)
        
        # Coin dispenser display
        coin_frame = ctk.CTkFrame(self.bin_grid)
        coin_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        coin_label = ctk.CTkLabel(
            coin_frame,
            text="🪙 Coin Dispenser",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        coin_label.pack(pady=(5, 2))
        
        self.coin_progress = ctk.CTkProgressBar(
            coin_frame,
            width=160,
            height=12,
            progress_color="#FFD700"
        )
        self.coin_progress.pack(pady=2)
        self.coin_progress.set(self.coin_count / self.coin_capacity)
        
        self.coin_count_label = ctk.CTkLabel(
            coin_frame,
            text=f"{self.coin_count}/{self.coin_capacity} coins",
            font=ctk.CTkFont(size=12)
        )
        self.coin_count_label.pack(pady=(2, 5))
    
    def _create_message_section(self):
        """Create the message log section"""
        # Message frame (in the bottom part of the splitter)
        self.message_frame = self.splitter_bottom
        
        # Message title and controls
        self.message_header = ctk.CTkFrame(self.message_frame)
        self.message_header.pack(fill="x", padx=10, pady=(10, 5))
        
        self.message_title = ctk.CTkLabel(
            self.message_header,
            text="💬 Communication Log",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.message_title.pack(side="left")
        
        # Clear log button
        self.clear_log_btn = ctk.CTkButton(
            self.message_header,
            text="🗑️ Clear",
            width=80,
            command=self._clear_message_log
        )
        self.clear_log_btn.pack(side="right", padx=(5, 0))
        
        # Auto-scroll toggle
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        self.auto_scroll_cb = ctk.CTkCheckBox(
            self.message_header,
            text="Auto-scroll",
            variable=self.auto_scroll_var
        )
        self.auto_scroll_cb.pack(side="right", padx=(5, 5))
        
        # Message log (using tkinter Text widget for better performance)
        self.message_log = scrolledtext.ScrolledText(
            self.message_frame,
            height=15,
            font=("Consolas", 11),
            bg="#2b2b2b",
            fg="#ffffff",
            insertbackground="#ffffff",
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.message_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Configure text tags for colored messages
        self.message_log.tag_configure("sent", foreground="#4CAF50")      # Green
        self.message_log.tag_configure("received", foreground="#2196F3")   # Blue
        self.message_log.tag_configure("error", foreground="#F44336")      # Red
        self.message_log.tag_configure("info", foreground="#FFC107")       # Amber
        self.message_log.tag_configure("timestamp", foreground="#9E9E9E")  # Gray
    
    def _create_control_section(self):
        """Create the bottom control section"""
        # Control frame
        self.control_frame = ctk.CTkFrame(self.root)
        self.control_frame.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
        
        # Connection controls
        self.connection_frame = ctk.CTkFrame(self.control_frame)
        self.connection_frame.pack(fill="x", padx=10, pady=10)
        
        # Connection status
        self.status_label = ctk.CTkLabel(
            self.connection_frame,
            text="🔴 Disconnected",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.status_label.pack(side="left", padx=(0, 10))
        
        # Connect/Disconnect button
        self.connect_btn = ctk.CTkButton(
            self.connection_frame,
            text="🔗 Connect",
            command=self._toggle_connection,
            width=120
        )
        self.connect_btn.pack(side="left", padx=(0, 10))
        
        # Auto-reconnect toggle
        self.auto_reconnect_var = ctk.BooleanVar(value=True)
        self.auto_reconnect_switch = ctk.CTkSwitch(
            self.connection_frame,
            text="Auto-Reconnect",
            variable=self.auto_reconnect_var,
            command=self._toggle_auto_reconnect
        )
        self.auto_reconnect_switch.pack(side="left", padx=(0, 20))
        
        # ESP32 MAC input
        self.mac_label = ctk.CTkLabel(self.connection_frame, text="ESP32 MAC:")
        self.mac_label.pack(side="left", padx=(20, 5))
        
        self.mac_entry = ctk.CTkEntry(
            self.connection_frame,
            placeholder_text="EC:E3:34:15:F2:62",
            width=150
        )
        self.mac_entry.pack(side="left", padx=(0, 10))
        self.mac_entry.insert(0, "EC:E3:34:15:F2:62")  # Default MAC
        
        # Manual command section
        self.command_frame = ctk.CTkFrame(self.control_frame)
        self.command_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.command_label = ctk.CTkLabel(
            self.command_frame,
            text="📤 Send Command:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.command_label.pack(side="left", padx=(0, 10))
        
        # Command input
        self.command_entry = ctk.CTkEntry(
            self.command_frame,
            placeholder_text="Enter command (e.g., RTC00)",
            width=200
        )
        self.command_entry.pack(side="left", padx=(0, 10))
        self.command_entry.bind("<Return>", lambda e: self._send_manual_command())
        
        # Send button
        self.send_btn = ctk.CTkButton(
            self.command_frame,
            text="📤 Send",
            command=self._send_manual_command,
            width=80
        )
        self.send_btn.pack(side="left", padx=(0, 10))
        
        # Quick commands - organized by category
        
        # Hardware control commands frame
        hardware_frame = ctk.CTkFrame(self.command_frame)
        hardware_frame.pack(fill="x", pady=(10, 5))
        
        hardware_label = ctk.CTkLabel(hardware_frame, text="🔧 Hardware Control", font=ctk.CTkFont(weight="bold"))
        hardware_label.pack(pady=(5, 5))
        
        # Row 1: Basic commands
        basic_frame = ctk.CTkFrame(hardware_frame)
        basic_frame.pack(fill="x", padx=5, pady=2)
        
        basic_commands = [
            ("🤝 Send Hello", "RTC00"),
            ("📷 Request Image", "IMG01"),
            ("🔄 Status", "STA01")
        ]
        
        for text, cmd in basic_commands:
            btn = ctk.CTkButton(
                basic_frame,
                text=text,
                command=lambda c=cmd: self._send_quick_command(c),
                width=100
            )
            btn.pack(side="left", padx=2, pady=2)
        
        # Row 2: Lid control
        lid_frame = ctk.CTkFrame(hardware_frame)
        lid_frame.pack(fill="x", padx=5, pady=2)
        
        lid_commands = [
            ("🔓 Open Lid", "LID00 open"),
            ("🔒 Close Lid", "LID00 close"),
            ("❓ Lid Status", "LID00 status"),
            ("🤖 Auto Lid", "LID00 auto"),
            ("✋ Manual Lid", "LID00 manual")
        ]
        
        for text, cmd in lid_commands:
            btn = ctk.CTkButton(
                lid_frame,
                text=text,
                command=lambda c=cmd: self._send_quick_command(c),
                width=100
            )
            btn.pack(side="left", padx=2, pady=2)
        
        # Row 3: Coin dispenser
        coin_frame = ctk.CTkFrame(hardware_frame)
        coin_frame.pack(fill="x", padx=5, pady=2)
        
        coin_commands = [
            ("🪙 Dispense Coin", "COIN0 dispense"),
            ("🪙💰 Dispense 3", "COIN0 dispense --count 3"),
            ("📊 Coin Status", "COIN0 status"),
            ("🔧 Test Dispenser", "COIN0 test")
        ]
        
        for text, cmd in coin_commands:
            btn = ctk.CTkButton(
                coin_frame,
                text=text,
                command=lambda c=cmd: self._send_quick_command(c),
                width=100
            )
            btn.pack(side="left", padx=2, pady=2)
        
        # Row 4: Buzzer control
        buzzer_frame = ctk.CTkFrame(hardware_frame)
        buzzer_frame.pack(fill="x", padx=5, pady=2)
        
        buzzer_commands = [
            ("🔊 Startup Sound", "BUZZ0 startup"),
            ("📦 Item Detected", "BUZZ0 detected"),
            ("✅ Sort Complete", "BUZZ0 complete"),
            ("🚨 Error Sound", "BUZZ0 error"),
            ("🔇 Buzzer Off", "BUZZ0 off")
        ]
        
        for text, cmd in buzzer_commands:
            btn = ctk.CTkButton(
                buzzer_frame,
                text=text,
                command=lambda c=cmd: self._send_quick_command(c),
                width=100
            )
            btn.pack(side="left", padx=2, pady=2)
    
    def _setup_protocol_integration(self):
        """Setup integration with the PySerial protocol"""
        # Create a custom protocol class that sends messages to GUI
        class GUIProtocol(SmartBinPySerialProtocol):
            def __init__(self, gui_instance, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.gui = gui_instance
            
            def _setup_rfcomm_binding(self) -> bool:
                """Setup RFCOMM binding with GUI password prompt"""
                try:
                    self.gui.message_queue.put({
                        'type': 'info',
                        'message': f"Setting up Bluetooth connection to {self.esp32_mac}...",
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })
                    
                    # First, try to release any existing binding
                    try:
                        release_cmd = ["sudo", "rfcomm", "release", "0"]
                        subprocess.run(release_cmd, capture_output=True, text=True, timeout=5)
                    except:
                        pass
                    
                    # Get password from GUI
                    password = self.gui._get_sudo_password()
                    if not password:
                        self.gui.message_queue.put({
                            'type': 'error',
                            'message': "Password required for Bluetooth setup",
                            'timestamp': datetime.now().strftime("%H:%M:%S")
                        })
                        return False
                    
                    # Bind the device with password
                    bind_cmd = ["sudo", "-S", "rfcomm", "bind", "0", self.esp32_mac, "1"]
                    bind_process = subprocess.Popen(
                        bind_cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    stdout, stderr = bind_process.communicate(input=password + "\n", timeout=10)
                    
                    if bind_process.returncode != 0:
                        self.gui.message_queue.put({
                            'type': 'error',
                            'message': f"Failed to bind RFCOMM: {stderr}",
                            'timestamp': datetime.now().strftime("%H:%M:%S")
                        })
                        return False
                    
                    self.rfcomm_bound = True
                    self.gui.message_queue.put({
                        'type': 'info',
                        'message': f"✅ RFCOMM device bound to {self.rfcomm_device}",
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })
                    
                    time.sleep(1)
                    return True
                    
                except Exception as e:
                    self.gui.message_queue.put({
                        'type': 'error',
                        'message': f"Failed to setup RFCOMM binding: {e}",
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })
                    return False
            
            def _process_line(self, line: str):
                """Override to send messages to GUI"""
                # Send to GUI message queue
                self.gui.message_queue.put({
                    'type': 'received',
                    'message': line,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
                
                # Call parent method for protocol handling
                super()._process_line(line)
            
            def _send_message(self, code: str, content: str = "") -> bool:
                """Override to log sent messages to GUI"""
                message = f"{code} {content}".strip()
                
                # Send to GUI message queue
                self.gui.message_queue.put({
                    'type': 'sent',
                    'message': message,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
                
                # Call parent method
                return super()._send_message(code, content)
            
            def _handle_protocol_message(self, code: str, content: str):
                """Override to handle GUI-specific protocol messages"""
                # Send protocol message to GUI
                self.gui.message_queue.put({
                    'type': 'protocol',
                    'code': code,
                    'content': content,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
                
                # Call parent method
                super()._handle_protocol_message(code, content)
            
            def _process_complete_image(self):
                """Override to send image data to GUI"""
                try:
                    # Reconstruct image (same as parent)
                    base64_data = ""
                    for i in range(1, self.expected_parts + 1):
                        if i in self.image_parts:
                            base64_data += self.image_parts[i]
                        else:
                            self.gui.message_queue.put({
                                'type': 'error',
                                'message': f"Missing image part {i}",
                                'timestamp': datetime.now().strftime("%H:%M:%S")
                            })
                            return
                    
                    # Decode image
                    image_data = base64.b64decode(base64_data)
                    image = Image.open(io.BytesIO(image_data))
                    
                    # Send image to GUI
                    self.gui.message_queue.put({
                        'type': 'image',
                        'image': image,
                        'metadata': self.image_metadata.copy(),
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })
                    
                    # Perform classification using YOLO backend
                    classification_result = self._classify_with_yolo_backend(image)
                    
                    if classification_result["success"]:
                        classification = classification_result["result"]
                        confidence = classification_result["confidence"]
                        all_classes = classification_result["all_confidences"]
                        
                        # Print raw YOLO backend results to console
                        print(f"\n🤖 YOLO BACKEND RAW RESULTS:")
                        print(f"   Top Class: {classification}")
                        print(f"   Confidence: {confidence:.4f}")
                        print(f"   All Classes: {all_classes}")
                        
                        # Send classification to GUI (full detailed result)
                        self.gui.message_queue.put({
                            'type': 'classification',
                            'result': classification,
                            'confidence': confidence,
                            'all_classes': all_classes,
                            'timestamp': datetime.now().strftime("%H:%M:%S")
                        })
                        
                        # Map 9-class classification to binary for ESP32
                        recyclable_classes = {
                            'aluminium', 'carton', 'glass', 
                            'paper_and_cardboard', 'plastic'
                        }
                        
                        # Determine if item is recyclable
                        if classification.lower() in recyclable_classes:
                            binary_result = "recyclable"
                        else:
                            binary_result = "non-recyclable"
                        
                        # Send binary classification result to ESP32
                        esp32_command = f"{binary_result} {confidence:.2f}"
                        if self._send_message("CLS01", esp32_command):
                            self.gui.message_queue.put({
                                'type': 'info',
                                'message': f"✅ Sent to ESP32: {esp32_command} (from {classification})",
                                'timestamp': datetime.now().strftime("%H:%M:%S")
                            })
                    else:
                        # Classification failed - no fallback
                        error_msg = classification_result.get('error', 'Unknown classification error')
                        self.gui.message_queue.put({
                            'type': 'error',
                            'message': f"❌ YOLO classification FAILED: {error_msg}",
                            'timestamp': datetime.now().strftime("%H:%M:%S")
                        })
                        
                        # Send error to ESP32
                        if self._send_message("CLS01", "ERROR 0.00"):
                            self.gui.message_queue.put({
                                'type': 'info', 
                                'message': f"🚨 Sent ERROR status to ESP32",
                                'timestamp': datetime.now().strftime("%H:%M:%S")
                            })
                
                except Exception as e:
                    self.gui.message_queue.put({
                        'type': 'error',
                        'message': f"Image processing error: {e}",
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })
                
                finally:
                    # Reset state
                    self.waiting_for_image = False
                    self.image_metadata = {}
                    self.image_parts = {}
                    self.expected_parts = 0
            
            def _classify_with_yolo_backend(self, image: Image.Image) -> Dict[str, Any]:
                """Classify image using the YOLO backend script"""
                try:
                    import subprocess
                    import tempfile
                    import os
                    
                    # Save image to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                        image.save(tmp_file.name, 'JPEG')
                        tmp_path = tmp_file.name
                    
                    try:
                        # Call the YOLO backend script with virtual environment python
                        venv_python = ".venv/bin/python"
                        cmd = [
                            venv_python, "yolo_classification_backend.py",
                            "--model", "runs/smartbin_9class/weights/best.pt",
                            "--image", tmp_path,
                            "--json"
                        ]
                        
                        self.gui.message_queue.put({
                            'type': 'info',
                            'message': f"🔄 Running YOLO classification: {' '.join(cmd)}",
                            'timestamp': datetime.now().strftime("%H:%M:%S")
                        })
                        
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        
                        if result.returncode == 0:
                            # Parse JSON result
                            import json
                            if result.stdout.strip():  # Check if output is not empty
                                self.gui.message_queue.put({
                                    'type': 'info',
                                    'message': f"✅ YOLO backend output received: {len(result.stdout)} characters",
                                    'timestamp': datetime.now().strftime("%H:%M:%S")
                                })
                                classification_data = json.loads(result.stdout)
                                return classification_data
                            else:
                                return {
                                    "success": False,
                                    "error": "Backend script returned empty output"
                                }
                        else:
                            error_msg = f"Backend script error (exit code {result.returncode}): {result.stderr}"
                            self.gui.message_queue.put({
                                'type': 'error',
                                'message': f"❌ YOLO backend failed: {error_msg}",
                                'timestamp': datetime.now().strftime("%H:%M:%S")
                            })
                            return {
                                "success": False,
                                "error": error_msg
                            }
                    
                    finally:
                        # Clean up temporary file
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass
                
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"YOLO backend integration error: {e}"
                    }
        
        self.protocol_class = GUIProtocol
    
    def _get_sudo_password(self) -> Optional[str]:
        """Get sudo password - uses stored password from startup"""
        try:
            # Return the password that was verified at startup
            if hasattr(self, 'sudo_password') and self.sudo_password:
                return self.sudo_password
            else:
                # Fallback to dialog if somehow not set
                from tkinter import messagebox
                messagebox.showerror(
                    "Password Not Available",
                    "Administrator password was not set during startup.\n"
                    "Please restart the application."
                )
                return None
        except Exception:
            return None
    
    def _request_startup_sudo_password(self) -> bool:
        """Request sudo password at startup - mandatory for operation"""
        try:
            # Show info dialog first
            from tkinter import messagebox
            messagebox.showinfo(
                "SmartBin Initialization",
                "SmartBin requires administrator privileges to configure Bluetooth connections.\n\n"
                "You will be prompted for your password to set up RFCOMM bindings.\n"
                "This is required for ESP32 communication."
            )
            
            # Request password
            password = simpledialog.askstring(
                "Administrator Password Required",
                "Enter your password to initialize SmartBin:\n"
                "(This will be used for Bluetooth setup throughout the session)",
                show='*'
            )
            
            if not password:
                messagebox.showerror(
                    "Password Required",
                    "Administrator password is required for SmartBin to function.\n"
                    "The application will now exit."
                )
                return False
            
            # Test the password by running a simple sudo command
            import subprocess
            test_cmd = f"echo '{password}' | sudo -S echo 'Password verified'"
            try:
                result = subprocess.run(
                    test_cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                if result.returncode != 0:
                    messagebox.showerror(
                        "Invalid Password",
                        "The password you entered is incorrect.\n"
                        "Please restart the application and try again."
                    )
                    return False
                
                # Store password for session (encrypted in memory)
                self.sudo_password = password
                
                messagebox.showinfo(
                    "Password Verified",
                    "Administrator password verified successfully!\n"
                    "SmartBin is ready to initialize Bluetooth connections."
                )
                
                return True
                
            except subprocess.TimeoutExpired:
                messagebox.showerror(
                    "Password Verification Timeout",
                    "Password verification timed out.\n"
                    "Please restart the application and try again."
                )
                return False
            except Exception as e:
                messagebox.showerror(
                    "Password Verification Error",
                    f"Failed to verify password: {e}\n"
                    "Please restart the application and try again."
                )
                return False
                
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror(
                "Startup Error",
                f"Failed to request password: {e}\n"
                "The application will now exit."
            )
            return False
    
    def _start_gui_updates(self):
        """Start the GUI update loop"""
        self._update_gui()
    
    def _update_gui(self):
        """Update GUI with messages from the queue"""
        try:
            # Process all messages in queue
            while not self.message_queue.empty():
                message_data = self.message_queue.get_nowait()
                self._handle_gui_message(message_data)
        except queue.Empty:
            pass
        
        # Schedule next update
        self.root.after(100, self._update_gui)
    
    def _handle_gui_message(self, data: Dict[str, Any]):
        """Handle different types of messages from the protocol"""
        msg_type = data['type']
        timestamp = data['timestamp']
        
        if msg_type == 'sent':
            self._add_message(f"[{timestamp}] ➡️ SENT: {data['message']}", "sent")
        
        elif msg_type == 'received':
            self._add_message(f"[{timestamp}] ⬅️ RECV: {data['message']}", "received")
        
        elif msg_type == 'protocol':
            self._add_message(f"[{timestamp}] 🔧 PROTOCOL: {data['code']} {data['content']}", "info")
        
        elif msg_type == 'error':
            self._add_message(f"[{timestamp}] ❌ ERROR: {data['message']}", "error")
        
        elif msg_type == 'info':
            self._add_message(f"[{timestamp}] ℹ️ INFO: {data['message']}", "info")
        
        elif msg_type == 'image':
            self._update_image_display(data['image'], data['metadata'], timestamp)
        
        elif msg_type == 'classification':
            self._update_classification_display(
                data['result'], 
                data['confidence'], 
                data['all_classes'], 
                timestamp
            )
            # Also update bin counts when classification happens
            self._update_bin_count(data['result'])
    
    def _update_bin_count(self, classified_item: str):
        """Update bin count when an item is classified (9-class system)"""
        if classified_item in self.bin_counts:
            # Increment the count
            self.bin_counts[classified_item] += 1
            
            # Update the visual display
            count_label = getattr(self, f"{classified_item}_count_label", None)
            if count_label:
                count_label.configure(text=f"{self.bin_counts[classified_item]}")
            
            # Check if item is recyclable for coin dispensing
            recyclable_classes = {
                'aluminium', 'carton', 'glass', 
                'paper_and_cardboard', 'plastic'
            }
            
            if classified_item.lower() in recyclable_classes:
                # Simulate coin dispensing (decrease coin count)
                if self.coin_count > 0:
                    self.coin_count -= 1
                    self.coin_progress.set(self.coin_count / self.coin_capacity)
                    self.coin_count_label.configure(text=f"{self.coin_count}/{self.coin_capacity} coins")
                    coin_msg = f" | Coin dispensed! Remaining: {self.coin_count}"
                else:
                    coin_msg = " | No coins left to dispense!"
            else:
                coin_msg = " | Non-recyclable (no coin)"
            
            self._add_message(f"[BIN UPDATE] {classified_item.replace('_', ' ').title()}: {self.bin_counts[classified_item]}{coin_msg}", "info")
    
    def _update_bin_visualization(self):
        """Update bin visualization with persistent stats for 9-class system"""
        try:
            # Update counts from bin_counts dictionary
            for waste_type, count in self.bin_counts.items():
                count_label = getattr(self, f"{waste_type}_count_label", None)
                if count_label:
                    count_label.configure(text=f"{count}")
            
            # Update coin display (simulate based on recyclable items processed)
            recyclable_classes = {
                'aluminium', 'carton', 'glass', 
                'paper_and_cardboard', 'plastic'
            }
            recyclable_count = sum(self.bin_counts[cls] for cls in recyclable_classes if cls in self.bin_counts)
            coins_used = min(recyclable_count, self.coin_capacity)  # 1 coin per recyclable item
            self.coin_count = max(0, self.coin_capacity - coins_used)
            
            if hasattr(self, 'coin_progress'):
                self.coin_progress.set(self.coin_count / self.coin_capacity)
                self.coin_count_label.configure(text=f"{self.coin_count}/{self.coin_capacity} coins")
                
        except Exception as e:
            # Silently fail for missing visual elements during initialization
            pass
    
    def _add_message(self, message: str, tag: str = ""):
        """Add a message to the log"""
        self.message_log.config(state=tk.NORMAL)
        self.message_log.insert(tk.END, message + "\n", tag)
        self.message_log.config(state=tk.DISABLED)
        
        # Auto-scroll if enabled
        if self.auto_scroll_var.get():
            self.message_log.see(tk.END)
    
    def _update_image_display(self, image: Image.Image, metadata: Dict, timestamp: str):
        """Update the image display"""
        try:
            # Store original image
            self.current_image = image.copy()
            
            # Resize for display (maintain aspect ratio)
            display_size = (400, 300)
            image_display = image.copy()
            image_display.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image_display)
            
            # Update label
            self.image_label.configure(image=photo, text="")
            self.image_label.image = photo  # Keep a reference
            
            # Update image info
            info_text = f"Size: {image.size[0]}x{image.size[1]} | Format: {image.format or 'Unknown'} | Time: {timestamp}"
            self.image_info.configure(text=info_text)
            
            self._add_message(f"[{timestamp}] 🖼️ IMAGE: Received {image.size[0]}x{image.size[1]} image", "info")
            
        except Exception as e:
            self._add_message(f"[{timestamp}] ❌ ERROR: Failed to display image: {e}", "error")
    
    def _update_classification_display(self, result: str, confidence: float, all_classes: Dict[str, float], timestamp: str):
        """Update the classification results display"""
        try:
            # ======= DETAILED CONSOLE OUTPUT =======
            print(f"\n{'='*60}")
            print(f"🔍 DETAILED CLASSIFICATION RESULTS [{timestamp}]")
            print(f"{'='*60}")
            print(f"📊 Top Prediction: {result} ({confidence*100:.2f}%)")
            print(f"📋 All Class Confidences:")
            
            # Sort classes by confidence for console display
            sorted_classes = sorted(all_classes.items(), key=lambda x: x[1], reverse=True)
            
            # Print all classes with confidences
            for i, (class_name, conf) in enumerate(sorted_classes):
                rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1:2d}."
                print(f"  {rank_emoji} {class_name:<20} : {conf*100:6.2f}%")
            
            # Check if class is recognized by our hard-coded system
            known_classes = set(self.bin_counts.keys())
            model_classes = set(all_classes.keys())
            
            print(f"\n🔧 System Analysis:")
            print(f"  • Known Classes (Hard-coded): {sorted(known_classes)}")
            print(f"  • Model Classes (Dynamic):    {sorted(model_classes)}")
            
            unknown_classes = model_classes - known_classes
            if unknown_classes:
                print(f"  ⚠️  Unknown Classes Detected: {sorted(unknown_classes)}")
            else:
                print(f"  ✅ All model classes are recognized by the system")
            
            # Binary mapping info
            recyclable_classes = {
                'aluminium', 'carton', 'glass', 
                'paper_and_cardboard', 'plastic'
            }
            binary_result = "RECYCLABLE" if result.lower() in recyclable_classes else "NON-RECYCLABLE"
            print(f"  🔄 Binary Mapping: {result} → {binary_result}")
            print(f"{'='*60}\n")
            
            # Update session stats with the classified item
            self._update_session_stats(result)
            
            # Clear existing widgets (but preserve the frame structure)
            for widget in self.classification_results.winfo_children():
                widget.destroy()
            
            # Ensure we have valid classification data
            if not all_classes or not result:
                # Restore default "no classification" message
                self.no_classification_label = ctk.CTkLabel(
                    self.classification_results,
                    text="No classification data\nyet available",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray60")
                )
                self.no_classification_label.pack(expand=True)
                return
            
            # Sort classes by confidence
            sorted_classes = sorted(all_classes.items(), key=lambda x: x[1], reverse=True)
            
            # Create display for each class
            for i, (class_name, conf) in enumerate(sorted_classes):
                # Class frame
                class_frame = ctk.CTkFrame(self.classification_results)
                class_frame.pack(fill="x", padx=5, pady=2)
                
                # Emoji for ranking
                emoji = ["🥇", "🥈", "🥉", "📝"][i] if i < 4 else "📝"
                
                # Class name and confidence
                class_label = ctk.CTkLabel(
                    class_frame,
                    text=f"{emoji} {class_name}: {conf*100:.1f}%",
                    font=ctk.CTkFont(size=14, weight="bold" if i == 0 else "normal")
                )
                class_label.pack(side="left", padx=10, pady=5)
                
                # Progress bar for confidence
                progress = ctk.CTkProgressBar(
                    class_frame,
                    width=150,
                    height=10
                )
                progress.pack(side="right", padx=10, pady=5)
                progress.set(conf)
            
            # Timestamp
            time_label = ctk.CTkLabel(
                self.classification_results,
                text=f"⏰ {timestamp}",
                font=ctk.CTkFont(size=12),
                text_color=("gray60", "gray40")
            )
            time_label.pack(pady=(10, 5))
            
            self._add_message(f"[{timestamp}] 🎯 CLASSIFICATION: {result} ({confidence*100:.1f}%)", "info")
            
        except Exception as e:
            self._add_message(f"[{timestamp}] ❌ ERROR: Failed to update classification: {e}", "error")
    
    def _toggle_connection(self):
        """Toggle connection to ESP32"""
        if not self.running:
            self._connect()
        else:
            self._disconnect()
    
    def _toggle_auto_reconnect(self):
        """Toggle auto-reconnect feature"""
        self.auto_reconnect = self.auto_reconnect_var.get()
        status = "enabled" if self.auto_reconnect else "disabled"
        self._add_message(f"[GUI] 🔄 Auto-reconnect {status}", "info")
        
        # If disabled while reconnecting, stop attempts
        if not self.auto_reconnect and not self.connected:
            self.status_label.configure(text="🔴 Disconnected")
            self.connect_btn.configure(text="🔗 Connect", state="normal")
    
    def _connect(self):
        """Connect to ESP32"""
        try:
            mac_address = self.mac_entry.get().strip()
            if not mac_address:
                self._add_message("[GUI] ❌ ERROR: Please enter ESP32 MAC address", "error")
                return
            
            self._add_message("[GUI] 🔗 Connecting to ESP32...", "info")
            self.status_label.configure(text="🟡 Connecting...")
            self.connect_btn.configure(text="⏳ Connecting...", state="disabled")
            
            # Enable auto-reconnect for new connections
            self.auto_reconnect = True
            self.reconnect_attempts = 0
            
            # Create protocol instance
            self.protocol = self.protocol_class(
                self,  # Pass GUI instance
                esp32_mac=mac_address,
                rfcomm_device="/dev/rfcomm0",
                baudrate=115200
            )
            
            # Start protocol in separate thread
            self.protocol_thread = threading.Thread(target=self._run_protocol, daemon=True)
            self.running = True
            self.protocol_thread.start()
            
        except Exception as e:
            self._add_message(f"[GUI] ❌ CONNECTION ERROR: {e}", "error")
            self.status_label.configure(text="🔴 Connection Failed")
            self.connect_btn.configure(text="🔗 Connect", state="normal")
    
    def _disconnect(self):
        """Disconnect from ESP32"""
        try:
            self._add_message("[GUI] 🛑 Disconnecting...", "info")
            self.running = False
            self.connected = False
            self.auto_reconnect = False  # Disable auto-reconnect on manual disconnect
            self.reconnect_attempts = 0  # Reset reconnection attempts
            
            if self.protocol:
                self.protocol.stop()
            
            if self.protocol_thread:
                self.protocol_thread.join(timeout=3)
            
            self.status_label.configure(text="🔴 Disconnected")
            self.connect_btn.configure(text="🔗 Connect", state="normal")
            
            self._add_message("[GUI] ✅ Disconnected successfully", "info")
            
        except Exception as e:
            self._add_message(f"[GUI] ❌ DISCONNECT ERROR: {e}", "error")
            self.connected = False
            self.status_label.configure(text="🔴 Disconnected")
            self.connect_btn.configure(text="🔗 Connect", state="normal")
    
    def _monitor_connection(self):
        """Monitor connection status and attempt reconnection if needed"""
        if not self.running:
            return
            
        try:
            # Check if protocol is still alive
            if self.protocol and hasattr(self.protocol, 'is_connected'):
                if not self.protocol.is_connected():
                    self._handle_disconnection()
            elif self.protocol_thread and not self.protocol_thread.is_alive():
                self._handle_disconnection()
        except Exception as e:
            self._add_message(f"[GUI] ⚠️ Connection monitoring error: {e}", "error")
        
        # Schedule next check
        if self.running and self.connected:
            self.root.after(5000, self._monitor_connection)  # Check every 5 seconds
    
    def _handle_disconnection(self):
        """Handle unexpected disconnection"""
        if not self.connected:
            return  # Already handling disconnection
            
        self.connected = False
        self._add_message("[GUI] ⚠️ Connection lost! Attempting to reconnect...", "error")
        
        if self.auto_reconnect:
            self.status_label.configure(text="🟡 Reconnecting...")
            self.connect_btn.configure(text="🔄 Auto-Reconnecting...", state="disabled")
            
            # Start reconnection attempts
            self.reconnect_attempts = 0
            self._attempt_reconnection()
        else:
            self.status_label.configure(text="🔴 Connection Lost")
            self.connect_btn.configure(text="🔗 Connect", state="normal")
            self._add_message("[GUI] ℹ️ Auto-reconnect disabled. Click Connect to reconnect manually.", "info")
    
    def _attempt_reconnection(self):
        """Attempt to reconnect to ESP32 with exponential backoff"""
        if not self.running or self.connected or not self.auto_reconnect:
            return
            
        self.reconnect_attempts += 1
        
        # Calculate delay with exponential backoff (1, 2, 4, 8, 16, 30, 30, ...)
        delay = min(2 ** min(self.reconnect_attempts - 1, 4), self.max_reconnect_interval)
        
        try:
            self._add_message(f"[GUI] 🔄 Reconnection attempt #{self.reconnect_attempts} (next in {delay}s)...", "info")
            
            # Clean up old protocol
            if self.protocol:
                try:
                    self.protocol.stop()
                except:
                    pass
            
            # Create new protocol instance
            mac_address = self.mac_entry.get().strip()
            self.protocol = self.protocol_class(
                self,
                esp32_mac=mac_address,
                rfcomm_device="/dev/rfcomm0",
                baudrate=115200
            )
            
            # Try to reconnect
            success = self.protocol.start()
            if success:
                self.connected = True
                attempts_made = self.reconnect_attempts
                self.reconnect_attempts = 0  # Reset counter on success
                self.status_label.configure(text="🟢 Reconnected")
                self.connect_btn.configure(text="🔌 Disconnect", state="normal")
                self._add_message(f"[GUI] ✅ Successfully reconnected after {attempts_made} attempts!", "info")
                self._monitor_connection()  # Resume monitoring
                return
            else:
                # Schedule next attempt with exponential backoff
                self._add_message(f"[GUI] ⚠️ Reconnect failed, retrying in {delay} seconds...", "warning")
                self.root.after(delay * 1000, self._attempt_reconnection)
                
        except Exception as e:
            self._add_message(f"[GUI] ❌ Reconnection attempt failed: {e}", "error")
            # Schedule next attempt with exponential backoff
            self.root.after(delay * 1000, self._attempt_reconnection)
    
    def _run_protocol(self):
        """Run the protocol in a separate thread"""
        try:
            self._add_message("[GUI] 🔗 Attempting to connect...", "info")
            success = self.protocol.start()
            if success:
                self.connected = True
                self.last_connection_time = datetime.now()
                self.system_stats['successful_connections'] += 1
                self.root.after(0, lambda: self.status_label.configure(text="🟢 Connected"))
                self.root.after(0, lambda: self.connect_btn.configure(text="🔌 Disconnect", state="normal"))
                self._add_message("[GUI] ✅ Successfully connected to ESP32", "info")
                
                # Start connection monitoring
                self._monitor_connection()
            else:
                self.connected = False
                self.system_stats['connection_failures'] += 1
                self.root.after(0, lambda: self.status_label.configure(text="🔴 Connection Failed"))
                self.root.after(0, lambda: self.connect_btn.configure(text="🔗 Connect", state="normal"))
                self.running = False
                self._add_message("[GUI] ❌ Failed to connect to ESP32", "error")
        except Exception as e:
            self.connected = False
            self.message_queue.put({
                'type': 'error',
                'message': f"Protocol error: {e}",
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
            self.running = False
            self.root.after(0, lambda: self.status_label.configure(text="🔴 Connection Error"))
            self.root.after(0, lambda: self.connect_btn.configure(text="🔗 Connect", state="normal"))
    
    def _send_manual_command(self):
        """Send a manual command"""
        command = self.command_entry.get().strip()
        if not command:
            return
        
        if not self.protocol or not self.running:
            self._add_message("[GUI] ❌ ERROR: Not connected to ESP32", "error")
            return
        
        try:
            # Parse command (assume format: "CODE CONTENT" or just "CODE")
            parts = command.split(' ', 1)
            code = parts[0]
            content = parts[1] if len(parts) > 1 else ""
            
            success = self.protocol._send_message(code, content)
            if not success:
                self._add_message("[GUI] ❌ ERROR: Failed to send command", "error")
            
            # Clear entry
            self.command_entry.delete(0, tk.END)
            
        except Exception as e:
            self._add_message(f"[GUI] ❌ ERROR: {e}", "error")
    
    def _send_quick_command(self, command: str):
        """Send a quick command"""
        if not self.protocol or not self.running:
            self._add_message("[GUI] ❌ ERROR: Not connected to ESP32", "error")
            return
        
        try:
            parts = command.split(' ', 1)
            code = parts[0]
            content = parts[1] if len(parts) > 1 else ""
            
            self.protocol._send_message(code, content)
        except Exception as e:
            self._add_message(f"[GUI] ❌ ERROR: {e}", "error")
    
    def _clear_message_log(self):
        """Clear the message log"""
        self.message_log.config(state=tk.NORMAL)
        self.message_log.delete(1.0, tk.END)
        self.message_log.config(state=tk.DISABLED)
        self._add_message("[GUI] 🗑️ Message log cleared", "info")
    
    def _load_persistent_stats(self):
        """Load persistent statistics from file"""
        try:
            stats_file = "smartbin_stats.json"
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                    self.bin_stats = data.get('bin_stats', self.bin_stats)
                    self.system_stats = data.get('system_stats', self.system_stats)
                    self.total_items_processed = data.get('total_items_processed', 0)
                    
                    # Convert timestamp strings back to datetime objects
                    for bin_id in self.bin_stats:
                        if self.bin_stats[bin_id]['last_updated']:
                            self.bin_stats[bin_id]['last_updated'] = datetime.fromisoformat(
                                self.bin_stats[bin_id]['last_updated']
                            )
                    
                    if self.system_stats['last_maintenance']:
                        self.system_stats['last_maintenance'] = datetime.fromisoformat(
                            self.system_stats['last_maintenance']
                        )
        except Exception as e:
            print(f"⚠️ Could not load stats: {e}")
    
    def _save_persistent_stats(self):
        """Save persistent statistics to file"""
        try:
            # Prepare data for JSON serialization
            data = {
                'bin_stats': {},
                'system_stats': self.system_stats.copy(),
                'total_items_processed': self.total_items_processed,
                'last_saved': datetime.now().isoformat()
            }
            
            # Convert datetime objects to strings
            for bin_id in self.bin_stats:
                data['bin_stats'][bin_id] = self.bin_stats[bin_id].copy()
                if data['bin_stats'][bin_id]['last_updated']:
                    data['bin_stats'][bin_id]['last_updated'] = data['bin_stats'][bin_id]['last_updated'].isoformat()
            
            if data['system_stats']['last_maintenance']:
                data['system_stats']['last_maintenance'] = data['system_stats']['last_maintenance'].isoformat()
            
            stats_file = "smartbin_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Could not save stats: {e}")
    
    def _start_stats_updates(self):
        """Start the stats update loop"""
        self._update_stats_display()
        
    def _update_stats_display(self):
        """Update the stats display in the GUI"""
        try:
            # Update uptime
            if self.connected and self.last_connection_time:
                current_uptime = datetime.now() - self.last_connection_time
                uptime_str = str(current_uptime).split('.')[0]  # Remove microseconds
            else:
                uptime_str = "Not connected"
            
            # Update title with connection status and uptime
            if self.connected:
                self.root.title(f"🤖 SmartBin Control Center - 🟢 Connected | ⏱️ {uptime_str}")
            else:
                session_time = datetime.now() - self.session_start_time
                session_str = str(session_time).split('.')[0]
                self.root.title(f"🤖 SmartBin Control Center - 🔴 Disconnected | 📊 Session: {session_str}")
            
            # Update bin status with persistent counts
            self._update_bin_visualization()
            
            # Save stats periodically
            self._save_persistent_stats()
            
        except Exception as e:
            print(f"⚠️ Stats update error: {e}")
        
        # Schedule next update
        self.root.after(1000, self._update_stats_display)  # Update every second
    
    def _update_session_stats(self, waste_type: str):
        """Update session statistics when item is classified (9-class system)"""
        try:
            # Map waste type to binary categories for persistent storage
            recyclable_classes = {
                'aluminium', 'carton', 'glass', 
                'paper_and_cardboard', 'plastic'
            }
            
            # Use binary mapping for legacy bin stats (0=recyclable, 1=non-recyclable)
            if waste_type.lower() in recyclable_classes:
                bin_id = 0  # Recyclable bin
            else:
                bin_id = 1  # Non-recyclable bin
            
            # Update bin stats
            self.bin_stats[bin_id]['count'] += 1
            self.bin_stats[bin_id]['last_updated'] = datetime.now()
            
            # Update system stats
            self.total_items_processed += 1
            self.system_stats['total_classifications'] += 1
            
            # Simulate coin dispensing for recyclable items only
            if waste_type.lower() in recyclable_classes:
                self.system_stats['coins_dispensed'] += 1
                self._add_message(f"[SYSTEM] 🪙 Coin dispensed for {waste_type}! Total: {self.system_stats['coins_dispensed']}", "info")
            
        except Exception as e:
            print(f"⚠️ Session stats update error: {e}")
    
    def _get_stats_summary(self):
        """Get a summary of current stats for display"""
        try:
            total_items = sum(self.bin_stats[i]['count'] for i in range(4))
            
            if self.connected and self.last_connection_time:
                uptime = datetime.now() - self.last_connection_time
                uptime_str = str(uptime).split('.')[0]
            else:
                uptime_str = "Not connected"
            
            return {
                'total_items': total_items,
                'items_today': self.total_items_processed,
                'coins_dispensed': self.system_stats['coins_dispensed'],
                'uptime': uptime_str,
                'connection_status': 'Connected' if self.connected else 'Disconnected',
                'bin_fullness': {
                    i: f"{self.bin_stats[i]['count']}/10" for i in range(4)
                }
            }
        except Exception as e:
            print(f"⚠️ Stats summary error: {e}")
            return {}
    
    def run(self):
        """Run the GUI application"""
        try:
            self._add_message("[GUI] 🚀 SmartBin Control Center started", "info")
            self._add_message("[GUI] 💡 Enter ESP32 MAC address and click Connect", "info")
            self._add_message("[GUI] 🔐 Administrator password verified and ready", "info")
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n🛑 GUI interrupted by user")
        finally:
            # Clear password from memory for security
            if hasattr(self, 'sudo_password'):
                self.sudo_password = None
            self._disconnect()

def main():
    """Main function"""
    print("🚀 Starting SmartBin Modern GUI...")
    
    try:
        app = SmartBinGUI()
        app.run()
    except Exception as e:
        print(f"❌ GUI Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
