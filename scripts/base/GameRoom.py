# -*- coding: utf-8 -*-

import KBEngine
from KBEDebug import *
import time
from datetime import datetime
from interfaces.GameObject import GameObject
from entitymembers.iRoomRules import iRoomRules
from entitymembers.PlayerProxy import PlayerProxy
import json
import const
import random
import switch
import utility
import math
import copy

class GameRoom(KBEngine.Base, GameObject, iRoomRules):
	"""
	这是一个游戏房间/桌子类
	该类处理维护一个房间中的实际游戏， 例如：斗地主、麻将等
	该房间中记录了房间里所有玩家的mailbox，通过mailbox我们可以将信息推送到他们的客户端。
	"""
	def __init__(self):
		GameObject.__init__(self)
		iRoomRules.__init__(self)

		self.owner_uid = 0
		self.agent = None
		self.roomID = None

		# 状态0：未开始游戏， 1：某一局游戏中
		self.state = 0

		# 存放该房间内的玩家mailbox
		self.players_dict = {}
		self.players_list = [None] * self.player_num
		self.origin_players_list = [None] * const.ROOM_PLAYER_NUMBER

		# 庄家index
		self.dealer_idx = 0
		# 当前控牌的玩家index
		self.current_idx = 0
		# 对当前打出的牌可以进行操作的玩家的index, 服务端会限时等待他的操作
		# 房间基础轮询timer
		self._poll_timer = None
		# 玩家操作限时timer
		self._op_timer = None
		# 一局游戏结束后, 玩家准备界面等待玩家确认timer
		self._next_game_timer = None

		#财神(多个)
		self.kingTiles = []
		#圈风
		self.prevailing_wind = const.WIND_EAST
		#玩家坐庄状态,所有玩家做过庄换圈风 0-没做过庄 1-做过庄
		self.player_dealer_state = [0] * self.player_num

		self.current_round = 0
		self.all_discard_tiles = []
		# 最后一位出牌的玩家
		self.last_player_idx = -1
		# 房间开局所有操作的记录(aid, src, des, tile)
		self.op_record = []
		# 确认继续的玩家
		self.confirm_next_idx = []

		# 解散房间操作的发起者
		self.dismiss_room_from = -1
		# 解散房间操作开始的时间戳
		self.dismiss_room_ts = 0
		# 解散房间操作投票状态
		self.dismiss_room_state_list = [0] * self.player_num
		self.dismiss_timer = None
		# 等待玩家确认胡的dict
		# self.wait_for_win_dict = {} # waitIdx:{"state": 0, "formIdx": idx, "win_op":aid, "quantity":4, "result":[]}
		# self.wait_for_win_list = []
		# 最后一张牌 状态
		self.finalTileWaitIdx = -1
		# self.addTimer(const.ROOM_EXIST_TIME, 0, const.TIMER_TYPE_ROOM_EXIST)
		self.roomOpenTime = time.time()
		# 四位玩家吃碰的次数
		self.full_list = [4*[0], 4*[0], 4*[0], 4*[0]]
		# 创建房间开始的时间戳
		self.create_room_timer = None
		self.create_room_ts = 0

		self.prepare_timer = None
		self.prepare_ts = 0
		self.playerCount = 0

		self.wait_op_info_list = []

	@property
	def isFull(self):
		count = sum([1 for i in self.players_list if i is not None])
		return count == self.player_num

	@property
	def isEmpty(self):
		count = sum([1 for i in self.players_list if i is not None])
		return count == 0 and self.agent is None

	@property
	def nextIdx(self):
		tryNext = (self.current_idx + 1) % self.player_num
		for j in range(2):
			for i in range(self.player_num):
				if self.player_num > tryNext:
					return tryNext
				tryNext = (tryNext + 1) % self.player_num
		return (self.current_idx + 1) % self.player_num

	def getSit(self):
		for i, j in enumerate(self.players_list):
			if j is None:
				return i

	def _reset(self):
		self.state = 0
		self.agent = None
		self.players_list = [None] * self.player_num
		self.dealer_idx = 0
		self.current_idx = 0
		self._poll_timer = None
		self._op_timer = None
		self._next_game_timer = None
		self.all_discard_tiles = []
		self.kingTiles = []
		self.current_round = 0
		self.confirm_next_idx = []
		self.prevailing_wind = const.WIND_EAST
		self.dismiss_timer = None
		self.dismiss_room_ts = 0
		self.dismiss_room_state_list = [0, 0, 0, 0]
		self.finalTileWaitIdx = -1
		self.create_room_timer = None
		self.create_room_ts = 0
		self.prepare_timer = None
		self.prepare_ts = 0
		self.playerCount = 0
		self.wait_op_info_list = []
		KBEngine.globalData["GameWorld"].delRoom(self)

	def throwTheDice(self, idxList):
		if self.player_num == 3:
			diceList = [[0, 0], [0, 0], [0, 0]]
		else:
			diceList = [[0, 0], [0, 0], [0, 0], [0, 0]]
		for idx in idxList:
			for i in range(0,2):
				diceNum = random.randint(1, 6)
				diceList[idx][i] = diceNum
		return diceList

	def getMaxDiceIdx(self, diceList):
		numList = []
		for i in range(len(diceList)):
			numList.append(diceList[i][0] + diceList[i][1])

		idx = 0
		num = 0
		for i in range(len(numList)):
			if numList[i] > num:
				idx = i
				num = numList[i]
		return idx, num

	def onTimer(self, id, userArg):
		DEBUG_MSG("Room.onTimer called: id %i, userArg: %i" % (id, userArg))

		if userArg == 9 or userArg == 13 or userArg == 14:
			self.delTimer(id)
			self.dropRoom()

		# if userArg == const.TIMER_TYPE_ROOM_EXIST:
		# 	self.game_round = self.current_round
		# 	self.delTimer(id)


	def reqEnterRoom(self, avt_mb, first=False):
		"""
		defined.
		客户端调用该接口请求进入房间/桌子
		"""
		if self.isFull:
			avt_mb.enterRoomFailed(const.ENTER_FAILED_ROOM_FULL)
			return

		def callback(content):
			content = content.decode()
			try:
				data = json.loads(content)
				card_cost, diamond_cost = switch.calc_cost(self.game_round, self.game_mode, self.pay_mode, self.player_num)
				if diamond_cost > data["diamond"]:
					avt_mb.enterRoomFailed(const.ENTER_FAILED_ROOM_DIAMOND_NOT_ENOUGH)
					return
				# 代开房
				if first and self.is_agent == 1:
					self.agent = PlayerProxy(avt_mb, self, -1)
					self.players_dict[avt_mb.userId] = self.agent
					avt_mb.enterRoomSucceed(self, -1)					
					return

				for i, p in enumerate(self.players_list):
					if p and p.mb and p.mb.userId == avt_mb.userId:
						p.mb = avt_mb
						avt_mb.enterRoomSucceed(self, i)
						return
				if first:
					self.create_room_ts = time.time()
					self.create_room_timer = self.addTimer(const.CREATE_ROOM_WAIT_TIMER, 0, const.TIMER_TYPE_CREATE_ROOM)

				DEBUG_MSG("Room.reqEnterRoom: %s" % (self.roomID))
				idx = self.getSit()
				n_player = PlayerProxy(avt_mb, self, idx)
				self.players_dict[avt_mb.userId] = n_player
				self.players_list[idx] = n_player

				# 确认准备
				# if idx not in self.confirm_next_idx:
				# 	self.confirm_next_idx.append(idx)

				if not first:
					self.broadcastEnterRoom(idx)
					self.check_same_ip()

				if self.isFull:
					self.origin_players_list = self.players_list[:]
			except:
				DEBUG_MSG("enterRoomFailed callback error:{}".format(content))
		if switch.DEBUG_BASE:
			callback('{"card":99, "diamond":999}'.encode())
		else:
			if first or self.pay_mode != 1:
				callback('{"card":99, "diamond":999}'.encode())
			else:
				utility.get_user_info(avt_mb.accountName, callback)		

	def reqReconnect(self, avt_mb):
		DEBUG_MSG("GameRoom reqReconnect userid = {}".format(avt_mb.userId))
		if avt_mb.userId not in self.players_dict.keys():
			return

		DEBUG_MSG("GameRoom reqReconnect player is in room".format(avt_mb.userId))
		# 如果进来房间后牌局已经开始, 就要传所有信息
		# 如果还没开始, 跟加入房间没有区别
		player = self.players_dict[avt_mb.userId]
		if self.agent and player.userId == self.agent.userId:
			self.agent.mb = avt_mb
			self.agent.online = 1
			avt_mb.enterRoomSucceed(self, -1)
			return
		
		player.mb = avt_mb
		player.online = 1
		if self.state == 1 or 0 < self.current_round <= self.game_round:
			if self.state == 0:
				# 重连回来直接准备
				self.roundEndCallback(avt_mb)
			rec_room_info = self.get_reconnect_room_dict(player.mb.userId)
			player.mb.handle_reconnect(rec_room_info)
		else:
			sit = 0
			for idx, p in enumerate(self.players_list):
				if p and p.mb:
					if p.mb.userId == avt_mb.userId:
						sit = idx
						break
			avt_mb.enterRoomSucceed(self, sit)

		# self.check_same_ip()

	def reqLeaveRoom(self, player):
		"""
		defined.
		客户端调用该接口请求离开房间/桌子
		"""
		DEBUG_MSG("Room.reqLeaveRoom:{0}, is_agent={1}".format(self.roomID, self.is_agent))
		if player.userId in self.players_dict.keys():
			n_player = self.players_dict[player.userId]
			idx = n_player.idx


			if idx == -1 and self.is_agent == 1:
				self.dropRoom()
			elif idx == 0 and self.is_agent == 0:
				# 房主离开房间, 则解散房间
				self.dropRoom()
			else:
				n_player.mb.quitRoomSucceed()
				self.players_list[idx] = None
				del self.players_dict[player.userId]
				if idx in self.confirm_next_idx:
					self.confirm_next_idx.remove(idx)
				# 通知其它玩家该玩家退出房间
				for i, p in enumerate(self.players_list):
					if i != idx and p and p.mb:
						p.mb.othersQuitRoom(idx)
				if self.agent and self.agent.mb:
					self.agent.mb.othersQuitRoom(idx)

		if self.isEmpty:
			self._reset()

	def dropRoom(self):
		for p in self.players_list:
			if p and p.mb:
				try:
					p.mb.quitRoomSucceed()
				except:
					pass

		if self.agent and self.agent.mb:
			try:
				# # 如果是代开房, 没打完一局返还房卡
				# if self.is_agent == 1 and self.current_round < 2:
				# 	# cost = 2 if self.game_round == 16 else 1
				# 	cost = 1
				# 	self.agent.mb.addCards(cost, "dropRoom")
				self.agent.mb.quitRoomSucceed()
			except:
				pass

		self._reset()

	def startGame(self):
		""" 开始游戏 """
		DEBUG_MSG("startGame")
		self.op_record = []
		self.finalTileWaitIdx = -1
		self.state = 1
		self.current_round += 1
		self.full_list = [4*[0], 4*[0], 4*[0], 4*[0]]		
		self.playerCount = 0
		for i,p in enumerate(self.players_list):
			if p is not None:
				p.wreaths = []

		diceList = self.throwTheDice([self.dealer_idx])
		idx, num = self.getMaxDiceIdx(diceList)

		if self.current_round == 1:
			self.dealer_idx = random.randint(0, 3)

		# self.dealer_idx = 0
		if self.create_room_timer:
			self.delTimer(self.create_room_timer)
			self.create_room_timer = None
			self.create_room_ts = 0

		if self.prepare_timer:
			self.delTimer(self.prepare_timer)
			self.prepare_timer = None
			self.prepare_ts = 0

		# 仅仅在第1局扣房卡, 不然每局都会扣房卡
		def callback(content):
			content = content.decode()
			try:
				if content[0] != '{':
					DEBUG_MSG(content)
					self.dropRoom()
					return
				# 第一局时房间默认房主庄家, 之后谁上盘赢了谁是, 如果臭庄, 最后摸牌的人是庄
				for p in self.players_list:
					p.reset()
				self.current_idx = self.dealer_idx
				#圈风
				if sum([1 for state in self.player_dealer_state if state == 1]) == self.player_num:
					windIdx = (self.prevailing_wind + 1 - const.WIND_EAST)%len(const.WINDS)
					self.prevailing_wind = const.WINDS[windIdx]
					self.player_dealer_state = [0, 0, 0, 0]
				self.player_dealer_state[self.dealer_idx] = 1
				#自风
				for i,p in enumerate(self.players_list):
					if p is not None:
						p.wind = (self.player_num + i - self.dealer_idx)%self.player_num + const.WIND_EAST
				self.initTiles()
				self.deal(self.king_num)
				wreathsList = [p.wreaths for i,p in enumerate(self.players_list)]
				playerWindList = [p.wind for i,p in enumerate(self.players_list)]				
				
				for p in self.players_list:
					if p and p.mb:
						DEBUG_MSG("start game,dealer_idx:{0},tiles:{1}, wreathsList:{2}, kingTiles:{3}, diceList:{4},leftTileNum:{5}".format(self.dealer_idx, p.tiles, wreathsList, self.kingTiles, diceList, len(self.tiles)))
						p.mb.startGame(self.dealer_idx, p.tiles, wreathsList, self.kingTiles, self.prevailing_wind, playerWindList, diceList)
				
				self.beginRound()
			except:
				DEBUG_MSG("consume failed!")

		if self.current_round == 1 and self.is_agent == 0:
			card_cost, diamond_cost = switch.calc_cost(self.game_round, self.game_mode, self.pay_mode, self.player_num)
			if switch.DEBUG_BASE:
				callback('{"card":99, "diamond":999}'.encode())
			elif self.pay_mode == 0:
				utility.update_card_diamond(self.players_list[0].mb.accountName, -card_cost, -diamond_cost, callback, "FengHua RoomID:{}".format(self.roomID))
			else:
				signal = 0
				def payCallback(content):
					nonlocal signal
					try:
						signal += 1
						if signal == len(self.players_list):
							callback(content)
					except:
						DEBUG_MSG("AA payCallback Failed")
				utility.update_card_diamond(self.players_list[0].mb.accountName, -card_cost, -diamond_cost, payCallback, "FengHua RoomID:{}".format(self.roomID))
				utility.update_card_diamond(self.players_list[1].mb.accountName, -card_cost, -diamond_cost, payCallback, "FengHua RoomID:{}".format(self.roomID))
				utility.update_card_diamond(self.players_list[2].mb.accountName, -card_cost, -diamond_cost, payCallback, "FengHua RoomID:{}".format(self.roomID))
				utility.update_card_diamond(self.players_list[3].mb.accountName, -card_cost, -diamond_cost, payCallback, "FengHua RoomID:{}".format(self.roomID))
			return

		DEBUG_MSG("start Game: Room{0} - Round{1}".format(self.roomID, str(self.current_round)+'/'+str(self.game_round)))

		callback('{"card":99, "diamond":999}'.encode())

	def cutAfterKong(self):
		if not self.can_cut_after_kong():
			return
		if len(self.tiles) <= 0:
			self.drawEnd()
		elif len(self.tiles) > 1:
			player = self.players_list[self.current_idx]
			ti = self.tiles[0]
			self.tiles = self.tiles[1:]
			player.cutTile(ti)

	def beginRound(self):
		if len(self.tiles) <= 0:
			self.drawEnd()
		elif len(self.tiles) == 1:
			self.notifyFinalTile()
		else:
			player = self.players_list[self.current_idx]
			ti = self.tiles[0]
			self.tiles = self.tiles[1:]
			DEBUG_MSG("beginRound len:{0}".format(len(self.tiles)))
			player.drawTile(ti)

	def notifyFinalTile(self):
		self.finalTileWaitIdx = self.current_idx
		p = self.players_list[self.current_idx]
		p.mb.notifyFinalTile()

	def decideFinalTile(self, avt_mb, isShow):
		idx = -1
		for i, p in enumerate(self.players_list):
			if p and p.userId == avt_mb.userId:
				idx = i
				break
		if idx != self.current_idx or len(self.tiles) != 1:
			DEBUG_MSG("open final tile error.")
			avt_mb.doOperationFailed(const.OP_ERROR_ILLEGAL)
			return
		tile = self.tiles[0]
		self.tiles = self.tiles[1:]
		if not isShow:
			self.beginRound()
		else:
			for i, p in enumerate(self.players_list):
				if p is not None:
					p.mb.showFinalTile(tile, idx)
			DEBUG_MSG("check final tile win.")
			self.all_discard_tiles.append(tile)
			self.last_player_idx = idx
			# self.wait_for_win_list = self.getFinalWinList(idx, tile)
			# if not self.wait_for_win_list:
			# 	self.beginRound()
			# else:
			# 	self.waitForOperation(idx, const.OP_FINAL_DRAW, tile, self.wait_for_win_list)
			self.waitForOperation(idx, const.OP_FINAL_DRAW, tile)

	def reqStopGame(self, player):
		"""
		客户端调用该接口请求停止游戏
		"""
		DEBUG_MSG("Room.reqLeaveRoom: %s" % (self.roomID))
		self.state = 0
		# self.delTimer(self._poll_timer)
		# self._poll_timer = None


	def drawEnd(self):
		""" 臭庄 """
		info = dict()
		info['win_op'] = -1
		info['win_idx'] = -1
		info['lucky_tiles'] = []
		info['result_list'] = []
		info['finalTile'] = 0
		info['from_idx'] = -1
		if self.game_mode == 1:			
			if self.current_round < self.game_round:
				self.broadcastRoundEnd(info)
			else:
				self.endAll(info)
		else:
			for i, p in enumerate(self.players_list):
				if p.total_score <= 0:
					self.endAll(info)
					break
			else:
				self.broadcastRoundEnd(info)

	def winGame(self, idx, op, finalTile, from_idx, quantity, result, kongType):
		""" 座位号为idx的玩家胡牌 """ 
		self.cal_score(idx, op, result, kongType, quantity)

		if self.game_mode == 0:
			self.dealer_idx = idx
		elif self.game_mode == 1:
			if self.dealer_idx == idx:
				self.dealer_idx = idx
			else:
				self.dealer_idx = (self.dealer_idx + 1) % self.player_num

		info = dict()
		info['win_op'] = op
		info['win_idx'] = idx
		info['lucky_tiles'] = []
		info['result_list'] = result
		info['finalTile'] = finalTile
		info['from_idx'] = from_idx

		if self.game_mode == 1:			
			if self.current_round < self.game_round:
				self.broadcastRoundEnd(info)
			else:
				self.endAll(info)
		else:
			for i, p in enumerate(self.players_list):
				DEBUG_MSG("total_score:{0}".format(p.total_score))
				if p.total_score <= 0:
					self.endAll(info)
					break
			else:
				self.broadcastRoundEnd(info)

	def endAll(self, info):
		""" 游戏局数结束, 给所有玩家显示最终分数记录 """

		# 先记录玩家当局战绩, 会累计总得分
		self.record_round_result()

		info['left_tiles'] = info['left_tiles'] = self.tiles
		info['player_info_list'] = [p.get_round_client_dict() for p in self.players_list if p is not None]
		player_info_list = [p.get_final_client_dict() for p in self.players_list if p is not None]
		# DEBUG_MSG("%" * 30)
		DEBUG_MSG("FinalEnd player_info_list = {0}  info = {1}".format(player_info_list, info))
		for p in self.players_list:
			if p and p.mb:
				p.mb.finalResult(player_info_list, info)

		self._reset()

	def sendEmotion(self, avt_mb, eid):
		""" 发表情 """
		# DEBUG_MSG("Room.Player[%s] sendEmotion: %s" % (self.roomID, eid))
		idx = None
		for i, p in enumerate(self.players_list):
			if p and avt_mb == p.mb:
				idx = i
				break
		else:
			if self.agent and self.agent.userId == avt_mb.userId:
				idx = -1

		if idx is None:
			return

		if self.agent and idx != -1 and self.agent.mb:
			self.agent.mb.recvEmotion(idx, eid)

		for i, p in enumerate(self.players_list):
			if p and i != idx:
				p.mb.recvEmotion(idx, eid)

	def sendMsg(self, avt_mb, mid):
		""" 发消息 """
		# DEBUG_MSG("Room.Player[%s] sendMsg: %s" % (self.roomID, mid))
		idx = None
		for i, p in enumerate(self.players_list):
			if p and avt_mb == p.mb:
				idx = i
				break
		else:
			if self.agent and self.agent.userId == avt_mb.userId:
				idx = -1

		if idx is None:
			return

		if self.agent and idx != -1 and self.agent.mb:
			self.agent.mb.recvMsg(idx, mid)

		for i, p in enumerate(self.players_list):
			if p and i != idx:
				p.mb.recvMsg(idx, mid)

	def sendVoice(self, avt_mb, url):
		# DEBUG_MSG("Room.Player[%s] sendVoice" % (self.roomID))
		idx = None
		for i, p in enumerate(self.players_list):
			if p and avt_mb.userId == p.userId:
				idx = i
				break
		else:
			if self.agent and self.agent.userId == avt_mb.userId:
				idx = -1

		if idx is None:
			return
		if self.agent and idx != -1 and self.agent.mb:
			self.agent.mb.recvVoice(idx, url)

		for i, p in enumerate(self.players_list):
			if p and p.mb:
				p.mb.recvVoice(idx, url)

	def sendAppVoice(self, avt_mb, url, time):
		# DEBUG_MSG("Room.Player[%s] sendVoice" % (self.roomID))
		idx = None
		for i, p in enumerate(self.players_list):
			if p and avt_mb.userId == p.userId:
				idx = i
				break
		else:
			if self.agent and self.agent.userId == avt_mb.userId:
				idx = -1

		if idx is None:
			return
		if self.agent and idx != -1 and self.agent.mb:
			self.agent.mb.recvAppVoice(idx, url, time)

		for i, p in enumerate(self.players_list):
			if p and p.mb:
				p.mb.recvAppVoice(idx, url, time)

	def doOperation(self, avt_mb, aid, tile_list):
		"""
		当前控牌玩家摸牌后向服务端确认的操作
		:param idx: 当前打牌的人的座位
		:param aid: 操作id
		:param tile: 针对的牌
		:return: 确认成功或者失败
		"""
		if self.dismiss_room_ts != 0 and int(time.time() - self.dismiss_room_ts) < const.DISMISS_ROOM_WAIT_TIME:
			# 说明在准备解散投票中,不能进行其他操作
			return

		tile = tile_list[0]
		idx = -1
		for i, p in enumerate(self.players_list):
			if p and p.mb == avt_mb:
				idx = i

		if idx != self.current_idx or len(self.wait_op_info_list) > 0:
			avt_mb.doOperationFailed(const.OP_ERROR_NOT_CURRENT)
			return

		# self.delTimer(self._op_timer)
		p = self.players_list[idx]
		if aid == const.OP_DISCARD and self.can_discard(p.tiles, tile):
			self.all_discard_tiles.append(tile)
			p.discardTile(tile)
		elif aid == const.OP_CONCEALED_KONG and self.can_concealed_kong(p.tiles, tile):
			p.concealedKong(tile)
		elif aid == const.OP_EXPOSED_KONG and self.can_self_exposed_kong(p, tile):
			DEBUG_MSG("ming gang")
			p.exposedKong(tile)
		elif aid == const.OP_KONG_WREATH and self.can_kong_wreath(p.tiles, tile):
			p.kongWreath(tile)
		elif aid == const.OP_RISK_KONG and self.can_self_exposed_kong(p, tile):
			DEBUG_MSG("feng xian gang")
			p.self_exposedKong(tile)
		elif aid == const.OP_PASS:
			# 自己摸牌的时候可以杠或者胡时选择过, 则什么都不做. 继续轮到该玩家打牌.
			pass
		elif aid == const.OP_DRAW_WIN: #普通自摸胡
			DEBUG_MSG("can_win 1111111111")
			is_win, score, result, kongType = self.can_win(list(p.tiles), p.last_draw, const.OP_DRAW_WIN, idx)
			if is_win:
				p.draw_win(tile, score, result, kongType)
			else:
				avt_mb.doOperationFailed(const.OP_ERROR_ILLEGAL)
				self.current_idx = self.nextIdx
				self.beginRound()
		elif aid == const.OP_WREATH_WIN: #自摸8张花胡
			DEBUG_MSG("can_win 2222222222")
			is_win, score, result, kongType = self.can_win(list(p.tiles), p.last_draw, const.OP_WREATH_WIN, idx)
			if is_win:
				p.draw_win(tile, score, result, kongType)
			else:
				avt_mb.doOperationFailed(const.OP_ERROR_ILLEGAL)
				self.current_idx = self.nextIdx
				self.beginRound()
		else:
			avt_mb.doOperationFailed(const.OP_ERROR_ILLEGAL)
			self.current_idx = self.nextIdx
			self.beginRound()


	def broadcastOperation(self, idx, aid, tile_list = None):
		"""
		将操作广播给所有人, 包括当前操作的玩家
		:param idx: 当前操作玩家的座位号
		:param aid: 操作id
		:param tile_list: 出牌的list
		"""
		for i, p in enumerate(self.players_list):
			if p is not None:
				p.mb.postOperation(idx, aid, tile_list)

	def broadcastOperation2(self, idx, aid, tile_list = None):
		""" 将操作广播除了自己之外的其他人 """
		for i, p in enumerate(self.players_list):
			if p and i != idx:
				p.mb.postOperation(idx, aid, tile_list)

	def broadcastMultiOperation(self, idx_list, aid_list, tile_list=None):
		for i, p in enumerate(self.players_list):
			if p is not None:
				p.mb.postMultiOperation(idx_list, aid_list, tile_list)

	def broadcastRoundEnd(self, info):
		# 广播胡牌或者流局导致的每轮结束信息, 包括算的扎码和当前轮的统计数据

		# 先记录玩家当局战绩, 会累计总得分
		self.record_round_result()

		self.state = 0
		info['left_tiles'] = self.tiles
		info['player_info_list'] = [p.get_round_client_dict() for p in self.players_list if p is not None]

		DEBUG_MSG("&" * 30)
		DEBUG_MSG("RoundEnd info = {}".format(info))
		self.confirm_next_idx = []
		for p in self.players_list:
			if p:
				p.mb.roundResult(info)

	def confirmOperation(self, avt_mb, aid, tile_list):
		""" 被轮询的玩家确认了某个操作 """
		if self.dismiss_room_ts != 0 and int(time.time() - self.dismiss_room_ts) < const.DISMISS_ROOM_WAIT_TIME:
			# 说明在准备解散投票中,不能进行其他操作
			return

		tile = tile_list[0]
		idx = -1
		for i, p in enumerate(self.players_list):
			if p and p.mb == avt_mb:
				idx = i
		#玩家是否可以操作
		DEBUG_MSG("wait_op_info_list:{0}".format(self.wait_op_info_list))
		if len(self.wait_op_info_list) <= 0 or sum([1 for waitOpDict in self.wait_op_info_list if (waitOpDict["idx"] == idx and waitOpDict["state"] == const.WAIT_STATE)]) <= 0:
			avt_mb.doOperationFailed(const.OP_ERROR_NOT_CURRENT)
			return
		
		#提交 玩家结果
		for waitOpDict in self.wait_op_info_list:
			if waitOpDict["idx"] == idx:
				if waitOpDict["aid"] == const.OP_CHOW and aid == const.OP_CHOW and waitOpDict["tileList"][0] == tile_list[0] and self.can_chow_one(self.players_list[waitOpDict["idx"]].tiles, tile_list):
					waitOpDict["state"] = const.SURE_STATE
					waitOpDict["tileList"] = tile_list
				elif waitOpDict["aid"] == aid and aid != const.OP_CHOW:
					waitOpDict["state"] = const.SURE_STATE		
				else:
					waitOpDict["state"] = const.GIVE_UP_STATE
		#有玩家可以操作
		isOver,confirmOpDict = self.getConfirmOverInfo()
		if isOver:
			DEBUG_MSG("commit over {0}.".format(confirmOpDict))
			DEBUG_MSG("tile_list: {0}.".format(tile_list))
			
			temp_wait_op_info_list = copy.deepcopy(self.wait_op_info_list)
			self.wait_op_info_list = []
			if len(confirmOpDict) > 0:
				sureIdx = confirmOpDict["idx"]
				p = self.players_list[sureIdx]
				if confirmOpDict["aid"] == const.OP_CHOW:
					self.current_idx = sureIdx
					p.chow(confirmOpDict["tileList"])
				elif confirmOpDict["aid"] == const.OP_PONG:
					self.current_idx = sureIdx
					p.pong(confirmOpDict["tileList"][0])
				elif confirmOpDict["aid"] == const.OP_EXPOSED_KONG:
					self.current_idx = sureIdx
					p.exposedKong(confirmOpDict["tileList"][0])
				elif confirmOpDict["aid"] == const.OP_KONG_WIN:
					p.kong_win(confirmOpDict["tileList"][0], confirmOpDict["score"], confirmOpDict["result"])
				elif confirmOpDict["aid"] == const.OP_GIVE_WIN:
					p.give_win(confirmOpDict["tileList"][0], confirmOpDict["score"], confirmOpDict["result"])
				elif confirmOpDict["aid"] == const.OP_FINAL_WIN:
					if confirmOpDict["idx"] == self.current_idx:
						p.draw_win(confirmOpDict["tileList"][0], confirmOpDict["score"], confirmOpDict["result"], 0, confirmOpDict["tileList"][0])
					else:
						p.give_win(confirmOpDict["tileList"][0], confirmOpDict["score"], confirmOpDict["result"])
				else:
					DEBUG_MSG("len(confirmOpDict) > 0 temp_wait_op_info_list: {0}.".format(temp_wait_op_info_list))
					lastAid = temp_wait_op_info_list[0]["aid"]
					if lastAid == const.OP_WREATH_WIN:
						self.current_idx = self.last_player_idx
					elif lastAid == const.OP_KONG_WIN:
						#*********没人抢杠胡 杠要算分？***********
						self.current_idx = self.last_player_idx
					else:
						self.current_idx = self.nextIdx
					self.beginRound()
			else:
				DEBUG_MSG("len(confirmOpDict) <= 0 temp_wait_op_info_list: {0}.".format(temp_wait_op_info_list))
				lastAid = temp_wait_op_info_list[0]["aid"]
				if lastAid == const.OP_WREATH_WIN:
					self.current_idx = self.last_player_idx
				elif lastAid == const.OP_KONG_WIN:
					#*********没人抢杠胡 杠要算分？***********
					self.current_idx = self.last_player_idx
				else:
					self.current_idx = self.nextIdx
				self.beginRound()

	def getConfirmOverInfo(self):
		for i in range(len(self.wait_op_info_list)):
			waitState = self.wait_op_info_list[i]["state"]
			if waitState == const.GIVE_UP_STATE:
				continue
			elif waitState == const.WAIT_STATE: #需等待其他玩家操作
				return False, {}
			elif waitState == const.SURE_STATE:	#有玩家可以操作
				return True, self.wait_op_info_list[i]
		return True, {}	#所有玩家选择放弃

	def getNotifyOpList(self, idx, aid, tile):
		# notifyOpList 和 self.wait_op_info_list 必须同时操作
		# 数据结构：问询玩家，操作玩家，牌，操作类型，得分，结果，状态
		notifyOpList = [[] for i in range(self.player_num)]
		self.wait_op_info_list = []
		#胡
		if aid == const.OP_KONG_WREATH and self.can_wreath_win(self.players_list[idx].wreaths): # 8花胡
			opDict = {"idx":idx, "from":idx, "tileList":[tile,], "aid":const.OP_WREATH_WIN, "score":0, "result":[], "state":const.WAIT_STATE}
			notifyOpList[idx].append(opDict)
			self.wait_op_info_list.append(opDict)
		elif aid == const.OP_RISK_KONG: # 抢杠胡
			wait_for_win_list = self.getKongWinList(idx, tile)
			self.wait_op_info_list.extend(wait_for_win_list)
			for i in range(len(wait_for_win_list)):
				dic = wait_for_win_list[i]
				notifyOpList[dic["idx"]].append(dic)
		elif aid == const.OP_FINAL_DRAW: # 海捞胡
			wait_for_win_list = self.getFinalWinList(idx, tile)
			self.wait_op_info_list.extend(wait_for_win_list)
			for i in range(len(wait_for_win_list)):
				dic = wait_for_win_list[i]
				notifyOpList[dic["idx"]].append(dic)
		elif aid == const.OP_DISCARD:
			#胡(放炮胡)
			wait_for_win_list = self.getGiveWinList(idx, tile)
			self.wait_op_info_list.extend(wait_for_win_list)
			for i in range(len(wait_for_win_list)):
				dic = wait_for_win_list[i]
				notifyOpList[dic["idx"]].append(dic)
			#杠 碰
			for i, p in enumerate(self.players_list):
				if p and i != idx:
					if self.can_exposed_kong(p.tiles, tile):
						opDict = {"idx":i, "from":idx, "tileList":[tile,], "aid":const.OP_EXPOSED_KONG, "score":0, "result":[], "state":const.WAIT_STATE}
						self.wait_op_info_list.append(opDict)
						notifyOpList[i].append(opDict)
					if self.can_pong(p.tiles, tile):
						opDict = {"idx":i, "from":idx, "tileList":[tile,], "aid":const.OP_PONG, "score":0, "result":[], "state":const.WAIT_STATE}
						self.wait_op_info_list.append(opDict)
						notifyOpList[i].append(opDict)
			#吃
			nextIdx = self.nextIdx
			if self.can_chow(self.players_list[nextIdx].tiles, tile):
				opDict = {"idx":nextIdx, "from":idx, "tileList":[tile,], "aid":const.OP_CHOW, "score":0, "result":[], "state":const.WAIT_STATE}
				self.wait_op_info_list.append(opDict)
				notifyOpList[nextIdx].append(opDict)
		return notifyOpList

	def waitForOperation(self, idx, aid, tile, nextIdx = -1): #  aid抢杠 杠花没人可胡 nextIdx还是自己
		notifyOpList = self.getNotifyOpList(idx, aid, tile)
		if sum([len(x) for x in notifyOpList]) > 0:
			DEBUG_MSG("waitForOperation idx:{0},aid:{1},tile:{2}==>notifyOpList:{3}".format(idx, aid, tile, notifyOpList))
			for i,p in enumerate(self.players_list):
				if p is not None and len(notifyOpList[i]) > 0:
					waitAidList = [notifyOp["aid"] for notifyOp in notifyOpList[i]]
					p.mb.waitForOperation(waitAidList, [tile,])
		else:
			DEBUG_MSG("nobody waitForOperation.idx:{0},aid:{1},tile:{2}".format(idx, aid, tile))
			self.current_idx = self.nextIdx if nextIdx < 0 else nextIdx
			self.beginRound()

	# 抢杠胡 玩家列表
	def getKongWinList(self, idx, tile):
		wait_for_win_list = []
		for i in range(self.player_num - 1):
			ask_idx = (idx+i+1)%self.player_num
			p = self.players_list[ask_idx]
			tryTiles = list(p.tiles)
			tryTiles.append(tile)
			tryTiles = sorted(tryTiles)
			DEBUG_MSG("getKongWinList {0}".format(ask_idx))
			is_win, score, result, kongType = self.can_win(tryTiles, tile, const.OP_KONG_WIN, ask_idx)
			if is_win:
				wait_for_win_list.append({"idx":ask_idx, "from":idx, "tileList":[tile,], "aid":const.OP_KONG_WIN, "score":score, "result":result, "state":const.WAIT_STATE})
		return wait_for_win_list

	# 放炮胡 玩家列表
	def getGiveWinList(self, idx, tile):
		wait_for_win_list = []
		for i in range(self.player_num - 1):
			ask_idx = (idx+i+1)%self.player_num
			p = self.players_list[ask_idx]
			tryTiles = list(p.tiles)
			tryTiles.append(tile)
			tryTiles = sorted(tryTiles)
			DEBUG_MSG("getGiveWinList {0}".format(ask_idx))
			is_win, score, result, kongType = self.can_win(tryTiles, tile, const.OP_GIVE_WIN, ask_idx)
			if is_win:
				wait_for_win_list.append({"idx":ask_idx, "from":idx, "tileList":[tile,], "aid":const.OP_GIVE_WIN, "score":score, "result":result, "state":const.WAIT_STATE})
		return wait_for_win_list

	# 最后一张牌胡 玩家列表
	def getFinalWinList(self, idx, tile):
		wait_for_win_list = []
		#玩家自己
		p = self.players_list[idx]
		tryTiles = list(p.tiles)
		tryTiles.append(tile)
		tryTiles = sorted(tryTiles)
		DEBUG_MSG("getFinalWinList {0}".format(idx))
		is_win, score, result, kongType = self.can_win(tryTiles, tile, const.OP_FINAL_WIN, idx)
		if is_win:
			wait_for_win_list.append({"idx":idx, "from":idx, "tileList":[tile,], "aid":const.OP_FINAL_WIN, "score":score, "result":result, "state":const.WAIT_STATE})
			
		#其他玩家
		for i in range(self.player_num - 1):
			ask_idx = (idx+i+1)%self.player_num
			p = self.players_list[ask_idx]
			tryTiles = list(p.tiles)
			tryTiles.append(tile)
			tryTiles = sorted(tryTiles)
			DEBUG_MSG("getFinalWinList {0}".format(ask_idx))
			is_win, score, result, kongType = self.can_win(tryTiles, tile, const.OP_FINAL_WIN, ask_idx)
			if is_win:
				wait_for_win_list.append({"idx":ask_idx, "from":idx, "tileList":[tile,], "aid":const.OP_FINAL_WIN, "score":score, "result":result, "state":const.WAIT_STATE})
		return wait_for_win_list

	def get_init_client_dict(self):
		agent_d = {
			'nickname': "",
			'userId': 0,
			'head_icon': "",
			'ip': '0.0.0.0',
			'sex': 1,
			'idx': -1,
			'uuid': 0,
			'online': 1,
		}
		if self.is_agent and self.agent:
			d = self.agent.get_init_client_dict()
			agent_d.update(d)

		create_room_time = const.CREATE_ROOM_WAIT_TIMER - (int(time.time() - self.create_room_ts))
		if self.create_room_ts == 0 or create_room_time >= const.CREATE_ROOM_WAIT_TIMER:
			create_room_time = 0

		prepare_time = const.CREATE_ROOM_WAIT_TIMER - (int(time.time() - self.prepare_ts))
		DEBUG_MSG("prepare_time: {0}".format(prepare_time))
		if self.prepare_ts == 0 or prepare_time >= const.CREATE_ROOM_WAIT_TIMER:
			prepare_time = 0

		return {
			'roomID': self.roomID,
			'ownerId': self.owner_uid,
			'isAgent': self.is_agent,
			'agentInfo': agent_d,
			'dealerIdx': self.dealer_idx,
			'curRound': self.current_round,
			'maxRound': self.game_round,
			'player_num': self.player_num,
			'win_quantity': self.win_quantity,
			'king_num': self.king_num,
			'pay_mode': self.pay_mode,
			'game_mode': self.game_mode,
			'player_base_info_list': [p.get_init_client_dict() for p in self.players_list if p is not None],
			'player_state_list': [1 if i in self.confirm_next_idx else 0 for i in range(const.ROOM_PLAYER_NUMBER)],
			'create_room_time': create_room_time,
			'prepare_time': prepare_time,
		}

	def get_reconnect_room_dict(self, userId):
		dismiss_left_time =const.DISMISS_ROOM_WAIT_TIME - (int(time.time() - self.dismiss_room_ts))
		if self.dismiss_room_ts == 0 or dismiss_left_time >= const.DISMISS_ROOM_WAIT_TIME:
			dismiss_left_time = 0

		create_room_time =const.CREATE_ROOM_WAIT_TIMER - (int(time.time() - self.create_room_ts))
		if self.create_room_ts == 0 or create_room_time >= const.CREATE_ROOM_WAIT_TIMER:
			create_room_time = 0

		prepare_time = const.CREATE_ROOM_WAIT_TIMER - (int(time.time() - self.prepare_ts))
		DEBUG_MSG("prepare_time: {0}, {1}, {2}".format(prepare_time, time.time(), self.prepare_ts))
		if self.prepare_ts == 0 or prepare_time >= const.CREATE_ROOM_WAIT_TIMER:
			prepare_time = 0

		idx = 0
		for p in self.players_list:
			if p and p.userId == userId:
				idx = p.idx
		
		
		return {
			'init_info' : self.get_init_client_dict(),
			'curPlayerSitNum': self.current_idx,
			'isPlayingGame': self.state,
			'player_state_list': [1 if i in self.confirm_next_idx else 0 for i in range(self.player_num)],
			'lastDiscardTile': 0 if not self.all_discard_tiles else self.all_discard_tiles[-1],
			'lastDrawTile' : self.players_list[idx].last_draw,
			'lastDiscardTileFrom': self.last_player_idx,
			'kingTiles' : self.kingTiles,
			'waitAidList': [self.wait_op_info_list[i]["aid"] for i in range(len(self.wait_op_info_list)) if self.wait_op_info_list[i]["idx"] == idx and self.wait_op_info_list[i]["state"] == const.WAIT_STATE],
			'finalTileWaitIdx' : self.finalTileWaitIdx,
			'leftTileNum': len(self.tiles),
			'applyCloseFrom': self.dismiss_room_from,
			'applyCloseLeftTime': dismiss_left_time,
			'applyCloseStateList': self.dismiss_room_state_list,
			'player_advance_info_list': [p.get_reconnect_client_dict(userId) for p in self.players_list if p is not None],
			'prevailing_wind': self.prevailing_wind,
			'createRoomTime': create_room_time,
			'prepareTime': prepare_time,
		}

	def broadcastEnterRoom(self, idx):
		new_p = self.players_list[idx]

		if self.is_agent == 1:
			if self.agent and self.agent.mb:
				self.agent.mb.othersEnterRoom(new_p.get_init_client_dict())

		for i, p in enumerate(self.players_list):
			if p is None:
				continue
			if i == idx:
				p.mb.enterRoomSucceed(self, idx)
			else:
				p.mb.othersEnterRoom(new_p.get_init_client_dict())

	def cal_score(self, idx, aid, result, kongType, quantity = 0):
		kong_score = 0
		op_list = []  #吃碰杠的list
		op_times_list = [0, 0 , 0, 0] #每个玩家吃碰杠的次数
		isAllFullIdx = -1 #包掉玩家的idx
		for i, p in enumerate(self.players_list):
			if p is not None and idx == i:
				for i in range(len(p.op_r)):
					if p.op_r[i][0] == 4 or p.op_r[i][0] == 5:
						op_list.append(p.op_r[i])
				kong_score = p.kong_list[0] * 50 + ( p.kong_list[1] +  p.kong_list[2]) * 100
		if kongType == 1:
			kong_score -= 50 # 直杠或暗杠-50分
		elif kongType == 2:
			kong_score -= 100 # 风险杠-100分
		elif kongType == 3:
			kong_score -= 200 # 两个暗杠，暗杠+风险杠，两个风险杠 -200分
		elif kongType == 4:
			kong_score -= 150 # 直杠+风险杠 -150分

		if quantity < 10:
				quantity += 10 # 不满10分则加至20分

		if len(op_list) >= 3:
			for i in range(len(op_list)):
				op_times_list[op_list[i][2]] += 1
		
		for i in range(len(op_times_list)):
			if op_times_list[i] == 4 :
				isAllFullIdx = i
			if op_times_list[i] == 3 and (result[4] == 1 or result[5] == 1 or result[2] == 1) and sum([i for i in op_times_list if i > 0]) == 3:
				isAllFullIdx = i
		DEBUG_MSG("score  idx:{0}, quantity :{1}, isAllFullIdx: {2}".format(idx, quantity, isAllFullIdx))

		if isAllFullIdx >= 0: #包掉
			if aid == const.OP_DRAW_WIN or (result[0] == 1 or result[1] ==1):#自摸
				sub_score = 0
				virtual_score = 0
				for i, p in enumerate(self.players_list):
					if p is not None:
						if isAllFullIdx == i:
							real_score = -(quantity + kong_score) * 3
							virtual_score += real_score
							sub_score += p.addScore(real_score, real_score)
							if aid == const.OP_KONG_WIN:
								real_score = -quantity * 3
								virtual_score += real_score
								sub_score += p.addScore(real_score, real_score)
				self.players_list[idx].addScore(-sub_score, -virtual_score)
				return
			elif aid == const.OP_KONG_WIN:  # 抢杠胡
				quantity +=  kong_score
				sub_score = 0
				virtual_score = 0
				for i, p in enumerate(self.players_list):
					if p is not None and i == isAllFullIdx:
						real_score = -quantity*3
						virtual_score += real_score
						sub_score += p.addScore(real_score, real_score)
				self.players_list[idx].addScore(-sub_score, -virtual_score)
				return
			elif aid == const.OP_GIVE_WIN and (result[0] != 1 or result[1] !=1) and len(self.tiles) > 0: # 点炮，放炮
				quantity +=  kong_score
				if quantity < 20:
					quantity = 20
				quantities = (int)(quantity / 2)
				if (quantities % 10) != 0:
					quantities += 5

				sub_score = 0
				virtual_score = 0
				for i, p in enumerate(self.players_list):
					if p is not None and idx != i:
						if isAllFullIdx == i:
							real_score = -(quantity + quantities * 2)
							virtual_score += real_score
							sub_score += p.addScore(real_score, real_score)
				self.players_list[idx].addScore(-sub_score, -virtual_score)
				return
			elif aid == const.OP_FINAL_WIN or len(self.tiles) <= 0: #最后一张牌
				quantity +=  kong_score
				if idx == self.last_player_idx:
					sub_score = 0
					virtual_score = 0
					for i, p in enumerate(self.players_list):
						if p is not None and isAllFullIdx == i:
							real_score = -quantity* 3
							virtual_score += real_score	
							sub_score += p.addScore(real_score, real_score)
					self.players_list[idx].addScore(-sub_score, -virtual_score)
				else:
					sub_score = 0
					virtual_score = 0
					for i, p in enumerate(self.players_list):
						if p is not None:
							if self.last_player_idx == i:
								real_score = -quantity
								virtual_score += real_score	
								sub_score += p.addScore(real_score, real_score)
							if isAllFullIdx == i:
								quantity = quantity - 150
								real_score = -quantity*3
								virtual_score += real_score	
								sub_score += p.addScore(real_score, real_score)
					self.players_list[idx].addScore(-sub_score, -virtual_score)
				return
		if aid == const.OP_EXPOSED_KONG: #直杠开花
			pass
		elif aid == const.OP_CONCEALED_KONG: #暗杠开花
			pass
		elif aid == const.OP_POST_KONG: #放杠
			pass
		elif aid == const.OP_GET_KONG:  #接杠
			pass
		elif aid == const.OP_DRAW_WIN or (result[0] == 1 or result[1] == 1 or result[7] == 1) : #自摸
			quantity +=  kong_score
			if quantity < 20:
				quantity = 20
			sub_score = 0
			virtual_score = 0
			for i, p in enumerate(self.players_list):
				if p is not None and idx != i:
					real_score = -quantity
					virtual_score += real_score
					sub_score += p.addScore(real_score, real_score)
			self.players_list[idx].addScore(-sub_score, -virtual_score)
		elif aid == const.OP_KONG_WIN:  # 抢杠胡
			quantity +=  kong_score
			sub_score = 0
			virtual_score = 0
			for i, p in enumerate(self.players_list):
				if p is not None and i == self.last_player_idx:
					real_score = -quantity*3
					virtual_score += real_score
					sub_score += p.addScore(real_score, real_score)
			self.players_list[idx].addScore(-sub_score, -virtual_score)
		elif aid == const.OP_GIVE_WIN and (result[0] != 1 or result[1] !=1) and len(self.tiles) > 0: # 点炮，放炮
			quantity +=  kong_score
			if quantity < 20:
				quantity = 20
			quantities = (int)(quantity / 2)
			if (quantities % 10) != 0:
				quantities += 5

			sub_score = 0
			virtual_score = 0
			for i, p in enumerate(self.players_list):
				if p is not None and idx != i:
					if self.last_player_idx == i:
						real_score = -quantity
						virtual_score += real_score	
						sub_score += p.addScore(real_score, real_score)
					else:
						real_score = -quantities
						virtual_score += real_score	
						sub_score += p.addScore(real_score, real_score)
			self.players_list[idx].addScore(-sub_score, -virtual_score)
		elif aid == const.OP_FINAL_WIN or len(self.tiles) <= 0: #最后一张牌
			quantity +=  kong_score
			if idx == self.last_player_idx:
				sub_score = 0
				virtual_score = 0
				for i, p in enumerate(self.players_list):
					if p is not None and idx != i:
						real_score = -quantity
						virtual_score += real_score	
						sub_score += p.addScore(real_score, real_score)
				self.players_list[idx].addScore(-sub_score, -virtual_score)
			else:
				sub_score = 0
				virtual_score = 0
				for i, p in enumerate(self.players_list):
					if p is not None and self.last_player_idx == i:
						real_score = -(quantity * 3)
						virtual_score += real_score	
						sub_score += p.addScore(real_score, real_score)
				self.players_list[idx].addScore(-sub_score, -virtual_score)

	def roundEndCallback(self, avt_mb):
		""" 一局完了之后玩家同意继续游戏 """
		if self.state == 1:
			return
		idx = -1
		for i, p in enumerate(self.players_list):
			if p and p.userId == avt_mb.userId:
				idx = i
				self.playerCount += 1
				break

		if self.playerCount == 1:
			self.prepare_ts = time.time()
			DEBUG_MSG("prepare_ts:{0}".format(self.prepare_ts))
			if self.current_round > 0:
				self.prepare_timer = self.addTimer(const.CREATE_ROOM_WAIT_TIMER, 0, const.TIMER_TYPE_PREPARE)

		if idx not in self.confirm_next_idx:
			self.confirm_next_idx.append(idx)
			for p in self.players_list:
				if p and p.idx != idx:
					p.mb.readyForNextRound(idx)
				else:
					p.mb.readyForTime(math.floor(self.prepare_ts))	

		if len(self.confirm_next_idx) == self.player_num and self.isFull:
			if self.current_round == 0 and self.is_agent == 1 and self.agent:
				try:
					self.agent.mb.quitRoomSucceed()
					leave_tips = "您代开的房间已经开始游戏, 您已被请离.\n房间号【{}】".format(self.roomID)
					self.agent.mb.showTip(leave_tips)
				except:
					pass
			self.startGame()

	def record_round_result(self):
		# 玩家记录当局战绩
		d = datetime.fromtimestamp(time.time())
		round_result_d = {
			'date': '-'.join([str(d.year), str(d.month), str(d.day)]),
			'time': ':'.join([str(d.hour), str(d.minute)]),
			'round_record': [p.get_round_result_info() for p in self.origin_players_list if p],
		}

		# 第一局结束时push整个房间所有局的结构, 以后就增量push
		if self.current_round == 1:
			game_result_l = [[round_result_d]]
			for p in self.players_list:
				if p:
					p.record_all_result(game_result_l)
		else:
			for p in self.players_list:
				if p:
					p.record_round_game_result(round_result_d)

	def check_same_ip(self):
		ip_list = []
		for p in self.players_list:
			if p and p.mb and p.ip != '0.0.0.0':
				ip_list.append(p.ip)
			else:
				ip_list.append(None)

		tips = []
		checked = []
		for i in range(self.player_num):
			if ip_list[i] is None or i in checked:
				continue
			checked.append(i)
			repeat = []
			repeat.append(i)
			for j in range(i+1, self.player_num):
				if ip_list[j] is None or j in checked:
					continue
				if ip_list[i] == ip_list[j]:
					repeat.append(j)
			if len(repeat) > 1:
				name = []
				for k in repeat:
					checked.append(k)
					name.append(self.players_list[k].nickname)
				tip = '和'.join(name) + '有相同的ip地址'
				tips.append(tip)
		if tips:
			tips = '\n'.join(tips)
			# DEBUG_MSG(tips)
			for p in self.players_list:
				if p and p.mb:
					p.mb.showTip(tips)

	def apply_dismiss_room(self, avt_mb):
		""" 游戏开始后玩家申请解散房间 """
		self.dismiss_room_ts = time.time()
		src = None
		for i, p in enumerate(self.players_list):
			if p.userId == avt_mb.userId:
				src = p
				break

		# 申请解散房间的人默认同意
		self.dismiss_room_from = src.idx
		self.dismiss_room_state_list[src.idx] = 1

		self.dismiss_timer = self.addTimer(const.DISMISS_ROOM_WAIT_TIME, 0, const.TIMER_TYPE_DISMISS_WAIT)

		for p in self.players_list:
			if p and p.mb and p.userId != avt_mb.userId:
				p.mb.req_dismiss_room(src.idx)

	def vote_dismiss_room(self, avt_mb, vote):
		""" 某位玩家对申请解散房间的投票 """
		src = None
		for p in self.players_list:
			if p and p.userId == avt_mb.userId:
				src = p
				break

		self.dismiss_room_state_list[src.idx] = vote
		for p in self.players_list:
			if p and p.mb:
				p.mb.vote_dismiss_result(src.idx, vote)

		yes = self.dismiss_room_state_list.count(1)
		no = self.dismiss_room_state_list.count(2)
		if yes >= 3:
			self.delTimer(self.dismiss_timer)
			self.dismiss_timer = None
			self.dropRoom()

		if no >= 2:
			self.delTimer(self.dismiss_timer)
			self.dismiss_timer = None
			self.dismiss_room_from = -1
			self.dismiss_room_ts = 0
			self.dismiss_room_state_list = [0,0,0,0]

	def notify_player_online_status(self, userId, status):
		src = -1
		for idx, p in enumerate(self.players_list):
			if p and p.userId == userId:
				p.online = status
				src = idx
				break

		if src == -1:
			return

		for idx, p in enumerate(self.players_list):
			if p and p.mb and p.userId != userId:
				p.mb.notifyPlayerOnlineStatus(src, status)

	# 判断玩家吃碰其他玩家的次数
	def allFullPlyer(self, idx, last_idx):
		self.full_list[idx][last_idx] += 1
		DEBUG_MSG("allFullPlyer full_list: {0}".format(self.full_list))
		for i, p in enumerate(self.players_list):
			if p and i == idx:
				for j in range(len(self.full_list[idx])):
					if self.full_list[idx][j] >= 2:
						for k in range(len(self.full_list[idx])):
							if j != k and self.full_list[idx][k] != 0:
								return
						DEBUG_MSG("chipeng 111111111 {0}".format(j))
						p.mb.all_full_plyer(j, self.full_list[idx][j], 0)

			if p and i == last_idx:
				for j in range(len(self.full_list[idx])):
					if self.full_list[idx][j] >= 2:
						for k in range(len(self.full_list[idx])):
							if j != k and self.full_list[idx][k] != 0:
								return
						DEBUG_MSG("chipeng 222222222 {0}".format(idx))
						p.mb.all_full_plyer(idx, self.full_list[idx][j], 1)
