#!/usr/bin/python3
# VK API lib

import requests
from .apiconf import app_id, dbg_user_id, api_service_key  # custom global config file
from PIL import Image
from utils.nolog import *; logstart('API')

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

api_version = '5.101'
lp_version = '5'
use_al_run_methods = ('messages', 'execute')
use_al_php_methods = ('audio',)
use_force_al_run = False
dont_use_al = False

@singleton
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


def ret(method, data={}, *, wrap=False, max_tries=5, use_al=False, force_al_run=False, vk_sid_=None, nolog=False):
	for i in range(max_tries if (wrap) else 1):
		time.sleep(i)
		try:
			if (use_al): res = (al if (not (use_force_al_run or force_al_run) and method.partition('.')[0] in use_al_php_methods) else al_run_method)(method, vk_sid_=vk_sid_, nolog=nolog, **data)
			else: res = requests.post(f"https://api.vk.com/method/{method}", data=data).json()
			if ('error' in res): raise \
				VKAPIError(res['error'], method)
			return res.get('response', res) if (isinstance(res, dict)) else res
		except (OSError, VKAPIError) as ex:
			if (not wrap or (isinstance(ex, VKAPIError) and ex.args[0]['error_code'] not in (6, 10, 14))): raise

def api(method, *, access_token='access_token', wrap=True, max_tries=5, allow_al=True, force_al_run=False, vk_sid_=None, nolog=False, **kwargs):
	parseargs(kwargs, lang=locale.getlocale()[0].split('_')[0], v=api_version)
	if (not method): return False
	if (access_token in tokens):
		is_user = (tokens.mode[access_token] != 'group')
		use_al = (use_force_al_run or force_al_run) or (method.partition('.')[0] in use_al_php_methods+use_al_run_methods)
		parseargs(kwargs, access_token=tokens[access_token])
	else:
		is_user = (API.mode == 'user')
		use_al = True # TODO
		parseargs(kwargs, access_token=access_token)
	if (dont_use_al or not allow_al): use_al = False
	if (not nolog): log(2, f"Request: method={method}, data={kwargs}")
	try: r = ret(method=method, data=kwargs, wrap=wrap, max_tries=max_tries, use_al=is_user and use_al, force_al_run=use_force_al_run or force_al_run, vk_sid_=vk_sid_, nolog=nolog)
	except VKAPIError as ex:
		if (isinstance(ex, VKAPIError) and ex.args[0]['error_code'] in (7, 15, 20, 21, 23, 28)):
			r = ret(method=method, data=kwargs, wrap=wrap, max_tries=max_tries, use_al=is_user, force_al_run=use_force_al_run or force_al_run, vk_sid_=vk_sid_, nolog=nolog)
		else: raise
	if (not nolog): log(3, f"Response: {r}")
	return r

vk_sid = str()
def setvksid(vk_sid_): global vk_sid; vk_sid = vk_sid_
def getvksid(): return vk_sid

#def al_retcode(r): return int(re.findall(r'<!>(\d+)<!>', r)[1]) # TODO
def al_unhtml_text(text): return html.unescape(re.sub(r'<.*?alt="(.*?)">', r'\1', text)).replace('\xa0', ' ').replace('<br>', '\n')
def al_parse_audio(a):
	return {
		'id': a[al_audio_consts.AUDIO_ITEM_INDEX_ID],
		'owner_id': a[al_audio_consts.AUDIO_ITEM_INDEX_OWNER_ID],
		'artist': al_unhtml_text(a[al_audio_consts.AUDIO_ITEM_INDEX_PERFORMER]),
		'title': al_unhtml_text(a[al_audio_consts.AUDIO_ITEM_INDEX_TITLE]),
		'duration': a[al_audio_consts.AUDIO_ITEM_INDEX_DURATION],
		#'date'
		'url': a[al_audio_consts.AUDIO_ITEM_INDEX_URL], # TODO vaud
		'covers': a[al_audio_consts.AUDIO_ITEM_INDEX_COVER_URL].split(','), # thx to @g_freddy; TODO: 'cover' and 'cover_N's
		'lyrics_id': a[al_audio_consts.AUDIO_ITEM_INDEX_LYRICS],
		'album_id': a[al_audio_consts.AUDIO_ITEM_INDEX_ALBUM],
		#'genre_id'
		'is_hq': bool(a[al_audio_consts.AUDIO_ITEM_INDEX_FLAGS] & al_audio_consts.AUDIO_ITEM_HQ_BIT),
		'track_code': a[al_audio_consts.AUDIO_ITEM_INDEX_TRACK_CODE],
		'is_explicit': bool(a[al_audio_consts.AUDIO_ITEM_INDEX_FLAGS] & al_audio_consts.AUDIO_ITEM_EXPLICIT_BIT),
		'is_restricted': bool(a[al_audio_consts.AUDIO_ITEM_INDEX_RESTRICTION]),
		'main_artists': a[al_audio_consts.AUDIO_ITEM_INDEX_MAIN_ARTISTS],
		'featured_artists': a[al_audio_consts.AUDIO_ITEM_INDEX_FEAT_ARTISTS],
		'subtitle': a[al_audio_consts.AUDIO_ITEM_INDEX_SUBTITLE],
		#'no_search'
		'hashes': dict(zip(('addHash', 'editHash', 'actionHash', 'deleteHash', 'replaceHash', 'urlHash', 'restoreHash'), a[al_audio_consts.AUDIO_ITEM_INDEX_HASHES].split('/'))),
	}
def al_parse_audio_id(a): return f"{a['owner_id']}_{a['id']}_{a['hashes']['actionHash']}_{a['hashes']['urlHash']}"
def al_audio_get_hash(a): return hash(f"{a.get('owner_id')}_{a.get('id')}_{a.get('hashes')}")
def al_audio_eq(a, b): return al_audio_get_hash(a) == al_audio_get_hash(b)

@cachedfunction
def al_audio_get_url(user_id, a, *, mp3=True, **kwargs):
	if (not a.get('hashes', {}).get('urlHash')): raise VKAlUrlError('no url')
	if (not a.get('url')): a['url'] = API.audio.getById(audios=al_parse_audio_id(a), **kwargs)[0]['url']
	a['url'] = al_audio_decode_url(user_id, a['url'])
	if (mp3 and 'index.' in a['url']): a['url'] = str().join((*re.match(r'^(https?:/(?:/[^/]+)+?/) [^/]+/ ((?:audios/)?[^/]+)/index\.', a['url'], re.X).groups(), '.mp3'))
	return a['url']
def al_audio_decode_url(user_id, url):
	if ('audio_api_unavailable' not in url): return url

	def splice(e, b, d):
		e.insert(b+1, d)
		return e.pop(b), e

	def decode_str(s):
		o = 0
		t = int()
		r = str()
		for i in s:
			n = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN0PQRSTUVWXYZO123456789+/='.find(i)
			if (n == -1): continue
			t = 64*t + n if (o % 4) else n
			o += 1
			if (not o-1 % 4): continue
			c = 255 & t >> (-o*2 & 6)
			if (c): r += chr(c)
		return r

	t, n = map(decode_str, url.partition('?extra=')[2].split('#'))
	a, (e, t) = splice(n.partition(chr(9))[0].split(chr(11)), 0, t)
	if (a == 'i'):
		t = abs(int(t)^user_id)

		r = dict()
		for i in range(len(e), 0, -1):
			r[i] = t = (len(e)*(i)^t+i-1) % len(e)
		s = sorted(r.keys())

		e = list(e)
		for i in range(1, len(e)):
			e, (e[i], *_) = splice(e, r[s[len(e)-1-i]], e[i])[::-1]
		return str().join(e)
	else: raise NotImplementedError(a)
	# based on unmaintained https://github.com/yuru-yuri/vk-audio-url-decoder

def al_parse_audio_albums(kwargs, r): # TODO: coverUrl & other info
	try: r = first(i for i in r if isinstance(i, dict)) if ('playlists' in r) else raise_(StopIteration)
	except StopIteration: r = {'playlists': [{'owner_id': int(i[0]), 'id': int(i[1]), 'title': i[3] if (len(i) > 3) else i[2], 'access_hash': i[2] if (len(i) > 3) else ''} for i in re.findall(r"showAudioPlaylist\((-?\d+),\ ?(\d+),\ ?'([\w\d]*)'.*?>(.+?)</a>", al_unhtml_text(first(i for i in r if 'showAudioPlaylist' in i)))]}
	return {
		'count': len(r['playlists']),
		'items': r['playlists'],
		'next': r.get('next'),
	}
def al_parse_audio_list(kwargs, r):
	r['list'] = list(map(al_parse_audio, r['list']))
	#for i in range(0, len(r['list']), 9): r['list'][i:i+10] = map(al_parse_audio, API.audio.getById(audios=','.join(map(al_parse_audio_id, r['list'][i:i+10])))) # too slow
	return S(r).translate({'owner_id': 'ownerId', 'access_hash': 'accessHash', 'has_more': ('hasMore', bool), 'next_from': 'nextOffset'})
def al_parse_audio_search(kwargs, r):
	r['playlist'] = al_parse_audio_list(kwargs, r['playlist']) if (r['playlist']) else {}
	if (r['playlists']): r['playlists'] = list(map(lambda x: al_parse_audio_list(kwargs, x), r['playlists']))
	else: r['playlists'] = {}
	return S(r).with_('has_more', True) # TODO

al_actions = {
	'audio.get': ('al_audio', 'load_section'),
	'audio.search': ('al_audio', 'section'),
	'audio.getById': ('al_audio', 'reload_audio'),
	'audio.getAlbums': ('al_audio', 'section'),
	'audio.getLyrics': ('al_audio', 'get_lyrics'),
	'audio.getFriends': ('al_audio', 'more_friends'),
	'audio.getRecommendations': ('al_audio', 'recoms_blocks'),
}
al_params = {
	'audio.get': lambda kwargs: {'owner_id': kwargs['owner_id'] if (kwargs.get('owner_id')) else user(force_al_run=True)[0]['id'], 'type': kwargs.get('type', kwargs['album_id'][:6] if (isinstance(kwargs.get('album_id', -1), str) and kwargs['album_id'][:6].isalpha()) else 'playlist'), 'playlist_id': kwargs.get('album_id', -1), 'offset': kwargs.get('offset', 0), 'count': kwargs.get('count', ''), 'access_hash': kwargs.get('access_hash', '')},
	'audio.search': lambda kwargs: {'owner_id': kwargs.get('owner_id', ''), 'section': 'search', 'q': kwargs.get('q', ''), 'offset': kwargs.get('offset', 0), 'count': kwargs.get('count', ''), **kwargs},
	'audio.getById': lambda kwargs: S(kwargs).translate({'ids': 'audios'}), # audios: «{owner_id}_{track_id}_{actionHash}_{urlHash}»
	'audio.getAlbums': lambda kwargs: {'owner_id': kwargs.get('owner_id', ''), 'section': kwargs.get('section', 'playlists'), 'offset': kwargs.get('offset', 0), 'count': kwargs.get('count', '')},
	'audio.getLyrics': lambda kwargs: {'lid': kwargs.get('lyrics_id', '')},
	'audio.getFriends': lambda kwargs: kwargs,
	'audio.getRecommendations': lambda kwargs: kwargs,
}
al_return = {
	'audio.get': lambda kwargs, r: al_parse_audio_list(kwargs, r[0]), # TODO api object
	'audio.search': lambda kwargs, r: al_parse_audio_search(kwargs, r[1]), # TODO api object
	'audio.getById': lambda kwargs, r: list(map(al_parse_audio, r[0])),
	'audio.getAlbums': al_parse_audio_albums,
	'audio.getLyrics': lambda kwargs, r: {'lyrics_id': kwargs.get('lyrics_id'), 'text': al_unhtml_text(r[0]).strip('"')},
	'audio.getFriends': lambda kwargs, r: r[1],
	'audio.getRecommendations': lambda kwargs, r: {'playlists': list(map(lambda x: al_parse_audio_list(kwargs, x), r[1]['playlists'])), 'next': r[1]['next']},
}

def al(method, vk_sid_=None, nolog=False, **kwargs):
	if (vk_sid_ is None): vk_sid_ = vk_sid
	if (not vk_sid_): raise VKAlLoginError()
	al, act = al_actions[method]
	data = al_params.get(method, lambda kwargs: kwargs)(kwargs)
	if (not al or not act): return False
	if (not nolog): log(2, f"Al Request: al={al}, act={act}, data={data}")
	try: r = requests.post(f"https://vk.com/{al}.php?act={act}&al=1", data=data, headers={'X-Requested-With': 'XMLHttpRequest'}, cookies={'remixsid': vk_sid_}); assert r.ok
	except Exception as ex: raise VKAPIError({'error_code': 0}, method) from ex
	r = json.loads(r.text)['payload']
	#if (r[0] == 3): raise VKAlLoginError() # TODO FIXME?
	r = al_return.get(method, lambda kwargs, r: r)(data, r[1])
	if (not nolog): log(3, f"Al Response: {r}")
	return r
def al_run_method(method, vk_sid_=None, nolog=False, **kwargs):
	if (vk_sid_ is None): vk_sid_ = vk_sid
	if (not vk_sid_): raise VKAlLoginError()
	data = {'param_'+k: v for k, v in kwargs.items() if k != 'method'}
	parseargs(data, method=method, hash=al_get_run_hash(method, vk_sid_=vk_sid_))
	if (not nolog): log(2, f"Al Dev Request: method={method}, data={data}")
	try: r = requests.post(f"https://vk.com/dev.php?act=a_run_method&al=1", data=data, headers={'X-Requested-With': 'XMLHttpRequest'}, cookies={'remixsid': vk_sid_}); assert r.ok
	except Exception as ex: raise VKAPIError({'error_code': 0}, method) from ex
	r = json.loads(al_unhtml_text(r.text))['payload']
	#if (r[0] == 3): raise VKAlLoginError() # TODO FIXME?
	r = json.loads(r[1][0])
	if (not nolog): log(3, f"Al Dev Response: {r}")
	return r
def al_login(login, password):
	global vk_sid
	s = requests.session()
	s.post(bs4.BeautifulSoup(s.get('https://m.vk.com/login').text, 'html.parser').form['action'], data={'email': login, 'pass': password})
	if ('remixsid' not in s.cookies): raise VKAlLoginError('Incorrect login')
	vk_sid = s.cookies['remixsid']
	return vk_sid
def al_login_stdin(): return al_login(input('VK Login: '), getpass.getpass())
def al_get_lp(vk_sid_=None):
	if (vk_sid_ is None): vk_sid_ = vk_sid
	r = re.search(r'lpConfig:\ ?({.*?})', requests.get('https://vk.com/im', headers={'User-Agent': 'Linux'}, cookies={'remixsid': vk_sid_}, allow_redirects=False).text, re.S)
	if (r is None): raise VKAlLoginError()
	def extract(x): return re.search(rf'''['"]?{x}['"]?:\ ?['"]?([\w.:/]+)['"]?''', r[1])[1]
	return {'server': extract('url'), 'key': extract('key'), 'ts': extract('ts')}
@cachedfunction
def al_get_run_hash(method, vk_sid_=None):
	if (vk_sid_ is None): vk_sid_ = vk_sid
	r = re.search(r"Dev\.\w+?\('(\d+:[\w\d]+)'.*?\)", requests.get(f"https://vk.com/dev/{method}", cookies={'remixsid': vk_sid_}, allow_redirects=False).text)
	if (r is None): raise VKAlLoginError()
	return r.group(1)

class _send:
	def __init__(self):
		self.prefix = None

	def __call__(self, peer_id, message, prefix=None, nolog=True, **kwargs):
		if (isinstance(peer_id, (int, str))): peer_id = (peer_id,)
		else: peer_id = tuple(peer_id)
		if (not peer_id): return
		if (len(peer_id) > 1):
			peer_id = S(',').join(peer_id)
			parseargs(kwargs, user_ids=peer_id)
		else:
			peer_id = peer_id[0]
			parseargs(kwargs, peer_id=peer_id)
		parseargs(kwargs, message=message, random_id=random.randrange(-2**63, 2**63))
		if (prefix is None): prefix = '👾' if (self.prefix is None and API.mode != 'group') else self.prefix or ''
		if ('keyboard' in kwargs and not kwargs['keyboard']): kwargs.pop('keyboard')
		if (not nolog): log(1, f"Sending message to {peer_id}:\n"+(kwargs['message']+str().join((f' <{i}>' for i in kwargs.get('attachment').split(',') or ()))).indent())
		kwargs.update({'message': prefix+' '+str(message), 'nolog': bool(nolog) and nolog != True})
		return (API.messages.send if (not kwargs.get('message_id')) else API.messages.edit)(**kwargs)

def openimg(img): # TODO: from cimg
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
	doc = API.docs.save(**requests.post(API.docs.getMessagesUploadServer(peer_id=peer_id, type=type, **kwargs)['upload_url'], files={'file': file}).json())
	return 'doc{owner_id}_{id}'.format_map(doc[doc['type']])
def setactivity(peer_id, type, **kwargs): parseargs(kwargs, peer_id=peer_id, type=type); return API.messages.setActivity(**kwargs)
def settyping(peer_id, type='typing', **kwargs): logexception(DeprecationWarning("*** settyping() → setactivity(type='typing') ***")); parseargs(kwargs, peer_id=peer_id, type=type); return setactivity(**kwargs)

commands = dict()
def sendhelp(peer_id, commands=commands, n=4, head='', title='Доступные команды:', tail='', keyboard=True, one_time=True, display=2, **kwargs): return send(peer_id, f"{head}\n\n{title}\n%s\n\n{tail}" % '\n'.join('%s — %s' % (i[0]+(' (%s)' % ', '.join(i[1:display])) if (display > 1) else '', i[-2]) for i in commands if i[-1] > -1), keyboard=mkkeyboard(commands if (keyboard) else {}, n, one_time=one_time) if (API.mode == 'group') else '', **kwargs) # •
def mkkeyboard(commands, n=4, one_time=True, inline=False):
	keyboard = {
		'one_time': one_time,
		'inline': inline,
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

def read(peer_id, start_message_id=int(), **kwargs):
	parseargs(kwargs, peer_id=peer_id, start_message_id=start_message_id or messages(peer_id, nolog=True)['items'][0]['id'])
	return API.messages.markAsRead(**kwargs)
def delete(peer_id, message_ids, **kwargs):
	parseargs(kwargs, message_ids=message_ids)
	return API.messages.delete(**kwargs)

def parsecommas(x):
	if (not x): return None
	if (isinstance(x, str)): return Stuple(map(str.strip, x.split(','))).strip() or None
	if (not isiterable(x)): return str(x).strip() or None
	return Stuple(map(parsecommas, x or ())).flatten().strip() or None

def user(*items, groups=False, neg_group_ids=False, **kwargs):
	items_ = list(parsecommas(items) or ())
	if ('items' in kwargs): items_ += parsecommas(kwargs.pop('items')) or ()
	elif (items and not items_): return ()
	items = items_
	res = list()
	if (not groups and items and '-' not in S('').join(items)): res += API.users.get(user_ids=S(',').join(items), **kwargs)
	elif (items):
		items_u = Slist(items)
		items_g = Slist(items)
		for i in items:
			if (isinstance(i, int) or i.lstrip('-').isdecimal()): (items_u, items_g)[int(i) > 0].remove(i)
		if (items_u):
			try: res += API.users.get(user_ids=','.join(map(str, items_u)), **kwargs) or []
			except VKAPIError: pass
		if (items_g):
			try: res += [S(i).with_('id', i['id']*pm(not neg_group_ids)) for i in API.groups.getById(group_ids=','.join(str(i).lstrip('-') for i in items_g), **kwargs)]
			except VKAPIError: pass
	else: res += API.users.get(**kwargs)
	for i in res:
		if ('first_name' not in i): i['first_name'] = i['name']
		if ('last_name' not in i): i['last_name'] = ''
		if ('name' not in i): i['name'] = ' '.join(S(i)@['first_name', 'last_name']).strip(' ')
		if ('domain' not in i): i['domain'] = i.get('screen_name', f"id{i['id']}")
		i['name_case'] = kwargs.get('name_case', 'nom')
	return Slist(map(Sdict, res))
@cachedfunction
def refuser(u, nopush=False, domain=False, fullname=False, **kwargs):
	if (not isinstance(u, dict) or not u.get('name') or kwargs.get('name_case') and u.get('name_case', kwargs.get('name_case')) != kwargs.get('name_case')): u = user(u['id'] if (isinstance(u, dict)) else u, groups=True, wrap=False, nolog=False, **kwargs)[0]
	name = u.get('name') if (fullname) else u.get('first_name') or u['name']
	return f"[{u['domain']}|{name}]" if (not domain and not nopush) else f"@{u['domain']} ({u['name']})" if (fullname and not nopush) else f"@{u['domain']}" if (not nopush) else name
@cachedfunction
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
	if (m.get('reply_message')): m['text'] += "\n\n[Ответ]\n"+S(refuser(m['reply_message']['from_id'], nopush=True, fullname=True)+': '+format_message(m['reply_message'])).indent(1, char='⠀| ')
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
		'photo':		('фотография', 'фотографии', 'фотографий'),
		'video':		('видеозапись', 'видеозаписи', 'видеозаписей'),
		'audio':		('аудиозапись', 'аудиозаписи', 'аудиозаписей'),
		'doc':			('документ', 'документа', 'документов'),
		'link':		('ссылка', 'ссылки', 'ссылок'),
		'market':		('товар', 'товара', 'товаров'),
		'market_album':	('подборка товаров', 'подборки товаров', 'подборок товаров'),
		'wall':		('запись на стене', 'записи на стене', 'записей на стене'),
		'wall_reply':		('комментарий на стене', 'комментария на стене', 'комментариев на стене'),
		'sticker':		('стикер', 'стикера', 'стикеров'),
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
def command_unknown(f): # TODO FIXME: «-1» → «...»
	commands[(-1,)] = f
	return f
f_proc = list()
def proc(n): # TODO: rewrite with dispatch()
	global f_proc, n_proc
	if (isnumber(n)):
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
	globals.update(S(m)(*fields) & S(locals())('c', 'm', 't'))
	try: return f(*args, **kwargs)
	finally:
		for field in fields:
			if (field in globals): del globals[field]

def setlp(**kwargs): parseargs(kwargs, enabled=1, message_new=1, group_id=group.id); return API.groups.setLongPollSettings(**kwargs)
lps = list()
class lp(threading.Thread):
	def __init__(self, lp_index=0, lp_timeout=1, mode=None, eq=None, **kwargs):
		super().__init__(daemon=True)
		self.lp_index, self.lp_timeout, self.mode, self.eq, self.kwargs = lp_index, lp_timeout, mode or API.mode, eq, kwargs
		self.lp_url = [str(), str()]
		self.stopped = threading.Event()
		self.start()
		lps.append(self)

	@staticmethod
	def format_url(server, key, ts='', mode=8, wait=25, version=lp_version):  # mode=8 -- voip data (event 115)
		return f"{server}?act=a_check&version={version}&key={key}&mode={mode}&wait={wait}&ts={ts}"

	@classmethod
	def get_lp(cls, mode, wait=25, version=lp_version, **kwargs):
		parseargs(kwargs, nolog=True)
		lp = API.groups.getLongPollServer(group_id=group.id, **kwargs) if (mode == 'group') else API.messages.getLongPollServer(lp_version=lp_version, **kwargs)
		if (not isinstance(lp, dict)): raise VKAlLoginError(lp)
		if ('https://' not in lp['server']): lp['server'] = 'https://'+lp['server']
		return (cls.format_url(server=lp['server'], key=lp['key'], wait=wait), str(lp['ts']))

	def run(self):
		log(f"LP #{self.lp_index} Started.")
		while (not self.stopped.is_set()):
			try:
				if (not all(self.lp_url)):
					self.lp_url = list(self.get_lp(mode=self.mode, wait=self.lp_timeout, **self.kwargs))
					#log(2, f"New LP Server: {str().join(self.lp_url)}")
				#log(3, f"New LP Request: {self.lp_url}")
				try: a = requests.get(str().join(self.lp_url)).json()
				except Exception as ex: a = dict(); logexception(LPError(ex))
				else: self.lp_url[1] = str(a.get('ts'))
				if (a.get('failed', 0) > 1):
					self.lp_url[0] = ''
					log(3, f"LP Error: {a}")
				for u in a.get('updates', ()):
					f_handle[self.lp_index](u)
				for i in range(len(f_proc)):
					if (time.time()-f_proc[i][2] >= f_proc[i][1]): f_proc[i][2] = time.time(); f_proc[i][0]()
			except BaseException as ex:
				if (self.eq): self.eq.put(ex)
				else: raise
				if (isinstance(ex, VKAlLoginError)):
					while (not getvksid()): time.sleep(0.1)

	def stop(self):
		self.stopped.set()

class _Tokens(metaclass=SlotsMeta):
	_scope_mask = dict(
		notify		= +1,
		friends		= +2,
		photos		= +4,
		audio		= +8,
		video		= +16,
		stories		= +64,
		pages		= +128,
		status		= +1024,
		notes		= +2048,
		messages	= +4096,
		wall		= +8192,
		ads		= +32768,
		offline		= +65536,
		docs		= +131072,
		groups		= +262144,
		notifications	= +524288,
		stats		= +1048576,
		email		= +4194304,
		market		= +134217728,
	)
	_tokens: dict
	onupdate: noop

	def __init__(self, service_key=None):
		if (service_key): self._tokens['service_key'] = {'token': api_service_key, 'mode': None, 'scope': ()}

	def __getstate__(self):
		return self._tokens

	def __setstate__(self, tokens):
		self._tokens = tokens

	def __getattr__(self, name):
		if (name in self.__slots__): return object.__getattribute__(self, name)
		if (not self._tokens[name]['token']):
			mode, scope = S(self._tokens[name])@['mode', 'scope']
			self._tokens[name]['token'] = self.readtoken(name, self.format_link(mode, scope))
			if (self._tokens[name]['mode'] == 'user'): self._set_scope(name, *self._parse_mask(API.account.getAppPermissions(access_token=name)))
			if (self.onupdate is not None): self.onupdate()
		return self._tokens[name]['token']

	def __setattr__(self, name, token):
		try: return object.__setattr__(self, name, token)
		except AttributeError: pass
		try: self._tokens[name]['token'] = token
		except KeyError as ex: raise AttributeError(*ex.args)

	__getitem__ = __getattr__
	__setitem__ = __setattr__

	def __contains__(self, name):
		return name in self._tokens

	def __repr__(self):
		return '<VK API Tokens>'

	def _set_scope(self, name, *scope):
		scope, self._tokens[name]['scope'] = self._tokens[name]['scope'].copy(), set(scope)
		return self._tokens[name]['scope'] != scope

	@classmethod
	def _in_scope(cls, scope, permission):
		return permission not in cls._scope_mask or scope & cls._scope_mask[permission]

	@classmethod
	def _parse_mask(cls, mask):
		return {i for i in cls._scope_mask if cls._in_scope(mask, i)}

	def require(self, name, *scope, mode=None):
		self._tokens[name] = {'mode': mode or API.mode, 'scope': set(), 'token': str()}
		if (len(scope) == 1): scope = scope[0]
		if (isinstance(scope, str)): scope = scope.split(',')
		self._set_scope(name, *scope)

	def increment_scope(self, name, *scope, nolog=True):
		scope = self._tokens[name]['scope'] | set(Slist(map(lambda x: x.split(','), scope)).flatten())
		if (self._set_scope(name, *scope) and not nolog): logexception(Warning(f"Incremented {name} scope: {','.join(scope)}"), nolog=True); self.discard(name)

	def discard(self, name):
		self._tokens[name]['token'] = str()

	@itemget
	def mode(self, name):
		return self._tokens[name]['mode']

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
		logexception(Warning(f"Get new {name}: {link}"), nolog=True)
		locklog()
		try: return input(name+' = ')
		finally: unlocklog()

access_token, admin_token, service_key = 'access_token', 'admin_token', 'service_key'
group_scope_all = 'manage,messages,photos,docs,wall'

class _API: # scope=messages,groups,photos,status,docs,wall,offline
	class User:
		def __init__(self, user, fields='', **kwargs):
			self.fields, self.kwargs = set(parsecommas(fields) or ()), kwargs
			if (isinstance(user, dict)): self.user_id, self.user = user['id'], user
			else: self.user_id, self.user = user, dict()

		def __getattr__(self, x):
			if (x not in self.fields): self.fields.add(x); self.update()
			return self.user[x]

		def __dir__(self):
			return set(super().__dir__()) | self.fields

		def __repr__(self):
			if (not self.user): self.update()
			return f"<VK User {refuser(self.user, domain=True, fullname=True)}>"

		def update(self):
			self.user = user(self.user_id, fields=self.fields, **self.kwargs)[0]
			self.fields = set(self.user.keys())

	def __init__(self, method='', mode='user', blacklist=['blacklisted.test'], whitelist=[]): # user mode is a reasonable default
		self.method, self.mode, self.blacklist, self.whitelist = method, mode, blacklist, whitelist
		if (method in self.blacklist or self.whitelist and method not in self.whitelist): raise \
			PermissionError(f"Method {method} is not allowed")

	def __getattr__(self, method):
		return self.__class__(method=(self.method+'.'+method).strip('.'), mode=self.mode, blacklist=self.blacklist, whitelist=self.whitelist)

	def __call__(self, *, access_token='access_token', **kwargs):
		if (access_token not in tokens and access_token != 'service_key'):
			#logexception(Warning(f"No {access_token} in tokens. Using service_key"), once=True, nolog=True) # TODO FIXME scripts
			access_token = 'service_key'
		try: return api(self.method, access_token=access_token, **kwargs)
		except VKAPIError as ex:
			if (not kwargs.get('wrap', True)): raise
			if (ex.args[0]['error_code'] in (27, 28) or (ex.args[0]['error_code'] == 5 and '(4)' in ex.args[0]['error_msg']) and access_token != 'service_key'): tokens.discard(access_token)
			elif (ex.args[0]['error_code'] == 15): tokens.increment_scope(access_token, self.method.split('.')[0], nolog=False)
			else: raise
			if (sys.flags.interactive): return self(access_token=access_token, **kwargs)
			else: raise

	def __repr__(self):
		return self.method or 'API'

def api_iter(method, to_=noop, **kwargs):
	parseargs(kwargs, access_token=access_token)
	offset = kwargs.pop('offset') if ('offset' in kwargs) else int()
	while (True):
		r = api(method, **kwargs, offset=offset)
		if (not r['items']): break
		offset += len(r['items'])
		for i in r['items']:
			if (to_(i)): break
			yield i
		else: continue
		break
	else: return 0
	return r['count']

class VKError(Exception): pass
class VKAPIError(Warning):
	def __str__(self):
		res = str()
		try: res += f"VK API Error #{self.args[0]['error_code']}: "; res += self.args[0]['error_msg']; res += f' ({self.args[1]})' if (self.args[1]) else ''
		except Exception: pass
		return res.strip(': ') or ' '.join(map(str, self.args)) or 'Unknown Error'
class VKKeyboardError(Exception): pass
class LPError(VKError, NonLoggingException): pass
class VKAlError(VKError): pass
class VKAlLoginError(VKAlError): pass
class VKAlUrlError(VKAlError): pass

class _group:
	def __init__(self):
		self._group = {'id': '', 'name': '', 'screen_name': ''}

	def __getattr__(self, x):
		if (API.mode == 'group' and not self._group['name']):
			try: self._group = groups()[0]
			except Exception as ex: raise VKError(f"Unable to get current group though mode is set to 'group' (ex.args mixin)") from ex
		return self._group[x]

_lastex = [tuple(), int(), -1] # [ex.args, message_id, repeated]
def _api_exc_handler(e, ex):
	global _lastex
	if (dbg_user_id is None): return
	sendexstr = f"{sys.argv[0]}: {e}\n"+str().join(traceback.format_tb(ex.__traceback__)).replace('  ', '⠀') # '⠀' &#10240; U+2800 Braille pattern blank
	if (ex.args != _lastex[0]): _lastex = [ex.args, int(), -1]
	_lastex[2] += 1
	if (_lastex[2]): sendexstr += f"(повторено ещё {decline(_lastex[2], ('раз', 'раза', 'раз'))})"
	try: msg_id = send(dbg_user_id, sendexstr, message_id=_lastex[1], nolog='force')
	except VKAPIError: msg_id = int()
	if (not _lastex[1]): _lastex[1] = msg_id
register_exc_handler(_api_exc_handler)
def set_dbg_user_id(x): global dbg_user_id; dbg_user_id = x

tokens = _Tokens(service_key=service_key)
db.register('tokens', 'vk_sid')
db.setsensitive(True)
API = _API()
send = _send()
group = _group()
if (sys.flags.interactive): tokens.require('access_token')

# TODO: argparse-like commands parsing
# TODO: check scope before using al

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

# by Sdore, 2020
