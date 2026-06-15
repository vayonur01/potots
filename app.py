from flask import Flask, render_template, jsonify, request
import time
import os

app = Flask(__name__, template_folder=os.getcwd())

# Cihaz verilerini tutan RAM veritabanı
aktif_cihazlar = {}

@app.route('/')
def ana_sayfa():
    return render_template('index.html')

@app.route('/api/durum', methods=['GET'])
def durumu_getir():
    global aktif_cihazlar
    su_an = time.time()
    
    # 8 saniye sinyal vermeyen cihazı listeden düşür
    silinecekler = [ip for ip, veri in aktif_cihazlar.items() if (su_an - veri["son_sinyal"]) > 8]
    for ip in silinecekler:
        if ip in aktif_cihazlar:
            del aktif_cihazlar[ip]
        
    temiz_liste = {}
    for ip, veri in aktif_cihazlar.items():
        temiz_liste[ip] = {
            "bilgisayar_adi": veri["bilgisayar_adi"],
            "son_ss": veri["son_ss"]  # Base64 görsel verisi direkt buradan gider
        }
    return jsonify(temiz_liste)

@app.route('/api/guncelle', methods=['POST'])
def durumu_guncelle():
    global aktif_cihazlar
    veri = request.json or {}
    ip_adresi = veri.get("ip_adresi")
    
    if ip_adresi and ip_adresi != "IP Tespit Edilemedi":
        if ip_adresi not in aktif_cihazlar:
            aktif_cihazlar[ip_adresi] = {
                "bilgisayar_adi": veri.get("bilgisayar_adi", "Bilinmeyen Cihaz"),
                "son_ss": "",
                "son_sinyal": time.time()
            }
        else:
            aktif_cihazlar[ip_adresi]["son_sinyal"] = time.time()
            
        # Eğer istemci güncelleme yaparken fotoğraf da yolladıysa doğrudan üzerine yaz
        if veri.get("ss_data"):
            aktif_cihazlar[ip_adresi]["son_ss"] = veri.get("ss_data")
            
    return jsonify({"durum": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
