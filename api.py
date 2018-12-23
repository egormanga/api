#!/usr/bin/python3
# VK API lib v1.2

import json, requests
from .apiconf import app_id, api_service_key
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

api_version = '5.85'
lp_version = '3'

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

def api(method, wrap=True, max_tries=5, nolog=False, **kwargs):
	parseargs(kwargs, v=api_version)
	if (not method): return False
	if (not nolog): log(2, f"Request: method={method}, data={kwargs}")
	r = ret("https://api.vk.com/method/"+method, data=kwargs, wrap=wrap, method=method, max_tries=max_tries)
	if (not nolog): log(3, f"Response: {r}")
	return r

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
def attach(peer_id, file, type='doc', **kwargs):
	if (Image.isImageType(file)): f = io.BytesIO(); file.save(f, type='png'); f.seek(0); file = f
	if (type == 'photo'): return "photo{owner_id}_{id}".format_map(API.photos.saveMessagesPhoto(**requests.post(API.photos.getMessagesUploadServer(peer_id=peer_id, **kwargs)['upload_url'], files={'photo': file}).json())[0])
	return "doc{owner_id}_{id}".format_map(API.docs.save(**requests.post(API.docs.getMessagesUploadServer(peer_id=peer_id, type=type, **kwargs)['upload_url'], files={'photo' if (type == 'photo') else 'file': file}).json())[0])
def setactivity(peer_id, type, **kwargs): parseargs(kwargs, peer_id=peer_id, type=type); return API.messages.setActivity(**kwargs)
def settyping(peer_id, type='typing', **kwargs): logexception(DeprecationWarning("*** settyping() → setactivity(type='typing') ***")); parseargs(kwargs, peer_id=peer_id, type=type); return setactivity(**kwargs)

commands = dict()
def sendhelp(peer_id, commands=commands, n=4, head='', title='Доступные команды:', tail='', keyboard=True, display=2, **kwargs): return send(peer_id, f"{head}\n\n{title}\n%s\n\n{tail}" % '\n'.join('%s — %s' % (i[0]+(' (%s)' % ', '.join(i[1:display])) if (display > 1) else '', i[-2]) for i in commands if i[-1] > -1), keyboard=mkkeyboard(commands, n, one_time=False) if (keyboard and API.mode == 'group') else '', **kwargs) # •
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
	parseargs(kwargs, group_ids=group_ids, fields='')
	return API.groups.getById(**kwargs)

def chat(chat_id, **kwargs): parseargs(kwargs, chat_id=(chat_id % 100000000)); return API.messages.getChat(**kwargs)
def chatonline(chat_id, **kwargs): parseargs(kwargs, chat_id=(chat_id % 100000000)); return execute('return API.messages.getChat({"chat_id": Args.chat_id, "fields": "online"}).users@.online;', **kwargs).count(1)
def chatadd(chat_id, user_ids, **kwargs): parseargs(kwargs, chat_id=(chat_id % 100000000), user_id=user_ids); return Slist([execute('var ret = [], user_ids = Args.user_ids.split(","); while (user_ids) ret.push(API.messages.addChatUser({"chat_id": Args.chat_id, "user_id": user_ids.pop()})); return ret;', user_ids=i, **kwargs) for i in Slist(user_ids).group(25)]).combine() if (hasattr(user_ids, '__iter__') and type(user_ids) != str) else API.messages.addChatUser(**kwargs)
def chatkick(chat_id, member_id, **kwargs): parseargs(kwargs, chat_id=(chat_id % 100000000), member_id=member_id); return API.messages.removeChatUser(**kwargs)
def chatinvitelink(peer_id, **kwargs): parseargs(kwargs, peer_id=peer_id); return API.messages.getInviteLink(**kwargs)
def chattitle(chat_id, title, **kwargs): parseargs(kwargs, chat_id=(chat_id % 100000000), title=title); return API.messages.editChat(**kwargs)
def chatphoto(chat_id, photo, **kwargs): parseargs(kwargs, chat_id=(chat_id % 100000000)); return API.messages.setChatPhoto(file=requests.post(API.photos.getChatUploadServer(**kwargs)['upload_url'], files={'photo': photo}).json()['response'], **kwargs)

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

def setcover(photo, **kwargs): parseargs(kwargs, group_id=group.id, crop_x2=1590, crop_y2=400); return API.photos.saveOwnerCoverPhoto(**requests.post(API.photos.getOwnerCoverPhotoUploadServer(**kwargs)['upload_url'], files={'photo': photo}).json())

def execute(code, **kwargs): parseargs(kwargs, code=code); return API.execute(**kwargs)

def copy_post(post, **kwargs): # TODO: use copy_attachments
	if (type(post) != dict): post = API.wall.getById(posts=str(post).replace('wall', ''), **kwargs)[0]
	return (post['text'], ','.join(f"{i['type']}{i[i['type']].get('owner_id') or ''}_{i[i['type']].get('id') or ''}_{i[i['type']].get('access_key') or ''}".strip('_') for i in post.get('attachments') or ()), f"vk.com/wall{post['owner_id']}_{post['id']}")
def copy_attachments(m, peer_id): # used in NyaBot, so fix there too.
	a = list()
	for i in m.get('attachments') or ():
		if (i['type'] == 'sticker'): a.append(attach(peer_id, openimg(i[i['type']]['images'][-1]['url']), type='photo'))
		a['attachment'].append(i['type']+'_'.join(map(str, S(i[i['type']])@['owner_id', 'id', 'access_key'])))
	return ','.join(a)
def format_message(m):
	types = {
		'photo': ('фотография', 'фотографии', 'фотографий'),
		'video': ('видеозапись', 'видеозаписи', 'видеозаписей'),
		'audio': ('аудиозапись', 'аудиозаписи', 'аудиозаписей'),
		'doc': ('документ', 'документа', 'документов'),
		'link': ('ссылка', 'ссылки', 'ссылок'),
		'market': ('товар', 'товара', 'товаров'),
		'market_album': ('подборка товаров', 'подборки товаров', 'подборок товаров'),
		'wall': ('запись на стене', 'записи на стене', 'записей на стене'),
		'wall_reply': ('комментарий на стене', 'комментария на стене', 'комментариев на стене'),
		'sticker': ('стикер', 'стикера', 'стикеров'),
		'gift': ('подарок', 'подарка', 'подарков'),
		'call': ('звонок', 'звонка', 'звонков'),
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
	if (type(n) == int):
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
def handle_command(t, m):
	c = proc_cmd(m['text'])
	if (not c): c = ['']
	for i in commands:
		if (c[0] in i[:-2] or m['text'].replace(' ', '\s') in i[:-2]): return exec_command(commands[i], c, m, t)
	else:
		if ((-1,) in commands): return exec_command(commands[(-1,)], c, m, t)
def exec_command(f, c, m, t, *args, **kwargs):
	fields = ('peer_id', 'from_id', 'text', 'attachments')
	globals = f.__globals__
	globals.update(S(m)(*fields)&S(locals())('c', 'm', 't'))
	try: return f(*args, **kwargs)
	finally:
		for field in fields:
			if (field in globals): del globals[field]

def setlp(**kwargs):
	parseargs(kwargs, enabled=1, message_new=1, group_id=group.id)
	logstart('Setting up LP')
	try: return API.groups.setLongPollSettings(**kwargs)
	except Exception as ex: return logex(ex)
	finally: logok()
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
		lp = API.groups.getLongPollServer(group_id=group.id, **kwargs) if (mode == 'group') else API.messages.getLongPollServer(lp_version=lp_version, **kwargs)
		return (cls.format_url(server=(lp['server'] if (mode == 'group') else 'https://'+lp['server']), key=lp['key'], wait=wait), str(lp['ts']))
	def run(self):
		log(f"LP #{self.lp_index} Started.")
		while (True):
			try:
				if (not all(self.lp_url)): self.lp_url = list(self.get_lp(mode=self.mode, wait=self.lp_timeout, **self.kwargs))#; log(2, f"New LP Server: {str().join(self.lp_url)}")
				#log(3, f"New LP Request: ts={self.lp_url[1]}")
				try: a = requests.get(str().join(self.lp_url)).json()
				except Exception: a = dict()
				self.lp_url[1] = str(a.get('ts'))
				if (a.get('failed')): self.lp_url = [str(), str()] #log(2, f"\033[91mLP Error:\033[0m {a}"); 
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
			self._tokens[name]['token'] = ...
			mode, scope = S(self._tokens[name])@['mode', 'scope']
			locklog()
			logexception(Warning(f"""Get new {name}: 
				https://oauth.vk.com/authorize?
				client_id={app_id}&
				redirect_uri=https://oauth.vk.com/blank.html&
				{f"group_ids={group.id}&" if (mode == 'group') else ''}
				{f"scope={','.join(scope)}&" if (scope) else ''}
				response_type=token&
				v={api_version}""".replace('\t', '').replace('\n', '')
			), nolog=True)
			logdumb(unlock=loglock[-1][0])
			self._tokens[name]['token'] = str()
			self._tokens[name]['token'] = input(name+' = ')
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
	def onupdate(): pass
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
		if (access_token not in tokens): access_token = 'service_key'; logexception(Warning(f"No {access_token} in tokens. Using service_key"), once=True, nolog=True)
		try: return api(self.method, access_token=tokens[access_token], **kwargs)
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

class _group:
	def __init__(self):
		self._group = {'id': '', 'name': '', 'screen_name': ''}
	def __getattr__(self, x):
		if (API.mode == 'group' and not self._group['name']):
			try: self._group = groups()[0]
			except Exception as ex: raise VKError(f"Unable to get current group though mode is set to 'group' (ex.args mixin)") from ex
		return self._group[x]

tokens = _Tokens(service_key=service_key)
db.register('tokens')
API = _API()
send = _send()
group = _group()
if (sys.flags.interactive): tokens.require('access_token')

if (__name__ == '__main__'): logstarted(); exit('Nope.')
else: logimported()

# by Sdore, 2018
