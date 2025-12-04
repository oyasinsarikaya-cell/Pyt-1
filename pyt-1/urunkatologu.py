import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import traceback
import shutil
from flask import Flask, render_template, request, jsonify, send_file, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
from io import BytesIO
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# LOGGING KURULUMU
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('kutu_dunyasi.log', maxBytes=10000000, backupCount=5),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'kutu_dunyasi_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kutu_dunyasi_web.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)

# ÜRÜN KATALOĞU YÜKLEME
def urun_katalogunu_yukle():
    """Excel dosyasından ürün kataloğunu yükler"""
    try:
        # Excel dosyasını oku
        df = pd.read_excel('urun_katalog.xlsx', sheet_name='Ürün Kataloğu')
        
        # Eksik değerleri temizle ve string işlemleri için hazırla
        df['Ürün Adı*'] = df['Ürün Adı*'].astype(str).str.strip()
        df['Bıçak Kodu*'] = df['Bıçak Kodu*'].astype(str).str.strip()
        
        # NaN değerleri boş string ile değiştir
        df = df.fillna('')
        
        logger.info(f"Ürün kataloğu başarıyla yüklendi. Toplam {len(df)} ürün.")
        return df
    except Exception as e:
        logger.error(f"Ürün kataloğu yükleme hatası: {e}")
        # Boş bir DataFrame döndür
        return pd.DataFrame(columns=['Ürün Adı*', 'Bıçak Kodu*', 'Bıçak Ebadı En (mm)*', 'Bıçak Ebadı Boy (mm)*'])

# TÜM ÜRÜN LİSTESİNİ GETİR
def tum_urun_listesi():
    """Tüm ürün listesini getirir"""
    try:
        urun_katalogu = urun_katalogunu_yukle()
        if urun_katalogu.empty:
            return []
        
        # Ürün adlarını temizle ve sırala
        urun_listesi = urun_katalogu['Ürün Adı*'].dropna().unique().tolist()
        urun_listesi = [urun.strip() for urun in urun_listesi if urun.strip()]
        urun_listesi.sort()
        
        return urun_listesi
    except Exception as e:
        logger.error(f"Ürün listesi getirme hatası: {e}")
        return []

# ÜRÜN BİLGİSİ GETİRME FONKSİYONU
def urun_bilgisi_getir(urun_adi):
    """
    Ürün adına göre bıçak kodu ve ebatlarını getirir
    """
    try:
        urun_katalogu = urun_katalogunu_yukle()
        
        if urun_katalogu.empty:
            return None
            
        urun_adi_aranan = urun_adi.strip()
        
        # Tam eşleşme ara
        bulunan_urun = urun_katalogu[urun_katalogu['Ürün Adı*'] == urun_adi_aranan]
        
        if not bulunan_urun.empty:
            urun_bilgisi = bulunan_urun.iloc[0]
            
            bicak_kodu = urun_bilgisi['Bıçak Kodu*']
            en = urun_bilgisi['Bıçak Ebadı En (mm)*']
            boy = urun_bilgisi['Bıçak Ebadı Boy (mm)*']
            
            # Bıçak kodu boşsa uygun mesaj döndür
            if pd.isna(bicak_kodu) or bicak_kodu == 'nan' or bicak_kodu == '':
                bicak_kodu = "Bıçak Kodu Bulunamadı"
            
            return {
                'bicak_kodu': bicak_kodu,
                'en': en,
                'boy': boy,
                'urun_adi': urun_adi_aranan  # Tam ürün adını da döndür
            }
        else:
            return None
            
    except Exception as e:
        logger.error(f"Ürün bilgisi getirme hatası: {e}")
        return None

# Veritabanı Modeli - Üretim Emri
class UretimEmri(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    musteri_adi = db.Column(db.String(200), nullable=False)
    urun_adi = db.Column(db.String(200))
    usiparis_miktari = db.Column(db.String(50))
    tabaka_adedi = db.Column(db.String(50))
    kagit_cinsi = db.Column(db.String(100))
    gramaj = db.Column(db.String(50))
    kagit_olcusu_1 = db.Column(db.String(50))
    kagit_olcusu_2 = db.Column(db.String(50))
    bicak_kodu = db.Column(db.String(100))
    bicak_olcusu_1 = db.Column(db.String(50))
    bicak_olcusu_2 = db.Column(db.String(50))
    renk_sayisi = db.Column(db.String(50))
    renk_bilgisi = db.Column(db.String(100))
    verim = db.Column(db.String(50))
    selefon_1 = db.Column(db.String(50))
    selefon_2 = db.Column(db.String(50))
    varak_yaldiz = db.Column(db.String(50))
    gofre = db.Column(db.String(50))
    yapistirma = db.Column(db.String(50))
    paketleme = db.Column(db.String(100))
    siparis_durumu = db.Column(db.String(50))
    notlar = db.Column(db.Text)
    baski_adedi = db.Column(db.String(50))
    selefon_adedi = db.Column(db.String(50))
    kesim_adedi = db.Column(db.String(50))
    karton_agirligi = db.Column(db.String(50))
    tarih = db.Column(db.String(50))
    olusturma_tarihi = db.Column(db.DateTime, default=datetime.now)

# Sipariş Formu Modeli
class SiparisFormu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teklif_siparis_no = db.Column(db.String(100))
    musteri_firma_adi = db.Column(db.String(200))
    firma_yetkilisi = db.Column(db.String(100))
    grafik_durumu = db.Column(db.String(100))
    telefon_mail = db.Column(db.String(200))
    odeme_sekli = db.Column(db.String(100))
    teslim_tarihi = db.Column(db.String(50))
    teslim_adresi = db.Column(db.Text)
    
    # Sıvamalı ürün bilgileri
    ic_kisim_kac_adet = db.Column(db.String(50))
    ic_kisim_urun_adi_cinsi = db.Column(db.String(200))
    ic_kisim_kutu_olcusu = db.Column(db.String(100))
    ic_kisim_karton_gramaji = db.Column(db.String(100))
    ic_kisim_renk_sayisi = db.Column(db.String(50))
    
    dis_kisim_ici_bos = db.Column(db.String(50))
    dis_kisim_sedef = db.Column(db.String(50))
    dis_kisim_selefon_metallize = db.Column(db.String(50))
    dis_kisim_ice_baski = db.Column(db.String(50))
    
    olusturma_tarihi = db.Column(db.DateTime, default=datetime.now)

# ANA SAYFA ŞABLONU (Aynı kalacak)
ANA_SAYFA_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KUTU DÜNYASI - Ana Sayfa</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .navbar-brand { 
            font-weight: bold; 
            color: #dc3545 !important;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .navbar-logo {
            height: 35px;
            width: auto;
            border-radius: 4px;
        }
        .firma-logo {
            max-height: 120px;
            width: auto;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .main-container {
            min-height: 80vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .btn-module {
            width: 300px;
            height: 120px;
            margin: 20px;
            font-size: 1.5rem;
            font-weight: bold;
            border-radius: 15px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .btn-module:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }
        .btn-module i {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        .btn-urun-takip {
            background: linear-gradient(135deg, #2196F3, #1976D2);
            border: none;
            color: white;
        }
        .btn-siparis {
            background: linear-gradient(135deg, #4CAF50, #388E3C);
            border: none;
            color: white;
        }
        .btn-fiyatlandirma {
            background: linear-gradient(135deg, #FF9800, #F57C00);
            border: none;
            color: white;
        }
        .module-description {
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 5px;
        }
        .firma-bilgi { 
            text-align: center; 
            background: linear-gradient(135deg, #e9ecef 0%, #f8f9fa 100%);
            padding: 25px; 
            border-radius: 15px; 
            margin-bottom: 40px;
            border: 2px solid #dee2e6;
            max-width: 600px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <img src="/logo" alt="Kutu Dünyası" class="navbar-logo" onerror="this.style.display='none'">
                <span>KUTU DÜNYASI</span>
            </a>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="main-container">
            <!-- Firma Bilgisi -->
            <div class="firma-bilgi">
                <img src="/logo" alt="Kutu Dünyası" class="firma-logo" onerror="this.style.display='none'">
                <h2 class="text-primary mb-3">KUTU DÜNYASI</h2>
                <p class="mb-1 text-muted">YUNUS EMRE MAH. 296. SK. NO: 6/2</p>
                <p class="mb-1 text-muted">ESENYURT/İSTANBUL 34510</p>
                <p class="mb-0 text-muted">0(212) 812 36 86 - 0(532) 233 39 96</p>
            </div>

            <!-- Modül Butonları -->
            <div class="row justify-content-center">
                <div class="col-md-4 text-center">
                    <button class="btn btn-module btn-urun-takip" onclick="window.location.href='/urun-takip'">
                        <i class="fas fa-clipboard-list"></i>
                        Ürün Takip Formu
                        <div class="module-description">Üretim takip ve yönetim sistemi</div>
                    </button>
                </div>
                <div class="col-md-4 text-center">
                    <button class="btn btn-module btn-siparis" onclick="window.location.href='/siparis-formu'">
                        <i class="fas fa-file-invoice"></i>
                        Sipariş Formu
                        <div class="module-description">Sipariş yönetim sistemi</div>
                    </button>
                </div>
                <div class="col-md-4 text-center">
                    <button class="btn btn-module btn-fiyatlandirma" onclick="window.location.href='/fiyatlandirma'">
                        <i class="fas fa-calculator"></i>
                        Fiyatlandırma
                        <div class="module-description">Fiyat hesaplama modülü</div>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Enter tuşu ile butonlara erişim
        document.addEventListener('keydown', function(event) {
            if (event.key === '1') {
                window.location.href = '/urun-takip';
            } else if (event.key === '2') {
                window.location.href = '/siparis-formu';
            } else if (event.key === '3') {
                window.location.href = '/fiyatlandirma';
            }
        });
    </script>
</body>
</html>
"""

# ÜRÜN TAKİP FORM ŞABLONU - OTOMATİK TAMAMLAMA ÖZELLİKLİ
URUN_TAKIP_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KUTU DÜNYASI - Ürün Takip Formu</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .navbar-brand { 
            font-weight: bold; 
            color: #dc3545 !important;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .navbar-logo {
            height: 35px;
            width: auto;
            border-radius: 4px;
        }
        .firma-logo {
            max-height: 80px;
            width: auto;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .btn-primary { background-color: #2196F3; border-color: #2196F3; }
        .btn-success { background-color: #4CAF50; border-color: #4CAF50; }
        .btn-danger { background-color: #f44336; border-color: #f44336; }
        .btn-warning { background-color: #FF9800; border-color: #FF9800; }
        .btn-info { background-color: #9C27B0; border-color: #9C27B0; }
        .btn-ana-sayfa {
            background-color: #6c757d;
            border-color: #6c757d;
            color: white;
        }
        .form-section { background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .section-title { color: #2196F3; border-bottom: 2px solid #2196F3; padding-bottom: 10px; margin-bottom: 15px; }
        .firma-bilgi { 
            text-align: center; 
            background: linear-gradient(135deg, #e9ecef 0%, #f8f9fa 100%);
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 20px;
            border: 2px solid #dee2e6;
        }
        .btn { margin: 2px; }
        .modal-lg { max-width: 90%; }
        .table-hover tbody tr:hover { background-color: rgba(0,0,0,.075); }
        .form-alt-alta .row { margin-bottom: 12px; }
        .form-alt-alta .form-label { font-weight: bold; margin-bottom: 5px; }
        .hesaplanan-alan { background-color: #e9ffe9 !important; font-weight: bold; }
        .pdf-only-section { display: none; }
        .auto-fill-section { background: #e8f4fd; border-left: 4px solid #2196F3; }
        
        /* Autocomplete Stilleri */
        .autocomplete {
            position: relative;
            display: inline-block;
            width: 100%;
        }
        .autocomplete-items {
            position: absolute;
            border: 1px solid #d4d4d4;
            border-bottom: none;
            border-top: none;
            z-index: 99;
            top: 100%;
            left: 0;
            right: 0;
            max-height: 200px;
            overflow-y: auto;
        }
        .autocomplete-items div {
            padding: 10px;
            cursor: pointer;
            background-color: #fff;
            border-bottom: 1px solid #d4d4d4;
        }
        .autocomplete-items div:hover {
            background-color: #e9e9e9;
        }
        .autocomplete-active {
            background-color: DodgerBlue !important;
            color: #ffffff;
        }
        .urun-list-modal .modal-dialog {
            max-width: 800px;
        }
        .urun-list-item {
            cursor: pointer;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        .urun-list-item:hover {
            background-color: #f8f9fa;
        }
        .urun-list-item:last-child {
            border-bottom: none;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <img src="/logo" alt="Kutu Dünyası" class="navbar-logo" onerror="this.style.display='none'">
                <span>KUTU DÜNYASI</span>
            </a>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- Geri Dön Butonu -->
        <div class="row mb-3">
            <div class="col-12">
                <button class="btn btn-ana-sayfa" onclick="window.location.href='/'">
                    <i class="fas fa-arrow-left"></i> Ana Sayfaya Dön
                </button>
            </div>
        </div>

        <!-- Firma Bilgisi - Logo ile -->
        <div class="firma-bilgi">
            <img src="/logo" alt="Kutu Dünyası" class="firma-logo" onerror="this.style.display='none'">
            <h4 class="text-primary">KUTU DÜNYASI</h4>
            <p class="mb-1 text-muted">YUNUS EMRE MAH. 296. SK. NO: 6/2</p>
            <p class="mb-1 text-muted">ESENYURT/İSTANBUL 34510</p>
            <p class="mb-0 text-muted">0(212) 812 36 86 - 0(532) 233 39 96</p>
        </div>

        <h2 class="text-center mb-4">Ürün Takip Formu</h2>

        <!-- Arama Çubuğu -->
        <div class="row mb-3">
            <div class="col-md-6">
                <div class="input-group">
                    <input type="text" id="searchInput" class="form-control" placeholder="Müşteri, Ürün veya Bıçak Kodu ara...">
                    <button class="btn btn-outline-primary" onclick="searchRecords()">
                        <i class="fas fa-search"></i> Ara
                    </button>
                </div>
            </div>
        </div>

        <!-- Form -->
        <form id="uretimForm" class="form-alt-alta">
            
            <!-- MÜŞTERİ BİLGİLERİ -->
            <div class="form-section">
                <h4 class="section-title">Müşteri Bilgileri</h4>
                
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Müşteri Adı *</label>
                        <input type="text" class="form-control" name="musteri_adi" required>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Ürün Adı</label>
                        <div class="input-group">
                            <input type="text" class="form-control" name="urun_adi" id="urun_adi" placeholder="Ürün adını yazın veya listeden seçin..." autocomplete="off">
                            <button type="button" class="btn btn-outline-info" onclick="showUrunListesi()">
                                <i class="fas fa-list"></i> Liste
                            </button>
                            <button type="button" class="btn btn-outline-success" onclick="urunBilgisiGetir()">
                                <i class="fas fa-search"></i> Getir
                            </button>
                        </div>
                        <small class="form-text text-muted">Ürün adını yazmaya başlayın veya liste butonundan seçin</small>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Tarih</label>
                        <input type="text" class="form-control" name="tarih" value="{{ bugun }}">
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Üretim/Sipariş Miktarı</label>
                        <input type="text" class="form-control" name="usiparis_miktari">
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Sipariş Durumu</label>
                        <select class="form-select" name="siparis_durumu">
                            <option value="RPT">RPT</option>
                            <option value="YENİ">YENİ</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- OTOMATİK DOLDURULACAK BILGILER -->
            <div class="form-section auto-fill-section">
                <h4 class="section-title"><i class="fas fa-magic"></i> Otomatik Bilgiler</h4>
                
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Bıçak Kodu</label>
                        <input type="text" class="form-control" name="bicak_kodu" id="bicak_kodu" readonly style="background-color: #f8f9fa;">
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Bıçak Ölçüsü (mm)</label>
                        <div class="input-group">
                            <input type="text" class="form-control" name="bicak_olcusu_1" id="bicak_olcusu_1" placeholder="En" readonly style="background-color: #f8f9fa;">
                            <span class="input-group-text">x</span>
                            <input type="text" class="form-control" name="bicak_olcusu_2" id="bicak_olcusu_2" placeholder="Boy" readonly style="background-color: #f8f9fa;">
                        </div>
                    </div>
                </div>
            </div>

            <!-- BASKI BİLGİLERİ -->
            <div class="form-section">
                <h4 class="section-title">Baskı Bilgileri</h4>
                
                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Renk Sayısı</label>
                        <input type="text" class="form-control" name="renk_sayisi">
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Renk Bilgisi</label>
                        <input type="text" class="form-control" name="renk_bilgisi">
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Verim</label>
                        <input type="text" class="form-control" name="verim">
                    </div>
                </div>
            </div>

            <!-- MALZEME BİLGİLERİ -->
            <div class="form-section">
                <h4 class="section-title">Malzeme Bilgileri</h4>
                
                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Kağıt/Karton Cinsi</label>
                        <select class="form-select" name="kagit_cinsi">
                            <option value="Krome">Krome</option>
                            <option value="Amerikan Bristol">Amerikan Bristol</option>
                            <option value="Diğer">Diğer</option>
                        </select>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Gramaj (gr/m²)</label>
                        <input type="text" class="form-control" name="gramaj" id="gramaj" onchange="hesaplaAgirlik()">
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Kağıt Ölçüsü (mm)</label>
                        <div class="input-group">
                            <input type="text" class="form-control" name="kagit_olcusu_1" id="kagit_olcusu_1" placeholder="En" onchange="hesaplaAgirlik()">
                            <span class="input-group-text">x</span>
                            <input type="text" class="form-control" name="kagit_olcusu_2" id="kagit_olcusu_2" placeholder="Boy" onchange="hesaplaAgirlik()">
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Tabaka Adedi</label>
                        <input type="text" class="form-control" name="tabaka_adedi" id="tabaka_adedi" onchange="hesaplaAgirlik()">
                    </div>
                </div>

                <!-- HESAPLANAN AĞIRLIK -->
                <div class="row">
                    <div class="col-md-4">
                        <label class="form-label">Kartonun Ağırlığı (kg)</label>
                        <input type="text" class="form-control hesaplanan-alan" id="karton_agirligi_goster" value="Hesaplanacak" readonly>
                        <input type="hidden" name="karton_agirligi" id="karton_agirligi">
                        <small class="form-text text-muted">* Otomatik hesaplanır</small>
                    </div>
                </div>
            </div>

            <!-- FİNİSAJ BİLGİLERİ -->
            <div class="form-section">
                <h4 class="section-title">Finisaj Bilgileri</h4>
                
                <div class="row">
                    <div class="col-md-4">
                        <label class="form-label">Selefon</label>
                        <div class="input-group">
                            <select class="form-select" name="selefon_1">
                                <option value="MAT">MAT</option>
                                <option value="PARLAK">PARLAK</option>
                                <option value="SEDEF">SEDEF</option>
                                <option value="YOK">YOK</option>
                            </select>
                            <span class="input-group-text">x</span>
                            <select class="form-select" name="selefon_2">
                                <option value="SEDEF">SEDEF</option>
                                <option value="MAT">MAT</option>
                                <option value="PARLAK">PARLAK</option>
                                <option value="YOK">YOK</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-2">
                        <label class="form-label">Varak Yaldız</label>
                        <select class="form-select" name="varak_yaldiz">
                            <option value="YOK">YOK</option>
                            <option value="VAR">VAR</option>
                        </select>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-2">
                        <label class="form-label">Gofre</label>
                        <select class="form-select" name="gofre">
                            <option value="YOK">YOK</option>
                            <option value="VAR">VAR</option>
                        </select>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-2">
                        <label class="form-label">Yapıştırma</label>
                        <select class="form-select" name="yapistirma">
                            <option value="YOK">YOK</option>
                            <option value="VAR">VAR</option>
                        </select>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Paketleme</label>
                        <input type="text" class="form-control" name="paketleme">
                    </div>
                </div>
            </div>

            <!-- PDF İÇİN ÜRETİM BİLGİLERİ (GİZLİ) -->
            <div class="form-section pdf-only-section">
                <h4 class="section-title">Üretim Bilgileri (PDF için)</h4>
                
                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Baskı Adedi</label>
                        <input type="text" class="form-control" name="baski_adedi" placeholder="Sadece PDF'de gösterilir">
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Selefon Adedi</label>
                        <input type="text" class="form-control" name="selefon_adedi" placeholder="Sadece PDF'de gösterilir">
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Kesim Adedi</label>
                        <input type="text" class="form-control" name="kesim_adedi" placeholder="Sadece PDF'de gösterilir">
                    </div>
                </div>
            </div>

            <!-- NOTLAR -->
            <div class="form-section">
                <h4 class="section-title">Notlar</h4>
                <div class="row">
                    <div class="col-12">
                        <textarea class="form-control" name="notlar" rows="3" placeholder="Detaylı notlarınızı buraya yazabilirsiniz..."></textarea>
                    </div>
                </div>
            </div>

            <!-- Butonlar -->
            <div class="row mt-4">
                <div class="col-12">
                    <button type="button" class="btn btn-success" onclick="saveRecord()">
                        <i class="fas fa-save"></i> KAYDET
                    </button>
                    <button type="button" class="btn btn-primary" onclick="exportToExcel()">
                        <i class="fas fa-file-excel"></i> EXCEL
                    </button>
                    <button type="button" class="btn btn-info" onclick="generatePDF()">
                        <i class="fas fa-file-pdf"></i> PDF OLUŞTUR
                    </button>
                    <button type="button" class="btn btn-warning" onclick="printForm()">
                        <i class="fas fa-print"></i> YAZDIR
                    </button>
                    <button type="button" class="btn btn-warning" onclick="showListModal()">
                        <i class="fas fa-list"></i> LİSTELE
                    </button>
                    <button type="button" class="btn btn-danger" onclick="clearForm()">
                        <i class="fas fa-broom"></i> TEMİZLE
                    </button>
                </div>
            </div>
        </form>
    </div>

    <!-- Ürün Listesi Modal -->
    <div class="modal fade urun-list-modal" id="urunListModal" tabindex="-1" aria-labelledby="urunListModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-info text-white">
                    <h5 class="modal-title" id="urunListModalLabel">
                        <i class="fas fa-boxes"></i> ÜRÜN LİSTESİ
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <!-- Arama Çubuğu -->
                    <div class="row mb-3">
                        <div class="col-md-12">
                            <div class="input-group">
                                <input type="text" id="urunAramaInput" class="form-control" placeholder="Ürün adında ara...">
                                <button class="btn btn-outline-info" onclick="urunListesiniAra()">
                                    <i class="fas fa-search"></i> Ara
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Ürün Listesi -->
                    <div class="table-responsive">
                        <table class="table table-striped table-bordered table-hover">
                            <thead class="table-info">
                                <tr>
                                    <th>Ürün Adı</th>
                                    <th width="100">İşlem</th>
                                </tr>
                            </thead>
                            <tbody id="urunListTableBody">
                                <!-- Ürünler buraya gelecek -->
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Kapat</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Liste Modal -->
    <div class="modal fade" id="listModal" tabindex="-1" aria-labelledby="listModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title" id="listModalLabel">
                        <i class="fas fa-list"></i> KAYIT LİSTESİ
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <!-- Arama Çubuğu Modal İçin -->
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <div class="input-group">
                                <input type="text" id="modalSearchInput" class="form-control" placeholder="Müşteri, Ürün veya Bıçak Kodu ara...">
                                <button class="btn btn-outline-primary" onclick="searchRecordsInModal()">
                                    <i class="fas fa-search"></i> Ara
                                </button>
                            </div>
                        </div>
                        <div class="col-md-6 text-end">
                            <button class="btn btn-success" onclick="loadAllRecords()">
                                <i class="fas fa-sync"></i> Tümünü Listele
                            </button>
                        </div>
                    </div>

                    <!-- Kayıt Listesi -->
                    <div class="table-responsive">
                        <table class="table table-striped table-bordered table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>ID</th>
                                    <th>Müşteri</th>
                                    <th>Ürün</th>
                                    <th>Bıçak Kodu</th>
                                    <th>Durum</th>
                                    <th>Tarih</th>
                                    <th>İşlemler</th>
                                </tr>
                            </thead>
                            <tbody id="modalRecordTableBody">
                                <!-- Kayıtlar buraya gelecek -->
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Kapat</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let listModal = new bootstrap.Modal(document.getElementById('listModal'));
        let urunListModal = new bootstrap.Modal(document.getElementById('urunListModal'));

        // OTOMATİK TAMAMLAMA FONKSİYONU
        function initAutocomplete() {
            const urunAdiInput = document.getElementById('urun_adi');
            
            urunAdiInput.addEventListener('input', function(e) {
                const value = this.value;
                if (value.length < 2) return;
                
                fetch('/urun-ara?q=' + encodeURIComponent(value))
                    .then(response => response.json())
                    .then(urunler => {
                        showAutocompleteSuggestions(urunler, value);
                    })
                    .catch(error => {
                        console.error('Autocomplete hatası:', error);
                    });
            });
            
            // Input'tan focus kaybolduğunda önerileri temizle
            urunAdiInput.addEventListener('blur', function() {
                setTimeout(() => {
                    const container = document.getElementById('autocomplete-list');
                    if (container) {
                        container.innerHTML = '';
                    }
                }, 200);
            });
        }

        function showAutocompleteSuggestions(urunler, query) {
            let container = document.getElementById('autocomplete-list');
            if (!container) {
                container = document.createElement('div');
                container.id = 'autocomplete-list';
                container.className = 'autocomplete-items';
                document.getElementById('urun_adi').parentNode.appendChild(container);
            }
            
            container.innerHTML = '';
            
            if (urunler.length === 0) {
                const item = document.createElement('div');
                item.innerHTML = 'Ürün bulunamadı';
                container.appendChild(item);
                return;
            }
            
            urunler.forEach(urun => {
                const item = document.createElement('div');
                // Arama terimini vurgula
                const highlightedUrun = urun.replace(new RegExp(query, 'gi'), match => `<strong>${match}</strong>`);
                item.innerHTML = highlightedUrun;
                item.addEventListener('click', function() {
                    document.getElementById('urun_adi').value = urun;
                    container.innerHTML = '';
                    // Seçildiğinde otomatik olarak bilgileri getir
                    urunBilgisiGetir();
                });
                container.appendChild(item);
            });
        }

        // ÜRÜN LİSTESİNİ GÖSTER
        function showUrunListesi() {
            fetch('/urun-listesi')
                .then(response => response.json())
                .then(urunler => {
                    showUrunListesiModal(urunler);
                })
                .catch(error => {
                    console.error('Ürün listesi yükleme hatası:', error);
                    alert('Ürün listesi yüklenirken hata oluştu.');
                });
        }

        function showUrunListesiModal(urunler) {
            const tbody = document.getElementById('urunListTableBody');
            tbody.innerHTML = '';
            
            if (urunler.length === 0) {
                tbody.innerHTML = '<tr><td colspan="2" class="text-center">Ürün bulunamadı.</td></tr>';
                return;
            }
            
            urunler.forEach(urun => {
                const row = `<tr>
                    <td>${urun}</td>
                    <td>
                        <button class="btn btn-sm btn-success" onclick="urunSec('${urun.replace(/'/g, "\\'")}')" data-bs-dismiss="modal">
                            <i class="fas fa-check"></i> Seç
                        </button>
                    </td>
                </tr>`;
                tbody.innerHTML += row;
            });
            
            urunListModal.show();
        }

        function urunListesiniAra() {
            const query = document.getElementById('urunAramaInput').value.toLowerCase();
            const rows = document.getElementById('urunListTableBody').getElementsByTagName('tr');
            
            for (let i = 0; i < rows.length; i++) {
                const urunAdi = rows[i].getElementsByTagName('td')[0].textContent.toLowerCase();
                if (urunAdi.includes(query)) {
                    rows[i].style.display = '';
                } else {
                    rows[i].style.display = 'none';
                }
            }
        }

        function urunSec(urunAdi) {
            document.getElementById('urun_adi').value = urunAdi;
            // Seçildiğinde otomatik olarak bilgileri getir
            urunBilgisiGetir();
        }

        // ÜRÜN BİLGİSİ GETİRME FONKSİYONU
        function urunBilgisiGetir() {
            const urunAdi = document.getElementById('urun_adi').value.trim();
            
            if (!urunAdi) {
                alert('Lütfen ürün adı giriniz!');
                return;
            }
            
            // Loading göster
            document.getElementById('bicak_kodu').value = 'Aranıyor...';
            document.getElementById('bicak_olcusu_1').value = 'Aranıyor...';
            document.getElementById('bicak_olcusu_2').value = 'Aranıyor...';
            
            fetch('/urun-bilgi?urun_adi=' + encodeURIComponent(urunAdi))
            .then(response => {
                if (!response.ok) {
                    throw new Error('Ürün bulunamadı');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    document.getElementById('bicak_kodu').value = data.bicak_kodu;
                    document.getElementById('bicak_olcusu_1').value = data.en;
                    document.getElementById('bicak_olcusu_2').value = data.boy;
                    
                    // Formdaki bıçak kodu alanını da güncelle
                    document.getElementsByName('bicak_kodu')[0].value = data.bicak_kodu;
                    document.getElementsByName('bicak_olcusu_1')[0].value = data.en;
                    document.getElementsByName('bicak_olcusu_2')[0].value = data.boy;
                    
                    showAlert('Ürün bilgileri başarıyla getirildi!', 'success');
                } else {
                    throw new Error(data.message || 'Ürün bulunamadı');
                }
            })
            .catch(error => {
                console.error('Hata:', error);
                document.getElementById('bicak_kodu').value = 'Bulunamadı';
                document.getElementById('bicak_olcusu_1').value = '';
                document.getElementById('bicak_olcusu_2').value = '';
                
                // Formdaki bıçak kodu alanını da güncelle
                document.getElementsByName('bicak_kodu')[0].value = 'Bulunamadı';
                document.getElementsByName('bicak_olcusu_1')[0].value = '';
                document.getElementsByName('bicak_olcusu_2')[0].value = '';
                
                showAlert(error.message, 'danger');
            });
        }

        function showAlert(message, type) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Formun üstüne ekle
            const form = document.getElementById('uretimForm');
            form.parentNode.insertBefore(alertDiv, form);
            
            // 5 saniye sonra otomatik kaldır
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.parentNode.removeChild(alertDiv);
                }
            }, 5000);
        }

        function showListModal() {
            loadAllRecords();
            listModal.show();
        }

        function loadAllRecords() {
            fetch('/list')
            .then(response => response.json())
            .then(data => {
                showRecordsInModal(data);
            })
            .catch(error => {
                console.error('Hata:', error);
                alert('Kayıtlar yüklenirken hata oluştu.');
            });
        }

        function searchRecordsInModal() {
            const query = document.getElementById('modalSearchInput').value;
            if (!query) {
                loadAllRecords();
                return;
            }
            
            fetch('/search?q=' + encodeURIComponent(query))
            .then(response => response.json())
            .then(data => {
                showRecordsInModal(data);
            });
        }

        function showRecordsInModal(records) {
            const tbody = document.getElementById('modalRecordTableBody');
            tbody.innerHTML = '';
            
            if (records.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center">Kayıt bulunamadı.</td></tr>';
                return;
            }
            
            records.forEach(record => {
                let statusClass = '';
                switch(record.siparis_durumu) {
                    case 'RPT': statusClass = 'bg-warning text-dark'; break;
                    case 'YENİ': statusClass = 'bg-primary'; break;
                    default: statusClass = 'bg-secondary';
                }
                
                const row = `<tr>
                    <td><strong>${record.id}</strong></td>
                    <td>${record.musteri_adi}</td>
                    <td>${record.urun_adi}</td>
                    <td><span class="badge bg-info">${record.bicak_kodu || '-'}</span></td>
                    <td><span class="badge ${statusClass}">${record.siparis_durumu}</span></td>
                    <td>${record.tarih}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="loadRecord(${record.id})" data-bs-dismiss="modal">
                            <i class="fas fa-edit"></i> Yükle
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteRecord(${record.id})">
                            <i class="fas fa-trash"></i> Sil
                        </button>
                    </td>
                </tr>`;
                tbody.innerHTML += row;
            });
        }

        function loadRecord(id) {
            fetch('/record/' + id)
            .then(response => response.json())
            .then(record => {
                const form = document.getElementById('uretimForm');
                Object.keys(record).forEach(key => {
                    if (form.elements[key]) {
                        form.elements[key].value = record[key] || '';
                    }
                });
                // Hesaplanan ağırlığı göster
                document.getElementById('karton_agirligi_goster').value = record.karton_agirligi || 'Hesaplanacak';
                document.getElementById('karton_agirligi').value = record.karton_agirligi || '';
                
                // Otomatik bilgileri güncelle
                document.getElementById('bicak_kodu').value = record.bicak_kodu || '';
                document.getElementById('bicak_olcusu_1').value = record.bicak_olcusu_1 || '';
                document.getElementById('bicak_olcusu_2').value = record.bicak_olcusu_2 || '';
            })
            .catch(error => {
                console.error('Hata:', error);
                alert('Kayıt yüklenirken hata oluştu.');
            });
        }

        function deleteRecord(id) {
            if (confirm('Bu kaydı silmek istediğinizden emin misiniz?')) {
                fetch('/delete/' + id, {method: 'DELETE'})
                .then(response => response.json())
                .then(result => {
                    alert(result.message);
                    loadAllRecords();
                })
                .catch(error => {
                    console.error('Hata:', error);
                    alert('Silme işlemi sırasında hata oluştu.');
                });
            }
        }

        function hesaplaAgirlik() {
            const en = parseFloat(document.getElementById('kagit_olcusu_1').value) || 0;
            const boy = parseFloat(document.getElementById('kagit_olcusu_2').value) || 0;
            const gramaj = parseFloat(document.getElementById('gramaj').value) || 0;
            const tabaka_adedi = parseFloat(document.getElementById('tabaka_adedi').value) || 0;
            
            if (en > 0 && boy > 0 && gramaj > 0 && tabaka_adedi > 0) {
                // DOĞRU FORMÜL: (En × Boy × Gramaj × Tabaka Adedi) / 1.000.000
                const agirlik_kg = (en * boy * gramaj * tabaka_adedi) / 1000000;
                const formattedWeight = agirlik_kg.toLocaleString('tr-TR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }) + ' kg';
                
                document.getElementById('karton_agirligi_goster').value = formattedWeight;
                document.getElementById('karton_agirligi').value = formattedWeight;
            } else {
                document.getElementById('karton_agirligi_goster').value = 'Hesaplanacak';
                document.getElementById('karton_agirligi').value = '';
            }
        }

        function saveRecord() {
            const formData = new FormData(document.getElementById('uretimForm'));
            const data = Object.fromEntries(formData.entries());
            
            // Validasyon
            if (!data.musteri_adi.trim()) {
                alert('Müşteri adı zorunludur!');
                return;
            }
            
            // Ağırlık hesaplamasını yap
            hesaplaAgirlik();
            data.karton_agirligi = document.getElementById('karton_agirligi').value;
            
            fetch('/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                alert(result.message);
                if (result.success) clearForm();
            })
            .catch(error => {
                console.error('Hata:', error);
                alert('Kayıt sırasında hata oluştu.');
            });
        }

        function searchRecords() {
            const query = document.getElementById('searchInput').value;
            if (!query) {
                alert('Lütfen arama metni giriniz.');
                return;
            }
            
            fetch('/search?q=' + encodeURIComponent(query))
            .then(response => response.json())
            .then(data => {
                showListModal();
                showRecordsInModal(data);
            })
            .catch(error => {
                console.error('Hata:', error);
                alert('Arama sırasında hata oluştu.');
            });
        }

        function exportToExcel() {
            window.open('/export/excel', '_blank');
        }

        function generatePDF() {
            const formData = new FormData(document.getElementById('uretimForm'));
            const data = Object.fromEntries(formData.entries());
            
            // Ağırlık hesaplamasını yap ve PDF'e gönder
            hesaplaAgirlik();
            data.karton_agirligi = document.getElementById('karton_agirligi').value;
            
            fetch('/export/pdf', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'KutuDunyasi_Form.pdf';
                a.click();
                window.URL.revokeObjectURL(url);
            })
            .catch(error => {
                console.error('Hata:', error);
                alert('PDF oluşturulurken hata oluştu.');
            });
        }

        function printForm() {
            const formData = new FormData(document.getElementById('uretimForm'));
            const data = Object.fromEntries(formData.entries());
            
            // Ağırlık hesaplamasını yap ve PDF'e gönder
            hesaplaAgirlik();
            data.karton_agirligi = document.getElementById('karton_agirligi').value;
            
            fetch('/print', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('PDF oluşturulamadı');
                }
                return response.blob();
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const printWindow = window.open(url, '_blank');
                if (printWindow) {
                    printWindow.onload = function() {
                        printWindow.print();
                    };
                } else {
                    alert('Popup engelleyici nedeniyle yazdırma penceresi açılamadı. Lütfen popup engelleyiciyi devre dışı bırakın.');
                }
            })
            .catch(error => {
                console.error('Hata:', error);
                alert('PDF oluşturulurken hata oluştu: ' + error.message);
            });
        }

        function clearForm() {
            document.getElementById('uretimForm').reset();
            document.getElementById('uretimForm').elements['tarih'].value = '{{ bugun }}';
            document.getElementById('uretimForm').elements['kagit_cinsi'].value = 'Krome';
            document.getElementById('uretimForm').elements['selefon_1'].value = 'MAT';
            document.getElementById('uretimForm').elements['selefon_2'].value = 'SEDEF';
            document.getElementById('uretimForm').elements['varak_yaldiz'].value = 'YOK';
            document.getElementById('uretimForm').elements['gofre'].value = 'YOK';
            document.getElementById('uretimForm').elements['yapistirma'].value = 'YOK';
            document.getElementById('uretimForm').elements['siparis_durumu'].value = 'RPT';
            document.getElementById('karton_agirligi_goster').value = 'Hesaplanacak';
            document.getElementById('karton_agirligi').value = '';
            
            // Otomatik bilgileri temizle
            document.getElementById('bicak_kodu').value = '';
            document.getElementById('bicak_olcusu_1').value = '';
            document.getElementById('bicak_olcusu_2').value = '';
            
            // Autocomplete listesini temizle
            const container = document.getElementById('autocomplete-list');
            if (container) {
                container.innerHTML = '';
            }
        }

        // Enter tuşu ile ürün bilgisi getirme
        document.getElementById('urun_adi').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                urunBilgisiGetir();
            }
        });

        // Ürün arama input'unda enter tuşu
        document.getElementById('urunAramaInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                urunListesiniAra();
            }
        });

        document.addEventListener('DOMContentLoaded', function() {
            clearForm();
            initAutocomplete();
        });
    </script>
</body>
</html>
"""

# YENİ ROUTE'LAR - ÜRÜN ARAMA VE LİSTELEME
@app.route('/urun-ara')
def urun_ara():
    """Ürün adında arama yapar"""
    try:
        query = request.args.get('q', '').strip().lower()
        
        if not query or len(query) < 2:
            return jsonify([])
        
        tum_urunler = tum_urun_listesi()
        
        # Arama yap
        sonuclar = [urun for urun in tum_urunler if query in urun.lower()]
        
        # İlk 10 sonucu döndür
        return jsonify(sonuclar[:10])
        
    except Exception as e:
        logger.error(f"Ürün arama hatası: {e}")
        return jsonify([])

@app.route('/urun-listesi')
def urun_listesi():
    """Tüm ürün listesini getirir"""
    try:
        tum_urunler = tum_urun_listesi()
        return jsonify(tum_urunler)
    except Exception as e:
        logger.error(f"Ürün listesi getirme hatası: {e}")
        return jsonify([])

@app.route('/urun-bilgi')
def urun_bilgi():
    """Ürün adına göre bıçak kodu ve ebatlarını getirir"""
    try:
        urun_adi = request.args.get('urun_adi', '').strip()
        
        if not urun_adi:
            return jsonify({'success': False, 'message': 'Ürün adı gerekli'})
        
        bilgiler = urun_bilgisi_getir(urun_adi)
        
        if bilgiler:
            return jsonify({
                'success': True,
                'bicak_kodu': bilgiler['bicak_kodu'],
                'en': bilgiler['en'],
                'boy': bilgiler['boy'],
                'urun_adi': bilgiler.get('urun_adi', urun_adi)
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Ürün katalogda bulunamadı'
            })
            
    except Exception as e:
        logger.error(f"Ürün bilgisi getirme hatası: {e}")
        return jsonify({
            'success': False, 
            'message': f'Sistem hatası: {str(e)}'
        })

# SİPARİŞ FORMU ŞABLONU (Aynı kalacak)
SIPARIS_FORMU_TEMPLATE = """
<!-- Mevcut sipariş formu şablonu aynı kalacak -->
"""

# FİYATLANDIRMA MODÜLÜ ŞABLONU (Aynı kalacak)
FIYATLANDIRMA_TEMPLATE = """
<!-- Mevcut fiyatlandırma şablonu aynı kalacak -->
"""

# DİĞER ROUTE'LAR AYNI KALACAK
@app.route('/')
def index():
    """Ana sayfa - 3 butonlu menü"""
    try:
        return ANA_SAYFA_TEMPLATE
    except Exception as e:
        logger.error(f"Ana sayfa hatası: {e}")
        return "Sistem geçici olarak hizmet veremiyor", 500

@app.route('/urun-takip')
def urun_takip():
    """Ürün Takip Formu sayfası"""
    try:
        bugun = datetime.now().strftime("%d.%m.%Y")
        return URUN_TAKIP_TEMPLATE.replace("{{ bugun }}", bugun)
    except Exception as e:
        logger.error(f"Ürün takip formu hatası: {e}")
        return "Sistem geçici olarak hizmet veremiyor", 500

@app.route('/siparis-formu')
def siparis_formu():
    """Sipariş Formu sayfası"""
    try:
        bugun_tarih = datetime.now().strftime("%d.%m.%Y")
        return SIPARIS_FORMU_TEMPLATE.replace("{{ bugun_tarih }}", bugun_tarih)
    except Exception as e:
        logger.error(f"Sipariş formu hatası: {e}")
        return "Sistem geçici olarak hizmet veremiyor", 500

@app.route('/fiyatlandirma')
def fiyatlandirma():
    """Fiyatlandırma modülü ana sayfası"""
    return FIYATLANDIRMA_TEMPLATE

# Diğer route'lar aynı kalacak...
# (save_record, search_records, list_records, get_record, delete_record, export_excel, vs.)

# VERİTABANI BAŞLATMA
def init_database():
    """Veritabanını başlat"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Veritabanı başlatıldı")
            
            # Ürün kataloğunu test et
            try:
                df = urun_katalogunu_yukle()
                urun_listesi = tum_urun_listesi()
                logger.info(f"Ürün kataloğu test edildi: {len(urun_listesi)} ürün yüklendi")
            except Exception as e:
                logger.warning(f"Ürün kataloğu yüklenemedi: {e}")
                
            return True
    except Exception as e:
        logger.error(f"Veritabanı başlatma hatası: {e}")
        return False

# UYGULAMA BAŞLATMA
if __name__ == '__main__':
    try:
        logger.info("KUTU DÜNYASI Web Uygulaması başlatılıyor...")
        
        # Veritabanını başlat
        if not init_database():
            logger.error("Veritabanı başlatılamadı!")
            sys.exit(1)
        
        # SENİN IP ADRESİN - 192.168.1.81
        local_ip = "192.168.1.81"
        
        logger.info(f"Uygulama http://localhost:5000 adresinde çalışıyor")
        logger.info(f"Lokal ağda erişim: http://{local_ip}:5000")
        print("🎯 KUTU DÜNYASI Web Uygulaması")
        print("📍 Yerel erişim: http://localhost:5000")
        print("🌐 Ağ erişimi: http://192.168.1.81:5000")
        print("⏹️  Durdurmak için: Ctrl + C")
        print("")
        print("📱 Aynı ağdaki diğer cihazlardan bağlanmak için:")
        print("   http://192.168.1.81:5000")
        print("")
        
        # Tüm ağa açık şekilde çalıştır
        app.run(
            debug=True,
            host='0.0.0.0', 
            port=5000,
            threaded=True
        )
    except Exception as e:
        logger.critical(f"Uygulama başlatma hatası: {e}")
        print(f"❌ KRİTİK HATA: {e}")
        sys.exit(1)