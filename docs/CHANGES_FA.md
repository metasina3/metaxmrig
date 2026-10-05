# تغییرات MetaXMRig 6.26.0-meta.1

## پایه و هدف نسخه

پایهٔ این نسخه، XMRig 6.26.0 با commit ثابت `b2ca72480c58d197e18c885d9fc1a0c8d517e60a` است. نسخه اصلی در بسته با نام `xmrig-baseline` قرار می‌گیرد و با همان کامپایلر، وابستگی‌ها و گزینه‌های ساخت candidate کامپایل می‌شود.

این اولین پیاده‌سازی پس از بررسی سورس RandomX است. بررسی قبلی و تست جداگانهٔ AES به‌تنهایی تغییر ماینر یا افزایش هشریت کامل محسوب نمی‌شد. هدف این ریلیز، قابل‌آزمایش‌کردن مسیر VAES512 روی CPUهای بیشتری و فراهم‌کردن مقایسهٔ قابل‌تکرار است.

## دقیقاً چه چیزی تغییر کرد؟

| فایل | تغییر و علت |
|---|---|
| `src/crypto/randomx/aes_hash.cpp` | انتخاب قابل‌کنترل VAES512، بررسی قابلیت‌های CPU/OS، جلوگیری از ورود مسیر software AES به VAES512، بررسی هم‌ترازی ۶۴ بایتی و اندازهٔ scratchpad |
| `src/crypto/randomx/aes_hash.hpp` | اعلان selector جدید برای فعال/غیرفعال‌کردن مسیر hardware AES |
| `src/crypto/rx/RxConfig.h` و `.cpp` | تنظیم `randomx.aes` با سه مقدار `auto`، `aes` و `vaes512`؛ خواندن، حفظ هنگام ذخیره و هشدار برای مقدار نامعتبر |
| `src/crypto/rx/Rx.cpp` | اعمال سیاست انتخاب قبل از شروع کار RandomX، لحاظ‌کردن `cpu.hw-aes` و چاپ مسیر واقعی و fallback در لاگ |
| `src/base/kernel/interfaces/IConfig.h` | شناسهٔ گزینهٔ CLI جدید |
| `src/core/config/Config_platform.h` و `ConfigTransform.cpp` | اتصال `--randomx-aes` به تنظیم JSON |
| `src/core/config/Config.cpp` | اعمال override خط فرمان فقط روی AES، با حفظ سایر تنظیمات `randomx` در فایل config |
| `src/core/config/usage.h` | توضیح گزینه در `--help` |
| `src/config.json` | نمونهٔ تنظیم با `"aes": "auto"` |
| `src/version.h` | نمایش نام MetaXMRig و نسخهٔ `6.26.0-meta.1`؛ اعداد سازگاری upstream حفظ شده‌اند |
| `scripts/compare_randomx.py` | اجرای آفلاین و محدود، بررسی checksum مرجع، مقایسهٔ baseline و candidate، چرخش ترتیب تست و ثبت JSON/لاگ |
| `tests/meta_aes_probe.cpp` و `scripts/test_aes.sh` | مقایسهٔ ۱۲۸ ورودی مستقل بین AES استاندارد و VAES512، سپس microbenchmark جداگانه با ۹ دور |
| `tests/test_aes_config.py` | آزمون یکپارچهٔ CLI با API محلی و CPU خاموش؛ بررسی حفظ تمام تنظیمات RandomX و fallback مقدار نامعتبر |
| `scripts/build_linux_release.sh` | ساخت استاتیک Linux x64 برای دو نسخه با وابستگی‌ها و گزینه‌های مشترک، بسته‌بندی، ثبت build info و SHA-256 |
| `.github/workflows/linux-experimental-release.yml` | ساخت و آزمون خودکار، سپس انتشار prerelease با فایل اجرایی و checksum؛ با تغییر نسخه، اسکریپت ساخت، workflow یا اجرای دستی شروع می‌شود؛ فایل‌های ریلیز موجود جایگزین نمی‌شوند |
| `release/VERSION` و `release/NOTES.md` | نسخه و توضیحات ریلیز |
| `README.md`، این فایل و `TESTING_FA.md` | معرفی فورک، شرح تغییر و روش بازتولید تست‌ها |
| `.gitignore` | حذف پوشه‌های خروجی ساخت و بنچمارک از فایل‌های commit |

## تغییر انتخاب AES چگونه کار می‌کند؟

تابع `hashAndFillAes1Rx4` در انتهای یک هش، scratchpad را می‌خواند و هم‌زمان آن را برای هش بعدی پر می‌کند. XMRig 6.26.0 یک کرنل VAES512 دارد، ولی انتخاب خودکار آن در این تابع به Zen 5 محدود بود. در MetaXMRig همان کرنل موجود قابل‌انتخاب شده است؛ الگوریتم جدیدی اختراع نشده و فایل `aes_hash_vaes512.cpp` تغییر نکرده است.

در شروع/تنظیم RandomX، selector قابلیت‌های hardware AES، VAES و AVX-512F را از تشخیص CPU موجود upstream می‌گیرد. تشخیص upstream وضعیت OSXSAVE و بیت‌های لازم XCR0 را نیز بررسی می‌کند، بنابراین صرفاً نام CPU یا یک بیت CPUID ملاک نیست. اگر برنامه بدون `WITH_VAES` ساخته شده باشد، selector همیشه fallback انتخاب می‌کند.

نتیجهٔ انتخاب با `std::atomic<bool>` ثبت می‌شود تا workerها بتوانند آن را با خواندن relaxed ببینند. داخل تابع، ورود به VAES512 فقط برای template مربوط به hardware AES مجاز است. علاوه بر قابلیت‌ها، آدرس scratchpad، خروجی hash و fill state باید همگی هم‌تراز ۶۴ بایتی باشند؛ اندازه باید حداقل ۷۱۶۸ بایت و مضرب ۱۲۸ باشد. این شروط با دسترسی‌های aligned و فاصلهٔ prefetch کرنل موجود سازگارند. در استفادهٔ معمول RandomX، scratchpad و stateها این شروط را دارند؛ در صورت عدم تطابق، مسیر استاندارد ادامه پیدا می‌کند.

`auto` همان سیاست انتخاب معماری upstream را حفظ می‌کند، همراه با بررسی‌های اضافی. `aes` برای مقایسه، مسیر VAES512 را خاموش می‌کند. `vaes512` روی CPUهای واجد شرایط مانند بعضی مدل‌های Zen 4 نیز اجازهٔ آزمایش می‌دهد. این انتخاب فقط بخش ترکیبی hash/fill را تغییر می‌دهد؛ تولید برنامه، JIT، حافظهٔ dataset، مراحل اجرای VM، تعداد iterationها و نتیجهٔ موردانتظار RandomX تغییر نکرده‌اند.

گزینهٔ CLI جدید ابتدا به یک override مستقل منتقل می‌شود و پس از خواندن تنظیمات RandomX، فقط مقدار AES را عوض می‌کند. این کار ضروری است چون JsonChain upstream آبجکت‌های تو‌در‌تو را عمیق ادغام نمی‌کند. بنابراین اضافه‌کردن `--randomx-aes` به config موجود، تنظیمات دیگر RandomX مانند MSR و prefetch را با پیش‌فرض‌ها جایگزین نمی‌کند. ابزار مقایسه هم benchmark و تمام تنظیمات CPU/RandomX را در یک JSON کامل قرار می‌دهد تا اثرهای ضمنی `--bench` روی CPU وارد آزمایش نشود.

پیش‌فرض با انتخاب پرریسک‌تر جایگزین نشده است، چون کارایی AVX-512 بین CPUها فرق می‌کند و افزایش سرعت همین مرحله ممکن است در هشریت کامل دیده نشود. در CPU فاقد قابلیت نیز درخواست صریح به اجرای دستور نامعتبر منجر نمی‌شود.

## آزمون‌ها و شواهد

نتایج کاملِ آزمون پیش از انتشار در [VALIDATION_FA.md](VALIDATION_FA.md) ثبت می‌شود. آزمون pipeline نیز به‌عنوان فایل `results.json` کنار فایل اجرایی در Release قرار می‌گیرد. نتیجهٔ CI برای صحت و قابل‌ساخت‌بودن است؛ CPU میزبان CI ممکن است VAES512 نداشته باشد و fallback را تست کند. اجرای واقعی VAES512 باید از لاگ `selected_aes` قابل‌تأیید باشد.

در بررسی اولیه، روی ماشین مجازی AMD EPYC 9V74 / Zen 4 با GCC 13.3، ۱۲۸ مقایسهٔ دقیق hash خروجی، fill state و تمام scratchpad دو مگابایتی موفق شد. microbenchmark جداگانهٔ ۹ دور، میانهٔ ۴۶٫۴۴۹ میکروثانیه برای AES128 و ۴۱٫۹۹۲ برای VAES512 نشان داد؛ throughput همان تابع حدود ۱۰٫۶۱٪ بالاتر بود. **این عدد افزایش هشریت کل ماینر نیست** و برای CPU کاربر نیز قابل تعمیم نیست.

ابزار مقایسهٔ این ریلیز checksumهای مرجع upstream را مستقلاً بررسی می‌کند، از جمله تفاوت مرجع تک‌ترد با چندترد. صرفاً exit code صفر یا شباهت دو خروجی معیار پذیرش نیست. شکست checksum، آماده‌نشدن همهٔ تردها، خروج زودهنگام یا timeout باعث شکست تست می‌شود.

## محدوده و محدودیت‌ها

- تمرکز این نسخه RandomX روی CPU و Linux x86-64 است. نسخهٔ اجرایی برای ARM/Windows/macOS تولید نشده است.
- تنظیمات huge pages، MSR، NUMA، prefetch و yield از upstream آمده‌اند. بستهٔ مقایسه، تغییر prefetch/yield را آسان می‌کند؛ این بخش‌ها در کد بهینه‌سازی جدیدی دریافت نکرده‌اند.
- فلگ سراسری `-march=native` یا `-mavx512f` اضافه نشده است. کرنل VAES512 مانند upstream با فلگ‌های جداگانه کامپایل می‌شود تا باینری اصلی به AVX-512 وابسته نباشد.
- هیچ تغییر در PoW، کیف پول، انتخاب استخر، donation، JIT یا سیاست nonce انجام نشده است. share واقعی استخر هنوز آزمایش نشده است.
- نتایج ماشین مجازی از کش، زمان‌بندی میزبان، huge pages، فرکانس و محدودیت توان تأثیر می‌گیرند. برای توصیهٔ تنظیم دائمی باید روی سیستم هدف، با تکرار و زمان کافی مقایسه شود.
- این نسخه ادعای افزایش تضمینی یا چندبرابری هشریت ندارد. اگر VAES512 کندتر بود، `aes` یا `auto` را انتخاب کن.

## منابع سورس و ساخت

- [XMRig اصلی در commit پایه](https://github.com/xmrig/xmrig/tree/b2ca72480c58d197e18c885d9fc1a0c8d517e60a)
- [کرنل VAES512 اصلی](https://github.com/xmrig/xmrig/blob/b2ca72480c58d197e18c885d9fc1a0c8d517e60a/src/crypto/randomx/aes_hash_vaes512.cpp)
- [checksumهای مرجع upstream](https://github.com/xmrig/xmrig/blob/b2ca72480c58d197e18c885d9fc1a0c8d517e60a/src/backend/common/benchmark/BenchState_test.h)
- [راهنمای تنظیم RandomX upstream](https://xmrig.com/docs/miner/randomx-optimization-guide)

مجوز پروژه GPL-3.0-or-later و اعلان‌های حقوق مؤلف upstream حفظ شده‌اند. مجوز RandomX و کتابخانه‌های استاتیک در پوشهٔ `licenses` بسته قرار می‌گیرد. سورس دقیق نسخه از tag ریلیز قابل دریافت است؛ اسکریپت ساخت، نسخه و hash وابستگی hwloc و commit baseline را مشخص می‌کند.
