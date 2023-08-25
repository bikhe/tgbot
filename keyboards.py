from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

back_to_menu_btn = InlineKeyboardButton('Назад в меню', callback_data='menu')

#menu
me_btn = InlineKeyboardButton('Профиль', callback_data='me')
casino_btn = InlineKeyboardButton('Казино', callback_data='casino')
work_btn = InlineKeyboardButton('Работа', callback_data='work')
donate_btn = InlineKeyboardButton('Донат', callback_data='donate')
help_btn = InlineKeyboardButton('Помощь', callback_data='help')
menu_markup = InlineKeyboardMarkup()
menu_markup.add(me_btn, casino_btn, work_btn, donate_btn, help_btn)

#Profil'
me_markup = InlineKeyboardMarkup()
me_markup.add(back_to_menu_btn)

#work
work_markup = InlineKeyboardMarkup()
work_markup.add(back_to_menu_btn)

#casino
dice_btn = InlineKeyboardButton('Кости', callback_data= 'dice')
casino_markup = InlineKeyboardMarkup()
casino_markup.add(back_to_menu_btn, dice_btn)


#donate menu
vip_btn = InlineKeyboardButton('VIP статус', callback_data='vip')
change_money = InlineKeyboardButton('Обмен на вирты', callback_data='change_money')

#donate
donate_check = InlineKeyboardButton('Проверить', callback_data= 'check_donate')
donate_markup = InlineKeyboardMarkup()
donate_markup.add(donate_check)