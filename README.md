# SOCAR Smart Analytics — Frontend demo

Bu layihə SOCAR quyularının monitorinqi üçün hazırlanmış komponent əsaslı React + TypeScript frontend nümunəsidir.

## Quraşdırma
1. ZIP faylını çıxarın.
2. Qovluğu VS Code-da açın.
3. Terminalda:
   ```bash
   npm install
   npm run dev
   ```
4. Terminalda göstərilən lokal ünvanı brauzerdə açın.

Eyni Wi-Fi şəbəkəsində telefondan yoxlamaq üçün `npm run dev -- --host 0.0.0.0` istifadə edə bilərsiniz (package script artıq `--host 0.0.0.0` parametrini ehtiva edir).

## Səhifələr
- Ümumi göstəricilər
- Quyular (axtarış, status filtri, seçilmiş quyu detalları)
- Analitika (parametr seçimi və qrafiklər)
- Ağıllı analiz (demo model nəticələri)
- Xəbərdarlıqlar (filtr və oxunmuş kimi işarələmə)

## Komponent strukturu
- `src/components/` — təkrar istifadə edilən UI komponentləri
- `src/pages/` — hər səhifənin ayrıca komponenti
- `src/data/mockData.ts` — bütün statik demo məlumatlar
- `src/types.ts` — TypeScript tipləri
- `src/styles.css` — ümumi dizayn və responsive stillər

## Vacib
Bütün göstəricilər hazırda statik demo məlumatlardır. Bu versiyada backend, Python modeli və real SOCAR məlumatları qoşulmayıb. Real data gələndə əsasən `src/data/mockData.ts` və səhifələrdəki data mənbələri API sorğuları ilə əvəz ediləcək. Xəritə də hazırda vizual maketdir, real koordinat xəritəsi deyil.
