# WARNING: The following code is known to the state of cancer to cause California.

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import re
import threading
import sys
from intelhex import IntelHex
import tempfile

# PyInstaller Commands:
# MacOs:
# pyinstaller --onefile --windowed --add-binary "/usr/local/bin/dfu-util:." --hidden-import=tkinter --hidden-import=ttk --hidden-import=threading --hidden-import=intelhex --clean Uploader.py

# Windows:
# pyinstaller --onefile --windowed --add-binary "C:\path\to\dfu-util.exe;." --hidden-import=tkinter --hidden-import=ttk --hidden-import=threading --hidden-import=intelhex --clean Uploader.py


class DFUApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DWM_V2 Firmware Uploader")
        self.root.geometry("600x500")
        self.hex_file = None  # Changed to hex_file
        self.bin_file = None  # Temporary bin file path
        self.selected_device = None
        self.max_flash_addr = 0x0807FFFF  # 512 KB limit for STM32G0B0RET

        # Determine dfu-util path
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            self.dfu_util_path = os.path.join(base_path, "dfu-util")
        else:
            self.dfu_util_path = "dfu-util"

        tk.Label(root, text="DWM_V2 Firmware Uploader",
                 font=("Helvetica", 14)).pack(pady=10)
        tk.Label(root, text="Select DFU Device:").pack(pady=5)
        self.device_combo = ttk.Combobox(root, state="readonly")
        self.device_combo.pack(pady=5)
        tk.Button(root, text="Refresh Devices",
                  command=self.refresh_devices).pack(pady=5)
        tk.Button(root, text="Select .hex File", command=self.select_file).pack(
            pady=5)  # Updated to .hex
        self.file_label = tk.Label(root, text="No file selected")
        self.file_label.pack(pady=5)
        tk.Button(root, text="Upload Firmware",
                  command=self.upload_firmware).pack(pady=10)
        self.output_text = tk.Text(
            root, height=15, wrap="word", state="disabled")
        self.output_text.pack(pady=10, fill="both", expand=True)
        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.pack(pady=5, fill="x")

        self.refresh_devices()

    def refresh_devices(self):
        try:
            self.device_combo["values"] = []
            self.selected_device = None
            result = subprocess.run(
                [self.dfu_util_path, "-l"], capture_output=True, text=True, check=True)
            devices = self.parse_dfu_devices(result.stdout)
            if not devices:
                self.device_combo["values"] = ["No DFU devices found"]
                self.device_combo.current(0)
            else:
                device_strings = [
                    f"DFU Device {
                        idx + 1}: VID={d['vid']}, PID={d['pid']}, Serial={d['serial']}"
                    for idx, d in enumerate(devices)
                ]
                self.device_combo["values"] = device_strings
                self.device_combo.current(0)
                self.selected_device = devices[0]
        except subprocess.CalledProcessError as e:
            messagebox.showerror(
                "Error", f"Failed to list devices: {e.stderr}")
            self.device_combo["values"] = ["Error listing devices"]
            self.device_combo.current(0)
            self.selected_device = None
        self.device_combo.bind("<<ComboboxSelected>>", self.on_device_select)

    def parse_dfu_devices(self, output):
        pattern = r"Found DFU: \[([0-9a-f]{4}):([0-9a-f]{4})\].*?serial=\"([^\"]+)\""
        devices = [{"vid": m[0], "pid": m[1], "serial": m[2]}
                   for m in re.findall(pattern, output, re.DOTALL)]
        unique_devices = {f"{d['vid']}:{d['pid']}:{
            d['serial']}": d for d in devices}
        return list(unique_devices.values())

    def on_device_select(self, event):
        if not self.device_combo["values"] or "No DFU devices" in self.device_combo.get():
            self.selected_device = None
            return
        idx = self.device_combo.current()
        devices = self.parse_dfu_devices(subprocess.run([self.dfu_util_path, "-l"],
                                                        capture_output=True, text=True).stdout)
        self.selected_device = devices[idx]

    def select_file(self):
        self.hex_file = filedialog.askopenfilename(
            filetypes=[("Hex Files", "*.hex")])  # Changed to .hex
        if self.hex_file:
            self.file_label.config(text=os.path.basename(self.hex_file))
            self.check_hex_file()

    def check_hex_file(self):
        try:
            ih = IntelHex(self.hex_file)
            start_addr = ih.minaddr()
            end_addr = ih.maxaddr()
            size = end_addr - start_addr + 1
            max_size = self.max_flash_addr - 0x08000000 + 1
            if size > max_size or end_addr > self.max_flash_addr:
                messagebox.showwarning(
                    "Warning",
                    f"Hex file exceeds STM32G0B0RET flash size (512 KB)!\n"
                    f"Start: {hex(start_addr)}\nEnd: {
                        hex(end_addr)}\nSize: {size} bytes"
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check .hex file: {e}")

    def hex_to_bin(self):
        """Convert .hex to .bin and return the .bin file path."""
        try:
            ih = IntelHex(self.hex_file)
            if ih.minaddr() < 0x08000000 or ih.maxaddr() > self.max_flash_addr:
                raise ValueError(
                    "Hex file addresses out of STM32G0B0RET flash range!")
            # Create a temporary .bin file
            with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp:
                ih.tobinfile(tmp.name)
                return tmp.name
        except Exception as e:
            raise Exception(f"Failed to convert .hex to .bin: {e}")

    def validate_dfu_suffix(self):
        # Disabled since we're converting to .bin
        pass

    def append_output(self, text):
        self.output_text.config(state="normal")
        self.output_text.insert("end", text + "\n")
        self.output_text.see("end")
        self.output_text.config(state="disabled")

    def upload_firmware(self):
        if not self.hex_file:
            messagebox.showerror("Error", "Please select a .hex file first!")
            return
        if not self.selected_device:
            messagebox.showerror("Error", "No DFU device selected!")
            return

        try:
            # Convert .hex to .bin
            self.append_output("Converting .hex to .bin...")
            self.bin_file = self.hex_to_bin()
            self.append_output(f"Created temporary .bin file: {
                               os.path.basename(self.bin_file)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        file_size = os.path.getsize(self.bin_file)
        max_size = self.max_flash_addr - 0x08000000 + 1
        if file_size > max_size:
            messagebox.showerror(
                "Error", "Generated .bin file too large for STM32G0B0RET (max 512 KB)!")
            os.unlink(self.bin_file)  # Clean up
            return

        self.progress.start()
        self.root.update()

        def run_dfu_util():
            try:
                cmd = [
                    self.dfu_util_path,
                    "-a", "0",
                    "-i", "0",
                    "-D", self.bin_file,
                    "-s", "0x08000000:leave",
                    "-R"
                ]
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                for line in process.stdout:
                    self.append_output(line.strip())
                for line in process.stderr:
                    self.append_output(line.strip())
                process.wait()
                if process.returncode == 0 or process.returncode == 74:
                    self.append_output("Firmware uploaded successfully!")
                    messagebox.showinfo(
                        "Success", "Firmware uploaded successfully!")
                else:
                    self.append_output(f"Upload failed with return code {
                                       process.returncode}")
                    messagebox.showerror("Error", f"Upload failed with return code {
                                         process.returncode}")
            except Exception as e:
                self.append_output(f"Error: {str(e)}")
                messagebox.showerror("Error", str(e))
            finally:
                self.progress.stop()
                # Clean up temporary .bin file
                if self.bin_file and os.path.exists(self.bin_file):
                    os.unlink(self.bin_file)
                    self.append_output("Cleaned up temporary .bin file")

        threading.Thread(target=run_dfu_util).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = DFUApp(root)
    root.lift()
    root.focus_force()
    root.mainloop()
