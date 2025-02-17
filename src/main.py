import json
import re

import time
from pyrogram import Client, Filters
from pyrogram import (InlineKeyboardMarkup,
                      InlineKeyboardButton,
                      CallbackQuery)

import functions as func
import raid_dynamax as raid

from Config import Config

app = Client(
    api_id=Config.aid,
    api_hash=Config.ahash,
    bot_token=Config.bot_token,
    session_name='hexadex'
)

texts = json.load(open('src/texts.json', 'r'))
data = json.load(open('src/pkmn.json', 'r'))
stats = json.load(open('src/stats.json', 'r'))
jtype = json.load(open('src/type.json', 'r'))

usage_dict = {'vgc': None}
raid_dict = {}





allowed_chat_ids = set()
all_enabled = False
@app.on_message(Filters.command(['tpin', 'tpin@hexa_dex_bot']))
def hpin(client, message):
    chat_id = message.chat.id
    chat_type = message.chat.type
    #message_id = message.reply_to_message.message_id
 

    user = message.from_user
    member = client.get_chat_member(chat_id, user.id)
    
    
    if member.status not in ['administrator', 'creator']:
        if chat_id not in allowed_chat_ids and not all_enabled:
            message.reply_text('Sorry, this is enabled for only admin in this group.')
            return

    if not message.reply_to_message or not message.reply_to_message.from_user or message.reply_to_message.from_user.id != 572621020:
           message.reply_text('Please reply to a message from Hexa to pin it.')
           return   

    message_id = message.reply_to_message.message_id
    
    if chat_type == "private":
        message.reply_text("This command can only be used in a group or channel.")
        return
    
    
    
    try:
        duration_str = message.text.split()[1]
        duration = int(re.sub(r'\D', '', duration_str))
        unit = duration_str[-1] if duration_str[-1] in ['h', 'm', 's'] else 'm'
     
        if unit == 'h':
            duration *= 60
        elif unit == 's':
            duration //= 60
        elif unit == 'm':
            pass
        
        else:
            raise ValueError
        if duration > 30:
           message.reply_text('Maximum pinning duration is 30 min.')
        if duration < 1:
           message.reply_text('Minimum pinning duration is 1 min.')
           return
    except (IndexError, ValueError):
        duration = 10  
    client.pin_chat_message(chat_id, message_id)
    
    message.reply_text(f'Message has been pinned for {duration} minute(s).')
    time.sleep(duration * 60)
    client.unpin_chat_message(chat_id)
    user_link = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
  
    if message.reply_to_message:
        message.reply_to_message.reply_text(f'Unpinned msg pinned by {user_link} for {duration} minute(s).', reply_to_message_id=message_id)
    else:
        client.send_message(chat_id, message.reply_text(f'Unpinned msg pinned by {user_link} for {duration} minute(s).', reply_to_message_id=message_id))
all_enabled = False
@app.on_message(Filters.command(['tpinall', 'tpinall@hexa_dex_bot']))
def hpinall(client, message):
    chat_id = message.chat.id
    user = message.from_user
    member = client.get_chat_member(chat_id, user.id)
    
    if member.status not in ['administrator', 'creator']:
        message.reply_text('You must be a group admin to use this command.')
        return
    
    
    
    global all_enabled
    args = message.text.split()
    if len(args) < 2:
        message.reply_text('Invalid argument. Use /hpinall on or /hpinall off.')
        return
    if args[1] == 'on':
        all_enabled = True
        message.reply_text('All users can now use the /hpin command.')
    elif args[1] == 'off':
        all_enabled = False
        message.reply_text('Only admins can use the /hpin command.')
    else:
        message.reply_text('Invalid argument. Use /hpinall on or /hpinall off.')


# ===== Stats =====
@app.on_message(Filters.private & Filters.create(lambda _, message: str(message.chat.id) not in stats['users']))
@app.on_message(Filters.group & Filters.create(lambda _, message: str(message.chat.id) not in stats['groups']))
def get_bot_data(app, message):
    cid = str(message.chat.id)
    if message.chat.type == 'private':
        stats['users'][cid] = {}
        name = message.chat.first_name
        try:
            name = message.chat.first_name + ' ' + message.chat.last_name
        except TypeError:
            name = message.chat.first_name
        stats['users'][cid]['name'] = name
        try:
            stats['users'][cid]['username'] = message.chat.username
        except AttributeError:
            pass

    elif message.chat.type in ['group', 'supergroup']:
        stats['groups'][cid] = {}
        stats['groups'][cid]['title'] = message.chat.title
        try:
            stats['groups'][cid]['username'] = message.chat.username
        except AttributeError:
            pass
        stats['groups'][cid]['members'] = app.get_chat(cid).members_count

    json.dump(stats, open('src/stats.json', 'w'), indent=4)
    print(stats)
    print('\n\n')
    message.continue_propagation()


@app.on_message(Filters.command(['stats', 'stats@hexa_dex_bot']))
def get_stats(app, message):
    if message.from_user.id in Config.sudo:
        members = 0
        for group in stats['groups']:
            members += stats['groups'][group]['members']
        text = texts['stats'].format(
            len(stats['users']),
            len(stats['groups']),
            members
        )
        app.send_message(
            chat_id=message.chat.id,
            text=text
        )


# ===== Home =====
@app.on_message(Filters.command(['start', 'start@hexa_dex_bot']))
def start(app, message):
    app.send_message(
        chat_id=message.chat.id,
        text=texts['start_message'],
        parse_mode='HTML'
    )

# ==== Type Pokemon =====
@app.on_message(Filters.command(['type', 'type@hexa_dex_bot']))
def ptype(app, message):
    try:
        gtype = message.text.split(' ')[1]
    except IndexError as s:
        app.send_message(
            chat_id=message.chat.id,
            text="`Syntex error: use eg '/type poison'`"
        )
        return
    try:
        data = jtype[gtype.lower()]
    except KeyError as s:
        app.send_message(
            chat_id=message.chat.id,
            text=("`This type doesn't exist good sir :/ `\n"
                  "`Do  /types  to check for the existing types.`")
        )
        return
    strong_against = ", ".join(data['strong_against'])
    weak_against = ", ".join(data['weak_against'])
    resistant_to = ", ".join(data['resistant_to'])
    vulnerable_to = ", ".join(data['vulnerable_to'])
    keyboard = ([[
        InlineKeyboardButton('All Types',callback_data=f"hexa_back_{message.from_user.id}")]])
    app.send_message(
        chat_id=message.chat.id,
        text=(f"Type  :  `{gtype.lower()}`\n\n"
              f"Strong Against:\n`{strong_against}`\n\n"
              f"Weak Against:\n`{weak_against}`\n\n"
              f"Resistant To:\n`{resistant_to}`\n\n"
              f"Vulnerable To:\n`{vulnerable_to}`"),
        reply_markup=InlineKeyboardMarkup(keyboard)
           
    )

# ==== Typew List =====
def ptype_buttons(user_id):
    keyboard = ([[
        InlineKeyboardButton('Normal',callback_data=f"type_normal_{user_id}"),
        InlineKeyboardButton('Fighting',callback_data=f"type_fighting_{user_id}"),
        InlineKeyboardButton('Flying',callback_data=f"type_flying_{user_id}")]])
    keyboard += ([[
        InlineKeyboardButton('Poison',callback_data=f"type_poison_{user_id}"),
        InlineKeyboardButton('Ground',callback_data=f"type_ground_{user_id}"),
        InlineKeyboardButton('Rock',callback_data=f"type_rock_{user_id}")]])
    keyboard += ([[
        InlineKeyboardButton('Bug',callback_data=f"type_bug_{user_id}"),
        InlineKeyboardButton('Ghost',callback_data=f"type_ghost_{user_id}"),
        InlineKeyboardButton('Steel',callback_data=f"type_steel_{user_id}")]])
    keyboard += ([[
        InlineKeyboardButton('Fire',callback_data=f"type_fire_{user_id}"),
        InlineKeyboardButton('Water',callback_data=f"type_water_{user_id}"),
        InlineKeyboardButton('Grass',callback_data=f"type_grass_{user_id}")]])
    keyboard += ([[
        InlineKeyboardButton('Electric',callback_data=f"type_electric_{user_id}"),
        InlineKeyboardButton('Psychic',callback_data=f"type_psychic_{user_id}"),
        InlineKeyboardButton('Ice',callback_data=f"type_ice_{user_id}")]])
    keyboard += ([[
        InlineKeyboardButton('Dragon',callback_data=f"type_dragon_{user_id}"),
        InlineKeyboardButton('Fairy',callback_data=f"type_fairy_{user_id}"),
        InlineKeyboardButton('Dark',callback_data=f"type_dark_{user_id}")]])
    keyboard += ([[
        InlineKeyboardButton('Delete',callback_data=f"hexa_delete_{user_id}")]])
    return keyboard
    
@app.on_message(Filters.command(['types', 'types@hexa_dex_bot']))
def types(app, message): 
    user_id = message.from_user.id
    app.send_message(
        chat_id=message.chat.id,
        text="List of types of Pokemons:",
        reply_markup=InlineKeyboardMarkup(ptype_buttons(user_id))
    )

# ===== Types Callback ====
@app.on_callback_query(Filters.create(lambda _, query: 'type_' in query.data))
def button(client: app, callback_query: CallbackQuery):
    q_data = callback_query.data
    query_data = q_data.split('_')[0]
    type_n = q_data.split('_')[1]
    user_id = int(q_data.split('_')[2])
    cuser_id = callback_query.from_user.id
    if cuser_id == user_id:
        if query_data == "type":
            data = jtype[type_n]
            strong_against = ", ".join(data['strong_against'])
            weak_against = ", ".join(data['weak_against'])
            resistant_to = ", ".join(data['resistant_to'])
            vulnerable_to = ", ".join(data['vulnerable_to'])
            keyboard = ([[
            InlineKeyboardButton('Back',callback_data=f"hexa_back_{user_id}")]])
            callback_query.message.edit_text(
                text=(f"Type  :  `{type_n}`\n\n"
                f"Strong Against:\n`{strong_against}`\n\n"
                f"Weak Against:\n`{weak_against}`\n\n"
                f"Resistant To:\n`{resistant_to}`\n\n"
                f"Vulnerable To:\n`{vulnerable_to}`"),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        callback_query.answer(
            text="You can't use this button!",
            show_alert=True
        )
    

@app.on_callback_query(Filters.create(lambda _, query: 'hexa_' in query.data))
def button2(client: app, callback_query: CallbackQuery):
    q_data = callback_query.data
    query_data = q_data.split('_')[1]
    user_id = int(q_data.split('_')[2])
    cuser_id = callback_query.from_user.id
    if user_id == cuser_id:
        if query_data == "back":
            callback_query.message.edit_text(
                "List of types of Pokemons:",
                reply_markup=InlineKeyboardMarkup(ptype_buttons(user_id))
            )
        elif query_data == "delete":
            callback_query.message.delete()
        else:
            return
    else:
        callback_query.answer(
            text="You can't use this button!",
            show_alert=True
        )
  
# ===== Pokemon Type Command ======
@app.on_message(Filters.command(['ptype', 'ptype@hexa_dex_bot']))
def poketypes(app, message): 
    user_id = message.from_user.id
    try:
        arg = message.text.split(' ')[1].lower()
    except IndexError:
        app.send_message(
            chat_id=message.chat.id,
            text=("`Syntex error: use eg '/ptype pokemon_name'`\n"
                  "`eg /ptype Pikachu`")
        )
        return  
    try:
        p_type = data[arg][arg]['type']
    except KeyError:
        app.send_message(
            chat_id=message.chat.id,
            text="`This pokemon doesn't exist good sir :/`"
        )
        return
    
    try:
        get_pt = f"{p_type['type1']}, {p_type['type2']:}"
        keyboard = ([[
        InlineKeyboardButton(p_type['type1'],callback_data=f"poket_{p_type['type1']}_{arg}_{user_id}"),
        InlineKeyboardButton(p_type['type2'],callback_data=f"poket_{p_type['type2']}_{arg}_{user_id}")]])
    except KeyError:
        get_pt = f"{p_type['type1']}"
        keyboard = ([[
        InlineKeyboardButton(p_type['type1'],callback_data=f"poket_{p_type['type1']}_{arg}_{user_id}")]])
    app.send_message(
        chat_id=message.chat.id,
        text=(f"Pokemon: `{arg}`\n\n"
              f"Types: `{get_pt}`\n\n"
              "__Click the button below to get the attact type effectiveness!__"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
@app.on_callback_query(Filters.create(lambda _, query: 'poket_' in query.data))
def poketypes_callback(client: app, callback_query: CallbackQuery):
    q_data = callback_query.data
    query_data = q_data.split('_')[1].lower()
    pt_name = q_data.split('_')[2]
    user_id = int(q_data.split('_')[3])  
    if callback_query.from_user.id == user_id:  
        data = jtype[query_data]
        strong_against = ", ".join(data['strong_against'])
        weak_against = ", ".join(data['weak_against'])
        resistant_to = ", ".join(data['resistant_to'])
        vulnerable_to = ", ".join(data['vulnerable_to'])
        keyboard = ([[
        InlineKeyboardButton('Back',callback_data=f"pback_{pt_name}_{user_id}")]])
        callback_query.message.edit_text(
            text=(f"Type  :  `{query_data}`\n\n"
            f"Strong Against:\n`{strong_against}`\n\n"
            f"Weak Against:\n`{weak_against}`\n\n"
            f"Resistant To:\n`{resistant_to}`\n\n"
            f"Vulnerable To:\n`{vulnerable_to}`"),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        callback_query.answer(
            text="You're not allow to use this!",
            show_alert=True
        )
    
@app.on_callback_query(Filters.create(lambda _, query: 'pback_' in query.data))
def poketypes_back(client: app, callback_query: CallbackQuery):
    q_data = callback_query.data
    query_data = q_data.split('_')[1].lower()
    user_id = int(q_data.split('_')[2]) 
    if callback_query.from_user.id == user_id:
        p_type = data[query_data][query_data]['type']
        try:
            get_pt = f"{p_type['type1']}, {p_type['type2']:}"
            keyboard = ([[
            InlineKeyboardButton(p_type['type1'],callback_data=f"poket_{p_type['type1']}_{query_data}_{user_id}"),
            InlineKeyboardButton(p_type['type2'],callback_data=f"poket_{p_type['type2']}_{query_data}_{user_id}")]])
        except KeyError:
            get_pt = f"{p_type['type1']}"
            keyboard = ([[
            InlineKeyboardButton(p_type['type1'],callback_data=f"poket_{p_type['type1']}_{query_data}_{user_id}")]])
        callback_query.message.edit_text(
            (f"Pokemon: `{query_data}`\n\n"
             f"Types: `{get_pt}`\n\n"
             "__Click the button below to get the attact type effectiveness!__"),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        callback_query.answer(
            text="You're not allow to use this!",
            show_alert=True
        )
    
        
# ===== Data command =====
@app.on_callback_query(Filters.create(lambda _, query: 'basic_infos' in query.data))
@app.on_message(Filters.command(['data', 'data@hexa_dex_bot']))
def pkmn_search(app, message):
    try:
        if message.text == '/data' or message.text == '/data@hexa_dex_bot':
            app.send_message(message.chat.id, texts['error1'], parse_mode='HTML')
            return None
        pkmn = func.find_name(message.text)
        result = func.check_name(pkmn, data)

        if type(result) == str:
            app.send_message(message.chat.id, result)
            return None
        elif type(result) == list:
            best_matches(app, message, result)
            return None
        else:
            pkmn = result['pkmn']
            form = result['form']
    except AttributeError:
        pkmn = re.split('/', message.data)[1]
        form = re.split('/', message.data)[2]


    if pkmn in form:
        text = func.set_message(data[pkmn][form], reduced=True)
    else:
        base_form = re.sub('_', ' ', pkmn.title())
        name = base_form + ' (' + data[pkmn][form]['name'] + ')'
        text = func.set_message(data[pkmn][form], name, reduced=True)

    markup_list = [[
        InlineKeyboardButton(
            text='➕ Expand',
            callback_data='all_infos/'+pkmn+'/'+form
        )
    ],
    [
        InlineKeyboardButton(
            text='⚔ Moveset',
            callback_data='moveset/'+pkmn+'/'+form
        ),
        InlineKeyboardButton(
            text='🗾 Locations',
            callback_data='locations/'+pkmn+'/'+form
        )
    ]]
    for alt_form in data[pkmn]:
        if alt_form != form:
            markup_list.append([
                InlineKeyboardButton(
                    text=data[pkmn][alt_form]['name'],
                    callback_data='basic_infos/'+pkmn+'/'+alt_form
                )
            ])
    markup = InlineKeyboardMarkup(markup_list)

    func.bot_action(app, message, text, markup)


def best_matches(app, message, result):
    text = texts['results']
    emoji_list = ['❶', '❷', '❸']
    index = 0
    for dictt in result:
        pkmn = dictt['pkmn']
        form = dictt['form']
        percentage = dictt['percentage']
        form_name = data[pkmn][form]['name']
        name = func.form_name(pkmn.title(), form_name)
        text += '\n{} <b>{}</b> (<i>{}</i>)'.format(
            emoji_list[index],
            name,
            percentage
        )
        if index == 0:
            text += ' [<b>Top result!</b>]'
        index += 1
    app.send_message(message.chat.id, text, parse_mode='HTML')


@app.on_callback_query(Filters.create(lambda _, query: 'all_infos' in query.data))
def all_infos(app, call):
    pkmn = re.split('/', call.data)[1]
    form = re.split('/', call.data)[2]
    
    if pkmn in form:
        text = func.set_message(data[pkmn][form], reduced=False)
    else:
        base_form = re.sub('_', ' ', pkmn.title())
        name = base_form + ' (' + data[pkmn][form]['name'] + ')'
        text = func.set_message(data[pkmn][form], name, reduced=False)

    markup_list = [[
        InlineKeyboardButton(
            text='➖ Reduce',
            callback_data='basic_infos/'+pkmn+'/'+form
        )
    ],
    [
        InlineKeyboardButton(
            text='⚔ Moveset',
            callback_data='moveset/'+pkmn+'/'+form
        ),
        InlineKeyboardButton(
            text='🗾 Locations',
            callback_data='locations/'+pkmn+'/'+form
        )
    ]]
    for alt_form in data[pkmn]:
        if alt_form != form:
            markup_list.append([
                InlineKeyboardButton(
                    text=data[pkmn][alt_form]['name'],
                    callback_data='basic_infos/'+pkmn+'/'+alt_form
                )
            ])
    markup = InlineKeyboardMarkup(markup_list)

    func.bot_action(app, call, text, markup)


@app.on_callback_query(Filters.create(lambda _, query: 'moveset' in query.data))
def moveset(app, call):
    pkmn = re.split('/', call.data)[1]
    form = re.split('/', call.data)[2]
    if len(re.split('/', call.data)) == 4:
        page = int(re.split('/', call.data)[3])
    else:
        page = 1
    dictt = func.set_moveset(pkmn, form, page)

    func.bot_action(app, call, dictt['text'], dictt['markup'])


@app.on_callback_query(Filters.create(lambda _, query: 'locations' in query.data))
def locations(app, call):
    pkmn = re.split('/', call.data)[1]
    form = re.split('/', call.data)[2]

    text = func.get_locations(data, pkmn)

    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text='⚔ Moveset',
            callback_data='moveset/'+pkmn+'/'+form
        )
    ],
    [
        InlineKeyboardButton(
            text='🔙 Back to basic infos',
            callback_data='basic_infos/'+pkmn+'/'+form
        )
    ]])

    func.bot_action(app, call, text, markup)


# ===== Usage command =====
@app.on_callback_query(Filters.create(lambda _, query: 'usage' in query.data))
@app.on_message(Filters.command(['usage', 'usage@hexa_dex_bot']))
def usage(app, message):
    try:
        page = int(re.split('/', message.data)[1])
        dictt = func.get_usage_vgc(int(page), usage_dict['vgc'])
    except AttributeError:
        page = 1
        text = '<i>Connecting to Pokémon Showdown database...</i>'
        message = app.send_message(message.chat.id, text, parse_mode='HTML')
        dictt = func.get_usage_vgc(int(page))
        usage_dict['vgc'] = dictt['vgc_usage']

    leaderboard = dictt['leaderboard']
    base_text = texts['usage']
    text = ''
    for i in range(15):
        pkmn = leaderboard[i]
        text += base_text.format(
            pkmn['rank'],
            pkmn['pokemon'],
            pkmn['usage'],
        )
    markup = dictt['markup']

    func.bot_action(app, message, text, markup)


# ===== FAQ command =====
@app.on_message(Filters.command(['faq', 'faq@hexa_dex_bot']))
def faq(app, message):
    text = texts['faq']
    app.send_message(
        chat_id=message.chat.id,
        text=text, 
        parse_mode='HTML',
        disable_web_page_preview=True
    )



# ===== About command =====
@app.on_message(Filters.command(['about', 'about@hexa_dex_bot']))
def about(app, message):
    text = texts['about']
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text='Github',
            url='https://github.com/alessiocelentano/rotomgram'
        )
    ]])

    app.send_message(
        chat_id=message.chat.id,
        text=text, 
        reply_markup=markup,
        disable_web_page_preview=True
    )

    
    
    
    # ===== tms command =====
@app.on_message(Filters.command(['tms', 'tms@hexa_dex_bot']))
def about(app, message):
    text = texts['tms']
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text='tms list',
            url='https://telegra.ph/file/8d39d02c47da829199810.png'
        )
    ]])
    
    app.send_message(
        chat_id=message.chat.id,
        text=text, 
        reply_markup=markup,
        disable_web_page_preview=True
    )
    
    
    

# ===== Raid commands =====
@app.on_message(Filters.command(['addcode', 'addcode@hexa_dex_bot']))
def call_add_fc(app, message):
    raid.add_fc(app, message, texts)

@app.on_message(Filters.command(['mycode', 'mycode@hexa_dex_bot']))
def call_show_my_fc(app, message):
    raid.show_my_fc(app, message, texts)

@app.on_message(Filters.command(['newraid', 'newraid@hexa_dex_bot']))
def call_new_raid(app, message):
    raid.new_raid(app, message, texts)

@app.on_callback_query(Filters.create(lambda _, query: 'stars' in query.data))
def call_stars(app, message):
    raid.stars(app, message, texts)

@app.on_callback_query(Filters.create(lambda _, query: 'join' in query.data))
def call_join(app, message):
    raid.join(app, message, texts)

@app.on_callback_query(Filters.create(lambda _, query: 'done' in query.data))
def call_done(app, message):
    raid.done(app, message, texts)

@app.on_callback_query(Filters.create(lambda _, query: 'yes' in query.data))
def call_confirm(app, message):
    raid.confirm(app, message, texts)

@app.on_callback_query(Filters.create(lambda _, query: 'no' in query.data))
def call_back(app, message):
    raid.back(app, message, texts)

@app.on_callback_query(Filters.create(lambda _, query: 'pin' in query.data))
def call_pin(app, message):
    raid.pin(app, message, texts)


# ===== Presentation =====
@app.on_message(Filters.create(lambda _, message: message.new_chat_members))
def bot_added(app, message):
    for new_member in message.new_chat_members:
        if new_member.id == 1860622985:
            text = texts['added']
            app.send_message(
                chat_id=message.chat.id,
                text=text
            )


app.run()
