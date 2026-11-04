# SOCAR Smart Analytics: ML servisi

Quyuların vəziyyətini təhlil edən, hasilatı proqnozlaşdıran, anomaliyaları aşkarlayan, risk və avadanlıq nasazlığını qiymətləndirən **ayrıca Python (FastAPI + scikit-learn) servisi**.

```
React (Vite)  →  Node.js / Express (TypeScript)  →  Python / FastAPI ML servisi
                        │                                   (bu layihə, port 8000)
                        └── PostgreSQL (quyu məlumatı və analiz tarixçəsi)
```

Express PostgreSQL-dən quyunun məlumatını oxuyur, HTTP ilə bu servisə göndərir, cavabı bazada saxlayır. ML servisi bazaya birbaşa qoşulmur. Express tərəfin kodu ZIP-in `express-integration/` qovluğundadır.

> ## ⚠️ Mütləq oxuyun: məlumat və dəqiqlik
> Hazırda **real SOCAR istehsalat məlumatı istifadə olunmayıb**. Modellər **SİNTETİK** (kompüterdə yaradılmış) məlumat üzərində öyrədilir. Bu, servisin **işləməsini və inteqrasiyanı** yoxlamaq üçündür. Metrikalar yalnız sintetik test hissəsinə aiddir və **real istehsalatda dəqiqliyə zəmanət vermir**. Hər cavabda `dataBasis: "synthetic"` sahəsi və xəbərdarlıq var. Real məlumat əldə etdikdə modelləri onunla yenidən öyrədin (bölmə 9).
> Servis **analitik qərar dəstəyidir**. O heç vaxt avtomatik idarəetmə və ya təhlükəsizlik qərarı vermir. Hər tövsiyədə `requiresEngineerReview: true` var.

---

## 1. Windows-da sıfırdan quraşdırma (Python bilmədən)

**Addım 1: Python quraşdırın** (bir dəfə)
1. https://www.python.org/downloads/ saytından **Python 3.11 və ya 3.12** yükləyin.
2. Quraşdırıcının **ilk ekranında "Add python.exe to PATH" qutusunu mütləq işarələyin**, sonra *Install Now*.
3. Yoxlama: Başlat menyusundan `cmd` açın və `python --version` yazın. `Python 3.11.x` və ya `3.12.x` görməlisiniz.

**Addım 2: ZIP-i açın.** Məsələn `C:\socar\ml-service` qovluğuna.

**Addım 3: Quraşdırma.** `ml-service` qovluğunda **`setup.bat`** faylına iki dəfə klikləyin. O avtomatik:
- virtual mühit (`venv`) yaradır,
- kitabxanaları yükləyir (internet lazımdır, 2-5 dəqiqə),
- `.env` faylını **təsadüfi API açarları ilə** yaradır,
- modelləri öyrədir (sintetik data, təxminən 1-3 dəqiqə).

Sonda `HAZIRDIR` görməlisiniz.

**Addım 4: Servisi başladın.** **`run.bat`** faylına iki dəfə klikləyin. Pəncərə açıq qalmalıdır (bağlasanız servis dayanır). Brauzerdə http://127.0.0.1:8000/docs açın, interaktiv API sənədləri görünəcək.

**Addım 5: Yoxlayın.** Servis işləyərkən **ikinci** pəncərədə **`test_endpoints.bat`** faylını işə salın. O bütün endpoint-ləri nümunə JSON-larla yoxlayır və hər biri üçün `[OK]` göstərir.

> Mümkün problemlər üçün bölmə 12-yə baxın.

### Komanda sətri ilə (istəyə bağlı)
```bat
cd C:\socar\ml-service
venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## 2. Endpoint-lər

Bütün endpoint-lər (yalnız `/health` istisna) **`X-API-Key: <.env-dəki API_KEY>`** başlığı tələb edir.

| Metod | Yol | Təyinatı |
|---|---|---|
| GET | `/health` | Servis və modellərin vəziyyəti (açar tələb olunmur) |
| GET | `/model/info` | Model versiyası, istifadə olunan feature-lər, dataset, test metrikalarının xülasəsi |
| POST | `/predict/production` | 7/30/90 günlük hasilat proqnozu + interval + proqnoz-faktiki müqayisə |
| POST | `/predict/anomaly` | Anomaliya balı, aşkarlama, əlaqəli göstəricilər |
| POST | `/predict/risk` | Risk səviyyəsi (low/medium/high), bal, səbəblər |
| POST | `/predict/equipment` | Növbəti 30 gündə nasazlıq ehtimalı, texniki xidmət ehtiyacı, gözlənilən dayanma |
| POST | `/predict/full-analysis` | Hamısı bir cavabda + səmərəlilik + tövsiyələr |
| POST | `/predict/batch` | Bir neçə quyu üçün tam analiz (`{"wells": [...]}`) |
| POST | `/model/retrain` | **Yalnız `X-Admin-Key` ilə.** Modeli arxa planda yenidən öyrədir |

**HTTP kodları:** `200` uğurlu, `401` açar yanlış/yoxdur, `403` retrain söndürülüb, `409` retrain artıq gedir, `413` sorğu böyükdür, `422` giriş məlumatı yanlışdır, `503` model yüklənməyib və ya `API_KEY` təyin edilməyib.

Nümunə JSON-lar `samples/` qovluğundadır: `sample_full.json` (120 günlük normal quyu), `sample_degraded_pump.json` (nasos sensorları pisləşən quyu), `sample_minimal.json` (yalnız 1 qeyd, az məlumat ssenarisi), `sample_batch.json`. Onları `scripts\make_samples.py` ilə yenidən yarada bilərsiniz.

PowerShell nümunəsi:
```powershell
$key = (Get-Content .env | Select-String '^API_KEY=').ToString().Split('=')[1]
curl.exe -X POST http://127.0.0.1:8000/predict/full-analysis -H "X-API-Key: $key" -H "Content-Type: application/json" --data-binary "@samples\sample_full.json"
```

---

## 3. Giriş sahələri (request)

Yalnız `wellId` və ən azı bir qeydli `history` məcburidir. **Qalan hər şey ixtiyaridir.** Məlumat yoxdursa sahəni göndərməyin və ya `null` yazın, **uydurma dəyər yazmayın**. Çatışmayan dəyərlər NaN kimi emal olunur.

### 3.1 Əsas quyu məlumatları (sorğunun yuxarı səviyyəsi)
| Sahə | Tip | Qeyd |
|---|---|---|
| `wellId` | string (məcburi) | Quyunun identifikatoru |
| `wellName`, `fieldName`, `region` | string | Məlumat üçün; modelə təsir etmir |
| `wellType` | string | `oil`, `gas`, `oil_gas`, `gas_condensate` (modelə təsir edir) |
| `wellStatus` | string | `shut_in`/`inactive` kimi dayanmış statuslarda xəbərdarlıq verilir |
| `latitude`, `longitude` | number | Hazırda modelə təsir etmir |
| `depth` | number (m, 0-20000) | Modelə təsir edir |
| `drillingDate`, `operationStartDate` | `YYYY-MM-DD` | Quyunun yaşı (istismara başlama, yoxdursa qazma tarixindən) hesablanır |
| `maintenanceDate` | `YYYY-MM-DD` | Son texniki xidmət; "son xidmətdən keçən gün" feature-i |
| `lastInspectionDate` | `YYYY-MM-DD` | Son baxış tarixi |
| `productionTarget` | number | Gündəlik hasilat hədəfi (`production` ilə **eyni vahid**); hədəfə çatma və səmərəlilik üçün |
| `production7dAvg`, `production30dAvg`, `production90dAvg`, `production7dChangePct`, `production30dChangePct` | number | **Yalnız ehtiyat**: tarixçədən hesablana bilmədikdə istifadə olunur (xəbərdarlıqda göstərilir) |
| `history` | massiv (1-2000 qeyd) | Zaman sırası (bölmə 3.2). **Tövsiyə: ən azı 90 günlük gündəlik qeyd** |

### 3.2 `history[]` qeydləri (ölçmələr)
| Sahə | Vahid / aralıq | Qeyd |
|---|---|---|
| `timestamp` (məcburi) | ISO 8601 | Məs. `2026-10-31T00:00:00Z`. Sıra məcburi deyil (özü sıralayır), təkrarlanan vaxtda sonuncu qalır. `hour/day/month/year` buradan çıxarılır |
| `production` | t/gün (≥ 0) | Ümumi mayə hasilatı. **Proqnozun əsas girişi** |
| `oilProduction`, `gasProduction`, `waterProduction` | ≥ 0 | Hazırda qəbul olunur, modeldə birbaşa istifadə olunmur |
| `pressure` | bar | Təzyiq |
| `temperature` | °C | Quyu/yataq temperaturu |
| `bottomHolePressure`, `wellheadPressure`, `casingPressure`, `tubingPressure` | bar | Dib, ağız, kəmər, boru təzyiqləri |
| `waterCut` | % (0-100) | Su payı |
| `gasOilRatio` | ≥ 0 | Qaz-neft nisbəti |
| `flowRate` | ≥ 0 | Axın sürəti |
| `vibration` | mm/s | Nasos/avadanlıq vibrasiyası |
| `equipmentTemperature` | °C | Avadanlıq temperaturu |
| `pumpEfficiency` | % (0-100) | Nasos səmərəliliyi |
| `pumpRuntime` | saat/gün (0-24) | Nasosun həmin gün işlədiyi saat |
| `pumpStatus` | string | `running`, `stopped`, `fault`... (`fault` = nasazlıq epizodu kimi sayılır) |
| `operatingHours` | saat/gün (0-24) | Əməliyyat saatları |
| `downtimeHours` | saat/gün (0-24) | Dayanma saatları (texniki xidmət/nasazlıq) |

> **Vahidlər:** model sintetik data ilə (`t/gün`, `bar`, `°C`, `%`, `mm/s`) öyrədilib. Real data ilə istifadədə **eyni vahidləri** göndərin, yaxud modeli öz vahidlərinizlə yenidən öyrədin.

---

## 4. Çıxış sahələri (`/predict/full-analysis`)

Hesablana bilməyən nəticə üçün **saxta rəqəm yox, `null`** qaytarılır və `componentStatus` səbəbi göstərir (`ok`, `insufficient_data`, `insufficient_sensor_data`, `error`).

| Sahə | Mənası |
|---|---|
| `wellId`, `analysisTimestamp`, `modelVersion`, `dataBasis` | Kimlik, analiz vaxtı (UTC), model versiyası, məlumat əsası (`synthetic`/`real`) |
| `currentProduction` | Ən son `production` ölçməsi (son 3 gün ərzində yoxdursa `null`) |
| `predictedProduction7d` / `30d` / `90d` | Növbəti 7/30/90 gün ərzində gözlənilən **orta gündəlik** hasilat (median proqnoz) |
| `predictionIntervals` | Hər ufuq üçün 80% proqnoz intervalı `{lower, upper, level}` (conformal kalibrasiya ilə) |
| `productionChangePct` | 30 günlük proqnozun cari 7 günlük ortaya nisbətən dəyişimi (%) |
| `forecastVsActual` | Keçmişdə (7 və 30 gün əvvəl) verilə biləcək proqnozun faktiki hasilatla müqayisəsi: `predicted`, `actual`, `errorPct`, `withinInterval` |
| `anomalyDetected` | Anomaliya var? (İzolyasiya meşəsi **və ya** quyunun öz tarixçəsindən çox güclü kənarlaşma) |
| `anomalyScore` | 0-1 nisbi bal (1 = təlim paylanmasının ən kənar 0.5%-i) |
| `detectedAnomalies[]` | Əlaqəli göstəricilər: `parameter`, `value`, `expectedValue`, `zScore`, `direction`, `basis` (`well_history`/`population`), `severity` |
| `riskLevel` | `low` / `medium` / `high` |
| `riskScore` | 0-1 nisbi model balı. **Kalibrə olunmuş ehtimal deyil** (etiketlər sintetikdir) |
| `riskReasons[]` | Riski artıran göstəricilər: dəyər, tipik səviyyə, z-score, mətn izahı |
| `equipmentFailureProbability` | Növbəti **30 gündə** nasos/avadanlıq nasazlığı ehtimalı (sintetik etiketlərlə öyrədilib, Platt ilə kalibrə edilib) |
| `maintenanceRisk`, `maintenanceRecommended` | Texniki xidmət ehtiyacı (qərar həddi validasiyada F1-ə görə seçilir) |
| `failureFactors[]` | Nasazlıq ehtimalını artıran amillər |
| `estimatedDowntime` | Növbəti 30 gün üçün **gözlənilən dayanma (saat)** = ehtimal × tipik nasazlıq dayanması |
| `operationalEfficiency` | 0-100 səmərəlilik KPI (50% hədəfə çatma + 30% əlçatanlıq + 20% nasos səmərəliliyi) |
| `efficiencyDetails` | Komponentlər, əvvəlki 30 günlə müqayisə (`changePoints`) və **izah mətni** |
| `indicators` | `productionDeclineRate` (%/gün, müsbət=azalma), `pressureChangeRate` (%/gün), `waterCutTrend` (b.b./gün), 7/30/90 günlük ortalar və dəyişimlər, `targetAttainment30d` |
| `recommendations[]` | Tövsiyələr: `text`, `reason`, `evidence`, `priority`, `confidence`, `requiresEngineerReview` |
| `dataQuality` | `level` (good/fair/poor), tamlıq %, çatışan sahələr, tarixçə uzunluğu, məlumatın yaşı, xəbərdarlıqlar |
| `confidence` | `{score, level, basis}`: məlumat tamlığı × tarixçə uzunluğuna əsaslanan **evristik** bal (statistik ehtimal deyil) |
| `componentStatus`, `warnings` | Komponent statusları, ümumi xəbərdarlıqlar |

---

## 5. Modellər necə işləyir

| Funksiya | Metod |
|---|---|
| Hasilat proqnozu | `HistGradientBoostingRegressor` (kvantil itkisi q10/q50/q90) hər ufuq üçün. Hədəf = gələcək orta hasilat / cari 7 günlük orta. İnterval validasiyada **conformalized quantile regression** ilə genişləndirilir |
| Anomaliya | `IsolationForest` (nəzarətsiz, etiket istifadə etmir) + hər parametr üçün quyunun öz son 30 günlük tarixçəsinə görə **robust z-score** (median/MAD). Vibrasiya, temperatur və nasos səmərəliliyi üçün populyasiya yoxlaması da var |
| Risk | `HistGradientBoostingClassifier` (3 sinif). Səbəblər = qlobal əhəmiyyət (permutation importance) × istiqamət (Spearman) × cari kənarlaşma |
| Avadanlıq nasazlığı | Binar `HistGradientBoostingClassifier` (30 gün ərzində nasazlıq), Platt kalibrasiyası; nasazlıq/təmir tarixçəsi (`days_since_maintenance`, `pump_fault_frac_*`, `downtime_*`) feature kimi istifadə olunur |
| Səmərəlilik | ML modeli deyil, **şəffaf formula** (izah edilə bilən KPI) |
| Tövsiyələr | Yalnız yuxarıdakı **model nəticələrinə** bağlı mətn şablonları. Hər tövsiyədə səbəb, sübut və etibarlılıq göstərilir. Hədlər `app/services/recommendations.py`-in başında sabitlərlə verilib |

Çatışan məlumat: modellərin hamısı NaN-ı özü idarə edir (`HistGradientBoosting`) və ya median ilə doldurur (anomaliya). **Heç bir ölçmə uydurulmur.** Təlim məlumatında təsadüfi boşluqlar, bütöv çatışmayan sensor sütunları və qısa tarixçələr də simulyasiya olunur.

~47 feature hesablanır (səviyyələr, 7/30/90 günlük ortalar, dəyişimlər, azalma sürəti `productionDeclineRate`, `pressureChangeRate`, `waterCutTrend`, vibrasiya/temperatur trendləri, dayanma, nasazlıq tezliyi, öz tarixçəsindən kənarlaşma və s.). Tam siyahı `GET /model/info` və `app/preprocessing/features.py` içindədir.

---

## 6. Dataset və təlim

- **Dataset:** `app/preprocessing/synthetic.py`. 280 sintetik quyu × 1000 gün: Arps hiperbolik azalma, təzyiqin eksponensial düşməsi, su payının sigmoid artımı, nasosun gizli "sağlamlıq" dəyişəninin tədricən pisləşməsi və nasazlıqlar, təsadüfi anomaliya hadisələri, çatışmayan məlumat.
- **Açıq datasetlər:** bu servisin giriş formatına (gündəlik quyu zaman sırası + nasazlıq/təmir tarixçəsi) uyğun, lisenziyası təsdiqlənmiş **açıq dataset istifadə olunmayıb**. Ona görə sintetik data seçilib. Real və ya açıq data bağlamaq üçün bölmə 9-a baxın.
- **Bölgü (temporal + quyu üzrə):** təlim quyuları gün 14-400; validasiya quyuları gün 490-580; test quyuları gün 670-909. Bölgülər arasında **90 gün boşluq** var (ən uzun proqnoz ufqu), quyular kəsişmir. Random split istifadə olunmur.
- **Sızma/overfitting yoxlamaları:** (1) gələcək məlumat istifadə olunmur (testlərdə yoxlanır), (2) yeni seed ilə yeni quyularda müstəqil qiymətləndirmə, (3) etiket qarışdırma testi (AUC≈0.5 olmalıdır), (4) train/test fərqi (`python -m training.evaluate`).
- **Təlim əmri:** `python -m training.train_all` (və ya `retrain.bat`). Artefaktlar `app/models/artifacts/` qovluğuna yazılır: `production.joblib`, `anomaly.joblib`, `risk.joblib`, `equipment.joblib`, `metadata.json` (versiya, dataset, bütün metrikalar). Versiya formatı: `1.0.0-synthetic-YYYYMMDD`.
- Hər modelin öz təlim skripti də var: `training/train_production.py`, `train_anomaly.py`, `train_risk.py`, `train_equipment.py`.

### Nəticələr (sintetik test hissəsi, görünməmiş quyular və sonrakı dövr; `python -m training.train_all` default parametrləri)
| Model | Göstərici | Nəticə |
|---|---|---|
| Hasilat 7 gün | MAE / RMSE / R² | 1.44 / 5.09 / 0.980 (sadə "dəyişməz qalacaq" bazası: MAE 2.01) |
| Hasilat 30 gün | MAE / RMSE / R² | 1.29 / 2.87 / 0.994 (baza MAE 2.44) |
| Hasilat 90 gün | MAE / RMSE / R² | 1.46 / 2.79 / 0.994 (baza MAE 3.36) |
| 80% interval | faktiki əhatə | 79.5% / 78.7% / 81.4% (7/30/90 gün) |
| Anomaliya | ROC-AUC; recall; precision | 0.94; 0.47; 0.69 |
| Risk (3 sinif) | accuracy; macro-F1; ROC-AUC | 0.79; 0.785; 0.93 (train macro-F1 0.81) |
| Nasazlıq (30 gün) | ROC-AUC; Average Precision; Brier | 0.84; 0.45; 0.058 (baza nasazlıq tezliyi 8.2%; train AUC 0.93) |

R² yüksəkdir, çünki quyular arasında hasilat fərqi böyükdür. **Əsl ölçü sadə bazaya qarşı MAE yaxşılaşmasıdır** (7/30/90 gündə təxminən 28% / 47% / 57%). Nasazlıq modelində train və test arasında AUC fərqi (0.93 vs 0.84) orta səviyyədə overfitting göstərir. Dəqiq rəqəmlər hər təlimdə bir qədər dəyişir.

> Bu rəqəmlər **sintetik datanın** xüsusiyyətlərini əks etdirir: sintetik nasazlıq prosesi sadədir. Real quyularda nəticələr fərqli (çox güman ki, daha zəif) olacaq.

---

## 7. Təhlükəsizlik

- **Servis-servis autentifikasiyası:** `X-API-Key` (uzun təsadüfi açar, `.env`-də, `hmac.compare_digest` ilə yoxlanılır). `API_KEY` təyin edilməyibsə servis bütün qorunan endpoint-lərdə 503 qaytarır (açıq qalmır).
- **`/model/retrain`:** ayrıca `X-Admin-Key` tələb edir; `ADMIN_API_KEY` boşdursa tamamilə söndürülür (403). Eyni anda yalnız bir öyrətmə gedir, köhnə modellər yalnız yeni təlim **tam** bitdikdən sonra dəyişdirilir.
- **Şəbəkə:** `run.bat` servisi yalnız `127.0.0.1`-də açır (xaricdən əlçatan deyil). Başqa serverdən çağıracaqsınızsa servisi daxili şəbəkədə saxlayın, HTTPS reverse proxy (nginx/IIS) arxasında işlədin və firewall ilə məhdudlaşdırın.
- **Ölçü limitləri:** sorğu ölçüsü (`MAX_REQUEST_BYTES`, default 5 MB, `Content-Length` ilə yoxlanılır), `history` ≤ 2000 qeyd, batch ≤ `MAX_BATCH_SIZE`. Reverse proxy-də də ölçü limiti qoyun.
- **Model faylları** `.gitignore`-dadır (Git-ə düşmür). `joblib` fayllarını **yalnız öz öyrətdiyiniz mənbədən** yükləyin (pickle formatı etibarsız fayl ilə kod icra edə bilər).
- **Məxfilik:** servis sorğu məzmununu loqlamır (yalnız xətalar və başlanğıc məlumatı). Real məlumatla işləyərkən loqlara və `datasets/` qovluğuna giriş hüququnu məhdudlaşdırın.
- Servis analitik dəstəkdir. **Mühəndis təsdiqi olmadan əməliyyat qərarı üçün istifadə edilməməlidir.**

---

## 8. Testlər

```bat
run_tests.bat          :: pytest: servis qatı + API (ilk dəfə kiçik model dəsti öyrədir, ~1 dəq)
test_endpoints.bat     :: işləyən servisi bütün endpoint-lər üzrə yoxlayır (run.bat açıq olmalıdır)
python -m training.evaluate   :: müstəqil qiymətləndirmə + sızma yoxlamaları
```
`tests/test_services.py`: cavab formatı, JSON təhlükəsizliyi (NaN yox), training/serving feature uyğunluğu, gələcək məlumat sızmaması, çatışan məlumat, enjekte edilmiş anomaliyanın aşkarlanması, zəifləmiş nasos üçün daha yüksək ehtimal, overfitting həddi, bölgü quruluşu. `tests/test_api.py`: autentifikasiya, bütün endpoint-lər, validasiya (422), batch limiti, retrain qorunması, ölçü limiti (413).

---

## 9. Real məlumata keçid

1. Real tarixi məlumatı gündəlik quyu cədvəli kimi hazırlayın (sütunlar bölmə 3.2-dəki adlarla) və nasazlıq/təmir tarixlərini ayrıca saxlayın.
2. `training/data.py` içindəki `build_dataset` funksiyasını real məlumatdan eyni sütunlarla (`FEATURE_NAMES` + hədəflər `y_ratio_*`, `fail30`, `risk_label`, `is_anomaly`) cədvəl qaytaracaq şəkildə əvəz edin. Feature-lər eyni `compute_features` ilə hesablanır, ona görə serving ilə uyğun qalır.
3. Risk etiketlərini real mühəndis qiymətləndirməsi və ya hadisələrlə əvəz edin. Onda `labelsAreSynthetic=False` təyin edin: cavabda ehtimallar da göstəriləcək.
4. Zaman üzrə bölgünü saxlayın (random split istifadə etməyin), `python -m training.evaluate` ilə yoxlayın.

---

## 10. Layihə strukturu

```
ml-service/
├── app/
│   ├── main.py                    FastAPI girişi, middleware, xəta idarəsi
│   ├── api/ (routes/, dependencies.py)   endpoint-lər, autentifikasiya
│   ├── core/ (config.py, logging.py, paths.py)
│   ├── schemas/ (well.py, responses.py)  Pydantic sxemləri
│   ├── services/                  forecast, anomaly, risk, equipment, efficiency, recommendations, quality, analysis
│   ├── models/ (bundle.py, registry.py, artifacts/)   model yükləmə, saxlanmış modellər
│   ├── preprocessing/ (features.py, synthetic.py)
│   └── utils/
├── training/  (train_all, train_production, train_anomaly, train_risk, train_equipment, evaluate, data, explain)
├── datasets/  tests/  samples/  scripts/
├── setup.bat  run.bat  test_endpoints.bat  run_tests.bat  retrain.bat
├── requirements.txt  .env.example  .gitignore  README.md
```

---

## 11. Express inteqrasiyası (qısa)

`express-integration/README.md` faylına baxın: TypeScript tipləri, timeout/təkrar cəhd və xəta idarəsi ilə `MlClient`, PostgreSQL ilə işləyən servis, controller, route və `ml_analysis_results` cədvəlinin SQL-i hazırdır. Əsas qaydalar: `.env`-də `ML_SERVICE_URL` və `ML_SERVICE_API_KEY`, sorğuda `X-API-Key` başlığı.

---

## 12. Problemlərin həlli

| Problem | Həll |
|---|---|
| `Python tapilmadi` | Python-u quraşdırarkən "Add python.exe to PATH" qutusu işarələnməyib. Python-u silib yenidən quraşdırın |
| `pip install` xətası / bağlantı xətası | İnternet və ya korporativ proxy. IT ilə əlaqə saxlayın. Python 3.14 kimi çox yeni versiyada bəzi paketlərin hazır quraşdırıcısı olmaya bilər, 3.11/3.12 istifadə edin |
| `503 Model hazır deyil` | Modellər öyrədilməyib: `retrain.bat` və ya `python -m training.train_all`, sonra servisi yenidən başladın |
| `503 API_KEY təyin edilməyib` | `.env` faylı yoxdur: `python scripts\init_env.py` |
| `401 Yanlış X-API-Key` | Express `.env`-indəki `ML_SERVICE_API_KEY`, `ml-service\.env`-dəki `API_KEY` ilə **eyni** olmalıdır |
| Port 8000 məşğuldur | `run.bat`-da `--port 8000` dəyərini dəyişin (və `ML_SERVICE_URL`-i də) |
| Nəticələrdə "köhnə məlumat" xəbərdarlığı | Son `timestamp` 3 gündən köhnədir: bu normal xəbərdarlıqdır |
| `1.0.0-synthetic` versiyası | Modellər sintetik datadadır; real data ilə yenidən öyrədin (bölmə 9) |

## 13. Məlum məhdudiyyətlər
- Real data ilə təsdiqlənməyib. Sintetik prosesin sadəliyi nəticələri real vəziyyətdən optimistik göstərir.
- `confidence` evristik göstəricidir, kalibrə olunmuş ehtimal deyil. `riskScore` da kalibrə olunmayıb.
- Sorğu ölçüsü limiti yalnız `Content-Length` başlığına əsaslanır (chunked sorğuları reverse proxy limitləməlidir).
- `estimatedDowntime` modelləşdirilmiş gözlənilən qiymətdir (ehtimal × tipik dayanma), planlaşdırılmış təmir dayanmalarını nəzərə almır.
