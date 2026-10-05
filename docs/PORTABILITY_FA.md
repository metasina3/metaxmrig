# ساخت Alpine و سازگاری توزیع‌های لینوکس

## هدف

MetaXMRig `6.26.0-meta.2` داخل **Alpine 3.22.6** با **musl** و `BUILD_STATIC=ON` ساخته می‌شود. libuv و OpenSSL صریحاً از فایل‌های `.a` لینک می‌شوند و hwloc 2.12.1 با قابلیت topology/NUMA و بدون وابستگی به plugin، libudev، libxml2، libnuma یا cairo ساخته می‌شود. libc و runtime C++ هم داخل executable قرار می‌گیرند.

این روش نیاز به loader و کتابخانه‌های glibc/musl نصب‌شده روی توزیع مقصد را حذف می‌کند. لازم نیست Alpine، Docker، compiler یا کتابخانه‌های توسعه را روی سیستم مقصد نصب کنی؛ کافی است بستهٔ متناسب با معماری را استخراج کنی. Python فقط برای اسکریپت مقایسه لازم است.

## انتخاب بسته

| خروجی `uname -m` | بسته | شرط CPU |
|---|---|---|
| `x86_64` | `metaxmrig-6.26.0-meta.2-linux-musl-x64.tar.gz` | Linux x86-64؛ AES/VAES طبق تشخیص runtime upstream انتخاب می‌شوند |
| `aarch64` | `metaxmrig-6.26.0-meta.2-linux-musl-arm64.tar.gz` | ARMv8 با crypto/AES؛ همان target موجود upstream |

VAES512 مخصوص بعضی CPUهای x86-64 است. درخواست آن روی ARM64 یا x86 فاقد قابلیت به مسیر استاندارد برمی‌گردد. بستهٔ ARM64 برای همهٔ تراشه‌های ARM قدیمی مناسب نیست. این فایل‌ها executable لینوکس هستند و به‌تنهایی روی Windows/macOS/Android اجرا نمی‌شوند.

## چه چیزی بررسی می‌شود؟

workflow به نام `Alpine static Linux release` دو runner بومی `ubuntu-24.04` و `ubuntu-24.04-arm` دارد. Ubuntu فقط میزبان Docker است؛ compiler، headers و تمام کتابخانه‌های لینک‌شده از **داخل Alpine** می‌آیند. digest تصویر واقعی Docker و فهرست نسخه‌های APK در BUILD_INFO ثبت می‌شوند. checksum ثابت hwloc و commit ثابت upstream در اسکریپت قرار دارند. بسته‌های APK از شاخهٔ Alpine 3.22 گرفته می‌شوند؛ نسخهٔ دقیقشان ثبت می‌شود، ولی rebuild آینده تضمین byte-for-byte ندارد.

قبل از بسته‌بندی، `readelf -l` و `readelf -d` نبودن loader دینامیک `INTERP` و وابستگی کتابخانه‌ای `NEEDED` را بررسی می‌کنند. خروجی این دو دستور برای هر executable همراه بسته ذخیره می‌شود. بعد، baseline و candidate یک بنچمارک کامل ۲۵۰ هزار هش `rx/0` انجام می‌دهند و checksum رسمی بررسی می‌شود.

برای هر معماری، **همان فایل ساخته‌شده** روی این محیط‌ها اجرا می‌شود؛ روی توزیع مقصد دوباره کامپایل نمی‌شود:

| محیط runtime | خانواده | بررسی |
|---|---|---|
| Alpine 3.22.6 و 3.20 | musl | راه‌اندازی، تنظیمات/API و TLS محلی |
| Ubuntu 22.04 و 24.04 | glibc / Ubuntu | همان بررسی‌ها |
| Debian 12 `bookworm-slim` | glibc / Debian | همان بررسی‌ها |
| Rocky Linux 9 | glibc / RHEL | همان بررسی‌ها |

دو executable قبل از نصب Python/openssl مربوط به ابزار تست، با `--version` در تصویر تمیز اجرا می‌شوند. هیچ libuv یا hwloc در تصویر مقصد نصب نمی‌شود. تست TLS خودش گواهی موقت تولید می‌کند، fingerprint صحیح را به miner می‌دهد، نام localhost و SNI را بررسی می‌کند و تنها پیام login را دریافت می‌کند؛ CPU خاموش است و هیچ job یا share ارسال نمی‌شود.

Ubuntu-basedهایی مثل Linux Mint و Zorin و سایر توزیع‌های هم‌معماری از همین روش مستقل از libc استفاده می‌کنند، اما در این workflow جداگانه آزمایش نشده‌اند. همهٔ توزیع‌ها، مدل‌های CPU یا kernelهای قدیمی قابل‌تضمین نیستند. containerهای تست از kernel میزبان استفاده می‌کنند؛ محدودیت seccomp، دسترسی به huge pages/MSR و ممنوعیت حافظهٔ JIT در سیستم مقصد همچنان می‌تواند اثر داشته باشد.

## بازتولید ساخت

دستور کامل ساخت با Docker در [TESTING_FA.md](TESTING_FA.md) است. روی خود Alpine، این وابستگی‌ها کافی‌اند:

```sh
apk add --no-cache bash build-base cmake git curl linux-headers binutils \
  libuv-dev libuv-static openssl-dev openssl-libs-static openssl \
  autoconf automake libtool python3 pkgconf
bash scripts/build_alpine_release.sh
```

برای بررسی فایل استخراج‌شده:

```sh
./metaxmrig --version
readelf -l ./metaxmrig
readelf -d ./metaxmrig
python3 compare_randomx.py --threads 4 --rounds 1 --output first-test
```

نتایج صحت هر معماری در `verification-ARCH.tar.gz` و لاگ سازگاری توزیع‌ها در `portability-ARCH.tar.gz` کنار بسته‌های Release منتشر می‌شوند. انتشار فقط پس از موفقیت هر دو معماری و تمام این آزمون‌ها انجام می‌شود. معماری و libc متفاوت baseline را با هم برای ادعای سرعت مقایسه نکن؛ هر بسته baseline اصلی هم‌معماری و هم‌compiler خودش را دارد.

## منابع و مجوزهای کتابخانه‌ها

- [musl FAQ](https://wiki.musl-libc.org/faq.html)
- [بستهٔ libuv استاتیک Alpine 3.22](https://pkgs.alpinelinux.org/package/v3.22/main/x86_64/libuv-static)
- [بستهٔ OpenSSL استاتیک Alpine 3.22](https://pkgs.alpinelinux.org/package/v3.22/main/x86_64/openssl-libs-static)
- [مستندات runnerهای بومی GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)

متن مجوزهای همراه بسته از منابع اصلی آمده است: libuv `v1.51.0/LICENSE`، OpenSSL `openssl-3.5.9/LICENSE.txt`، musl `v1.2.5/COPYRIGHT` و GCC `releases/gcc-14.2.0/COPYING.RUNTIME`. GPL-3.0 پروژه، استثنای runtime GCC، اعلان‌های RandomX و hwloc و مجوزهای موجود در سورس third-party هم حفظ می‌شوند.
