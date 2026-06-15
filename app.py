from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
import os
import time

app = Flask(__name__, template_folder=os.getcwd())
app.config['SECRET_KEY'] = 'vayonur_secret!'
# CORS ayarları ile dışarıdan gelen canlı yayın bağlantılarına izin veriyoruz
socketio = SocketIO(app, cors_allowed_origins="*")

# Cihazların bilgilerini ve anlık ekran karelerini tutan dinamik bellek
aktif_cihazlar = {}

@app.route('/')
def ana_sayfa():
    return render_template('index.html')

# İstemci bilgisayar sunucuya bağlandığında tetiklenir
@socketio.on('cihaz_baglan')
def cihaz_baglan(veri):
    ip = veri.get('ip')
    if ip:
        aktif_cihazlar[ip] = {
            "sid": request.sid,
            "bilgisayar_adi": veri.get('cihaz_adi', 'Bilinmeyen Cihaz'),
            "son_sinyal": time.time(),
            "kare": b""
        }
        # Web arayüzündeki kullanıcılara cihaz listesini güncellemesini söyler
        emit('cihaz_listesi_guncelle', get_temiz_liste(), broadcast=True)

@socketio.on('ekran_akisi')
def ekran_akisi(veri):
    ip = veri.get('ip')
    if ip in aktif_cihazlar:
        # Gelen yeni kare eskisinin üzerine yazılır, eski veri hafızadan silinir
        aktif_cihazlar[ip]["kare"] = veri.get('kare')
        aktif_cihazlar[ip]["son_sinyal"] = time.time()

@socketio.on('disconnect')
def baglanti_koptu():
    # Bağlantısı kesilen cihazı tespit edip listeden temizler
    for ip, veri in list(aktif_cihazlar.items()):
        if veri["sid"] == request.sid:
            del aktif_cihazlar[ip]
            emit('cihaz_listesi_guncelle', get_temiz_liste(), broadcast=True)
            break

def get_temiz_liste():
    return {ip: {"bilgisayar_adi": v["bilgisayar_adi"]} for ip, v in aktif_cihazlar.items()}

def kare_ustureteci(ip_adresi):
    while True:
        time.sleep(0.03) # ~30 FPS yayın hızı
        if ip_adresi in aktif_cihazlar:
            kare = aktif_cihazlar[ip_adresi].get("kare", "")
            if kare:
                # Base64 veya binary olarak gelen kareyi tarayıcıya gönderir
                import base64
                if isinstance(kare, str) and "," in kare:
                    kare_bytes = base64.b64decode(kare.split(",")[1])
                else:
                    kare_bytes = kare
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + kare_bytes + b'\r\n')
        else:
            break

@app.route('/api/canli_yayin/<ip_adresi>')
def canli_yayin(ip_adresi):
    return Response(kare_ustureteci(ip_adresi),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, debug=False, port=port, host='0.0.0.0')
