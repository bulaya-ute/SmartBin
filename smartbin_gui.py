#!/usr/bin/env python3
"""
SmartBin Modern GUI Application
A modern CustomTkinter interface for the SmartBin PySerial Bluetooth protocol
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import time
import base64
import io
import json
from datetime import datetime
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
        
        # GUI state
        self.current_image = None
        self.classification_data = {}
        self.message_queue = queue.Queue()
        
        # Initialize GUI
        self._setup_gui()
        self._setup_protocol_integration()
        
        # Start GUI update loop
        self._start_gui_updates()
    
    def _setup_gui(self):
        """Setup the main GUI layout"""
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=2)  # Left side (image + controls)
        self.root.grid_columnconfigure(1, weight=1)  # Right side (classification)
        self.root.grid_rowconfigure(1, weight=1)     # Message log area
        
        # Top section: Image and Classification
        self._create_top_section()
        
        # Middle section: Message log
        self._create_message_section()
        
        # Bottom section: Controls
        self._create_control_section()
    
    def _create_top_section(self):
        """Create the top section with image and classification"""
        # Left frame: Image preview
        self.image_frame = ctk.CTkFrame(self.root)
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
        
        # Right frame: Classification results
        self.classification_frame = ctk.CTkFrame(self.root)
        self.classification_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        
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
    
    def _create_message_section(self):
        """Create the message log section"""
        # Message frame
        self.message_frame = ctk.CTkFrame(self.root)
        self.message_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="nsew")
        
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
        self.control_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        
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
        
        # Quick commands
        quick_commands = [
            ("🤝 Connect", "RTC00"),
            ("📷 Request Image", "IMG01"),
            ("🔄 Status", "STA01")
        ]
        
        for text, cmd in quick_commands:
            btn = ctk.CTkButton(
                self.command_frame,
                text=text,
                command=lambda c=cmd: self._send_quick_command(c),
                width=100
            )
            btn.pack(side="left", padx=(5, 0))
    
    def _setup_protocol_integration(self):
        """Setup integration with the PySerial protocol"""
        # Create a custom protocol class that sends messages to GUI
        class GUIProtocol(SmartBinPySerialProtocol):
            def __init__(self, gui_instance, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.gui = gui_instance
            
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
                    
                    # Perform classification
                    classification, confidence = self._mock_classify(image)
                    
                    # Send classification to GUI
                    self.gui.message_queue.put({
                        'type': 'classification',
                        'result': classification,
                        'confidence': confidence,
                        'all_classes': self._get_all_class_confidences(),
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })
                    
                    # Send classification result to ESP32
                    result = f"{classification} {confidence:.2f}"
                    if self._send_message("CLS01", result):
                        self.gui.message_queue.put({
                            'type': 'info',
                            'message': f"✅ Sent classification: {result}",
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
            
            def _get_all_class_confidences(self) -> Dict[str, float]:
                """Generate mock confidence scores for all classes"""
                import random
                classes = ["plastic", "metal", "paper", "misc"]
                confidences = {}
                
                # Generate random confidences that sum to ~1.0
                remaining = 1.0
                for i, cls in enumerate(classes[:-1]):
                    if i == 0:  # First class gets highest confidence
                        conf = random.uniform(0.6, 0.9)
                    else:
                        conf = random.uniform(0.01, remaining * 0.5)
                    confidences[cls] = conf
                    remaining -= conf
                
                # Last class gets remaining confidence
                confidences[classes[-1]] = max(0.01, remaining)
                
                return confidences
        
        self.protocol_class = GUIProtocol
    
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
            # Clear existing widgets
            for widget in self.classification_results.winfo_children():
                widget.destroy()
            
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
            
            if self.protocol:
                self.protocol.stop()
            
            if self.protocol_thread:
                self.protocol_thread.join(timeout=3)
            
            self.status_label.configure(text="🔴 Disconnected")
            self.connect_btn.configure(text="🔗 Connect", state="normal")
            
            self._add_message("[GUI] ✅ Disconnected successfully", "info")
            
        except Exception as e:
            self._add_message(f"[GUI] ❌ DISCONNECT ERROR: {e}", "error")
    
    def _run_protocol(self):
        """Run the protocol in a separate thread"""
        try:
            success = self.protocol.start()
            if success:
                self.root.after(0, lambda: self.status_label.configure(text="🟢 Connected"))
                self.root.after(0, lambda: self.connect_btn.configure(text="🔌 Disconnect", state="normal"))
            else:
                self.root.after(0, lambda: self.status_label.configure(text="🔴 Connection Failed"))
                self.root.after(0, lambda: self.connect_btn.configure(text="🔗 Connect", state="normal"))
                self.running = False
        except Exception as e:
            self.message_queue.put({
                'type': 'error',
                'message': f"Protocol error: {e}",
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
            self.running = False
    
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
    
    def run(self):
        """Run the GUI application"""
        try:
            self._add_message("[GUI] 🚀 SmartBin Control Center started", "info")
            self._add_message("[GUI] 💡 Enter ESP32 MAC address and click Connect", "info")
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n🛑 GUI interrupted by user")
        finally:
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
