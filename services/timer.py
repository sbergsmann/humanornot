import threading
import time
import flet as ft

class Timer(ft.UserControl):
    def __init__(self, name="Timer", duration=30, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.duration = duration
        self.remaining_time = duration
        self.active = False
        self.th = threading.Thread(target=self.tick, daemon=True)
        self.display = ft.Text(f"Time remaining: {self.remaining_time}s")

    def did_mount(self):
        self.th.start()

    def start(self):
        self.active = True
        self.remaining_time = self.duration
        self.update_display()

    def stop(self):
        self.active = False

    def tick(self):
        while True:
            if self.active and self.remaining_time > 0:
                time.sleep(1)
                self.remaining_time -= 1
                self.update_display()
                if self.remaining_time <= 0:
                    self.stop()
                    print(f"Timer {self.name} finished!")
            else:
                time.sleep(1)

    def update_display(self):
        self.display.value = f"Time remaining: {self.remaining_time}s"
        self.update()

    def build(self):
        return ft.Container(
            content=self.display
        )

    def will_unmount(self):
        self.stop()
        super().will_unmount()