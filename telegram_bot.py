import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from uuid import uuid4

# تنظیمات لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# توکن ربات و آیدی کانال
BOT_TOKEN = "7831120822:AAGmJ9idVGe_uCg1xx9kDqapw6m5P0etK2Y"
CHANNEL_ID = "@FumFoodChannel"

# آیدی مدیر (آیدی عددی @abasi_mohammad)
ADMIN_ID = "123456789"  # لطفاً آیدی عددی واقعی خودت رو جایگزین کن

# فایل JSON برای ذخیره آگهی‌ها و چت‌ها
DATA_FILE = "ads.json"
CHAT_FILE = "chats.json"

# لود کردن آگهی‌ها از فایل
def load_ads():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            logger.info("Ads loaded successfully")
            return data
    except FileNotFoundError:
        logger.warning("Ads file not found, creating new one")
        return {}
    except Exception as e:
        logger.error(f"Error loading ads: {e}")
        return {}

# ذخیره آگهی‌ها در فایل
def save_ads(ads):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(ads, f, ensure_ascii=False, indent=4)
        logger.info("Ads saved successfully")
    except Exception as e:
        logger.error(f"Error saving ads: {e}")

# لود کردن چت‌ها از فایل
def load_chats():
    try:
        with open(CHAT_FILE, 'r') as f:
            data = json.load(f)
            logger.info("Chats loaded successfully")
            return data
    except FileNotFoundError:
        logger.warning("Chats file not found, creating new one")
        return {}
    except Exception as e:
        logger.error(f"Error loading chats: {e}")
        return {}

# ذخیره چت‌ها در فایل
def save_chats(chats):
    try:
        with open(CHAT_FILE, 'w') as f:
            json.dump(chats, f, ensure_ascii=False, indent=4)
        logger.info("Chats saved successfully")
    except Exception as e:
        logger.error(f"Error saving chats: {e}")

# چک کردن عضویت در کانال
async def check_channel_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        return False

# دستور شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not await check_channel_membership(user_id, context):
        await update.message.reply_text(
            "هی رفیق! 😎 برای استفاده از ربات، اول باید توی کانالم عضو بشی: @FumFoodChannel\n"
            "بعدش برگرد و دوباره /start بزن!"
        )
        return
    
    await update.message.reply_text(
        "سلام رفیق! 😋 به ربات غذای دانشگاه FUM خوش اومدی! 🍔\n"
        "اینجا می‌تونی غذای رزروشده‌ت رو بفروشی یا غذای بقیه رو رزرو کنی.\n"
        "برای ثبت آگهی: /add\n"
        "برای دیدن آگهی‌هات: /list\n"
        "برای راهنما: /help"
    )

# دستور راهنما
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not await check_channel_membership(user_id, context):
        await update.message.reply_text(
            "اول باید توی کانال عضو بشی: @FumFoodChannel"
        )
        return
    
    await update.message.reply_text(
        "دستورات ربات:\n"
        "/add - ثبت آگهی غذای رزروشده\n"
        "/list - مشاهده آگهی‌های فعالت\n"
        "برای رزرو غذا، به کانال سر بزن: @FumFoodChannel"
    )

# ثبت آگهی
async def add_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not await check_channel_membership(user_id, context):
        await update.message.reply_text(
            "اول باید توی کانال عضو بشی: @FumFoodChannel"
        )
        return
    
    await update.message.reply_text(
        "خب، حالا بگو چه غذایی داری! 🍽️\n"
        "مثال: ناهار - چلوکباب - ۱۲:۳۰ - ۱۵۰۰۰ تومن"
    )
    context.user_data['adding_ad'] = True
    logger.info(f"User {user_id} started adding an ad")

# دریافت اطلاعات آگهی و ارسال به مدیر
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if not await check_channel_membership(user_id, context):
        await update.message.reply_text(
            "اول باید توی کانال عضو بشی: @FumFoodChannel"
        )
        return
    
    # چک کردن حالت چت
    chats = load_chats()
    user_chat = None
    for chat_id, chat in chats.items():
        if chat['buyer_id'] == user_id and chat['status'] == 'active':
            user_chat = chat
            break
        if chat['seller_id'] == user_id and chat['status'] == 'active':
            user_chat = chat
            break
    
    if user_chat:
        # ارسال پیام به طرف مقابل
        if user_chat['buyer_id'] == user_id:
            other_id = user_chat['seller_id']
            await context.bot.send_message(
                chat_id=other_id,
                text=f"پیام از رزروکننده: {update.message.text}"
            )
        else:
            other_id = user_chat['buyer_id']
            await context.bot.send_message(
                chat_id=other_id,
                text=f"پیام از فروشنده: {update.message.text}"
            )
        return
    
    # ثبت آگهی و ارسال به مدیر
    if context.user_data.get('adding_ad'):
        logger.info(f"User {user_id} submitted an ad: {update.message.text}")
        ad_id = str(uuid4())
        ad_text = update.message.text
        ads = load_ads()
        
        # ذخیره آگهی با وضعیت pending
        ads[ad_id] = {
            'user_id': user_id,
            'text': ad_text,
            'status': 'pending',
            'submitter_id': user_id,
            'submitter_username': update.message.from_user.username or 'ناشناس'
        }
        save_ads(ads)
        
        # ارسال به مدیر برای تأیید
        keyboard = [
            [InlineKeyboardButton("✅ تأیید آگهی", callback_data=f"approve_{ad_id}")],
            [InlineKeyboardButton("❌ رد آگهی", callback_data=f"reject_{ad_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"آگهی جدید برای تأیید:\n\n📋 **متن آگهی**:\n{ad_text}\n\n👤 **ثبت‌کننده**: @{ads[ad_id]['submitter_username']}\n🆔 **شناسه آگهی**: {ad_id}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            await update.message.reply_text(f"آگهی شما با شناسه {ad_id} ثبت شد و منتظر تأیید مدیره! ⏳")
        except Exception as e:
            logger.error(f"Error sending ad to admin for user {user_id}: {e}")
            await update.message.reply_text("یه مشکل توی ارسال آگهی به مدیر پیش اومد. لطفاً دوباره امتحان کن یا با پشتیبانی تماس بگیر.")
        
        context.user_data['adding_ad'] = False

# مدیریت تأیید آگهی
async def approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if str(user_id) != ADMIN_ID:
        await query.answer("فقط مدیر می‌تونه این کار رو بکنه!")
        return
    
    ad_id = query.data.split('_')[1]
    ads = load_ads()
    
    if ad_id not in ads:
        await query.answer("این آگهی وجود نداره!")
        return
    if ads[ad_id]['status'] != 'pending':
        await query.answer("این آگهی قبلاً بررسی شده!")
        return
    
    ads[ad_id]['status'] = 'active'
    save_ads(ads)
    
    # ارسال به کانال
    keyboard = [[InlineKeyboardButton("رزرو", callback_data=f"reserve_{ad_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        message = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"آگهی جدید:\n{ads[ad_id]['text']}",
            reply_markup=reply_markup
        )
        ads[ad_id]['message_id'] = message.message_id
        save_ads(ads)
        
        # اطلاع به کاربر
        await context.bot.send_message(
            chat_id=ads[ad_id]['user_id'],
            text=f"آگهی شما با شناسه {ad_id} تأیید شد و توی کانال قرار گرفت! 🎉"
        )
        await query.message.edit_text(f"آگهی با شناسه {ad_id} تأیید شد و توی کانال قرار گرفت!")
    except Exception as e:
        logger.error(f"Error posting ad to channel for ad_id {ad_id}: {e}")
        await query.message.edit_text("یه مشکل توی ارسال آگهی به کانال پیش اومد!")
    
    await query.answer()

# رد آگهی
async def reject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if str(user_id) != ADMIN_ID:
        await query.answer("فقط مدیر می‌تونه این کار رو بکنه!")
        return
    
    ad_id = query.data.split('_')[1]
    ads = load_ads()
    
    if ad_id not in ads:
        await query.answer("این آگهی وجود نداره!")
        return
    if ads[ad_id]['status'] != 'pending':
        await query.answer("این آگهی قبلاً بررسی شده!")
        return
    
    user_id = ads[ad_id]['user_id']
    del ads[ad_id]
    save_ads(ads)
    
    # اطلاع به کاربر
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"آگهی شما با شناسه {ad_id} توسط مدیر رد شد. 😔 لطفاً یه آگهی دیگه ثبت کن."
        )
        await query.message.edit_text(f"آگهی با شناسه {ad_id} رد شد!")
    except Exception as e:
        logger.error(f"Error notifying user about rejection for ad_id {ad_id}: {e}")
        await query.message.edit_text(f"آگهی با شناسه {ad_id} رد شد، اما اطلاع‌رسانی به کاربر با خطا مواجه شد!")
    
    await query.answer()

# مدیریت رزرو و شروع چت
async def reserve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if not await check_channel_membership(user_id, context):
        await query.answer("اول باید توی کانال عضو بشی: @FumFoodChannel")
        return
    
    ad_id = query.data.split('_')[1]
    ads = load_ads()
    
    if ad_id not in ads:
        await query.answer("این آگهی دیگه معتبر نیست!")
        return
    if ads[ad_id]['status'] != 'active':
        logger.info(f"Ad {ad_id} status is {ads[ad_id]['status']} instead of active")
        await query.answer("این آگهی هنوز تأیید نشده یا معتبر نیست!")
        return
    
    ad = ads[ad_id]
    buyer_id = str(query.from_user.id)
    
    if ad['user_id'] == buyer_id:
        await query.answer("نمی‌تونی آگهی خودت رو رزرو کنی!")
        return
    
    # شروع چت ناشناس
    chats = load_chats()
    chat_id = str(uuid4())
    chats[chat_id] = {
        'ad_id': ad_id,
        'seller_id': ad['user_id'],
        'buyer_id': buyer_id,
        'status': 'active'
    }
    save_chats(chats)
    
    # اطلاع به خریدار
    buyer_username = query.from_user.username or 'ناشناس'
    await context.bot.send_message(
        chat_id=buyer_id,
        text=f"تو آگهی «{ad['text']}» رو رزرو کردی! 🎉\n"
             f"حالا می‌تونی با فروشنده به‌صورت ناشناس چت کنی. پیامت رو بنویس:"
    )
    
    # اطلاع به فروشنده
    keyboard = [[InlineKeyboardButton("پایان چت", callback_data=f"endchat_{chat_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=ad['user_id'],
        text=f"آگهی تو («{ad['text']}») توسط یه نفر رزرو شد! 😊\n"
             f"حالا می‌تونی باهاش به‌صورت ناشناس چت کنی. پیامت رو بنویس:\n"
             f"وقتی کارتون تموم شد، از دکمه زیر برای پایان چت استفاده کن:",
        reply_markup=reply_markup
    )
    
    await query.answer("رزرو با موفقیت انجام شد! به ربات برو و چت رو شروع کن.")

# پایان چت
async def end_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    chat_id = query.data.split('_')[1]
    chats = load_chats()
    
    if chat_id not in chats:
        await query.answer("این چت دیگه معتبر نیست!")
        return
    
    chat = chats[chat_id]
    if chat['seller_id'] != user_id:
        await query.answer("فقط فروشنده می‌تونه چت رو ببنده!")
        return
    
    # دکمه‌های انتخاب برای حذف آگهی
    keyboard = [
        [InlineKeyboardButton("حذف آگهی و خروج", callback_data=f"deleteandexit_{chat_id}")],
        [InlineKeyboardButton("خروج بدون حذف", callback_data=f"exit_{chat_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "می‌خوای آگهی رو حذف کنی یا فقط از چت خارج شی؟",
        reply_markup=reply_markup
    )
    await query.answer()

# حذف آگهی و خروج
async def delete_and_exit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    chat_id = query.data.split('_')[1]
    chats = load_chats()
    
    if chat_id not in chats:
        await query.answer("این چت دیگه معتبر نیست!")
        return
    
    chat = chats[chat_id]
    if chat['seller_id'] != user_id:
        await query.answer("فقط فروشنده می‌تونه این کار رو بکنه!")
        return
    
    ad_id = chat['ad_id']
    ads = load_ads()
    if ad_id in ads:
        ads[ad_id]['status'] = 'deleted'
        save_ads(ads)
        
        # ویرایش پیام در کانال
        try:
            await context.bot.edit_message_text(
                chat_id=CHANNEL_ID,
                message_id=ads[ad_id]['message_id'],
                text=f"~~{ads[ad_id]['text']}~~\n(این آگهی حذف شد)",
                reply_markup=None
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
    
    # پایان چت
    chats[chat_id]['status'] = 'closed'
    save_chats(chats)
    
    # اطلاع به هر دو کاربر
    await context.bot.send_message(
        chat_id=chat['buyer_id'],
        text="چت تموم شد. فروشنده آگهی رو حذف کرد و از چت خارج شد."
    )
    await query.message.edit_text("آگهی حذف شد و چت بسته شد! ✅")
    await query.answer()

# خروج بدون حذف
async def exit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    chat_id = query.data.split('_')[1]
    chats = load_chats()
    
    if chat_id not in chats:
        await query.answer("این چت دیگه معتبر نیست!")
        return
    
    chat = chats[chat_id]
    if chat['seller_id'] != user_id:
        await query.answer("فقط فروشنده می‌تونه این کار رو بکنه!")
        return
    
    # پایان چت
    chats[chat_id]['status'] = 'closed'
    save_chats(chats)
    
    # اطلاع به هر دو کاربر
    await context.bot.send_message(
        chat_id=chat['buyer_id'],
        text="چت تموم شد. فروشنده از چت خارج شد."
    )
    await query.message.edit_text("چت بسته شد، ولی آگهی حذف نشد. ✅")
    await query.answer()

# لیست آگهی‌های کاربر
async def list_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not await check_channel_membership(user_id, context):
        await update.message.reply_text(
            "اول باید توی کانال عضو بشی: @FumFoodChannel"
        )
        return
    
    ads = load_ads()
    user_ads = [ad for ad_id, ad in ads.items() if ad['user_id'] == str(user_id) and ad['status'] == 'active']
    
    if not user_ads:
        await update.message.reply_text("تو هیچ آگهی فعالی نداری! 😕")
        return
    
    for ad_id, ad in ads.items():
        if ad['user_id'] == str(user_id) and ad['status'] == 'active':
            await update.message.reply_text(
                f"آگهی:\n{ad['text']}\nشناسه: {ad_id}"
            )

# مدیریت خطاها
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add", add_ad))
    app.add_handler(CommandHandler("list", list_ads))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(reserve_callback, pattern="reserve_"))
    app.add_handler(CallbackQueryHandler(end_chat_callback, pattern="endchat_"))
    app.add_handler(CallbackQueryHandler(delete_and_exit_callback, pattern="deleteandexit_"))
    app.add_handler(CallbackQueryHandler(exit_callback, pattern="exit_"))
    app.add_handler(CallbackQueryHandler(approve_callback, pattern="approve_"))
    app.add_handler(CallbackQueryHandler(reject_callback, pattern="reject_"))
    
    # هندلر خطا
    app.add_error_handler(error_handler)
    
    # شروع ربات
    app.run_polling()

if __name__ == '__main__':
    main()
