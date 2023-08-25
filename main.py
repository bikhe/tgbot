#импорты
from aiogram import Bot, Dispatcher, executor,types
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import psycopg2
from yoomoney import Quickpay, Client
import uuid
import keyboards as kb
import config as conf
import defines as df

# yoomoney
client = Client(conf.YM_TOKEN)

# aiogram
bot = Bot(conf.TG_TOKEN)
dp = Dispatcher(bot, storage = MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# sql

# conn = sql.connect()
# cur = conn.cursor()

conn = psycopg2.connect(dbname=f'{conf.DB_NAME}.db', user=conf.DB_USER, password=conf.DB_PASS, host='localhost')
cur = conn.cursor()
conn.autocommit = True


sql_dbmake = """CREATE TABLE IF NOT EXISTS users(
id INT PRIMARY KEY,
money INT,
donate INT,
isadmin INT
);"""
cur.execute(sql_dbmake)

# main
class DONATE(Helper): # Используется для машины состояний при донате
    mode = HelperMode.snake_case
    SUMM_DONATE = ListItem()

def check_pay(comm):  # Проверка получения доната
    history = client.operation_history(label=comm)
    if history.operations == []:
        return False
    else:
        for operation in history.operations:
            if operation.status == 'success':
             return True

def check_summ(comm): # Проверка суммы доната(библиотека yoomoney). TODO: обьединить с проверкой
    history = client.operation_history(label=comm)
    if history.operations == []:
        return 0
    else:
        for operation in history.operations:
             return int(operation.amount)

@dp.message_handler(commands=['start'])
async def register(message: types.Message):
    id = message.from_user.id
    cur.execute(f'SELECT * FROM users WHERE id = {id}')
    check = cur.fetchone()
    if check == None:
        cur.execute(f'INSERT INTO users VALUES({id}, {conf.START_MONEY}, {0});')
        await message.answer(f'Привет, спасибо за регистрацию!', reply_markup=kb.menu_markup)
    else:
        await message.answer(f'Привет, {message.from_user.full_name}!', reply_markup=kb.menu_markup)
    

@dp.message_handler(text = ['я', 'Я'])
@dp.message_handler(commands=['me'])
@dp.callback_query_handler(text ='me')
async def profil(message: types.Message):
    id = message.from_user.id
    cur.execute(f'SELECT * FROM users WHERE id = {id}')
    data = cur.fetchone()
    db_id, money, admin, donate = data
    isadmin = False
    if donate == None:
        donate = 0
    if admin == 1:
        isadmin = True
    await bot.send_message(id,f'Твой ID: {db_id}\nТвой баланс: {money}$\nАдмин-права: {isadmin}\n Донат: {donate} RUB', reply_markup=kb.me_markup)

@dp.message_handler(text = ['Помощь', 'помощь'])
@dp.callback_query_handler(text ='help')
async def help(message: types.Message):
    await bot.send_message(message.from_user.id, f'"Помощь" - эта справка\n"Меню" - основное меню\n"Я" - Информация о игроке\n/dice [1-6] [ставка] (пример: /dice 1 100) - игра в кости.\nДополнительная помощь - {conf.OWNER_NICK}')

@dp.message_handler(commands=['ahelp'])
@dp.message_handler(text = ['апомощь'])
async def ahelp(message: types.Message):
    await message.answer(f'/setmoney [id] [money](Пример /setmoney 1234567890 10000)\nДоп.Помощь {conf.OWNER_NICK}')


@dp.message_handler(text = ['меню','Меню'])
@dp.callback_query_handler(text = 'menu')
async def menu(message: types.Message):
    await bot.send_message(message.from_user.id,f'Привет, {message.from_user.full_name}!', reply_markup=kb.menu_markup)

@dp.message_handler(commands=['makeadmin'])
async def makeadmin(message: types.Message):
    id = str(message.from_user.id)
    args = message.get_args()
    cur.execute(f'SELECT isadmin FROM users WHERE id = {args}')
    data = cur.fetchone()
    if data != None and 0 in data:    
        if id == conf.OWNER_ID:
            adm_status = 1
            sql_makeadm = f'UPDATE users SET isadmin = {adm_status} WHERE id = {args}'
            cur.execute(sql_makeadm)
            await message.answer(f'Пользователь с ID {args} назначен администратором!')
            await bot.send_message(args, 'Вам выданы права администратора!') 
        else:
            await message.answer('Ты не основатель!')      
    else:
        await message.answer('ID неверный или юзер уже админ!')


@dp.message_handler(commands=['unmakeadmin'])
async def makeadmin(message: types.Message):
    id = str(message.from_user.id)
    args = message.get_args()
    cur.execute(f'SELECT isadmin FROM users WHERE id = {args}')
    data = cur.fetchone()
    if data != None and 1 in data:    
        if id == conf.OWNER_ID:
            adm_status = 0
            sql_makeadm = f'UPDATE users SET isadmin = {adm_status} WHERE id = {args}'
            cur.execute(sql_makeadm)
            await message.answer(f'У пользователя с ID {args} отняты админ-права!')
            await bot.send_message(args, 'У вас отняты права администратора!') 
        else:
            await message.answer('Ты не основатель!')      
    else:
        await message.answer('ID неверный или юзер уже админ!')

@dp.message_handler(commands=['setmoney'])
async def setmoney(message: types.Message):
    id = message.from_user.id
    args = message.get_args()
    args_tuple = tuple(args.split(' '))
    aim_id, money = args_tuple
    cur.execute(f'SELECT isadmin FROM users WHERE id = {id}')
    data = cur.fetchone()
    if money.isdigit() == True:
        money = int(money)
        if 1 in data:
            if None in data:
                message.answer('Аккаунта с таким ID нет!')
            else:
                sql_setmoney = f'UPDATE users SET money = {money} WHERE id = {aim_id}'
                cur.execute(sql_setmoney)
                await bot.send_message(aim_id, f'Админ установил вам баланс: {money}$')
        else:
            message.answer('Ты не админ!')
    else:
        message.answer('Введи число, а не текст!')


@dp.message_handler(commands=['dice'])
async def dice(message: types.Message):
    id = message.from_user.id
    args = message.get_args()
    args_tuple = tuple(args.split(' '))
    bet, money = args_tuple
    dice = ['1','2','3','4','5','6']
    cur.execute(f'SELECT money FROM users WHERE id = {id}')
    money_sqlquery = cur.fetchone()
    money_begin = int(money_sqlquery[0])
    money = int(money)
    if bet.isdigit() and bet in dice:
        bet = int(bet)
        if money > money_begin:
            await message.answer('У тебя нет столько денег!')
        else:
            msg = await bot.send_dice(message.chat.id)
            dice_value = msg.dice.value
            if bet == dice_value:
                money_after = money_begin + money
                sql_dicesetmoney = f'UPDATE users SET money = {money_after} WHERE id = {id}'
                cur.execute(sql_dicesetmoney)
                await message.answer(f'Ты ставил на {bet} и выиграл {money}$\n Твой баланс: {money_after}$')
            else:
                money_after = money_begin - money
                sql_dicesetmoney = f'UPDATE users SET money = {money_after} WHERE id = {id}'
                cur.execute(sql_dicesetmoney)
                await message.answer(f'Ты ставил на {bet} и проиграл {money}$\n Твой баланс: {money_after}$')
    else:
        await message.answer('Ставить можно на число от 1 до 6')        


@dp.callback_query_handler(text = 'donate')
async def donate_summ(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    
    await state.set_state(DONATE.all()[0])
    await message.reply(f'Какую сумму готовы пожертвовать(Например 100, 243, 666)?\nЕсли передумали - введите НЕ число')
    
@dp.message_handler(state= DONATE.SUMM_DONATE)
async def donatello(message: types.Message):
    args['text'] = message.get_args
    id = message.from_user.id
    state = dp.current_state(user=message.from_user.id)
    if args.isdigit():
        args = int(args['text'])
        uid = f'{str(uuid.uuid4)} - {message.from_user.username}'
        quickpay = Quickpay(
            receiver=conf.YM_NUMBER,
            quickpay_form="shop",
            targets="Пожертвование",
            paymentType="SB",
            sum=args,
            label=uid
        )
        await message.reply(f'Ссылка для оплаты: {quickpay.base_url}\nПо любому вопросу - пиши владельцу {conf.OWNER_NICK}', reply_markup= kb.donate_check)
    else:
        await state.reset_state
        await message.reply('Я понял, перемещаю вас в меню', reply_markup= kb.menu_markup)    
        
        
@dp.callback_query_handler(text = 'check_donate')  #TODO:Переделать,ибо неработает
async def check_don(message: types.Message):
    cur.execute(f'SELECT donate FROM users WHERE id = {id}')
    donate_before = cur.fetchone()
    check = check_pay(uid)
        if check == 1:
            amount = check_summ(uid)
            donate_after = donate_before + donate_after
            sql_setdonate = f'UPDATE users SET donate = {donate_after} WHERE id = {id}'
            cur.execute(sql_setdonate)
            await state.reset_state
            await message.reply('Донат получен, удачного дня!', reply_markup= kb.menu_markup)
        else:
            time.sleep(10)
            check = check_pay(uid)
            if check == 1:
                amount = check_summ(uid)
                donate_after = donate_before + donate_after
                sql_setdonate = f'UPDATE users SET donate = {donate_after} WHERE id = {id}'
                cur.execute(sql_setdonate)
                await state.reset_state
                await message.reply('Донат получен, удачного дня!', reply_markup= kb.menu_markup)
            else:
                time.sleep(5)
                check = check_pay(uid)
                if check == 1:
                    amount = check_summ(uid)
                    donate_after = donate_before + donate_after
                    sql_setdonate = f'UPDATE users SET donate = {donate_after} WHERE id = {id}'
                    cur.execute(sql_setdonate)
                    await state.reset_state
                    await message.reply('Донат получен, удачного дня!', reply_markup= kb.menu_markup)
                else:
                    await state.reset_state
                    await message.reply(f'Я не дождался вашего доната, если уже оплатили - {conf.OWNER_NICK}', reply_markup= kb.menu_markup)
    

@dp.message_handler(commands=['setdonate'])
async def setmoney(message: types.Message):
    id = message.from_user.id
    args = message.get_args()
    args_tuple = tuple(args.split(' '))
    aim_id, donate = args_tuple
    cur.execute(f'SELECT isadmin FROM users WHERE id = {id}')
    data = cur.fetchone()
    if donate.isdigit() == True:
        donate = int(donate)
        if 1 in data:
            if None in data:
                message.answer('Аккаунта с таким ID нет!')
            else:
                sql_setdonate = f'UPDATE users SET donate = {donate} WHERE id = {aim_id}'
                cur.execute(sql_setdonate)
                await bot.send_message(aim_id, f'Админ установил вам баланс: {donate}$')
        else:
            message.answer('Ты не админ!')
    else:
        message.answer('Введи число, а не текст!')

        



async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()
    


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)