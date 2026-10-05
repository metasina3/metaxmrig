# MetaXMRig 6.26.0-meta.2 — Alpine static Linux x64 / ARM64

این پیش‌انتشار، همان تغییرات AES نسخهٔ قبلی را با بسته‌های کاملاً استاتیک musl برای توزیع‌های مختلف لینوکس ارائه می‌کند. ساخت واقعی داخل Alpine 3.22.6 انجام می‌شود؛ x64 و ARM64 روی runnerهای بومی جدا ساخته می‌شوند.

## تغییرات نسبت به meta.1

- لینک کامل musl، libuv، OpenSSL و hwloc؛ نبود loader دینامیک یا وابستگی shared در هر دو executable بررسی می‌شود.
- بستهٔ Linux x86-64 و بستهٔ جداگانهٔ Linux ARM64 با target موجود upstream (ARMv8 crypto/AES).
- اجرای همان فایل در Alpine 3.20، Ubuntu 22.04/24.04، Debian 12 و Rocky Linux 9؛ بررسی version، API/حفظ تنظیمات و TLS محلی با fingerprint/SNI صحیح.
- صحت کامل checksum رسمی ۲۵۰ هزار هش rx/0 برای MetaXMRig و XMRig اصلی روی هر دو معماری.
- اطلاعات ساخت، digest تصویر Alpine، نسخهٔ کتابخانه‌ها و مجوزهای runtime همراه بسته هستند.

کد PoW، JIT، nonce، pool، wallet و donation تغییر نکرده است. انتخاب `--randomx-aes=auto|aes|vaes512` همچنان وجود دارد و پیش‌فرض auto باقی می‌ماند. VAES512 فقط روی x86-64 واجد قابلیت قابل اجراست؛ روی ARM64 یا CPU فاقد قابلیت به مسیر استاندارد برمی‌گردد. **musl یا VAES512 افزایش قطعی هشریت را تضمین نمی‌کنند.**

## انتخاب فایل دانلود

| سیستم | فایل |
|---|---|
| Intel/AMD، خروجی uname -m برابر x86_64 | metaxmrig-6.26.0-meta.2-linux-musl-x64.tar.gz |
| ARM64 با AES، خروجی uname -m برابر aarch64 | metaxmrig-6.26.0-meta.2-linux-musl-arm64.tar.gz |

هر بسته شامل `metaxmrig`، نسخهٔ اصلی `xmrig-baseline` از commit ثابت XMRig 6.26.0، ابزار مقایسه، مستندات فارسی، اطلاعات ساخت و مجوزهاست. فایل `.sha256` برای بررسی دانلود است. Python فقط برای ابزار مقایسه لازم است؛ خود miner به نصب musl، OpenSSL، libuv یا hwloc نیاز ندارد.

```bash
sha256sum -c metaxmrig-6.26.0-meta.2-linux-musl-x64.sha256
tar -xzf metaxmrig-6.26.0-meta.2-linux-musl-x64.tar.gz
cd metaxmrig-6.26.0-meta.2-linux-musl-x64
python3 compare_randomx.py --threads 4 --rounds 1 --output first-test
```

برای ARM64، در نام فایل‌ها `x64` را با `arm64` جایگزین کن. برای مقایسهٔ دقیق‌تر `--rounds 3` بگذار. تست آفلاین بدون استخر، والت و ارسال نتیجه است و huge pages/نوشتن MSR را پیش‌فرض خاموش می‌کند. برای ماینینگ با تنظیمات خودت:

```bash
./metaxmrig -c /path/to/your-config.json --randomx-aes=auto
```

آرشیوهای `verification-x64.tar.gz` و `verification-arm64.tar.gz` شامل checksum، تنظیمات و لاگ آزمون کامل‌اند؛ `portability-x64.tar.gz` و `portability-arm64.tar.gz` لاگ سازگاری توزیع‌ها را دارند. اطلاعات دقیق فایل ساخته‌شده در `BUILD_INFO.txt` هر بسته است.

تست توزیع‌ها در containerهای دارای kernel مشترک runner انجام شده؛ همهٔ kernelها و سخت‌افزارها آزمایش نشده‌اند. آزمون TLS یک fixture محلی بدون job است و پذیرش share واقعی استخر را ثابت نمی‌کند. بسته‌ها مخصوص CPU هستند؛ OpenCL/CUDA/KawPow/GhostRider در این ساخت غیرفعال‌اند. Windows، macOS، Android و معماری‌های ۳۲ بیتی در این ریلیز ارائه نمی‌شوند.

- [نصب و تست](https://github.com/metasina3/metaxmrig/blob/v6.26.0-meta.2/docs/TESTING_FA.md)
- [تمام تغییرات و نحوهٔ پیاده‌سازی](https://github.com/metasina3/metaxmrig/blob/v6.26.0-meta.2/docs/CHANGES_FA.md)
- [ساخت Alpine و سازگاری لینوکس](https://github.com/metasina3/metaxmrig/blob/v6.26.0-meta.2/docs/PORTABILITY_FA.md)
- [صحت و محدودیت نتایج](https://github.com/metasina3/metaxmrig/blob/v6.26.0-meta.2/docs/VALIDATION_FA.md)

پایهٔ baseline: `b2ca72480c58d197e18c885d9fc1a0c8d517e60a`. مجوزها، credits و donation upstream حفظ شده‌اند؛ این fork ریلیز رسمی تیم XMRig نیست.
