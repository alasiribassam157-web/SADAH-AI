# تدريب عقل SADAH التوليدي على Kaggle

عقل يكتب جملاً بنفسه (مو يختار من قوالب)، يتدرب من الصفر على بيانات عربية + إنجليزية (ويكيبيديا كاملة
بالعربي + جزء إنجليزي)، بدون أي اتصال بنموذج خارجي.

## خطوات التشغيل على Kaggle (مرة واحدة فقط)

1. ادخل https://www.kaggle.com/code → **New Notebook**.
2. من القائمة يمين: **Settings → Accelerator → GPU T4 x2** (أو P100 إذا توفر).
3. **Settings → Internet → On** (لازم عشان يحمّل الكود من GitHub وبيانات ويكيبيديا).
4. في أول خلية (Cell) الصق:

```python
!git clone --depth 1 https://github.com/alasiribassam157-web/SADAH-AI.git
%cd SADAH-AI
!pip install -q -r gpu/requirements.txt
```

5. في خلية ثانية، شغّل التدريب (يوقف تلقائياً قبل ما تنتهي الـ 12 ساعة بـ 20 دقيقة ويحفظ):

```python
!python -m gpu.train_gpt --size large --hours 11.5
```

6. قبل ما تنتهي الجلسة: **File → Save Version → Save & Run All (Commit)**.
   هذا يحفظ `checkpoints/gpt/ckpt.pt` + `tokenizer.json` + `train.bin`/`val.bin` كـ **Output** للـ notebook،
   حتى لو الجلسة قفلت.

## كيف تكمل التدريب في الأسبوع الجاي

1. افتح نفس الـ notebook → **Add Input → Notebook Output Files** → اختر نفس النوتبوك (نسخته القديمة).
   هذا يحط ملف `ckpt.pt` القديم تحت `/kaggle/input/...`.
2. شغّل نفس خلايا التثبيت، وبعدين:

```python
!python -m gpu.train_gpt --size large --hours 11.5
```

السكربت يلقى `ckpt.pt` القديم تلقائياً (من `/kaggle/input/`) ويكمل من نفس الخطوة، بدون ما يبدأ من
الصفر، وبدون ما يعيد تجهيز التوكنايزر أو البيانات.

كرر هذا كل أسبوع (30 ساعة GPU متاحة أسبوعياً في Kaggle) إلى أن يوصل العقل للمستوى المطلوب.

## تنزيل الأوزان لجهازك

من صفحة الـ notebook → **Output** → نزّل `ckpt.pt` و `tokenizer.json`، وحطهم في:
`models/gpt/ckpt.pt` و `models/gpt/tokenizer.json` على جهازك، وأنا أربطهم بالسيرفر.

## Data pipeline (stage 1 of the generative plan)

- `data/sources.json`: every text source with its license; `gpu/sources.py` refuses any source that is not human-written and `approved`. A dataset's `sources.json` manifest is written beside `train.bin`.
- `gpu/clean.py`: normalisation, quality filters, near-duplicate removal, and a leak guard that drops any text sharing a 4-6 word run with a held-out evaluation question.
- Test: `python -m tests.gen_data_test` (offline, no PyTorch).
