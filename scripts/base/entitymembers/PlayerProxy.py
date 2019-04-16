# -*- coding: utf-8 -*-

import KBEngine
from KBEDebug import *
import weakref
import const

class PlayerProxy(object):

	def __init__(self, avt_mb, owner, idx):
		# 玩家的mailbox
		self.mb = avt_mb
		# 所属的游戏房间
		self.owner = owner if isinstance(owner, weakref.ProxyType) else weakref.proxy(owner)
		# 玩家的座位号
		self.idx = idx
		# 玩家在线状态
		self.online = 1
		# 玩家的手牌
		self.tiles = []
		# 玩家的桌牌
		self.upTiles = []
		# 玩家的花牌
		self.wreaths = []
		# 玩家打过的牌
		self.discard_tiles = []
		# 玩家的所有操作记录 (cid, [tiles,])
		# 包括摸牌, 打牌, 碰, 明杠, 暗杠, 胡牌 ,吃..
		self.op_r = []

		self.last_draw = -1
		# 玩家当局的得分
		self.score = 0
		# 玩家该房间总得分
		if self.owner.game_mode == 0:			
			self.total_score = 200
		else:
			self.total_score = 0
		# 胡牌次数
		self.win_times = 0
		# 暗杠次数
		self.concealed_kong = 0
		# 明杠次数
		self.exposed_kong = 0
		# 自风
		self.wind = const.WIND_EAST
		# 当前玩家直杠，暗杠，风险杠的list
		self.kong_list = [0, 0, 0] #直杠，暗杠，风险杠

	# 用于UI显示的信息
	@property
	def head_icon(self):
		DEBUG_MSG("PlayerProxy get head_icon = {}".format(self.mb.head_icon))
		return self.mb.head_icon

	@property
	def nickname(self):
		return self.mb.name

	@property
	def sex(self):
		return self.mb.sex

	@property
	def userId(self):
		return self.mb.userId

	@property
	def uuid(self):
		return self.mb.uuid

	@property
	def ip(self):
		return self.mb.ip

	def addScore(self, score, virtual_score = 0):
		DEBUG_MSG("addScore,{0},{1},{2}".format(score, self.score, self.total_score))
		if self.owner.game_mode == 0:
			self.score += virtual_score
			if self.total_score + score < 0 :
				
				real_score = -self.total_score
				self.total_score = 0
				return real_score
			else:
				self.total_score += score
		else:
			self.score += score
			self.total_score += self.score
		return score
		

	def tidy(self, kingTiles):
		self.tiles = sorted(self.tiles)
		#宁波麻将 有俩财神
		kingTileList = []
		othersList = []
		for t in self.tiles:
			if t in kingTiles:
				kingTileList.append(t)
			else:
				othersList.append(t)
		kingTileList.extend(othersList)
		self.tiles = kingTileList
		DEBUG_MSG("Player{0} has tiles: {1}".format(self.idx, self.tiles))

	def reset(self):
		""" 每局开始前重置 """
		self.tiles = []
		self.upTiles = []
		self.discard_tiles = []
		self.op_r = []
		self.last_draw = -1
		self.score = 0
		self.wind = const.WIND_EAST
		self.kong_list = [0, 0, 0] 

	def chow(self, tile_list):
		""" 吃 """
		self.tiles.remove(tile_list[1])
		self.tiles.remove(tile_list[2])

		self.upTiles.append(tile_list)
		self.op_r.append((const.OP_CHOW, tile_list, self.owner.last_player_idx))
		self.owner.allFullPlyer(self.idx, self.owner.last_player_idx)
		# 操作记录
		self.owner.op_record.append((const.OP_CHOW, self.idx, self.owner.last_player_idx, tile_list))
		self.owner.broadcastOperation(self.idx, const.OP_CHOW, tile_list)

	def pong(self, tile):
		""" 碰 """
		self.tiles.remove(tile)
		self.tiles.remove(tile)
		self.upTiles.append([tile,tile,tile])
		self.op_r.append((const.OP_PONG, [tile,], self.owner.last_player_idx))
		self.owner.allFullPlyer(self.idx, self.owner.last_player_idx)
		# 操作记录
		self.owner.op_record.append((const.OP_PONG, self.idx, self.owner.last_player_idx, [tile,]))
		self.owner.broadcastOperation(self.idx, const.OP_PONG, [tile, tile, tile])
		
	def concealedKong(self, tile):
		self.tiles.remove(tile)
		self.tiles.remove(tile)
		self.tiles.remove(tile)
		self.tiles.remove(tile)

		self.upTiles.append([tile, tile, tile, tile])

		self.op_r.append((const.OP_CONCEALED_KONG, [tile,], self.idx))
		self.kong_list[1] += 1
		# 操作记录
		self.owner.op_record.append((const.OP_CONCEALED_KONG, self.idx, self.idx, [tile,]))
		# 算接杠和放杠的分
		# self.owner.cal_score(self.idx, const.OP_CONCEALED_KONG)
		self.owner.broadcastOperation2(self.idx, const.OP_CONCEALED_KONG, [0, 0, 0, tile])

		self.owner.current_idx = self.idx
		# self.owner.cutAfterKong()
		self.owner.beginRound()

	#明杠 包牌
	def exposedKong(self, tile):
		""" 公杠, 自己手里有三张, 杠别人打出的牌. 需要计算接杠和放杠得分 """
		self.tiles.remove(tile)
		self.tiles.remove(tile)
		self.tiles.remove(tile)
		self.upTiles.append([tile, tile, tile, tile])
		self.op_r.append((const.OP_EXPOSED_KONG, [tile,], self.owner.last_player_idx))
		self.kong_list[0] += 1
		# 操作记录
		self.owner.op_record.append((const.OP_GET_KONG, self.idx, self.owner.last_player_idx, [tile,]))
		# 算接杠和放杠的分
		# self.owner.cal_score(self.idx, const.OP_GET_KONG)
		# 不放杠
		# self.owner.cal_score(self.owner.last_player_idx, const.OP_POST_KONG)
		
		self.owner.broadcastOperation(self.idx, const.OP_EXPOSED_KONG, [tile] * 4)
		self.owner.last_player_idx = self.idx
		self.owner.current_idx = self.idx
		# self.owner.cutAfterKong()
		self.owner.beginRound()

	#只有碰后接杠 可以被抢杠，包牌
	def self_exposedKong(self, tile):
		""" 自摸的牌能够明杠 """
		self.tiles.remove(tile)
		for i in range(len(self.upTiles)):
			meld = self.upTiles[i]
			if meld[0] == meld[-1] and meld[0] == tile:
				self.upTiles[i].append(tile)
		self.op_r.append((const.OP_RISK_KONG, [tile,], self.idx))
		self.kong_list[2] += 1
		# 操作记录
		self.owner.op_record.append((const.OP_RISK_KONG, self.idx, self.idx, [tile,]))
		self.owner.last_player_idx = self.idx
		self.owner.broadcastOperation(self.idx, const.OP_RISK_KONG, [tile] * 4)

		# 明杠得分, 只有不被抢杠胡才能得分
		self.owner.waitForOperation(self.idx, const.OP_RISK_KONG, tile, self.idx)
		# self.owner.wait_for_win_list = self.owner.getKongWinList(self.idx, tile)
		# DEBUG_MSG("wait_for_win_list: {0}".format(self.owner.wait_for_win_list))
		# if not self.owner.wait_for_win_list:
		# 	self.owner.current_idx = self.idx
		# 	# self.owner.cutAfterKong()
		# 	self.owner.beginRound()
		# else:
		# 	self.owner.waitForOperation(self.idx, const.OP_RISK_KONG, tile, self.owner.wait_for_win_list)

	#杠花
	def kongWreath(self, tile):
		DEBUG_MSG("Player[%s] kongWreath: %s" % (self.idx, tile))
		self.tiles.remove(tile)
		self.wreaths.append(tile)
		self.op_r.append((const.OP_KONG_WREATH, [tile,], self.idx))
		self.owner.op_record.append((const.OP_KONG_WREATH, self.idx, self.idx, [tile,]))
		self.owner.broadcastOperation2(self.idx, const.OP_KONG_WREATH, [tile,])

		self.owner.waitForOperation(self.idx, const.OP_KONG_WREATH, tile, self.idx)
		# self.owner.waitForOperation(self.idx, const.OP_KONG_WREATH, tile)

	def draw_win(self, tile, score, result,  kongType = 0, finalTile = 0):
		""" 普通自摸胡 + 自摸8张花胡 """
		last_draw = finalTile if finalTile != 0 else self.last_draw
		if finalTile != 0:
			self.tiles.append(finalTile)
		self.win_times += 1
		self.op_r.append((const.OP_DRAW_WIN, [last_draw,], self.idx))
		self.owner.op_record.append((const.OP_DRAW_WIN, self.idx, self.idx, [last_draw,]))
		self.owner.broadcastOperation(self.idx, const.OP_DRAW_WIN, [last_draw,])
		self.owner.winGame(self.idx, const.OP_DRAW_WIN, last_draw, self.idx, score, result, kongType)

	def kong_win(self, tile, score, result, kongType = 0):
		""" 抢杠胡 """
		self.tiles.append(tile)
		self.win_times += 1
		self.op_r.append((const.OP_KONG_WIN, [tile,], self.owner.last_player_idx))
		self.owner.op_record.append((const.OP_KONG_WIN, self.idx, self.owner.last_player_idx, [tile,]))
		self.owner.winGame(self.idx, const.OP_KONG_WIN, tile, self.owner.last_player_idx, score, result, kongType)

	def give_win(self, tile, score, result,  kongType = 0):
		""" 放炮胡 """
		self.tiles.append(tile)
		self.win_times += 1
		self.op_r.append((const.OP_GIVE_WIN, [tile,], self.owner.last_player_idx))
		self.owner.op_record.append((const.OP_GIVE_WIN, self.idx, self.owner.last_player_idx, [tile,]))
		self.owner.broadcastOperation(self.idx, const.OP_GIVE_WIN, [tile,])
		self.owner.winGame(self.idx, const.OP_GIVE_WIN, tile, self.owner.last_player_idx, score, result, kongType)

	def drawTile(self, tile):
		""" 摸牌 """
		DEBUG_MSG("Player{0} drawTile: {1}, left = {2}".format(self.idx, tile, len(self.owner.tiles)))
		self.last_draw = tile
		self.tiles.append(tile)
		self.op_r.append((const.OP_DRAW, [tile,], self.idx))
		self.owner.op_record.append((const.OP_DRAW, self.idx, self.idx, [tile,]))
		self.owner.broadcastOperation2(self.idx, const.OP_DRAW, [0,])
		self.mb.postOperation(self.idx, const.OP_DRAW, [tile,])
		# if tile in const.SEASON or tile in const.FLOWER:
		# 	self.kongWreath(tile)
		# self.owner._op_timer = self.owner.addTimer(const.PLAYER_DISCARD_WAIT_TIME, 0, const.TIMER_TYPE_OPERATION)

	def cutTile(self, tile):
		"""切牌"""
		DEBUG_MSG("Player[%s] cutTile: %s" % (self.idx, tile))
		self.discard_tiles.append(tile)
		self.op_r.append((const.OP_CUT, [tile,], self.idx))
		self.owner.op_record.append((const.OP_CUT, self.idx, self.idx, [tile,]))
		self.owner.broadcastOperation2(self.idx, const.OP_CUT, [tile,])
		self.mb.postOperation(self.idx, const.OP_CUT, [tile,])

	def discardTile(self, tile = None):
		""" 打牌 """
		if tile is None:
			tile = self.last_draw
		DEBUG_MSG("Player[%s] discardTile: %s" % (self.idx, tile))
		self.tiles.remove(tile)
		self.owner.last_player_idx = self.idx
		self.discard_tiles.append(tile)
		self.op_r.append((const.OP_DISCARD, [tile,], self.idx))
		self.owner.op_record.append((const.OP_DISCARD, self.idx, self.idx, [tile,]))
		self.owner.broadcastOperation2(self.idx, const.OP_DISCARD, [tile,])
		self.owner.wait_for_win_list = self.owner.getGiveWinList(self.idx, tile)
		self.owner.waitForOperation(self.idx, const.OP_DISCARD, tile)
		# self.owner.waitForOperation(self.idx, const.OP_DISCARD, tile, self.owner.wait_for_win_list)


	def get_init_client_dict(self):
		return {
			'nickname': self.nickname,
			'head_icon': self.head_icon,
			'sex': self.sex,
			'idx': self.idx,
			'userId': self.userId,
			'uuid': self.uuid,
			'online': self.online,
			'ip': self.ip,
		}

	def get_round_client_dict(self):
		DEBUG_MSG("get_round_client_dict,{0},{1},{2},{3}".format(self.idx, self.tiles, self.score, self.total_score))
		return {
			'idx': self.idx,
			'tiles': self.tiles,
			'wreaths': self.wreaths,
			'concealed_kong': [op[1][0] for op in self.op_r if op[0] == const.OP_CONCEALED_KONG or op[0] == const.OP_RISK_KONG],
			'score': self.score,
			'total_score': self.total_score,
		}

	def get_final_client_dict(self):
		return {
			'idx': self.idx,
			'win_times': self.win_times,
			'exposed_kong': self.exposed_kong,
			'concealed_kong': self.concealed_kong,
			'score': self.total_score if self.owner.game_mode == 1 else self.total_score - 200,
		}

	def get_reconnect_client_dict(self, userId):
		# 掉线重连时需要知道所有玩家打过的牌以及自己的手牌
		disCardTileList, cutTileIdxList = self.reconnect_discard()
		return {
			'score': self.score,
			'total_score': self.total_score,
			'tiles': self.tiles if userId == self.userId else [0]*len(self.tiles),
			'wreaths': self.wreaths,
			'wind': self.wind,
			'discard_tiles': disCardTileList,
			'cut_idxs': cutTileIdxList,
			'op_list': self.process_op_record(),
		}

	def get_round_result_info(self):
		# 记录信息后累计得分
		self.concealed_kong += sum([1 for op in self.op_r if op[0] == const.OP_CONCEALED_KONG])
		self.exposed_kong += sum([1 for op in self.op_r if op[0] == const.OP_EXPOSED_KONG])

		return {
			'nickname': self.nickname,
			'score': self.score,
		}

	def record_round_game_result(self, round_record_dict):
		self.mb.recordRoundResult(round_record_dict)

	def record_all_result(self, game_record_list):
		self.mb.recordGameResult(game_record_list)

	def process_op_record(self):
		""" 处理断线重连时候的牌局记录 """
		ret = []
		length = len(self.op_r)
		for i, op in enumerate(self.op_r):
			if op[0] in [const.OP_PONG, const.OP_EXPOSED_KONG, const.OP_CONCEALED_KONG, const.OP_CHOW]:
				# if op[0] == const.OP_PONG:
				# 	# 碰了之后自己再摸牌杠的, 重连之后只保留杠的记录.
				# 	for j in range(i + 1, length):
				# 		op2 = self.op_r[j]
				# 		if op2[0] == const.OP_EXPOSED_KONG and op2[1][0] == op[1][0]:
				# 			break
				# 	else:
				# 		ret.append({'opId': op[0], 'tiles': op[1], 'fromIdx': op[2]})
				# else:
				# 	ret.append({'opId': op[0], 'tiles': op[1], 'fromIdx': op[2]})
				ret.append({'opId': op[0], 'tiles': op[1], 'fromIdx': op[2]})
		return ret

	def reconnect_discard(self):
		""" 处理断线重连回来丢弃的牌的记录 """
		ret = []
		cutTileIdxList = []
		length = len(self.owner.op_record)
		for i, opr in enumerate(self.owner.op_record):
			aid, src_idx, des_idx, tiles = opr
			if src_idx == self.idx:
				if aid == const.OP_DISCARD:
					j = i + 1
					if j < length:
						next = self.owner.op_record[i+1]
						if next[0] in [const.OP_PONG, const.OP_GET_KONG, const.OP_CHOW] and next[2] == self.idx:
							# 如果自己丢弃的牌被碰了或者放杠了或者被吃了, 重连时处理, 不再显示在牌桌上
							continue
					ret.append(tiles[0])
				elif aid == const.OP_CUT:
					cutTileIdxList.append(len(ret))
					ret.append(tiles[0])
		return (ret, cutTileIdxList)