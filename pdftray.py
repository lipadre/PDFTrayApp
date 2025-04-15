import os
import shutil
import time
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pystray import Icon as TrayIcon, Menu as TrayMenu, MenuItem as TrayMenuItem
from PIL import Image, ImageDraw
import threading

kaynak_klasorler = [
    r"F:\CTP GIDECEK\R700 YENI",
    r"F:\CTP GIDECEK\R900",
    r"F:\CTP GIDECEK\KBA"
]
hedef_klasor = r"F:\CTP PAYLASIM"
gecersiz_sure = timedelta(days=45)

kopyalanan_dosyalar = {}
loglar = []

def log_yaz(mesaj):
    zaman = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    mesaj = f"[{zaman}] {mesaj}"
    loglar.append(mesaj)
    print(mesaj)

def dosya_kopyala(kaynak_yolu):
    if not kaynak_yolu.lower().endswith('.pdf'):
        return

    for _ in range(5):
        try:
            boyut1 = os.path.getsize(kaynak_yolu)
            time.sleep(1)
            boyut2 = os.path.getsize(kaynak_yolu)
            if boyut1 == boyut2:
                break
        except FileNotFoundError:
            log_yaz(f"⛔ Dosya silinmiş: {kaynak_yolu}")
            return
    else:
        log_yaz(f"⏳ Aktarım bitmedi: {kaynak_yolu}")
        return

    try:
        dosya_adi = os.path.basename(kaynak_yolu)
        hedef_yolu = os.path.join(hedef_klasor, dosya_adi)
        kaynak_zaman = os.path.getmtime(kaynak_yolu)

        if hedef_yolu in kopyalanan_dosyalar:
            if kopyalanan_dosyalar[hedef_yolu] == kaynak_zaman:
                return

        shutil.copy2(kaynak_yolu, hedef_yolu)
        kopyalanan_dosyalar[hedef_yolu] = kaynak_zaman
        log_yaz(f"✅ Kopyalandı: {kaynak_yolu} → {hedef_yolu}")
    except Exception as e:
        log_yaz(f"⚠️ Hata: {e}")

def eski_dosyalari_temizle():
    simdi = time.time()
    for dosya in os.listdir(hedef_klasor):
        tam_yol = os.path.join(hedef_klasor, dosya)
        if not tam_yol.lower().endswith(".pdf"):
            continue
        if os.path.isfile(tam_yol):
            dosya_zaman = os.path.getmtime(tam_yol)
            if simdi - dosya_zaman > gecersiz_sure.total_seconds():
                try:
                    os.remove(tam_yol)
                    log_yaz(f"🗑️ Silindi: {tam_yol}")
                    if tam_yol in kopyalanan_dosyalar:
                        del kopyalanan_dosyalar[tam_yol]
                except Exception as e:
                    log_yaz(f"⚠️ Silme hatası: {e}")

class PDFWatcherHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            dosya_kopyala(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            dosya_kopyala(event.src_path)

def izleme_baslat():
    if not os.path.exists(hedef_klasor):
        os.makedirs(hedef_klasor)

    for klasor in kaynak_klasorler:
        for kok, _, dosyalar in os.walk(klasor):
            for dosya in dosyalar:
                yol = os.path.join(kok, dosya)
                dosya_kopyala(yol)

    observer = Observer()
    handler = PDFWatcherHandler()
    for klasor in kaynak_klasorler:
        observer.schedule(handler, path=klasor, recursive=True)

    observer.start()
    log_yaz("📂 İzleme başladı...")

    try:
        while True:
            eski_dosyalari_temizle()
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def simge_olustur():
    image = Image.new('RGB', (64, 64), "white")
    d = ImageDraw.Draw(image)
    d.rectangle([16, 16, 48, 48], fill="black")
    return image

def menu_goster(icon, item):
    from tkinter import Tk, Text, Scrollbar, RIGHT, Y, LEFT, BOTH, END
    pencere = Tk()
    pencere.title("PDF Kopyalama Logları")
    text = Text(pencere, wrap='word')
    text.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar = Scrollbar(pencere, command=text.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    text.configure(yscrollcommand=scrollbar.set)

    for log in loglar:
        text.insert(END, log + "
")
    pencere.mainloop()

def sistem_tepsisi_baslat():
    icon = TrayIcon("PDFTray", simge_olustur(), menu=TrayMenu(
        TrayMenuItem('Logları Göster', menu_goster),
        TrayMenuItem('Çıkış', lambda icon, item: icon.stop())
    ))
    icon.run()

if __name__ == "__main__":
    t1 = threading.Thread(target=izleme_baslat, daemon=True)
    t1.start()
    sistem_tepsisi_baslat()
