import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import threading
from datetime import datetime
import os
import keyboard

# Load timings.csv
all_timings = pd.read_csv('timing/elite_info/elite_pitchinfo.csv')

# only certian folders
timings = all_timings

# shuffle
timings = timings.sample(frac=1, random_state=None).reset_index(drop=True)

# videos played
played_videos = set()

# store testing
session_results = []


def play_video(video_path, on_finish):
    try:
        if os.name == 'nt':  
            os.startfile(video_path)
    except Exception as e:
        messagebox.showerror('Error', f'Could not play video: {e}')
    on_finish()

# Main App Class
class PitchApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Pitch Video App')
        self.current_idx = 0
        self.pitch_type_var = tk.StringVar()
        self.result_var = tk.StringVar()
        self.next_button = None
        self.video_label = None
        self.app_state = None
        self.space_bar_pressed = False
        keyboard.hook(self.on_key_press)
        self.build_gui()
        self.show_next_video()
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    def on_key_press(self, event):
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == 's':
                self.space_bar_pressed = True
            if event.name == '9':
                self.root.after(0, lambda: self.result_var.set('Strike'))
            elif event.name == '0':
                self.root.after(0, lambda: self.result_var.set('Ball'))
            elif event.name == '1':
                self.root.after(0, lambda: self.pitch_type_var.set('Fastball'))
            elif event.name == '2':
                self.root.after(0, lambda: self.pitch_type_var.set('Offspeed'))
            elif event.name == '3':
                self.root.after(0, lambda: self.pitch_type_var.set('Breaking'))
            elif event.name == 'enter':
                if self.app_state == 'PLAY':
                    self.root.after(0, self.on_play_video)
                elif self.app_state == 'SUBMIT':
                    self.root.after(0, self.on_submit)
    
    def build_gui(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill='both', expand=True)

        self.video_label = ttk.Label(frm, text='')  
        self.video_label.pack(pady=10)

        self.video_count = ttk.Label(frm, text='')  
        self.video_count.pack(pady=15)

        button_frame = ttk.Frame(frm, padding=10)
        button_frame.pack(pady=10)
        self.next_button = ttk.Button(frm, text='Play Video', command=self.on_play_video) 
        self.next_button.pack(pady=10)
        quit_button = ttk.Button(frm, text='Quit', command=self.on_close)
        quit_button.pack(pady=5)

    def show_next_video(self):
        self.space_bar_pressed = False 

        while self.current_idx < len(timings) and timings.iloc[self.current_idx]['new_name'] in played_videos:
            self.current_idx += 1

        if self.current_idx >= len(timings):
            self.video_label.config(text='All videos played!')
            self.next_button.config(state='disabled')
            return
        
        entry = timings.iloc[self.current_idx]
        self.video_label.config(text=f"Video: {entry['new_name']}")
        self.video_count.config(text=f"Played {len(played_videos)} / 33")
        self.pitch_type_var.set('')
        self.result_var.set('')
        self.next_button.config(text='Play Video', state='normal')
        self.app_state = 'PLAY'

    def on_play_video(self):
        entry = timings.iloc[self.current_idx]
        video_path = os.path.join(entry['new_name'])

        self.next_button.config(state='disabled')

        def after_video():
            self.root.after(100, self.enable_selection)

        threading.Thread(target=play_video, args=(video_path, after_video), daemon=True).start()

    def enable_selection(self):
        self.next_button.config(text='Submit (Enter)', state='normal', command=self.on_submit)
        self.app_state = 'SUBMIT'

    def on_submit(self):
        entry = timings.iloc[self.current_idx]

        if not self.pitch_type_var.get() or not self.result_var.get():
            messagebox.showwarning('Incomplete', 'Please select both pitch type and result.')
            return
        
        session_results.append({
            'video': entry['new_name'],
            'pitch_type': self.pitch_type_var.get(),
            'result': self.result_var.get(),
            'space_bar': self.space_bar_pressed 
        })
        played_videos.add(entry['new_name'])
        self.current_idx += 1
        self.show_next_video()

    def on_close(self):
        keyboard.unhook_all()
        if session_results:
            log_dir = 'logs'
            os.makedirs(log_dir, exist_ok=True)

            current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filepath = os.path.join(log_dir, f'{current_time}_session_results.csv')
            pd.DataFrame(session_results).to_csv(filepath, index=False)
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = PitchApp(root)
    root.mainloop()
