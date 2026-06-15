from flask import Flask, render_template, jsonify, request, Response
import time
import os

app = Flask(__name__, template_folder=os.getcwd())

# Aktif cihazların verileri ve canlı ekran kareleri
aktif_cihazlar = {}

@app.route('/')
def ana_sayfa():
    return render_template('index.html')

@app.route('/api/durum', methods=['GET'])
def durumu_getir():
    global aktif_cihazlar
    su_an = time.time()
    
    # 6 saniye boyunca sinyal vermeyen cihazı listeden siler
    silinecekler = [ip for ip, veri in aktif_cihazlar.items() if (su_an - veri["son_sinyal"]) > 6]
    for ip in silinecekler:
        if ip in aktif_cihazlar:
            del aktif_cihazlar[ip]
        
    temiz_liste = {}
    for ip, veri in aktif_cihazlar.items():
        temiz_liste[ip] = {
            "bilgisayar_adi": veri["bilgisayar_adi"]
        }
    return jsonify(temiz_liste)

@app.route('/api/guncelle', methods=['POST'])
def durumu_guncelle():
    global aktif_cihazlar
    veri = request.json or {}
    ip_adresi = veri.get("ip_adresi")
    durum = veri.get("aktif_kullanici", 0)
    
    if ip_adresi and ip_adresi != "IP Tespit Edilemedi":
        if durum == 1:
            if ip_adresi not in aktif_cihazlar:
                aktif_cihazlar[ip_adresi] = {
                    "bilgisayar_adi": veri.get("bilgisayar_adi", "Bilinmeyen Cihaz"),
                    "canli_kare": b"",
                    "son_sinyal": time.time()
                }
            else:
                aktif_cihazlar[ip_adresi]["son_sinyal"] = time.time()
        else:
            if ip_adresi in aktif_cihazlar:
                del aktif_cihazlar[ip_adresi]
                
    return jsonify({"durum": "ok"})

@app.route('/api/yayin_yukle', methods=['POST'])
def yayin_yukle():
    global aktif_cihazlar
    ip_adresi = request.headers.get("X-Device-IP")
    
    if ip_adresi in aktif_cihazlar:
        aktif_cihazlar[ip_adresi]["canli_kare"] = request.data
        aktif_cihazlar[ip_adresi]["son_sinyal"] = time.time()
        return "ok", 200
    return "cihaz yok", 404

def kare_ustureteci(ip_adresi):
    global aktif_cihazlar
    while True:
        time.sleep(0.04)
        if ip_adresi in aktif_cihazlar:
            kare = aktif_cihazlar[ip_adresi].get("canli_kare", b"")
            if kare:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + kare + b'\r\n')
        else:
            break

@app.route('/api/canli_yayin/<ip_adresi>')
def canli_yayin(ip_adresi):
    return Response(kare_ustureteci(ip_adresi),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # İnternet sunucularında port otomatik atanacağı için çevre değişkenine uyumlu hale getirildi
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
