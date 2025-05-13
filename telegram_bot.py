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

# فایل JSON برای ذخیره آگهی‌ها
DATA_FILE = "ads.json"

# لود کردن آگهی‌ها از فایل
def load_ads():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# ذخیره آگهی‌ها در فایل
def save_ads(ads):
    with open(DATA_FILE, 'w') as f:
        json.dump(ads, f, ensure_ascii=False, indent=4)

# چک کردن عضویت در کانال
async def check_channel_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
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
        "/delete <id> - حذف آگهی با شناسه\n"
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

# دریافت اطلاعات آگهی
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if not await check_channel_membership(user_id, context):
        await update.message.reply_text(
            "اول باید توی کانال عضو بشی: @FumFoodChannel"
        )
        return
    
    if context.user_data.get('adding_ad'):
        ad_id = str(uuid4())
        ad_text = update.message.text
        ads = load_ads()
        
        # ذخیره آگهی
        ads[ad_id] = {
            'user_id': user_id,
            'text': ad_text,
            'status': 'active'
        }
        save_ads(ads)
        
        # ساخت دکمه رزرو
        keyboard = [[InlineKeyboardButton("رزرو", callback_data=f"reserve_{ad_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # ارسال به کانال
        message = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"آگهی جدید:\n{ad_text}\nثبت‌کننده: @{update.message.from_user.username or 'ناشناس'}",
            reply_markup=reply_markup
        )
        
        ads[ad_id]['message_id'] = message.message_id
        save_ads(ads)
        
        await update.message.reply_text(f"آگهی شما با شناسه {ad_id} ثبت شد و توی کانال گذاشتم! 😎")
        context.user_data['adding_ad'] = False

# مدیریت رزرو
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
    
    ad = ads[ad_id]
    buyer_id = str(query.from_user.id)
    
    if ad['user_id'] == buyer_id:
        await query.answer("نمی‌تونی آگهی خودت رو رزرو کنی!")
        return
    
    # اطلاع به خریدار
    await query.message.reply_text(
        f"تو آگهی «{ad['text']}» رو رزرو کردی! 🎉\n"
        f"برای هماهنگی با فروشنده: @{query.message.chat.username or 'ناشناس'}"
    )
    
    # اطلاع به فروشنده
    await context.bot.send_message(
        chat_id=ad['user_id'],
        text=f"آگهی تو («{ad['text']}») توسط @{query.from_user.username or 'ناشناس'} رزرو شد! 😊\n"
             f"برای هماهنگی باهاش تماس بگیر.\n"
             f"اگه می‌خوای آگهی رو حذف کنی: /delete {ad_id}"
    )
    
    await query.answer("رزرو با موفقیت انجام شد!")

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
    
    response = "آگهی‌های تو:\n"
    for ad_id, ad in ads.items():
        if ad['user_id'] == str(user_id) and ad['status'] == 'active':
            response += f"شناسه: {ad_id}\n{ad['text']}\n\n"
    
    await update.message.reply_text(response)

# حذف آگهی
async def delete_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not await check_channel_membership(user_id, context):
        await update.message.reply_text(
            "اول باید توی کانال عضو بشی: @FumFoodChannel"
        )
        return
    
    if not context.args:
        await update.message.reply_text("لطفا شناسه آگهی رو وارد کن: /delete <id>")
        return
    
    ad_id = context.args[0]
    ads = load_ads()
    
    if ad_id not in ads or ads[ad_id]['user_id'] != str(user_id):
        await update.message.reply_text("این آگهی وجود نداره یا مال تو نیست!")
        return
    
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
    
    await update.message.reply_text(f"آگهی با شناسه {ad_id} حذف شد! ✅")

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
    app.add_handler(CommandHandler("delete", delete_ad))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(reserve_callback, pattern="reserve_"))
    
    # هندلر خطا
    app.add_error_handler(error_handler)
    
    # شروع ربات
    app.run_polling()

if __name__ == '__main__':
    main()
