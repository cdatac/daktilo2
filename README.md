# Daktilo2 Magazine Generator

Bu program, Daktilo1984.com sitesindeki makaleleri otomatik olarak çekerek "Pazar Eki" formatında baskıya hazır bir dergi (HTML) oluşturur.

## Kurulum ve Kullanım

Bu yazılımı kullanmak için bilgisayarınızda **Python** yüklü olmalıdır.

### 1. Kütüphaneleri Yükleyin
Terminal veya Komut İstemi'ni (CMD) açın ve şu komutu çalıştırın:
```bash
pip install beautifulsoup4 jinja2 requests
```
*(Eğer Tkinter hatası alırsanız Python kurulumunuzda "tcl/tk" seçeneğinin işaretli olduğundan emin olun, genellikle standart gelir.)*

### 2. Programı Çalıştırın
Programın bulunduğu klasörde terminali açın ve:
```bash
python weekly_magazine.py
```
komutunu verin.

### 3. Tarih Seçimi
- Kod çalıştığında bir **Takvim** penceresi açılacaktır.
- İstediğiniz dergi tarihini seçin.
- Program o tarihteki tüm makaleleri bulup dergiyi oluşturacaktır.

### 4. Sonuç
- İşlem bitince klasörde `7Aralık25-daktilo2.html` (tarihe göre değişir) isminde bir dosya oluşur.
- Bu dosyayı tarayıcınızda açın.
- Yazdır (Ctrl+P) -> **PDF Olarak Kaydet** diyerek çıktısını alabilirsiniz.

## Önemli Not
`weekly_magazine.py` ve `template.html` dosyaları **aynı klasörde** durmalıdır. Dosyaların yerini değiştirmeyin.

## Profesyonel Dağıtım (EXE)
Eğer Python kurmakla uğraşmak istemeyen birine gönderecekseniz, **`dist`** klasörü içindeki **`Daktilo2Generator.exe`** dosyasını paylaşmanız yeterlidir.
- Bu dosya **tek başınadır**, yanında başka dosya gerekmez.
- Takvim ve dergi üretimi her bilgisayarda çalışır.
