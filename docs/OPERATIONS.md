# دليل التشغيل: التدريب الآمن، التقييم، الاعتماد، الرجوع

القاعدة: **التدريب لا يغيّر العقل الذي يخدم المستخدمين أبدًا.** كل تدريب ينتج *مرشحًا* يُخزَّن في السجل، ولا يصير `models/router.pt` أو `models/coder.pt` إلا إذا نجح في بوابة الانحدار.

## 1. الإعداد (مرة واحدة من مستودع نظيف)

```bash
pip install -r requirements.txt                                          # الخادم والتقييم (NumPy فقط)
pip install -r requirements-train.txt --extra-index-url https://download.pytorch.org/whl/cpu   # للتدريب فقط
python -m core.lifecycle init      # يسجّل الأوزان الحالية كنسخة stable v1 ويقيسها
python -m core.lifecycle status
```

`init` آمن للتكرار: إن وُجدت نسخة stable لا يفعل شيئًا.

## 2. التقييم (بلا شبكة وبلا PyTorch)

```bash
python -m core.lifecycle evaluate router            # أداء الأوزان المخدومة لكل مهارة
python -m core.lifecycle evaluate router --version 3
python -m unittest tests.regression_gate_test tests.regression_registry_test   # اختبارات الانحدار الآلية
python -m tests.heldout                              # الاختبار القديم (يكتب models/heldout.json)
python -m tests.benchmark                            # شامل ويحتاج الإنترنت؛ يرجع exit 1 تحت الحد الأدنى
```

مجموعات القياس (`core/evalsuite.py`) تقيس **العقل وحده** بلا ناقد:

| المجموعة | العقل | المصدر |
|---|---|---|
| `heldout` | router | `tests/heldout_cases.py` (91 سؤالًا لا يُدرَّب عليها) |
| `benchmark` | router | الـ 310 سؤالًا الرسمية (النية المتوقعة فقط). تنبيه: 48 منها تطابق نص التدريب حرفيًا، لذلك `heldout` هو الأصدق |
| `coder_heldout` | coder | `tests/coder_heldout.py` (صياغتان جديدتان لكل مهمة من 45) |
| أي ملف | كلاهما | `tests/eval_extra/<brain>/*.jsonl`، كل ملف مجموعة قياس إضافية |

## 3. دورة التجربة

```bash
python -m core.lifecycle new-experiment add-skill-x --brain router --size pretrained --epochs 12 --notes "..."
python -m core.trainer --experiment add-skill-x          # يدرّب مرشحًا ثم يشغّل البوابة ويعرض الحكم
python -m core.trainer router pretrained 12 --promote    # أو: يعتمده تلقائيًا فقط إذا نجح في البوابة
python -m core.trainer router medium 12 --no-review      # يخزّن المرشح فقط
```

ما يحدث بعد التدريب (`core/lifecycle.py`):

1. المرشح يُخزَّن `models/registry/<brain>/vN/` بحالة `candidate` مع sha256 وبصمة بيانات التدريب ومعاملاته (`seed`, `epochs_run`, `truncated`, `git_commit`, `torch`).
2. **`review`**: تُقاس أوزان stable الحالية وأوزان المرشح على نفس الأسئلة، وتُقارَن مهارة بمهارة.
3. الحكم: `gated-pass` أو `rejected` (لا يمكن اعتماد المرفوض أبدًا).
4. **`promote`**: ينسخ الأوزان إلى `models/<brain>.pt` ذريًا بعد التحقق من sha256، ويؤرشف النسخة السابقة.

```bash
python -m core.lifecycle review router 3        # exit 0 = نجح، 1 = رُفض
python -m core.lifecycle promote router 3       # يتطلب مراجعة ناجحة ضد نفس stable الحالية
python -m core.lifecycle reject router 3 --reason "لماذا"
```

### قواعد الرفض (`models/gate.json`)

| الحد | الافتراضي | المعنى |
|---|---|---|
| `max_overall_drop` | 0.01 | أقصى نزول لدقة المهارات المعروفة مجتمعة، في كل مجموعة قياس |
| `max_skill_drop` | 0.05 | أقصى نزول لأي مهارة منفردة (يُغيَّر لمهارة بعينها في `skill_overrides`) |
| `min_new_skill_accuracy` | 0.80 | أدنى دقة لمهارة جديدة لم تكن في stable |

ويُرفض المرشح أيضًا إذا فقد نية كانت في stable. تغيير الحدود يتم بتعديل `models/gate.json` ويظهر في git.

## 4. الرجوع إلى نسخة مستقرة

```bash
python -m core.lifecycle status                  # كل النسخ وحالاتها
python -m core.lifecycle rollback router         # يعود للنسخة التي حلّت stable مكانها
python -m core.lifecycle rollback router --to 2  # أو لنسخة محددة (غير مرفوضة)
```

الأوزان تُسترجع من `models/registry/<brain>/vN/model.pt` بعد فحص sha256. إذا لم تكن الأوزان على الجهاز (فهي لا تُرفع إلى git عدا النسخة المخدومة) استرجع الملف من تاريخ git إلى مكان مؤقت (`git show <commit>:models/router.pt > /tmp/old.pt`) ثم سجّله كمرشح يمرّ على البوابة: `python -m core.lifecycle import router /tmp/old.pt` ثم `review` و`promote`.

## 5. إضافة مهارة جديدة دون المساس بالمستقر

1. أضف نية جديدة في `core/templates_router.py` (`INTENTS` و`TEMPLATES`).
2. اكتب أسئلة اختبارها **قبل التدريب** في `tests/eval_extra/router/<skill>.jsonl` بصيغة `{"q": "...", "intent": "<skill>"}`، صياغات لا تشبه القوالب.
3. `new-experiment` ثم `trainer --experiment ...`.
4. البوابة تحكم: المهارة الجديدة ≥ 80%، وكل مهارة قديمة ضمن الحدود. لا شيء يُكتب فوق `models/router.pt` قبل النجاح.

## 6. هيكل الحفظ

```
models/
  router.pt  coder.pt              العقلان المخدومان (stable) — يُرفعان إلى git ويقرأهما الخادم
  gate.json                        حدود البوابة
  versions.json                    سجل قديم للوحة المطوّر (للقراءة)
  heldout.json  benchmark.json     آخر نتائج الاختبارات القديمة
  registry/
    <brain>/stable.json            النسخة المستقرة والنسخ التي حلّت محلها
    <brain>/history.jsonl          سجل تدقيق append-only (added/review/promote/rollback/rejected)
    <brain>/vN/meta.json           الحالة، sha256، معاملات التدريب، نتائج التقييم، حكم البوابة (يُرفع)
    <brain>/vN/model.pt            الأوزان (لا تُرفع إلى git)
    experiments/<name>.json        إعداد التجربة (brain, size, epochs, notes)
data/custom_examples.jsonl         أمثلة علّمها المطوّر (تُدرَّب بوزن 8)
tests/eval_extra/                  أسئلة اختبار إضافية لكل مهارة
```

## 7. ملاحظات

- `val_acc` في التدريب مقياس سلامة فقط (بيانات مولّدة من قوالب). المرجع هو البوابة.
- `truncated: true` في meta يعني أن سقف الوقت (`SADAH_MAX_TRAIN_SECONDS`) أوقف التدريب قبل اكتمال الحلقات.
- لوحة المطوّر (`TrainingJob`) تعيد تحميل العقل الحي فقط إذا نجح المرشح في البوابة.
- `Dockerfile` يدرّب عند غياب الأوزان بـ `--promote`: أول نسخة تُعتمد بلا مقارنة لأنه لا يوجد ما يُقارَن به.

## 8. المنشئ (builder)

- **الاختبارات** (بلا شبكة): `python -m tests.builder_stage1_test` و`tests.builder_stage2_test` و`tests.builder_api_test`.
- **القياس**: `builder.evaluate.evaluate(suite=...)` يعيد تقريرًا بشكل تقرير البوابة نفسه، فيعمل `core.gate.compare` عليه لرفض أي تراجع في مهارة (landing/dashboard/shop/webapp/ask/refuse).
- **قاعدة المجموعة المحجوزة**: `tests/builder_heldout.py` تُقاس مرة واحدة قبل أي ضبط للقواعد؛ بعدها تُنقل حالاتها إلى `tests/builder_requests.py` (`SUITE`) وتُكتب مجموعة محجوزة جديدة. لا تضبط القواعد على حالة ما زالت محجوزة.
- **ميزة جديدة غير مدعومة**: أضف كلمتها إلى `OUT_OF_SCOPE` في `builder/understand.py` حتى يرفضها المنشئ صراحة بدل أن يتجاهلها.
- **الأمان**: الملفات المسموحة `index.html` و`style.css` و`app.js` فقط، و`app.js` نص ثابت من القالب لا يتغير بالطلب؛ معاينة الواجهة داخل iframe بلا `allow-same-origin`.
- **لم يُختبر هنا**: تشغيل `app.py` فعليًا (FastAPI غير مثبّت في بيئة التطوير)، وعرض كل القوالب في متصفح حقيقي (فُحصت صفحة الهبوط بصريًا فقط).

