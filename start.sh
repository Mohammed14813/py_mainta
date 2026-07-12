#!/bin/bash
# start.sh

echo "🚀 Py_Mainta - بدء التشغيل..."

# تثبيت المكتبات
echo "📦 جاري تحميل المكتبات..."
pip install -r requirements.txt

# تشغيل التطبيق
echo "🚀 تشغيل التطبيق..."
python app.py