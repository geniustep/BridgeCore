#!/bin/bash
# سكريبت لتتبع logs Odoo

LOG_DIR="/opt/BridgeCore/logs"
LOG_FILE="$LOG_DIR/app.log"
ERROR_LOG="$LOG_DIR/errors.log"

# ألوان للـ output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== BridgeCore Odoo Logs Watcher ===${NC}"
echo ""

# التحقق من وجود ملفات الـ logs
if [ ! -f "$LOG_FILE" ]; then
    echo -e "${YELLOW}Warning: $LOG_FILE not found. Creating...${NC}"
    mkdir -p "$LOG_DIR"
    touch "$LOG_FILE"
fi

# عرض القائمة
echo "اختر نوع التتبع:"
echo "1) جميع الـ logs (Real-time)"
echo "2) أخطاء Odoo فقط"
echo "3) عمليات Search Read"
echo "4) جميع عمليات Odoo"
echo "5) آخر 50 سطر من الـ logs"
echo "6) آخر 20 خطأ"
echo "7) تتبع مع تصفية متقدمة"
echo ""
read -p "اختيارك (1-7): " choice

case $choice in
    1)
        echo -e "${GREEN}تتبع جميع الـ logs...${NC}"
        tail -f "$LOG_FILE"
        ;;
    2)
        echo -e "${RED}تتبع أخطاء Odoo فقط...${NC}"
        tail -f "$ERROR_LOG" | grep --color=always -i "odoo"
        ;;
    3)
        echo -e "${YELLOW}تتبع عمليات Search Read...${NC}"
        tail -f "$LOG_FILE" | grep --color=always -iE "search_read|SEARCHREAD"
        ;;
    4)
        echo -e "${BLUE}تتبع جميع عمليات Odoo...${NC}"
        tail -f "$LOG_FILE" | grep --color=always -iE "ODOO|odoo|Odoo"
        ;;
    5)
        echo -e "${GREEN}عرض آخر 50 سطر...${NC}"
        tail -n 50 "$LOG_FILE"
        ;;
    6)
        echo -e "${RED}عرض آخر 20 خطأ...${NC}"
        tail -n 200 "$LOG_FILE" | grep -i "error" | tail -20
        ;;
    7)
        echo -e "${YELLOW}تتبع مع تصفية متقدمة...${NC}"
        echo "أدخل كلمة البحث (مثال: search_read, ERROR, shuttle.trip):"
        read search_term
        tail -f "$LOG_FILE" | grep --color=always -iE "$search_term"
        ;;
    *)
        echo -e "${RED}اختيار غير صحيح${NC}"
        exit 1
        ;;
esac
