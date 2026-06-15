from flask import Flask, render_template, Response, request, jsonify
import os
import time

app = Flask(__name__, template_folder=os.getcwd())

# Dinamik bellek yapısı
aktif_cihazlar = {}

@app.route('/')
def ana_sayfa():
    return render_template('index.html')

@app.route('/api/durum', methods=['GET'])
def durumu_getir():
    global aktif_cihazlar
    su_an = time.time()
    
    # Sinyal kesilen cihazları listeden temizle
    silinecekler = [ip for ip, veri in aktif_cihazlar.items() if (su_an - veri["son_sinyal"]) > 8]
    for ip in silinecekler:
        if ip in aktif_cihazlar:
            del aktif_cihazlar[ip]
        
    return jsonify({ip: {"bilgisayar_adi": v["bilgisayar_adi"]} for ip, v in aktif_cihazlar.items()})

@app.route('/api/yayin_yukle', methods=['POST'])
def yayin_yukle():
    global aktif_cihazlar
    ip_adresi = request.headers.get("X-Device-IP")
    cihaz_adi = request.headers.get("X-Device-Name", "Bilinmeyen Cihaz")
    
    if ip_adresi:
        # Yeni gelen kare eskisini doğrudan ezer (Eskiler silinir)
        aktif_cihazlar[ip_adresi] = {
            "bilgisayar_adi": cihaz_adi,
            "canli_kare": request.data,
            "son_sinyal": time.time()
        }
        return "ok", 200
    return "hata", 400

def kare_ustureteci(ip_adresi):
    global aktif_cihazlar
    while True:
        time.sleep(0.04) # Saniyede ~25 kare hız sınırı
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
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
