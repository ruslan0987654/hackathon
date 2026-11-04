# Express + TypeScript inteqrasiyası

Bu qovluqdakı fayllar mövcud Express backend-inizə əlavə olunur. Backend PostgreSQL-dən quyu məlumatını oxuyur, ML servisinə (`ml-service`) HTTP ilə göndərir və nəticəni bazada saxlayır.

```
express-integration/
├── .env.example                      ML_SERVICE_URL, ML_SERVICE_API_KEY, timeout, retry
├── sql/001_ml_analysis_results.sql   nəticə tarixçəsi cədvəli
├── src/ml/mlTypes.ts                 TypeScript request/response interface-ləri
├── src/ml/mlClient.ts                ML client (timeout, təkrar cəhd, xəta sinfi), əlavə paket tələb etmir
├── src/ml/mlService.ts               PostgreSQL oxuma + ML çağırışı + nəticəni saxlama
├── src/controllers/mlController.ts   Express controller + xəta xəritələməsi
├── src/routes/mlRoutes.ts            router (buildMlRouter)
└── tsconfig.example.json
```

## Quraşdırma (5 addım)

1. **Faylları kopyalayın:** `src/ml/`, `src/controllers/mlController.ts`, `src/routes/mlRoutes.ts` fayllarını öz backend layihənizin `src/` qovluğuna köçürün (yolları öz strukturunuza uyğun düzəldin).
2. **Asılılıqlar** (yoxdursa): `npm install pg` və `npm install -D @types/pg @types/express @types/node`. `MlClient` Node.js **18+** daxili `fetch`-dən istifadə edir.
3. **`.env`:** `.env.example`-dəki dəyişənləri backend `.env`-inə əlavə edin. `ML_SERVICE_API_KEY` = `ml-service\.env` faylındakı `API_KEY`.
4. **Cədvəl:** `psql -U <istifadəçi> -d <baza> -f sql/001_ml_analysis_results.sql`
5. **Router-i qoşun** (mövcud `app.ts`/`server.ts` daxilində):
   ```ts
   import { buildMlRouter } from './routes/mlRoutes';
   // pool = mövcud pg.Pool; yourAuthMiddleware = layihənizdəki autentifikasiya (JWT və s.)
   app.use('/api/ml', yourAuthMiddleware, buildMlRouter(pool));
   ```

## ⚠️ Mütləq uyğunlaşdırılmalı: SQL sütun adları

`src/ml/mlService.ts` içində `loadWell` metodundakı iki `SELECT` sorğusu **nümunə** `wells` və `well_measurements` cədvəllərini fərz edir. Öz cədvəl və sütun adlarınıza uyğun dəyişin (və `toRecord` funksiyasındakı `r.sütun_adı` xəritələməsini). Başqa heç nə dəyişməlidir. Vahidlər: hasilat `t/gün`, təzyiq `bar`, temperatur `°C`, `waterCut` və `pumpEfficiency` faizlə (0-100), saatlar 0-24. Bazada olmayan göstəricilər üçün `NULL` buraxın (0 yazmayın).

## Endpoint-lər (Express tərəfdə)

| Metod | Yol | Təsvir |
|---|---|---|
| GET | `/api/ml/health` | ML servisinin vəziyyəti |
| POST | `/api/ml/wells/:wellId/analyze?days=120&save=true` | Quyunu bazadan oxuyub tam analiz edir və saxlayır |
| POST | `/api/ml/analyze-batch` | Body: `{"wellIds": ["W-1","W-2"]}` (1-50 quyu) |
| GET | `/api/ml/wells/:wellId/history?limit=30` | Saxlanmış analiz tarixçəsi |

Sınaq:
```bash
curl -X POST "http://localhost:3000/api/ml/wells/W-1/analyze?days=120" -H "Authorization: Bearer <token>"
```

## Xəta davranışı

- ML servisi söndürülüb / cavab vermir / `503` → Express `503` qaytarır (müvəqqəti xətalarda `ML_SERVICE_RETRIES` qədər avtomatik təkrar cəhd).
- `422` (yanlış məlumat) təkrar cəhd olunmur, detal frontend-ə ötürülür.
- `401/403` (yanlış API açarı) daxili konfiqurasiya xətası sayılır: istifadəçiyə `502` göstərilir, detal yalnız serverin logunda qalır.
- Quyu bazada yoxdursa `404`.

## Frontend üçün qeydlər

- `null` dəyərləri "hesablanmayıb" deməkdir. Onları `0` kimi göstərməyin; `componentStatus` səbəbi izah edir.
- `dataBasis === 'synthetic'` olduqda UI-da "Test rejimi: sintetik model" xəbərdarlığı göstərmək tövsiyə olunur.
- `recommendations[]` tövsiyədir, əmr deyil: `requiresEngineerReview` həmişə `true`-dur.
