import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# توكن البوت
API_TOKEN = '7384121018:AAGItlGVQY8FR3xemQSjU6JpL_Zrppcza-8'
CHANNEL_USERNAME = '@talabaksyria'  # معرف القناة

bot = telebot.TeleBot(API_TOKEN)

# لتخزين الطلبات المعلقة (معاينة للموافقة)
pending_orders = {}

# معرف المدير (إبراهيم) حتى يستقبل الطلبات للموافقة
ADMIN_ID = 809571974

# استقبال أي رسالة (صور، نصوص) من المستخدم
@bot.message_handler(content_types=['text', 'photo'])
def handle_user_message(message):
    user_id = message.from_user.id

    # تخزين الطلب في pending_orders
    if user_id not in pending_orders:
        pending_orders[user_id] = []

    # حفظ الرسالة (صور أو نصوص)
    pending_orders[user_id].append(message)

    bot.reply_to(message, "تم استلام طلبك، أرسل كل التفاصيل المطلوبة أو اكتب /done لإنهاء الطلب.")

# أمر /done لإنهاء التجميع وإرسال المعاينة للإدمن
@bot.message_handler(commands=['done'])
def done_collecting(message):
    user_id = message.from_user.id

    if user_id not in pending_orders or not pending_orders[user_id]:
        bot.reply_to(message, "لم ترسل أي شيء بعد.")
        return

    order_msgs = pending_orders[user_id]
    del pending_orders[user_id]

    # تجميع الرسالة للعرض على الأدمن
    media_group = []
    text_parts = []
    for msg in order_msgs:
        if msg.content_type == 'photo':
            # نضيف الصورة للمعاينة
            file_id = msg.photo[-1].file_id
            media_group.append(telebot.types.InputMediaPhoto(file_id))
        elif msg.content_type == 'text':
            text_parts.append(msg.text)

    preview_text = "\n".join(text_parts)
    preview_caption = f"طلب جديد من @{message.from_user.username or message.from_user.first_name}:\n\n{preview_text}\n\nهل توافق على نشر هذا الطلب؟"

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ انشر الطلب", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton("❌ رفض الطلب", callback_data=f"reject_{user_id}")
    )

    if media_group:
        # إرسال مجموعة صور مع التعليق
        bot.send_media_group(ADMIN_ID, media_group)
        bot.send_message(ADMIN_ID, preview_caption, reply_markup=markup)
    else:
        bot.send_message(ADMIN_ID, preview_caption, reply_markup=markup)

    bot.reply_to(message, "تم إرسال طلبك للموافقة وسيتم الرد عليك قريبًا.")

# التعامل مع أزرار الموافقة أو الرفض
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data
    if data.startswith('approve_') or data.startswith('reject_'):
        action, user_id_str = data.split('_')
        user_id = int(user_id_str)

        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "أنت غير مخول لاتخاذ هذا الإجراء.")
            return

        if action == 'approve':
            # نرسل الطلب للقناة
            send_order_to_channel(user_id)
            bot.answer_callback_query(call.id, "تم نشر الطلب.")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        elif action == 'reject':
            # نرسل رسالة رفض للمستخدم
            bot.send_message(user_id, "نأسف، تم رفض طلبك من قبل الإدارة.")
            bot.answer_callback_query(call.id, "تم رفض الطلب.")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

def send_order_to_channel(user_id):
    # إرسال رسالة نصية للقناة كمثال
    bot.send_message(CHANNEL_USERNAME, f"تم نشر طلب جديد من مستخدم معرّف: {user_id}\n\n(الطلب هنا يحتاج تخزين مفصل لاحقاً)")

if __name__ == '__main__':
    print("البوت شغال...")
    bot.infinity_polling()