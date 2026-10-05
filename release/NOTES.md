# MetaXMRig 6.26.0-meta.1 — پیش‌انتشار آزمایشی لینوکس

اولین ریلیز آزمایشی بر پایهٔ XMRig 6.26.0. مسیر موجود VAES512 برای آزمایش روی CPUهای سازگار قابل‌انتخاب شده است؛ افزایش هشریت تضمین نشده و باید روی سیستم هدف مقایسه شود.

## تغییر اصلی

- گزینهٔ جدید `--randomx-aes=auto|aes|vaes512` و عضو JSON به نام `randomx.aes`.
- `auto` سیاست پیش‌فرض upstream را حفظ می‌کند. `vaes512` روی CPU واجد شرایط با hardware AES فعال قابل اجراست؛ در غیر این صورت fallback و هشدار دارد.
- بررسی قابلیت CPU/OS و هم‌ترازی حافظه، ثبت مسیر واقعی در لاگ و حفظ مسیر software AES.
- ابزار آفلاین برای مقایسهٔ هشریت و بررسی checksum رسمی RandomX.

## فایل دانلود

`metaxmrig-6.26.0-meta.1-linux-x64.tar.gz` شامل فایل اجرایی استاتیک `metaxmrig`، نسخهٔ اصلی `xmrig-baseline`، ابزار `compare_randomx.py`، مستندات فارسی، اطلاعات ساخت و مجوزهاست. فایل `.sha256` صحت دانلود را بررسی می‌کند. `results.json` نتیجهٔ آزمون checksum روی runner ساخت است.

```bash
sha256sum -c metaxmrig-6.26.0-meta.1-linux-x64.sha256
tar -xzf metaxmrig-6.26.0-meta.1-linux-x64.tar.gz
cd metaxmrig-6.26.0-meta.1-linux-x64
python3 compare_randomx.py --threads 4 --rounds 1 --output first-test
```

برای مقایسهٔ دقیق‌تر `--rounds 3` بگذار. ابزار به‌صورت پیش‌فرض huge pages و نوشتن MSR را خاموش می‌کند، استخر ندارد و نتیجه‌ای ارسال نمی‌کند. برای ماینینگ با config فعلی:

```bash
./metaxmrig -c /path/to/your-config.json --randomx-aes=vaes512
```

**عدد ۱۰٫۶۱٪ آزمایش اولیه مربوط به سرعت یک تابع AES بود، نه هشریت کامل ماینر.** نتیجهٔ کامل پیش از انتشار، روش کار و محدودیت‌ها در مستندات آمده است. share واقعی استخر آزمایش نشده است. بستهٔ این ریلیز Linux x86-64 و CPU است؛ OpenCL، CUDA، KawPow و GhostRider در باینری بسته غیرفعال‌اند.

- [راهنمای کامل تست](https://github.com/metasina3/metaxmrig/blob/v6.26.0-meta.1/docs/TESTING_FA.md)
- [شرح فایل‌ها، تغییرات و نحوهٔ پیاده‌سازی](https://github.com/metasina3/metaxmrig/blob/v6.26.0-meta.1/docs/CHANGES_FA.md)
- [نتایج صحت و مقایسهٔ کامل](https://github.com/metasina3/metaxmrig/blob/v6.26.0-meta.1/docs/VALIDATION_FA.md)

پایهٔ baseline: `b2ca72480c58d197e18c885d9fc1a0c8d517e60a`. نام، credits، مجوزها و donation upstream در سورس حفظ شده‌اند. این fork ریلیز رسمی تیم XMRig نیست.
