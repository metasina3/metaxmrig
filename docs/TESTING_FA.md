# نصب و تست MetaXMRig 6.26.0-meta.2

این نسخه یک **پیش‌انتشار آزمایشی Linux x86-64 و ARM64، ساخته‌شده در Alpine با musl استاتیک** است. بسته شامل `metaxmrig`، نسخه اصلی `xmrig-baseline` از XMRig 6.26.0، ابزار مقایسه، اطلاعات ساخت و مجوزهاست. هدف نسخهٔ جدید، قابل‌اجراکردن همین کد روی توزیع‌های مختلف لینوکس است؛ این تغییر به‌خودی‌خود ادعای افزایش هشریت ندارد. VAES512 فقط روی CPUهای x86-64 واجد شرایط قابل اجراست؛ روی ARM64 به مسیر موجود upstream برمی‌گردد.

## دریافت و اجرای اولین تست

فایل‌های `.tar.gz` و `.sha256` را از [Releases همین ریپو](https://github.com/metasina3/metaxmrig/releases) دانلود کن. در پوشهٔ دانلود:

```bash
sha256sum -c metaxmrig-6.26.0-meta.2-linux-musl-x64.sha256
tar -xzf metaxmrig-6.26.0-meta.2-linux-musl-x64.tar.gz
cd metaxmrig-6.26.0-meta.2-linux-musl-x64
./metaxmrig --version
python3 compare_randomx.py --threads 4 --rounds 3 --output test-4-threads
```

تست بالا بدون استخر و بدون ارسال نتیجه به سرویس بنچمارک اجرا می‌شود. به اینترنت، والت و `sudo` نیاز ندارد. در هر دور، نسخه اصلی، MetaXMRig با `aes` و MetaXMRig با `vaes512` به‌ترتیب اجرا می‌شوند؛ ترتیب بین دورها می‌چرخد. هر اجرا ۲۵۰ هزار هش محاسبه می‌کند، checksum مرجع را بررسی می‌کند و سپس برنامه را می‌بندد. در مجموع ۹ اجراست؛ زمان آن به CPU بستگی دارد. برای اولین بررسی کوتاه‌تر `--rounds 1` بگذار.

`--threads 4` صرفاً نمونه است. تعداد مناسب را با هسته‌های CPU و کش L3 خودت انتخاب کن؛ بیشترکردن تعداد تردها همیشه هشریت را بالا نمی‌برد. اگر CPU را نمی‌شناسی، ابتدا `lscpu` را بررسی کن. عدد ترد در تمام نسخه‌ها یکسان اعمال می‌شود.

با `uname -m` معماری را مشخص کن: برای `x86_64` بستهٔ `x64` و برای `aarch64` بستهٔ `arm64` را بگیر. برای ARM64 در فرمان‌های بالا `x64` را با `arm64` عوض کن. باینری ARM64 طبق target موجود upstream به ARMv8 با پشتیبانی AES نیاز دارد.

اگر `python3` نصب نیست، روی Ubuntu/Debian با `sudo apt-get install python3` یا روی Alpine با `apk add python3` نصبش کن. خود فایل‌های اجرایی به Python یا نصب libuv/hwloc/OpenSSL/musl نیاز ندارند. ساخت واقعی داخل Alpine 3.22.6 انجام می‌شود و نبودن loader دینامیک و وابستگی shared با `readelf` بررسی می‌شود. تست‌های راه‌اندازی، API محلی و TLS محلی روی چند توزیع پیش‌شرط انتشارند. دامنهٔ سازگاری و روش بازتولید در [PORTABILITY_FA.md](PORTABILITY_FA.md) آمده است؛ همهٔ کرنل‌ها و سخت‌افزارهای ممکن آزمایش نشده‌اند.

## معنی گزینهٔ جدید

```bash
./metaxmrig -c /path/to/your-config.json --randomx-aes=vaes512
```

در JSON نیز می‌توانی داخل بخش `randomx` اضافه کنی:

```json
"aes": "vaes512"
```

| مقدار | رفتار |
|---|---|
| `auto` | پیش‌فرض؛ سیاست XMRig اصلی: انتخاب VAES512 برای Zen 5 واجد شرایط، مسیر استاندارد برای سایر CPUها |
| `aes` | مسیر استاندارد AES را انتخاب می‌کند؛ اگر hardware AES غیرفعال باشد، مسیر نرم‌افزاری باقی می‌ماند |
| `vaes512` | درخواست مسیر VAES512 حتی روی CPUهای دیگر؛ فقط با hardware AES فعال و پشتیبانی AES، VAES، AVX-512F و وضعیت مناسب سیستم‌عامل اجرا می‌شود |

در شروع RandomX به خط زیر دقت کن:

```text
AES implementation: vaes512 (requested: vaes512)
```

اگر CPU یا ساخت برنامه پشتیبانی نکند، انتخاب به مسیر استاندارد برمی‌گردد و پیغام `using fallback` چاپ می‌شود. اگر `hw-aes: false` باشد، درخواست VAES512 به مسیر نرم‌افزاری برمی‌گردد. مقدار نامعتبر مثل `vaes256` با هشدار به `auto` برمی‌گردد. بررسی هم‌ترازی حافظه نیز داخل تابع انجام می‌شود؛ ورودی نامناسب از مسیر استاندارد می‌گذرد.

برای استخراج نمونهٔ config از تنظیمات ذخیره‌شده، XMRig همچنان از همان روش قبلی استفاده می‌کند. JSON بالا تنها یک عضو جدید است؛ آن را به config موجود اضافه کن و فایل را با همین تکه جایگزین نکن. کلید جدید هنگام ذخیرهٔ تنظیمات حفظ می‌شود. برای برگشت به انتخاب پیش‌فرض، `auto` بگذار یا گزینه را حذف کن.

## خواندن خروجی مقایسه

در پوشهٔ انتخاب‌شده با `--output` این فایل‌ها ساخته می‌شوند:

- `results.json`: مشخصات سیستم، تنظیمات، زمان/هشریت هر اجرا، مسیر انتخاب‌شده، checksum و میانهٔ نتیجه‌ها.
- فایل‌های `.log`: لاگ کامل هر تست شامل تردهای آماده و وضعیت واقعی huge pages.
- فایل‌های `.stdout.log`: خطاهای احتمالی قبل از راه‌افتادن logger.
- فایل‌های `.config.json`: تنظیم دقیق همان اجرا، برای بازتولید نتیجه.

`vs_upstream_percent` اختلاف میانه با نسخه اصلی است. مقدار مثبت یعنی در همین آزمایش سریع‌تر بوده، مقدار منفی یعنی کندتر. برای نتیجهٔ قابل‌اعتماد، برنامه‌های سنگین دیگر را ببند، دمای CPU و محدودیت توان را یکسان نگه دار، تست را چند بار تکرار کن و اختلاف را با بازهٔ `min_hs` و `max_hs` مقایسه کن. افزایش کوچک‌تر از نوسان اجراها دلیل کافی برای سریع‌ترشدن نیست.

اگر برای `vaes512` فیلد `selected_aes` برابر `aes` باشد، آن تست در واقع مسیر fallback را اجرا کرده است. اگر checksum یا تعداد تردهای آماده اشتباه باشد، ابزار با خطا متوقف می‌شود؛ زمان نامحدود اجرا نمی‌شود. timeout هر اجرا به‌صورت پیش‌فرض ۹۰۰ ثانیه است و می‌توان با `--timeout 1800` تغییرش داد. پوشهٔ نتیجه را برای هر آزمایش جدید عوض کن؛ ابزار روی `results.json` قبلی بازنویسی نمی‌کند.

## آزمایش دقیق‌تر و تنظیمات بعدی

```bash
# مقایسه با یک میلیون هش در هر اجرا
python3 compare_randomx.py --threads 8 --rounds 3 --size 1M --output test-1m

# تست هر دو نوع RandomX موجود در این نسخه
python3 compare_randomx.py --threads 8 --rounds 1 --algorithms rx/0 rx/2 --output test-both

# مقایسهٔ دو مسیر داخل خود MetaXMRig، بدون فایل baseline
python3 compare_randomx.py --skip-baseline --threads 4 --rounds 3 --output test-modes

# تست سیاست پیش‌فرض نیز کنار دو انتخاب اجباری
python3 compare_randomx.py --modes auto aes vaes512 --threads 4 --rounds 3 --output test-auto

# آزمایش جداگانهٔ تنظیم موجود yield
python3 compare_randomx.py --threads 8 --rounds 3 --no-yield --output test-no-yield

# آزمایش یکی از حالت‌های موجود prefetch؛ مقدار مجاز 0، 1، 2 یا 3 است
python3 compare_randomx.py --threads 8 --rounds 3 --prefetch 2 --output test-prefetch-2

# استفاده از huge pages، اگر روی سیستم خودت قبلاً آماده شده باشد
python3 compare_randomx.py --threads 8 --rounds 3 --huge-pages --output test-huge-pages
```

ابزار به‌صورت پیش‌فرض huge pages و نوشتن MSR را خاموش می‌کند تا اولین تست بدون تغییر تنظیمات سیستم اجرا شود. تغییر prefetch و yield امکانات موجود XMRig هستند؛ در این فورک بازنویسی نشده‌اند. پارامترها در baseline و candidate یکسان‌اند. هر بار یک پارامتر را عوض کن تا علت اختلاف مشخص بماند. مسیر `vaes512` ممکن است در بعضی CPUها به‌دلیل هزینهٔ AVX-512 یا رفتار کش کندتر شود.

برای تست استخر، config فعلی خودت را به `metaxmrig` بده و فقط `--randomx-aes=vaes512` را اضافه کن. الگوریتم اعلام‌شده توسط استخر را ملاک قرار بده. به نرخ shareهای پذیرفته‌شده، هشریت پایدار و دما توجه کن؛ چند ثانیه هشریت لحظه‌ای کافی نیست. این ریلیز آزمون share واقعی استخر را انجام نداده است. تنظیمات استخر، والت و کارمزد upstream در کد تغییر نکرده‌اند.

## ساخت از سورس

```bash
git clone --branch v6.26.0-meta.2 https://github.com/metasina3/metaxmrig.git
cd metaxmrig
docker run --rm -v "$PWD:/src" -w /src alpine:3.22.6 sh -ec '
  apk add --no-cache bash build-base cmake git curl linux-headers binutils \
    libuv-dev libuv-static openssl-dev openssl-libs-static openssl \
    autoconf automake libtool python3 pkgconf
  bash scripts/build_alpine_release.sh
'
```

روی خود Alpine، ابتدا همان `apk add` و سپس `bash scripts/build_alpine_release.sh` را اجرا کن؛ Docker لازم نیست. این اسکریپت hwloc 2.12.1 را با SHA-256 ثابت دریافت و به‌صورت استاتیک می‌سازد، سپس فورک و commit ثابت XMRig اصلی را با فلگ‌های یکسان می‌سازد. خروجی در `build-release` است. `BUILD_JOBS=8` تعداد jobهای ساخت را تغییر می‌دهد. CI معماری x64 و ARM64 را روی runnerهای بومی جدا می‌سازد؛ ساخت با شبیه‌ساز یا cross compiler نیست. فایل `BUILD_INFO.txt` داخل بسته، commit سورس، تصویر container، کامپایلر و نسخهٔ وابستگی‌های واقعی را ثبت می‌کند.

بستهٔ این ریلیز مخصوص ماینینگ CPU است؛ OpenCL، CUDA، KawPow و GhostRider در ساخت بسته غیرفعال‌اند. سایر گزینه‌های CPU upstream حفظ شده‌اند. سورس ریپو هنوز قابلیت ساخت backendهای دیگر را دارد. فایل ویندوز، macOS و اندروید در این ریلیز ارائه نشده است؛ فایل Alpine استاتیک همچنان executable لینوکس است.

## چه اطلاعاتی برای مرحلهٔ بعد بفرستی؟

`results.json` و لاگ تست‌ها را همراه با خروجی `lscpu`، `free -h` و هشریت پایدار فعلی بفرست. اگر تست استخر انجام دادی، قبل از ارسال لاگ، آدرس والت و اطلاعات حساب/استخر خصوصی را حذف کن. بر اساس نتیجه می‌توانیم تعداد ترد، چیدمان هسته‌ها، prefetch و مسیر AES مناسب CPU تو را انتخاب کنیم.
