# سیستم شخصی‌سازی پیشرفته حساسیت تشخیص تقلب

## نمای کلی

سیستم جدید امکان کنترل دقیق و گرانولار بر روی نحوه تشخیص تقلب را فراهم می‌کند. استاد می‌تواند برای هر عنصر کد به صورت جداگانه تصمیم بگیرد که آیا نادیده گرفته شود یا خیر.

## سطوح پیش‌تعریف شده

### 1. Smart Mode (حالت هوشمند)
- نادیده گرفتن نام متغیرها ✓
- نادیده گرفتن نام توابع ✓
- حفظ نام انواع
- حفظ رشته‌ها و اعداد
- **استفاده**: زمانی که می‌خواهید حتی با تغییر نام متغیرها و توابع هم تقلب را تشخیص دهید

### 2. Balanced Mode (حالت متعادل) - پیش‌فرض
- نادیده گرفتن نام متغیرها ✓
- حفظ نام توابع
- حفظ نام انواع
- حفظ رشته‌ها و اعداد
- **استفاده**: حالت متعادل برای بیشتر موارد

### 3. Strict Mode (حالت سخت‌گیرانه)
- حفظ تمام شناسه‌ها
- حفظ رشته‌ها و اعداد
- فقط کدهای کاملاً یکسان تشخیص داده می‌شوند
- **استفاده**: زمانی که فقط می‌خواهید کپی‌های مستقیم را شناسایی کنید

## تنظیمات گرانولار

می‌توانید هر یک از این موارد را به صورت جداگانه تنظیم کنید:

### شناسه‌ها (Identifiers)
- `ignore_variable_names`: نادیده گرفتن نام متغیرها
- `ignore_function_names`: نادیده گرفتن نام توابع
- `ignore_type_names`: نادیده گرفتن نام انواع (struct, typedef, enum)

### مقادیر (Literals)
- `ignore_string_literals`: نادیده گرفتن رشته‌های متنی
- `ignore_numeric_literals`: نادیده گرفتن اعداد

### ساختاری (Structural)
- `normalize_whitespace`: نرمال‌سازی فاصله‌ها
- `remove_comments`: حذف کامنت‌ها
- `remove_includes`: حذف #include ها
- `ignore_operator_spacing`: نادیده گرفتن فاصله اطراف عملگرها
- `ignore_bracket_style`: نادیده گرفتن سبک آکولاد

## نحوه استفاده

### از طریق API

```python
# استفاده از حالت پیش‌تعریف شده
POST /upload?sensitivity_mode=smart

# استفاده از حالت شخصی‌سازی شده
POST /upload?
    ignore_variable_names=true&
    ignore_function_names=true&
    ignore_string_literals=false
```

### از طریق کد

```python
from config import SensitivityConfig

# حالت پیش‌تعریف شده
config = SensitivityConfig.smart()

# حالت شخصی‌سازی شده
config = SensitivityConfig.custom(
    ignore_variable_names=True,
    ignore_function_names=False,
    ignore_string_literals=True
)
```

## مثال‌های کاربردی

### مثال 1: فقط نام متغیرها را نادیده بگیر
```python
config = SensitivityConfig.custom(
    ignore_variable_names=True,
    ignore_function_names=False,
    ignore_type_names=False
)
```

### مثال 2: همه چیز به جز اعداد را نادیده بگیر
```python
config = SensitivityConfig.custom(
    ignore_variable_names=True,
    ignore_function_names=True,
    ignore_type_names=True,
    ignore_string_literals=True,
    ignore_numeric_literals=False
)
```

### مثال 3: حالت فوق‌العاده سخت‌گیرانه
```python
config = SensitivityConfig.strict()
# یا
config = SensitivityConfig.custom(
    ignore_variable_names=False,
    ignore_function_names=False,
    ignore_type_names=False,
    ignore_string_literals=False,
    ignore_numeric_literals=False
)
```

## سازگاری با نسخه قبلی

برای سازگاری با کدهای موجود، پارامتر `ignore_variable_names` همچنان کار می‌کند:
- `ignore_variable_names=True` → Smart mode
- `ignore_variable_names=False` → Strict mode

## نکات مهم

1. حالت Smart قوی‌ترین حالت برای تشخیص تقلب است
2. حالت Strict فقط کپی‌های مستقیم را می‌گیرد
3. حالت Balanced تعادل خوبی بین این دو است
4. می‌توانید ترکیب‌های مختلفی از تنظیمات را امتحان کنید تا به سطح مطلوب برسید

