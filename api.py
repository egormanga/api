#!/usr/bin/python3
# VK API lib

import vaud, requests
from .apiconf import app_id, al_im_hash, api_service_key
from bs4 import BeautifulSoup as bs4
from PIL import Image
from utils import *; logstart('API')

""" Base main() function for a bot:
def main():
	db.load()
	setonsignals(exit)
	setonline()
	exceptions = queue.Queue()
	lp(eq=exceptions)
	while (True):
		try:
			try: ex = exceptions.get()
			except queue.Empty: pass
			except TypeError: raise KeyboardInterrupt()
			else: raise ex
		except Exception as ex: exception(ex)
		except KeyboardInterrupt as ex: exit(ex)
(not a bare minimum though) """

api_version = '5.89'
lp_version = '3'
use_al_apis = { # {'mask': use_for_group
	'audio.*': True,
	'messages.send': False,
	'messages.edit': False,
	'messages.delete': False,
	'messages.setActivity': False,
	'messages.getLongPollServer': False,
	'messages.getConversations': False,
	'messages.getHistoryAttachments': False,
}


class al_audio_consts:
	AUDIO_ITEM_INDEX_ID = 0
	AUDIO_ITEM_INDEX_OWNER_ID = 1
	AUDIO_ITEM_INDEX_URL = 2
	AUDIO_ITEM_INDEX_TITLE = 3
	AUDIO_ITEM_INDEX_PERFORMER = 4
	AUDIO_ITEM_INDEX_DURATION = 5
	AUDIO_ITEM_INDEX_ALBUM_ID = 6
	AUDIO_ITEM_INDEX_AUTHOR_LINK = 8
	AUDIO_ITEM_INDEX_LYRICS = 9
	AUDIO_ITEM_INDEX_FLAGS = 10
	AUDIO_ITEM_INDEX_CONTEXT = 11
	AUDIO_ITEM_INDEX_EXTRA = 12
	AUDIO_ITEM_INDEX_HASHES = 13
	AUDIO_ITEM_INDEX_COVER_URL = 14
	AUDIO_ITEM_INDEX_ADS = 15
	AUDIO_ITEM_INDEX_SUBTITLE = 16
	AUDIO_ITEM_INDEX_MAIN_ARTISTS = 17
	AUDIO_ITEM_INDEX_FEAT_ARTISTS = 18
	AUDIO_ITEM_INDEX_ALBUM = 19
	AUDIO_ITEM_INDEX_TRACK_CODE = 20
	AUDIO_ITEM_INDEX_RESTRICTION = 21
	AUDIO_ITEM_INDEX_ALBUM_PART = 22
	AUDIO_ITEM_INDEX_NEW_STATS = 23
	AUDIO_ITEM_HAS_LYRICS_BIT = 1
	AUDIO_ITEM_CAN_ADD_BIT = 2
	AUDIO_ITEM_CLAIMED_BIT = 4
	AUDIO_ITEM_HQ_BIT = 64#16
	AUDIO_ITEM_LONG_PERFORMER_BIT = 32
	AUDIO_ITEM_UMA_BIT = 128
	AUDIO_ITEM_REPLACEABLE = 512
	AUDIO_ITEM_EXPLICIT_BIT = 1024

def ret(url, data=None, wrap=False, method='ret', max_tries=5):
	for i in range(max_tries if (wrap) else 1):
		time.sleep(i)
		try:
			res = requests.post(url, data=data).json()
			if ('error' in res): raise \
				VKAPIError(res['error'], method)
			return res['response']
		except Exception as ex:
			if (not wrap or (type(ex) == VKAPIError and ex.args[0]['error_code'] not in (6, 10, 14))): raise

def api(method, mode='user', wrap=True, max_tries=5, nolog=False, **kwargs): # TODO: move api() & ret() into API [maybe.]
	parseargs(kwargs, v=api_version)
	if (not method): return False
	use_al = al_get_method(method)
	if (use_al is not None and (use_al or mode == 'user')): return al(method, nolog=nolog, **kwargs)
	if (not nolog): log(2, f"Request: method={method}, data={kwargs}")
	r = ret("https://api.vk.com/method/"+method, data=kwargs, wrap=wrap, method=method, max_tries=max_tries)
	if (not nolog): log(3, f"Response: {r}")
	return r

vk_sid = str()
def setvksid(vk_sid_): global vk_sid; vk_sid = vk_sid_
def getvksid(): return vk_sid

def al_get_method(method): return use_al_apis.get(method, use_al_apis.get(method.partition('.')[0]+'.*'))
def al_extract(r): return regex.findall(r'<!\w+>(.*?)<!>', r)
def al_unhtml_text(text): return html.unescape(re.sub(r'<.*?alt="(.*?)">', r'\1', text)).replace('\xa0', ' ').replace('<br>', '\n')
def al_parse_attachments(a):
	try: return [{'type': a[i+'_type'], a[i+'_type']: (
		API.photos.getById(photos=a[i]) if (a[i+'_type'] == 'photo') else
		API.video.get(videos=a[i]) if (a[i+'_type'] == 'video') else
		API.audio.getById(audios=a[i]) if (a[i+'_type'] == 'audio') else
		API.docs.getById(docs=a[i]) if (a[i+'_type'] == 'doc') else
		API.wall.getById(posts=a[i]) if (a[i+'_type'] == 'wall') else
		a[i]
	)} for i in a if re.match(r'attach\d+$', i)]
	except VKAPIError: return []
def al_parse_audio(a):
	return {
		'id': a[al_audio_consts.AUDIO_ITEM_INDEX_ID],
		'owner_id': a[al_audio_consts.AUDIO_ITEM_INDEX_OWNER_ID],
		'artist': al_unhtml_text(a[al_audio_consts.AUDIO_ITEM_INDEX_PERFORMER]),
		'title': al_unhtml_text(a[al_audio_consts.AUDIO_ITEM_INDEX_TITLE]),
		'duration': a[al_audio_consts.AUDIO_ITEM_INDEX_DURATION],
		#'date'
		'url': a[al_audio_consts.AUDIO_ITEM_INDEX_URL], # TODO vaud
		'lyrics_id': a[al_audio_consts.AUDIO_ITEM_INDEX_LYRICS],
		'album_id': a[al_audio_consts.AUDIO_ITEM_INDEX_ALBUM],
		#'genre_id'
		'is_hq': a[al_audio_consts.AUDIO_ITEM_INDEX_FLAGS] & al_audio_consts.AUDIO_ITEM_HQ_BIT,
		'track_code': a[al_audio_consts.AUDIO_ITEM_INDEX_TRACK_CODE],
		'is_explicit': a[al_audio_consts.AUDIO_ITEM_INDEX_FLAGS] & al_audio_consts.AUDIO_ITEM_EXPLICIT_BIT,
		'main_artists': a[al_audio_consts.AUDIO_ITEM_INDEX_MAIN_ARTISTS],
		'featured_artists': a[al_audio_consts.AUDIO_ITEM_INDEX_FEAT_ARTISTS],
		'subtitle': a[al_audio_consts.AUDIO_ITEM_INDEX_SUBTITLE],
		#'no_search'
		'hashes': dict(zip(('addHash', 'editHash', 'actionHash', 'deleteHash', 'replaceHash', 'urlHash', 'restoreHash'), a[al_audio_consts.AUDIO_ITEM_INDEX_HASHES].split('/'))),
	}
def al_parse_audio_id(a): return f"{a['owner_id']}_{a['id']}_{a['hashes']['actionHash']}_{a['hashes']['urlHash']}"
def al_audio_get_hash(a): return hash(f"{a.get('owner_id')}_{a.get('id')}_{a.get('hashes')}")
def al_audio_eq(a, b): return al_audio_get_hash(a) == al_audio_get_hash(b)
def al_audio_get_url(user_id, a):
	if (not a.get('url')): a['url'] = API.audio.getById(audios=al_parse_audio_id(a))[0]['url']
	a['url'] = vaud.decode(user_id, a['url'])
	return a['url']

def al_parse_audio_list(kwargs, r):
	r['list'] = list(map(al_parse_audio, r['list']))
	#for i in range(0, len(r['list']), 9): r['list'][i:i+10] = map(al_parse_audio, API.audio.getById(audios=','.join(map(al_parse_audio_id, r['list'][i:i+10])))) # too slow
	return S(r).translate({'has_more': ('hasMore', bool), 'next_from': 'nextOffset'})
def al_parse_audio_search(kwargs, r):
	r = json.loads(al_extract(r)[0])
	r['playlists'] = list(map(lambda x: al_parse_audio_list(kwargs, x), r['playlists']))
	return S(r).with_('has_more', False) # TODO
def al_parse_dialogs(kwargs, r):
	r = tuple(map(json.loads, al_extract(r)))
	return {
		#'count'
		'items': [{
			'conversation': {
				'peer': {
					'id': i['peerId'],
					'type': 'group' if (i['peerId'] < 0) else 'chat' if (i['peerId'] > 2000000000) else 'user',
					#'local_id'
				},
				'in_read': i['in_up_to'],
				'out_read': i.get('out_up_to'),
				'last_message_id': i['lastmsg_meta'][0],
				#'unread_count'
				'can_write': {
					#'allowed'
				},
				'chat_settings': {
					'title': al_unhtml_text(i['tab']),
					#'pinned_message'
					'members_count': i.get('membersCount'),
					#'state'
					'photo': {j: i.get('photo') for j in ('photo_50', 'photo_100', 'photo_200')},# if (i.get('photo')) else S(user(i['peerId'], fields='photo_50,photo_100,photo_200', groups=True)[0])@['photo_50', 'photo_100', 'photo_200'], # too long
					'active_ids': i.get('data', {}).get('active'),
					#'acl'
					#'is_group_channel'
					'owner_id': i.get('ownerId'),
				},
				'push_settings': {
					#'no_sound'
					#'disabled_until'
					#'disabled_forever'
				}
			},
			'last_message': {
				#'date'
				'from_id': i['lastmsg_meta'][5].get('from') if (isinstance(i['lastmsg_meta'][5], dict)) else None,
				'id': i['lastmsg_meta'][0],
				'out': i['lastmsg_meta'][1] & +2,
				'peer_id': i['lastmsg_meta'][2],
				'text': al_unhtml_text(i['lastmsg_meta'][4]),
				'conversation_message_id': i['lastmsg_meta'][8],
				#'fwd_messages'
				'important': i['lastmsg_meta'][1] & +8,
				'random_id': i['lastmsg_meta'][7],
				'attachments': al_parse_attachments(i['lastmsg_meta'][5]) if (kwargs.get('parse_attachments')) else [],
				'is_hidden': i['lastmsg_meta'][1] & +65536,
			}
		} for i in r[1].values()],
		#'unread_count'
		'profiles': user(S(r[2])@['id']) if (kwargs.get('extended')) else [],
		'groups': groups(-i for i in S(r[2])@['id'] if i < 0) if (kwargs.get('extended')) else [],
		'offset': r[0]['offset'],
		'has_more': r[0]['has_more'],
	}
def al_parse_history_attachments(kwargs, r):
	count, offset = S(json.loads(al_extract(r)[1]))@['count', 'offset']
	if (kwargs['media_type'] == 'audio'):
		res = [al_parse_audio(json.loads(html.unescape(i))) for i in re.findall(r'data-audio="(\[.*\])"', r)]
	else: raise NotImplementedError(kwargs['media_type'])
	return {
		'count': count,
		'items': [{
			#'message_id'
			'attachment': {
				'type': kwargs['media_type'],
				kwargs['media_type']: i,
			},
		} for i in res],
		'next_from': offset,
		'has_more': count > offset,
	}

al_actions = {
	'audio.get': ('al_audio', 'load_section'),
	'audio.getById': ('al_audio', 'reload_audio'),
	'audio.getFriends': ('al_audio', 'more_friends'),
	'audio.search': ('al_audio', 'section'),
	'messages.send': ('al_im', 'a_send'),
	'messages.edit': ('al_im', 'a_edit_message'),
	'messages.delete': ('al_im', 'a_mark'),
	'messages.setActivity': ('al_im', 'a_activity'),
	'messages.getConversations': ('al_im', 'a_get_dialogs'),
	'messages.getHistoryAttachments': ('wkview', 'show'),
}
al_params = {
	'audio.get': lambda kwargs: {'owner_id': kwargs.get('owner_id', ''), 'type': 'playlist', 'playlist_id': kwargs.get('album_id', -1), 'offset': kwargs.get('offset', 0), 'count': kwargs.get('count', '')},
	'audio.getById': lambda kwargs: {'ids': kwargs.get('audios')},
	'audio.getFriends': lambda kwargs: kwargs,
	'audio.search': lambda kwargs: {'owner_id': kwargs.get('owner_id', ''), 'section': 'search', 'q': kwargs.get('q', ''), 'offset': kwargs.get('offset', 0), 'count': kwargs.get('count', ''), **kwargs},
	'messages.send': lambda kwargs: {'to': kwargs.get('peer_id', ''), 'msg': kwargs.get('message', ''), 'media': kwargs.get('attachment', '')},
	'messages.edit': lambda kwargs: {'peerId': kwargs.get('peer_id', ''), 'msg': kwargs.get('message', ''), 'media': kwargs.get('attachment', ''), 'id': kwargs.get('message_id', '')},
	'messages.delete': lambda kwargs: {'peer': kwargs.get('peer_id', ''), 'msgs_ids': kwargs.get('message_ids', ''), 'mark': 'deleteforall' if (kwargs.get('delete_for_all', False)) else 'delete'},
	'messages.setActivity': lambda kwargs: {'peer': kwargs.get('peer_id', ''), 'type': kwargs.get('type', '')},
	'messages.getConversations': lambda kwargs: kwargs, # TODO?
	'messages.getHistoryAttachments': lambda kwargs: {'w': f"history{kwargs.get('peer_id')}_{kwargs.get('media_type')}", 'offset': kwargs.get('start_from'), 'count': kwargs.get('count')},
}
al_return = {
	'audio.get': lambda kwargs, r: al_parse_audio_list(kwargs, json.loads(al_extract(r)[0])), # TODO api object
	'audio.getById': lambda kwargs, r: list(map(al_parse_audio, json.loads(al_extract(r)[0]))),
	'audio.getFriends': lambda kwargs, r: json.loads(al_extract(r)[0]),
	'audio.search': al_parse_audio_search, # TODO api object
	'messages.send': lambda kwargs, r: json.loads(al_extract(r)[0])['msg_id'],
	'messages.edit': lambda kwargs, r: json.loads(al_extract(r)[0])['msg_id'],
	'messages.delete': lambda kwargs, r: int(al_extract(r)[0]),
	'messages.setActivity': lambda kwargs, r: int(al_extract(r)[0]),
	'messages.getConversations': al_parse_dialogs,
	'messages.getHistoryAttachments': al_parse_history_attachments,
}

def al(method, vk_sid_=None, nolog=False, **kwargs):
	if (vk_sid_ is None): vk_sid_ = vk_sid
	assert vk_sid_ # TODO: auto-login
	if (method == 'messages.getLongPollServer'): return al_get_lp(vk_sid_)
	al, act = al_actions.get(method, method.partition('.')[::2])
	data = al_params.get(method, lambda x: x)(kwargs)
	if (method.partition('.')[0] == 'messages'): parseargs(data, im_v=2, hash=al_im_hash)
	parseargs(data, al=1)
	if (not al or not act): return False
	if (not nolog): log(2, f"Al Request: al={al}, act={act}, data={data}")
	e = None
	r = None
	try: r = requests.post(f"https://vk.com/{al}.php?act={act}", data=data, cookies={'remixsid': vk_sid_}).text+'<!>'
	except Exception as ex: raise VKAPIError({'error_code': 0}, method) from ex
	r = al_return.get(method, lambda x: x)(kwargs, r)
	if (not nolog): log(3, f"Al Response: {r}")
	return r
def al_login(login, password):
	global vk_sid
	s = requests.session()
	s.post(bs4(s.get('https://m.vk.com/login').text, 'html.parser').form['action'], data={'email': login, 'pass': password})
	vk_sid = s.cookies['remixsid']
def al_login_stdin(): return al_login(input('VK Login: '), getpass.getpass())
def al_get_lp(vk_sid_=None):
	if (vk_sid_ is None): vk_sid_ = vk_sid
	r = re.search(r'lpConfig:\ ?({.*?})', requests.get('https://vk.com/im', headers={'User-Agent': 'Linux'}, cookies={'remixsid': vk_sid_}, allow_redirects=False).text, re.S)[1]
	def extract(x): return re.search(rf'''['"]?{x}['"]?:\ ?['"]?([\w.:/]+)['"]?''', r)[1]
	return {'server': extract('url'), 'key': extract('key'), 'ts': extract('ts')}

class _send:
	def __init__(self):
		self.prefix = None
	def __call__(self, peer_id, message, prefix=None, nolog=True, **kwargs):
		parseargs(kwargs, peer_id=peer_id, message=message)
		#if (not message.strip()): return
		if (prefix is None): prefix = '👾' if (self.prefix is None and API.mode != 'group') else self.prefix or ''
		if ('keyboard' in kwargs and not kwargs['keyboard']): kwargs.pop('keyboard')
		if (not nolog): log(1, f"Sending message to {peer_id}:\n"+(kwargs['message']+str().join((f' <{i}>' for i in kwargs.get('attachment').split(',') or ()))).indent())
		kwargs.update({'message': prefix+' '+str(message), 'nolog': bool(nolog) and nolog != True})
		return (API.messages.send if (not kwargs.get('message_id')) else API.messages.edit)(**kwargs)

def openimg(img):
	try: return img if (Image.isImageType(img)) else Image.open(img)
	except: pass
	try: return Image.open(requests.get(img, stream=True).raw)
	except: pass
	raise \
		FileNotFoundError(img)
def saveimg(img):
	if (Image.isImageType(img)): f = io.BytesIO(); f.name = 'saveimg.png'; img.save(f); f.seek(0); return f
	if (isinstance(img, io.IOBase)): return img
	try: f = requests.get(img, stream=True).raw; f.name = 'saveimg.png'; return f
	except: pass
	return saveimg(openimg(img))

def attach(peer_id, file, type='doc', **kwargs):
	file = saveimg(file)
	if (type == 'photo'): return "photo{owner_id}_{id}".format_map(API.photos.saveMessagesPhoto(**requests.post(API.photos.getMessagesUploadServer(peer_id=peer_id, **kwargs)['upload_url'], files={'photo': file}).json())[0])
	return "doc{owner_id}_{id}".format_map(API.docs.save(**requests.post(API.docs.getMessagesUploadServer(peer_id=peer_id, type=type, **kwargs)['upload_url'], files={'photo' if (type == 'photo') else 'file': file}).json())[0])
def setactivity(peer_id, type, **kwargs): parseargs(kwargs, peer_id=peer_id, type=type); return API.messages.setActivity(**kwargs)
def settyping(peer_id, type='typing', **kwargs): logexception(DeprecationWarning("*** settyping() → setactivity(type='typing') ***")); parseargs(kwargs, peer_id=peer_id, type=type); return setactivity(**kwargs)

commands = dict()
def sendhelp(peer_id, commands=commands, n=4, head='', title='Доступные команды:', tail='', keyboard=True, display=2, **kwargs): return send(peer_id, f"{head}\n\n{title}\n%s\n\n{tail}" % '\n'.join('%s — %s' % (i[0]+(' (%s)' % ', '.join(i[1:display])) if (display > 1) else '', i[-2]) for i in commands if i[-1] > -1), keyboard=mkkeyboard(commands if (keyboard) else {}, n, one_time=keyboard) if (API.mode == 'group') else '', **kwargs) # •
def mkkeyboard(commands, n=4, one_time=True):
	keyboard = {
		'one_time': one_time,
		'buttons': Slist({
			'action': {
				'type': 'text',
				'label': i[0],
				#'payload': i[0]
			},
			'color': ('default', 'primary', 'positive', 'negative')[i[-1]]
		} for i in commands if i[-1] != -1).group(n)
	}
	#log(1, json.dumps(keyboard, ensure_ascii=False, indent=4))
	if (len(keyboard['buttons']) > 10): raise \
		VKKeyboardError(len(keyboard['buttons']))
	return json.dumps(keyboard, ensure_ascii=False)

def message(message_ids, **kwargs): parseargs(kwargs, message_ids=message_ids); return API.messages.getById(**kwargs)
def messages(peer_id, **kwargs): parseargs(kwargs, peer_id=peer_id); return API.messages.getHistory(**kwargs)
def dialogs(**kwargs): return API.messages.getConversations(**kwargs)
def getcounters(**kwargs): return API.account.getCounters(**kwargs)

def read(peer_id, start_message_id=int(), **kwargs): parseargs(kwargs, peer_id=peer_id, start_message_id=start_message_id or messages(peer_id, nolog=True)['items'][0]['id']); return API.messages.markAsRead(**kwargs)
def delete(message_ids, **kwargs): parseargs(kwargs, message_ids=message_ids); return API.messages.delete(**kwargs)

def user(items=None, groups=False, **kwargs):
	if (isinstance(items, int)): items = (items,)
	elif (isinstance(items, str)): items = (*map(str.strip, items.split(',')),)
	res = list()
	if (not groups and items is not None): res += API.users.get(user_ids=','.join(map(str, items)), **kwargs)
	elif (items is not None):
		items_u = Slist(items).copy()
		items_g = Slist(items).copy()
		for i in items:
			if (isinstance(i, int) or i.lstrip('-').isdecimal()): (items_u, items_g)[int(i) > 0].remove(i)
		if (items_u):
			try: res += API.users.get(user_ids=','.join(map(str, items_u)), **kwargs) or []
			except VKAPIError: pass
		if (items_g):
			try: res += [S(i).with_('id', -i['id']) for i in API.groups.getById(group_ids=','.join(str(i).lstrip('-') for i in items_g), **kwargs) or []]
			except VKAPIError: pass
	else: res += API.users.get(**kwargs)
	for i in res:
		if ('first_name' not in i): i['first_name'] = i['name']
		if ('last_name' not in i): i['last_name'] = ''
		if ('name' not in i): i['name'] = ' '.join(S(i)@['first_name', 'last_name']).strip(' ')
		if ('domain' not in i): i['domain'] = i.get('screen_name', f"id{i['id']}")
		i['name_case'] = kwargs.get('name_case', 'nom')
	return res
def refuser(u, nopush=False, domain=False, fullname=False, **kwargs):
	try:
		if (not isinstance(u, dict) or not u.get('name') or kwargs.get('name_case') and u.get('name_case', kwargs.get('name_case')) != kwargs.get('name_case')): u = user(u['id'] if (isinstance(u, dict)) else u, groups=True, wrap=False, nolog=False, **kwargs)[0]
		name = u.get('name') if (fullname) else u.get('first_name') or u['name']
		return f"[{u['domain']}|{name}]" if (not domain and not nopush) else f"@{u['domain']}" if (not nopush) else name
	except Exception as ex: raise#logexception(ex); return f'@{u}'
def derefuser(s):
	try: r = regex.match(r'(?| \[(.*?)\|(.*?)\] | @(\w+)\ ?(?:\((\w+)\))? | (?:https?://)?(?:vk.com/)?(\w+) )(.*)', s, regex.X).groups()
	except AttributeError: r = (None, None, None)
	return (r[0] or s, r[1] or s, r[2] or s)

def proc_cmd(c): return (re.sub(rf'\[(?:club{group.id}|{group.screen_name})\|.*?\]', '', c).strip(' ') if (API.mode == 'group') else c).split()

def groups(group_ids='', **kwargs):
	parseargs(kwargs, group_ids=S(',').join(group_ids) if (not isinstance(group_ids, (str, int))) else group_ids, fields='')
	try: return API.groups.getById(**kwargs)
	except VKAPIError as ex:
		if (ex.args[0]['error_code'] == 100): return []
		else: raise
def ismember(group_id, user_ids, **kwargs): return API.groups.isMember(group_id=group_id, user_ids=user_ids, **kwargs)

def chat(chat_id, **kwargs): parseargs(kwargs, chat_id=(chat_id % 100000000)); return API.messages.getChat(**kwargs)
def chatonline(chat_id, **kwargs): parseargs(kwargs, chat_id=(chat_id % 100000000)); return execute('return API.messages.getChat({"chat_id": Args.chat_id, "fields": "online"}).users@.online;', **kwargs).count(1)
def chatadd(chat_id, user_ids, **kwargs): parseargs(kwargs, chat_id=(chat_id % 100000000), user_id=user_ids); return Slist([execute('var ret = [], user_ids = Args.user_ids.split(","); while (user_ids) ret.push(API.messages.addChatUser({"chat_id": Args.chat_id, "user_id": user_ids.pop()})); return ret;', user_ids=i, **kwargs) for i in Slist(user_ids).group(25)]).combine() if (hasattr(user_ids, '__iter__') and type(user_ids) != str) else API.messages.addChatUser(**kwargs)
def chatkick(chat_id, member_id, **kwargs): parseargs(kwargs, chat_id=(chat_id % 100000000), member_id=member_id); return API.messages.removeChatUser(**kwargs)
def chatinvitelink(peer_id, **kwargs): parseargs(kwargs, peer_id=peer_id); return API.messages.getInviteLink(**kwargs)
def chattitle(chat_id, title, **kwargs): parseargs(kwargs, chat_id=(chat_id % 100000000), title=title); return API.messages.editChat(**kwargs)
def chatphoto(chat_id, photo, **kwargs): parseargs(kwargs, chat_id=(chat_id % 100000000)); return API.messages.setChatPhoto(file=requests.post(API.photos.getChatUploadServer(**kwargs)['upload_url'], files={'photo': saveimg(photo)}).json()['response'], **kwargs)

def friends(user_id=0, **kwargs): parseargs(kwargs, user_id=user_id); return API.friends.get(**kwargs)

def getstatus(**kwargs): return API.status.get(**kwargs)['text']
def setstatus(text, **kwargs): parseargs(kwargs, text=text, group_id=group.id); return API.status.set(**kwargs)

def setonline(x=True, nolog=True, **kwargs):
	parseargs(kwargs, nolog=nolog)
	if (not nolog): logstart(f"{('Disabling', 'Enabling')[x]} {API.mode} online")
	if (API.mode == 'group'):
		#return not nolog and log("Online switch disabled during developement.", raw=True)
		parseargs(kwargs, group_id=group.id)
	try:
		#r = api('groups.%sOnline' % x, **kwargs) if (API.mode == 'group') else api('account.set%s' % 'Online' if (x) else 'Offline', **kwargs)
		r = ((API.groups.disableOnline, API.groups.enableOnline)[x] if (API.mode == 'group') else (API.account.setOffline, API.account.setOnline)[x])(**kwargs)
		if (not nolog): logok()
		return r
	except Exception as ex:
		if (not nolog): logex(ex)

def setcover(photo, **kwargs): parseargs(kwargs, group_id=group.id, crop_x2=1590, crop_y2=400); return API.photos.saveOwnerCoverPhoto(**requests.post(API.photos.getOwnerCoverPhotoUploadServer(**kwargs)['upload_url'], files={'photo': saveimg(photo)}).json())

def execute(code, **kwargs): parseargs(kwargs, code=code); return API.execute(**kwargs)

def copy_message(m, peer_id, stickers_size=-1, **kwargs):
	if (m.get('fwd_messages')): m['text'] += "\n\n[Пересланные сообщения]\n"+'\n'.join(S(refuser(i['from_id'], nopush=True, fullname=True)+': '+format_message(i)).indent(1, char='⠀| ') for i in m['fwd_messages'])
	return send(peer_id, m['text'], attachment=copy_attachments(m, peer_id, stickers_size=stickers_size), **kwargs)
def copy_post(post, **kwargs): # TODO: use copy_attachments
	if (type(post) != dict): post = API.wall.getById(posts=str(post).replace('wall', ''), **kwargs)[0]
	return (post['text'], ','.join(f"{i['type']}{i[i['type']].get('owner_id') or ''}_{i[i['type']].get('id') or ''}_{i[i['type']].get('access_key') or ''}".strip('_') for i in post.get('attachments') or ()), f"vk.com/wall{post['owner_id']}_{post['id']}")
def copy_attachments(m, peer_id, stickers_size=-1):
	a = list()
	for i in m.get('attachments') or ():
		if (i['type'] == 'sticker'):
			if (stickers_size): a.append(attach(peer_id, i[i['type']]['images'][stickers_size]['url'], type='photo'))
		else: a.append(i['type']+'_'.join(map(str, S(i[i['type']])@['owner_id', 'id', 'access_key'])))
	return ','.join(a)
def format_message(m):
	types = {
		'photo':	('фотография', 'фотографии', 'фотографий'),
		'video':	('видеозапись', 'видеозаписи', 'видеозаписей'),
		'audio':	('аудиозапись', 'аудиозаписи', 'аудиозаписей'),
		'doc':		('документ', 'документа', 'документов'),
		'link':		('ссылка', 'ссылки', 'ссылок'),
		'market':	('товар', 'товара', 'товаров'),
		'market_album':	('подборка товаров', 'подборки товаров', 'подборок товаров'),
		'wall':		('запись на стене', 'записи на стене', 'записей на стене'),
		'wall_reply':	('комментарий на стене', 'комментария на стене', 'комментариев на стене'),
		'sticker':	('стикер', 'стикера', 'стикеров'),
		'gift':		('подарок', 'подарка', 'подарков'),
		'call':		('звонок', 'звонка', 'звонков'),
	}
	attachments = Sdict(int)
	for i in m['attachments']: attachments[i['type']] += 1
	return (m['text']+(' '+S(', ').join((decline(attachments[i], types.get(i, (i,)*3), show_one=False) for i in attachments), last=' и ').capitalize().join('[]') if (attachments) else '')).strip(' ')

def command(*cmd):
	if (type(cmd) == str): cmd = [cmd]
	else: cmd = list(cmd)
	if (type(cmd[-1]) != int): cmd.append(-1)
	if (cmd[-1] == -1): cmd.insert(-1, '')
	cmd = tuple(map(lambda x: x.replace(' ', '\s'), cmd[:-2]))+(*(cmd[-2:]),)
	#log(2, "Registered command:\n"+str(cmd))
	def decorator(f):
		commands[cmd] = f
		return f
	return decorator
def command_unknown(f):
	commands[(-1,)] = f
	return f
f_proc = list()
def proc(n):
	global f_proc, n_proc
	if (isinteger(n)):
		def decorator(f):
			global f_proc
			f_proc.append([f, n, int()])
			return f
		return decorator
	else:
		f_proc.append([n, 0, int()])
		return n
f_handle = dict()
def handler(n):
	global f_handle
	if (type(n) == int):
		def decorator(f):
			global f_handle
			f_handle[n] = f
			return f
		return decorator
	else:
		f_handle[0] = n
		return n
	return f

@handler
def handle(u):
	log(2, u)
	if ((u['type'] if (type(u) == dict) else u[0]) in (4, 5, 'message_new', 'message_edit')): return handle_command(*((u['type'], u['object']) if (type(u) == dict) else (u[0], message(u[1], nolog=True)['items'][0])))
	else: log(1, "Unhandled event"+(f" {u['type']}: {u['object']}" if (type(u) == dict) else f": {u}"))
_users_filter = lambda peer_id, from_id: True
def filter_users(func): global _users_filter; _users_filter = func
def handle_command(t, m):
	if (not _users_filter(*S(m)@['peer_id', 'from_id'])): log(2, f"Rejected from {m['from_id']} (filtered)"); return 'filtered'
	c = proc_cmd(m['text'])
	if (not c): c = ['']
	for i in commands:
		if (c[0] in i[:-2] or m['text'].replace(' ', '\s') in i[:-2]): return exec_command(commands[i], c, m, t)
	else:
		if ((-1,) in commands): return exec_command(commands[(-1,)], c, m, t)
	return... # :(
def exec_command(f, c, m, t, *args, **kwargs):
	fields = ('peer_id', 'from_id', 'text', 'attachments')
	globals = f.__globals__
	globals.update(S(m)(*fields)&S(locals())('c', 'm', 't'))
	try: return f(*args, **kwargs)
	finally:
		for field in fields:
			if (field in globals): del globals[field]

def setlp(**kwargs): parseargs(kwargs, enabled=1, message_new=1, group_id=group.id); return API.groups.setLongPollSettings(**kwargs)
lps = list()
class lp(threading.Thread):
	def __init__(self, lp_index=0, lp_timeout=1, mode=None, eq=None, **kwargs):
		threading.Thread.__init__(self, daemon=True)
		self.lp_index, self.lp_timeout, self.mode, self.eq, self.kwargs = lp_index, lp_timeout, mode or API.mode, eq, kwargs
		self.lp_url = [str(), str()]
		self.stopped = threading.Event()
		self.start()
		lps.append(self)
	@staticmethod
	def format_url(server, key, ts='', wait=25, version=lp_version):
		return f"{server}?act=a_check&version={version}&key={key}&wait={wait}&ts={ts}"
	@classmethod
	def get_lp(cls, mode, wait=25, version=lp_version, **kwargs):
		parseargs(kwargs, nolog=True)
		lp = API.groups.getLongPollServer(group_id=group.id, **kwargs) if (mode == 'group') else API.messages.getLongPollServer(lp_version=lp_version, **kwargs)
		if ('https://' not in lp['server']): lp['server'] = 'https://'+lp['server']
		return (cls.format_url(server=lp['server'], key=lp['key'], wait=wait), str(lp['ts']))
	def run(self):
		log(f"LP #{self.lp_index} Started.")
		while (True):
			try:
				if (not all(self.lp_url)): self.lp_url = list(self.get_lp(mode=self.mode, wait=self.lp_timeout, **self.kwargs))#; log(2, f"New LP Server: {str().join(self.lp_url)}")
				#log(3, f"New LP Request: {self.lp_url}")
				try: a = requests.get(str().join(self.lp_url)).json()
				except Exception as ex: a = dict(); logexception(LPError(ex))
				else: self.lp_url[1] = str(a.get('ts'))
				if (a.get('failed')): self.lp_url = [str(), str()]
				for u in a.get('updates') or (): f_handle[self.lp_index](u)
				for i in range(len(f_proc)):
					if (time.time()-f_proc[i][2] >= f_proc[i][1]): f_proc[i][2] = time.time(); f_proc[i][0]()
				if (self.stopped.is_set()): break
			except BaseException as ex:
				if (self.eq): self.eq.put(ex)
				else: raise
	def stop(self):
		self.stopped.set()

class _Tokens:
	_scope_mask = dict(
		notify =	+1,
		friends =	+2,
		photos =	+4,
		audio =		+8,
		video =		+16,
		stories =	+64,
		pages =		+128,
		status =	+1024,
		notes =		+2048,
		messages =	+4096,
		wall =		+8192,
		ads =		+32768,
		offline =	+65536,
		docs =		+131072,
		groups =	+262144,
		notifications =	+524288,
		stats =		+1048576,
		email =		+4194304,
		market =	+134217728
	)
	def __init__(self, service_key=None):
		self._tokens = dict()
		if (service_key): self._tokens['service_key'] = {'token': api_service_key}
	def __getstate__(self):
		return self._tokens
	def __setstate__(self, tokens):
		self._tokens = tokens
	def __getattr__(self, name):
		if (not self._tokens[name]['token']):
			#self._tokens[name]['token'] = ... # ???
			mode, scope = S(self._tokens[name])@['mode', 'scope']
			#self._tokens[name]['token'] = str() # ???
			self._tokens[name]['token'] = self.readtoken(name, self.format_link(mode, scope))
			if (self._tokens[name]['mode'] == 'user'): self._set_scope(name, *self._parse_mask(API.account.getAppPermissions(access_token=name)))
			self.onupdate()
		return self._tokens[name]['token']
	__getitem__ = __getattr__
	def __contains__(self, name):
		return name in self._tokens
	def _set_scope(self, name, *scope):
		scope, self._tokens[name]['scope'] = self._tokens[name]['scope'].copy(), set(scope)
		return self._tokens[name]['scope'] != scope
	@classmethod
	def _in_scope(cls, scope, permission):
		return permission in cls._scope_mask and scope & cls._scope_mask[permission]
	@classmethod
	def _parse_mask(cls, mask):
		return {i for i in cls._scope_mask if cls._in_scope(mask, i)}
	def require(self, name, *scope, mode=None):
		self._tokens[name] = {'mode': mode or API.mode, 'scope': set(), 'token': str()}
		self._set_scope(name, *scope)
	def increment_scope(self, name, *scope, nolog=True):
		scope = self._tokens[name]['scope'] | set(Slist(map(lambda x: x.split(','), scope)).flatten())
		if (self._set_scope(name, *scope) and not nolog): logexception(Warning(f"Incremented {name} scope: {','.join(scope)}"), nolog=True); self.discard(name)
	def discard(self, name):
		self._tokens[name]['token'] = str()
	@staticmethod
	def format_link(mode, scope):
		return f"""
			https://oauth.vk.com/authorize?
			client_id={app_id}&
			redirect_uri=https://oauth.vk.com/blank.html&
			{f"group_ids={group.id}&" if (mode == 'group') else ''}
			{f"scope={','.join(scope)}&" if (scope) else ''}
			response_type=token&
			v={api_version}
		""".replace('\t', '').replace('\n', '')
	def readtoken(self, name, link):
		locklog()
		logexception(Warning(f"Get new {name}: {link}"), nolog=True)
		logdumb(unlock=loglock[-1][0])
		return input(name+' = ')
	def onupdate(self): pass
access_token, admin_token, service_key = 'access_token', 'admin_token', 'service_key'
group_scope_all = 'manage,messages,photos,docs,wall'

class _API: # scope=messages,groups,photos,status,docs,wall,offline
	def __init__(self, method='', mode='user', blacklist=['blacklisted.test'], whitelist=[]): # user mode is a reasonable default
		self.method, self.mode, self.blacklist, self.whitelist = method, mode, blacklist, whitelist
		if (method in self.blacklist or self.whitelist and method not in self.whitelist): raise \
			PermissionError(f"Method {method} is not allowed")
	def __getattr__(self, method):
		return self.__class__((self.method+'.'+method).strip('.'))
	def __call__(self, *, access_token='access_token', **kwargs):
		if (al_get_method(self.method) is not None): access_token = ''
		else:
			if (access_token not in tokens and access_token != 'service_key'): logexception(Warning(f"No {access_token} in tokens. Using service_key"), once=True, nolog=True); access_token = 'service_key'
			access_token = tokens[access_token]
		try: return api(self.method, mode=self.mode, access_token=access_token, **kwargs)
		except VKAPIError as ex:
			if (ex.args[0]['error_code'] in (27, 28) or (ex.args[0]['error_code'] == 5 and '(4)' in ex.args[0]['error_msg']) and access_token != 'service_key'): tokens.discard(access_token)
			elif (ex.args[0]['error_code'] == 15): tokens.increment_scope(access_token, self.method.split('.')[0], nolog=False)
			else: raise
			if (sys.flags.interactive): return self(access_token=access_token, **kwargs)
			else: raise
	def __repr__(self):
		return self.method or 'API'

class VKError(Exception): pass
class VKAPIError(Warning):
	def __str__(self):
		res = str()
		try: res += f"VK API Error #{self.args[0]['error_code']}: "; res += self.args[0]['error_msg']; res += f' ({self.args[1]})' if (self.args[1]) else ''
		except Exception: pass
		return res.strip(': ') or ' '.join(map(str, self.args)) or 'Unknown Error'
class VKKeyboardError(Exception): pass
class LPError(VKError): pass

class _group:
	def __init__(self):
		self._group = {'id': '', 'name': '', 'screen_name': ''}
	def __getattr__(self, x):
		if (API.mode == 'group' and not self._group['name']):
			try: self._group = groups()[0]
			except Exception as ex: raise VKError(f"Unable to get current group though mode is set to 'group' (ex.args mixin)") from ex
		return self._group[x]

tokens = _Tokens(service_key=service_key)
db.register('tokens', 'vk_sid')
API = _API()
send = _send()
group = _group()
if (sys.flags.interactive): tokens.require('access_token')

if (__name__ == '__main__'):
	logstarted()
	setonsignals(exit)
	handler(plog)
	al_login_stdin()
	exceptions = queue.Queue()
	lp(eq=exceptions)
	while (True):
		try:
			try: ex = exceptions.get()
			except queue.Empty: pass
			except TypeError: raise KeyboardInterrupt()
			else: raise ex
		except Exception as ex: exception(ex)
		except KeyboardInterrupt as ex: exit(ex)
else: logimported()

# by Sdore, 2019
