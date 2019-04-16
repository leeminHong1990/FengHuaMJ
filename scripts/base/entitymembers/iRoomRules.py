# -*- coding: utf-8 -*-

import KBEngine
from KBEDebug import *
import utility
import const
import random

class iRoomRules(object):

	def __init__(self):
		# 房间的牌堆
		self.tiles = []
		self.meld_dict = dict()

	def initTiles(self):
		# 万 条 筒
		self.tiles = const.CHARACTER * 4 + const.BAMBOO * 4 + const.DOT * 4
		# 东 西 南 北
		self.tiles += [const.WIND_EAST, const.WIND_SOUTH, const.WIND_WEST, const.WIND_NORTH] * 4
		# 中 发 白
		self.tiles += [const.DRAGON_RED, const.DRAGON_GREEN, const.DRAGON_WHITE] * 4
		# 春 夏 秋 冬
		self.tiles += [const.SEASON_SPRING, const.SEASON_SUMMER, const.SEASON_AUTUMN, const.SEASON_WINTER]
		# 梅 兰 竹 菊
		self.tiles += [const.FLOWER_PLUM, const.FLOWER_ORCHID, const.FLOWER_BAMBOO, const.FLOWER_CHRYSANTHEMUM]
		DEBUG_MSG(self.tiles)
		self.shuffle_tiles()

	def shuffle_tiles(self):
		random.shuffle(self.tiles)

	# def deal(self, kingTypeNum = 1):
	# 	self.players_list[0].tiles = [8,11,5,4,32,6,17,12,23,27,35,25,36]
	# 	self.players_list[1].tiles = [8,8,11,11,16,16,19,17,34,25,28,31,36]
	# 	self.players_list[2].tiles = [3,3,11,11,11,12,13,31,36,18,19,24,26]
	# 	self.players_list[3].tiles = [9,9,9,5,5,8,32,8,17,15,15,15,25]

	# 	self.tiles = [37,34, 28, 29, 32, 1, 37,25, 24, 19,17,34,26,28, 37,34, 28, 29, 32, 1, 37, 24, 19,26]

	# 	self.kingTiles = [3]

	def deal(self, kingTypeNum = 1):
		""" 发牌 """
		for i in range(const.INIT_TILE_NUMBER):
			for j in range(self.player_num):
				self.players_list[j].tiles.append(self.tiles[j])
			self.tiles = self.tiles[self.player_num:]

		for i, p in enumerate(self.players_list):
			DEBUG_MSG("deal{0}:{1}".format(i, p.tiles))
		""" 杠花 """
		for i in range(self.player_num):
			for j in range(len(self.players_list[i].tiles)-1, -1, -1):
				tile = self.players_list[i].tiles[j]
				if tile in const.SEASON or tile in const.FLOWER:
					del self.players_list[i].tiles[j]
					self.players_list[i].wreaths.append(tile)
					DEBUG_MSG("kong wreath{0},{1}".format(i, tile))
		""" 补花 """
		for i in range(self.player_num):
			while len(self.players_list[i].tiles) < const.INIT_TILE_NUMBER:
				if len(self.tiles) <= 0:
					break
				tile = self.tiles[0]
				self.tiles = self.tiles[1:]
				if tile in const.SEASON or tile in const.FLOWER:
					self.players_list[i].wreaths.append(tile)
					DEBUG_MSG("add wreath{0},{1}".format(i, tile))
				else:
					self.players_list[i].tiles.append(tile)
					DEBUG_MSG("add wreath_{0},{1}".format(i, tile))
		""" 财神 """
		#第一张非花牌
		for i in range(len(self.tiles)): 
			t = self.tiles[i]
			if t not in const.SEASON and t not in const.FLOWER:
				# 1-9为一圈 东南西北为一圈 中发白为一圈
				self.kingTiles = [t]
				if kingTypeNum > 1:
					if t in const.CHARACTER:
						index = const.CHARACTER.index(t)
						self.kingTiles.append(const.CHARACTER[(index + 1)%len(const.CHARACTER)])
					elif t in const.DOT:
						index = const.DOT.index(t)
						self.kingTiles.append(const.DOT[(index + 1)%len(const.DOT)])
					elif t in const.BAMBOO:
						index = const.BAMBOO.index(t)
						self.kingTiles.append(const.BAMBOO[(index + 1)%len(const.BAMBOO)])
					elif t in const.WINDS:
						index = const.WINDS.index(t)
						self.kingTiles.append(const.WINDS[(index + 1)%len(const.WINDS)])
					elif t in const.DRAGONS:
						index = const.DRAGONS.index(t)
						self.kingTiles.append(const.DRAGONS[(index + 1)%len(const.DRAGONS)])
				del self.tiles[i]
				break
		""" 整理 """
		for i in range(self.player_num):
			self.players_list[i].tidy(self.kingTiles)

	def swapTileToTop(self, tile):
		if tile in self.tiles:
			tileIdx = self.tiles.index(tile)
			self.tiles[0], self.tiles[tileIdx] = self.tiles[tileIdx], self.tiles[0]

	def winCount(self):
		pass
	
	def can_cut_after_kong(self):
		return True

	def can_discard(self, tiles, t):
		if t in tiles:
			return True
		return False

	def can_chow(self, tiles, t):		
		if t >= 30:
			return False
		neighborTileNumList = [0, 0, 1, 0, 0]
		for i in range(len(tiles)):
			if (tiles[i] - t >= -2 and tiles[i] - t <= 2):
				neighborTileNumList[tiles[i] - t + 2] += 1
		for i in range(0,3):
			tileNum = 0
			for j in range(i,i+3):
				if neighborTileNumList[j] > 0:
					tileNum += 1
				else:
					break
			if tileNum >= 3:
				return True
		return False

	def can_chow_one(self, tiles, tile_list):
		# """ 能吃 """
		if tile_list[0] >= 30:
			return False
		if sum([1 for i in tiles if i == tile_list[1]]) >= 1 and sum([1 for i in tiles if i == tile_list[2]]) >= 1:
			sortLis = sorted(tile_list)
			if (sortLis[2] + sortLis[0])/2 == sortLis[1] and sortLis[2] - sortLis[0] == 2:
				return True
		return False

	def can_pong(self, tiles, t):
		""" 能碰 """
		if t in self.kingTiles:
			return False
		return sum([1 for i in tiles if i == t]) >= 2

	def can_exposed_kong(self, tiles, t):
		""" 能明杠 """
		if t in self.kingTiles:
			return False
		return utility.get_count(tiles, t) == 3

	def can_self_exposed_kong(self, player, t):
		""" 自摸的牌能够明杠 """
		if t in self.kingTiles:
			return False
		for op in player.op_r:
			if op[0] == const.OP_PONG and op[1][0] == t:
				return True
		return False

	def can_concealed_kong(self, tiles, t):
		""" 能暗杠 """
		if t in self.kingTiles:
			return False
		return utility.get_count(tiles, t) == 4

	def can_kong_wreath(self, tiles, t):
		if t in tiles and (t in const.SEASON or t in const.FLOWER):
			return True
		return False

	def can_wreath_win(self, wreaths):
		if len(wreaths) == len(const.SEASON) + len(const.FLOWER):
			return True
		return False

	def classify_tiles(self, tiles):
		chars = []
		bambs = []
		dots  = []
		dragon_red = 0
		for t in tiles:
			if t in const.CHARACTER:
				chars.append(t)
			elif t in const.BAMBOO:
				bambs.append(t)
			elif t in const.DOT:
				dots.append(t)
			elif t == const.DRAGON_RED:
				dragon_red += 1
			else:
				DEBUG_MSG("iRoomRules classify tiles failed, no this tile %s"%t)
		return chars, bambs, dots, dragon_red

	def can_win(self, handTiles, finalTile, win_op, idx):
		isDrawWin = True if win_op == const.OP_DRAW_WIN or (win_op == const.OP_FINAL_WIN and idx == self.last_player_idx) else False
		isGunWin = True if win_op == const.OP_GIVE_WIN or (win_op == const.OP_FINAL_WIN and idx != self.last_player_idx) else False
		handCopyTiles = handTiles[:]
		handCopyTiles.remove(finalTile)		
		if self.kingTiles[0] == finalTile and isGunWin:
			return False, 0, [], 0

		p = self.players_list[idx]
		copyTiles = handTiles[:]
		copyTiles = sorted(copyTiles)
		isWin, quantity, stand, result, kongType = self.getCanWinQuantity(copyTiles, p.upTiles, p.wreaths, finalTile, p.op_r, p.wind, win_op, idx, isDrawWin, isGunWin)
		DEBUG_MSG("idx{0}can_win:{1},{2},{3},{4}".format(idx, quantity,stand, self.win_quantity, result))
		if stand < 10:
			stand = 10
		if stand < 20 and stand > 10:
			stand = 20
		quantities = quantity + stand
		DEBUG_MSG("zui zhong fenshu isWin: {0}, quantities :{1}".format(isWin, quantities))
		if isWin:
			return True, quantities, result, kongType
		return False, quantities, result, kongType

	def getCanWinQuantity (self, handTiles, uptiles, wreaths, finalTile, p_op_r, p_wind, win_op, idx ,isDrawWin, isGunWin):

		#测试样例
		# self.kingTiles = [1]
		# handTiles = [12,13,14,16,16,23,24]
		# uptiles = [[5,6,7],[7,8,9]]
		# wreaths = [41,44]
		# finalTile = 25
		# p_op_r = [(1,[23],1),(3,[34],1),(4,[23,24,25],1)]
		# p_wind = 31
		# win_op = 15
		# idx = 1
		# isDrawWin = True

		DEBUG_MSG("handTiles : {0}, uptiles: {1}, wreaths: {2} , finalTile: {3}".format(handTiles, uptiles, wreaths, finalTile))
		DEBUG_MSG("p_op_r: {0}, p_wind: {1}, win_op: {2}, idx: {3}, isDrawWin: {4}".format(p_op_r, p_wind, win_op, idx ,isDrawWin))

		result = [0] * 47  #胡牌类型
		handTiles = sorted(handTiles)
		classifyList = utility.classifyTiles(handTiles, self.kingTiles)  
		kingTilesNum = len(classifyList[0])  #百搭的数量
		handTilesButKing = []  #除百搭外的手牌
		kingDict = utility.getTile2NumDict(classifyList[0])  #百搭的dict
		isGiveWin = False  #是否能放炮胡
		isSelfWin = False  #是否自摸
		isHunadaWin = False # 是否是还搭
		kongType = 0 #杠开的类型 0：不是杠开  1：直杠或暗杠杠开  2：风险杠杠开

		for i in range(1, len(classifyList)):
			handTilesButKing.extend(classifyList[i])
		def removeCheckPairWin(handTilesButKing, removeTuple, useKingNum, kingTilesNum):
			if useKingNum <= kingTilesNum:
				tryHandTilesButKing = handTilesButKing[:]
				tryHandTilesButKing = sorted(tryHandTilesButKing)
				for t in removeTuple:
					if t != -1:
						try:
							tryHandTilesButKing.remove(t)
						except:
							DEBUG_MSG("removeCheckPairWin remove fail.{0},{1}".format(removeTuple, tryHandTilesButKing))
				if utility.meld_with_pair_need_num(tryHandTilesButKing, {}) <= kingTilesNum - useKingNum:
					return True
			return False
		def removeCheckOnlyWin(handTilesButKing, removeTuple, useKingNum, kingTilesNum):
			if useKingNum <= kingTilesNum:
				tryHandTilesButKing = handTilesButKing[:]
				tryHandTilesButKing = sorted(tryHandTilesButKing)
				for t in removeTuple:
					if t != -1:
						try:
							tryHandTilesButKing.remove(t)
						except:
							DEBUG_MSG("removeCheckOnlyWin remove fail.{0},{1}".format(removeTuple, tryHandTilesButKing))
				if utility.meld_only_need_num(tryHandTilesButKing, {}) <= kingTilesNum - useKingNum:
					return True
			return False

		#显示杠的类型
		for i in range(0, len(p_op_r))[::-1]:
			if p_op_r[i][0] == const.OP_CONCEALED_KONG:
				result[36] = 1
			elif p_op_r[i][0] == const.OP_EXPOSED_KONG:
				result[34] = 1
			elif p_op_r[i][0] == const.OP_RISK_KONG:
				result[38] = 1

		quantity = 0 #分数
		stand = 1 #台数  坐台为一台
		result[16] = 1
		DEBUG_MSG("zuotai: 1")
		if win_op == const.OP_WREATH_WIN:#8张花
			if len(wreaths) == 8:
				# 8张花胡 = 8张花(14台) + 胡(8台) = 22台
				quantities, stands= utility.getWreathQuantity(wreaths, p_wind)
				quantity += quantities
				stand += stands
				result[33] = 1
				DEBUG_MSG("wreaths quantity:{0}, stand: {1}".format(quantities, stands))
		elif len(handTiles) % 3 == 2: #其他 3x+2 胡
			#抛百搭不能放炮胡
			if isGunWin and kingTilesNum > 0 and len(self.tiles) > 0:
				if utility.getCheckWinThorw(handTiles, finalTile, self.kingTiles):
					DEBUG_MSG("pao baida buneng fangpao hu ")
					return False, 0, 0, 0, 0

			#七对头 注：需要判断finalTile最后一张牌是别人的还是自己的
			is7Double, isBrightTiles, isDarkTiles = utility.get7DoubleWin(handTiles, handTilesButKing, kingTilesNum, finalTile)
			starType = utility.getStarType(handTilesButKing, kingDict, finalTile, isDrawWin)
			if utility.getTileColorType(handTilesButKing, uptiles) == const.SAME_HONOR and (utility.meld_with_pair_need_num(handTilesButKing, {}) <= kingTilesNum or is7Double):
				quantity += 1000
				result[0] = 1   # 清老头
				DEBUG_MSG("qing laotou: 1000")

				if is7Double:
					if kingTilesNum > 0:
						quantity += 70  #七对头有搭
						result[8] = 1
						DEBUG_MSG("qiduitou youda: 70")					
					else:    
						quantity += 170  #七对头无搭
						result[8] = 1
						DEBUG_MSG("qiduitou wuda: 170")

					if isBrightTiles: 
						quantity += 50  #明炸七对头
						result[26] = 1
						DEBUG_MSG("mingzha qiduitou: 50")
					if isDarkTiles: 
						quantity += 100  #暗炸七对头
						result[27] = 1
						DEBUG_MSG("anzha qiduitou: 100")

				# 天胡 地胡
				drawNum = utility.getDiscardNum(self.op_record)
				if drawNum == 1 and len(handTiles) == 14:
					if  self.dealer_idx == idx:
						quantity += 150
						result[6] = 1  #天胡
						DEBUG_MSG("tian hu: 150")
					else:
						quantity += 150
						result[7] = 1	#地胡
						isSelfWin = True
						DEBUG_MSG("di hu: 150")

				isGiveWin = True
				isSelfWin = True
			elif is7Double:
				if kingTilesNum > 0:
					quantity += 70  #七对头有搭
					result[8] = 1
					DEBUG_MSG("qiduitou youda: 70")					
				else:    
					quantity += 170  #七对头无搭
					result[8] = 1
					DEBUG_MSG("qiduitou wuda: 170")

				if isBrightTiles: 
					quantity += 50  #明炸七对头
					result[26] = 1
					DEBUG_MSG("mingzha qiduitou: 50")
				if isDarkTiles: 
					quantity += 100  #暗炸七对头
					result[27] = 1
					DEBUG_MSG("anzha qiduitou: 100")

				#清一色 混一色
				colorType = utility.getTileColorType(handTilesButKing, uptiles)
				if colorType == const.SAME_SUIT:
					quantity += 150
					result[4] = 1
					isGiveWin = True
					DEBUG_MSG("qing yi se 150")
				elif colorType == const.MIXED_ONE_SUIT:
					quantity += 70
					result[5] = 1
					isGiveWin = True
					DEBUG_MSG("hun yi se: 70")

				# 天胡 地胡
				drawNum = utility.getDiscardNum(self.op_record)
				if drawNum == 1 and len(handTiles) == 14:
					if  self.dealer_idx == idx:
						quantity += 150
						result[6] = 1  #天胡
						DEBUG_MSG("tian hu: 150")
					else:
						quantity += 150
						result[7] = 1	#地胡
						isSelfWin = True
						DEBUG_MSG("di hu: 150")
				isGiveWin = True
				isSelfWin = True
			elif len(starType) != 0:
				if starType[0] == 0:
					quantity += 50 #十三不搭
					DEBUG_MSG("shisan buda: 50")
				elif starType[0] == 1:
					quantity += 200
					result[30] = 1  # 十三不搭缺色
					DEBUG_MSG("shisan buda quese: 200")
				elif starType[0] == 2:
					quantity += 150
					result[28] = 1  # 十三不搭暗七星
					DEBUG_MSG("shisan buda anqixing: 150")
				elif starType[0] == 3:
					quantity += 100
					result[29] = 1  # 十三不搭明七星
					DEBUG_MSG("shisan buda mingqixing: 100")
				elif starType[0] == 4:
					quantity += 300
					result[28] = 1
					result[30] = 1  # 十三不搭暗7星 缺色
					DEBUG_MSG("shisan buda: 300")
				elif starType[0] == 5:
					quantity += 250
					result[29] = 1
					result[30] = 1  # 十三不搭明7星 缺色
					DEBUG_MSG("shisan buda: 250")
				result[9] = 1

				# 天胡 地胡
				drawNum = utility.getDiscardNum(self.op_record)
				if drawNum == 1 and len(handTiles) == 14:
					if  self.dealer_idx == idx:
						quantity += 150
						result[6] = 1  #天胡
						DEBUG_MSG("tian hu: 150")
					else:
						quantity += 150
						result[7] = 1	#地胡
						isSelfWin = True
						DEBUG_MSG("di hu: 150")
				isGiveWin = True
				isSelfWin = True
			elif utility.getAllColorType(uptiles, handTilesButKing): 
				quantity += 500
				result[1] = 1  # 乱老头
				DEBUG_MSG("luan laotou: 500")

				# 天胡 地胡
				drawNum = utility.getDiscardNum(self.op_record)
				if drawNum == 1 and len(handTiles) == 14:
					if  self.dealer_idx == idx:
						quantity += 150
						result[6] = 1  #天胡
						DEBUG_MSG("tian hu: 150")
					else:
						quantity += 150
						result[7] = 1	#地胡
						isSelfWin = True
						DEBUG_MSG("di hu: 150")
				isGiveWin = True
				isSelfWin = True
			elif utility.meld_with_pair_need_num(handTilesButKing, {}) <= kingTilesNum:

				# 碰碰胡？
				isPongPongWin = utility.checkIsPongPongWin(handTilesButKing, uptiles, kingTilesNum)
				if isPongPongWin:
					if kingTilesNum > 0:
						quantity += 50
					else:
						quantity += 100
					result[2] = 1
					isGiveWin = True
					DEBUG_MSG("peng peng hu: 50+")

				# 天胡 地胡
				drawNum = utility.getDiscardNum(self.op_record)
				if drawNum == 1 and len(handTiles) == 14:
					if  self.dealer_idx == idx:
						quantity += 150
						result[6] = 1  #天胡
						DEBUG_MSG("tian hu: 150")
					else:
						quantity += 150
						result[7] = 1	#地胡
						isSelfWin = True
						DEBUG_MSG("di hu: 150")

				# 自摸
				if isDrawWin:
					stand += 1
					result[15] = 1
					isSelfWin = True
					DEBUG_MSG("zi mo: 1")

				# 抢杠胡
				if win_op == const.OP_KONG_WIN:
					isSelfWin = True

				# 杠上开花
				isKongWin, kongWinType = utility.checkIsKongDrawWin(p_op_r)
				# 连杠开花
				isSeriesKongWin = utility.checkIsSeriesKongWin(p_op_r) 
				if win_op == const.OP_DRAW_WIN and isSeriesKongWin > 0:
					if isSeriesKongWin == 1:
						quantity += 300
						kongType = 3
						DEBUG_MSG("liangge angang gangkai 300")
					elif isSeriesKongWin == 2:
						quantity += 350
						kongType = 3
						DEBUG_MSG("angang,fengxiangang gangkai 350")
					elif isSeriesKongWin == 3:
						quantity += 300
						kongType = 4
						DEBUG_MSG("zhigang,fengxiangang gangkai 300")
					elif isSeriesKongWin == 4:
						quantity += 400
						kongType = 3
						DEBUG_MSG("liangge fengxinagang gangkai 400")
					result[46] = 1
				elif win_op == const.OP_DRAW_WIN and isKongWin:
					if kongWinType == 1:
						quantity += 150
						result[37] = 1
						kongType = 1
						DEBUG_MSG("angang gang kai 50+")
					elif kongWinType == 2:
						quantity += 100
						result[35] = 1
						kongType = 1
						DEBUG_MSG("zhigang gang kai 50+")
					elif kongWinType == 3:
						quantity += 50
						result[41] = 1
						DEBUG_MSG("huagang gang kai 50+")
					elif kongWinType == 4:
						quantity += 200
						result[39] = 1
						kongType = 2
						DEBUG_MSG("fengxian gang kai 50+")
				
				# #海捞
				if len(self.tiles) <= 0:
					quantity += 150
					result[10] = 1
					isGiveWin = True
					DEBUG_MSG("haidi lao yue 150")

				#大吊车
				if len(handTiles) == 2:
					if kingTilesNum > 0:
						quantity += 50
					else:
						quantity += 100
					result[3] = 1
					isGiveWin = True
					DEBUG_MSG("da diao che 50+")

				#清一色 混一色
				colorType = utility.getTileColorType(handTilesButKing, uptiles)
				if colorType == const.SAME_SUIT:
					quantity += 150
					result[4] = 1
					isGiveWin = True
					DEBUG_MSG("qing yi se 150")
				elif colorType == const.MIXED_ONE_SUIT:
					quantity += 70
					result[5] = 1
					isGiveWin = True
					DEBUG_MSG("hun yi se: 70")

				# 座风三个为一台
				sit_wind = const.WINDS[(idx - self.dealer_idx + 4) % 4];
				isSitWind = utility.checkIsSitWind(sit_wind, uptiles, handTiles, handTilesButKing, kingTilesNum, self.kingTiles)
				if isSitWind > 0:
					if self.game_mode == 0:						
						stand += 2
					elif self.game_mode == 1:
						stand += 1
					result[25] = 1
					isGiveWin = True
					DEBUG_MSG("zuo feng: 1 or 2")

				# 判断是否有东风碰出暗刻
				if self.game_mode == 0:
					isEastWind = utility.checkIsEastWind(const.WIND_EAST, uptiles, handTiles, handTilesButKing, kingTilesNum, self.kingTiles)
					if isEastWind > 0 and sit_wind != const.WIND_EAST:
						stand += 1
						isGiveWin = True
						DEBUG_MSG("dongfeng pengchu: 1")

				# 中发白
				isWordColor, dragon_type = utility.checkIsWordColor(uptiles, handTiles, handTilesButKing, kingTilesNum, self.kingTiles)
				if isWordColor > 0:
					stand += 1			
					isGiveWin = True
					if dragon_type[0] == 1:
						result[17] = 1
					if dragon_type[1] == 1:
						result[18] = 1
					if dragon_type[2] == 1:
						result[19] = 1
					DEBUG_MSG("zhong fa bai: 1")

				#平打里面的圈风
				if self.game_mode == 1:
					isCircleWind = utility.checkIsSitWind(self.prevailing_wind, uptiles, handTiles, handTilesButKing, kingTilesNum, self.kingTiles)
					if isCircleWind > 0 :
						stand += 1
						DEBUG_MSG("quan feng: 1")

				# 还搭  抛百搭 朋胡
				friend_win = False				
				if kingTilesNum > 0 and kingTilesNum < 3:
					# 还搭  抛百搭
					DEBUG_MSG("============ {0}, {1}".format(utility.meld_with_pair_need_num(handTilesButKing, {}), kingTilesNum))
					if utility.meld_with_pair_need_num(handTilesButKing, {}) < kingTilesNum:						
						stand += 1
						result[24] = 1
						isHunadaWin = True
						DEBUG_MSG("huan da: 1")

					series_win = True
					#判断对倒，只用过朋胡的条件
					seriesDict = utility.getRemoveMatchOrderDict(handTilesButKing, finalTile, self.kingTiles)
					for key in seriesDict:
						seriesKingNum = seriesDict[key]
						if removeCheckPairWin(handTilesButKing, key, seriesKingNum, kingTilesNum):
							series_win = False
							DEBUG_MSG("dui dao")
							break
					# 朋胡
					DEBUG_MSG("############# {0}".format(utility.meld_with_pair_need_num(handTiles, {})))
					if series_win and (utility.getFriendWin(uptiles, handTiles, handTilesButKing, kingTilesNum, sit_wind, self.game_mode, self.prevailing_wind)):
						stand += 1
						result[23] = 1
						friend_win = True
						isGiveWin = True
						DEBUG_MSG("peng hu: 1")

				#胡两头
				# if finalTile < 30:
				# 	isWinTwoSides = utility.getRemoveTwoSides(handTilesButKing, finalTile, kingTilesNum,self.kingTiles)
				# 	if isWinTwoSides:
				# 		if (isSitWind + isWordColor) >= 2 or (isSitWind > 0 and sit_wind == const.WIND_EAST) or friend_win:
				# 			isGiveWin = True
				# 			DEBUG_MSG("hu liangtou: 1")
				# 		else:
				# 			# isGiveWin = False
				# 			DEBUG_MSG("buneng hu liangtou")

				#对倒 边 嵌 单吊
				#对倒				
				removeMatchOrderDict = utility.getRemoveMatchOrderDict(handTilesButKing, finalTile, self.kingTiles)
				for key in removeMatchOrderDict:
					useKingNum = removeMatchOrderDict[key]
					if removeCheckPairWin(handTilesButKing, key, useKingNum, kingTilesNum):
						stand += 1
						result[22] = 1
						DEBUG_MSG("dui dao: 1")
						break
				else:
					if not isPongPongWin:
						#边
						removeEdgeDict = utility.getRemoveEdgeDict(handTilesButKing, finalTile, self.kingTiles)
						for key in removeEdgeDict:
							useKingNum = removeEdgeDict[key]
							if removeCheckPairWin(handTilesButKing, key, useKingNum, kingTilesNum):
								stand += 1
								result[45] = 1
								DEBUG_MSG("bian: 1")
								break
						else:
							#嵌
							removeMidDict = utility.getRemoveMidDict(handTilesButKing, finalTile, self.kingTiles)
							for key in removeMidDict:
								useKingNum = removeMidDict[key]
								if removeCheckPairWin(handTilesButKing, key, useKingNum, kingTilesNum):
									stand += 1
									result[20] = 1
									DEBUG_MSG("jia: 1")
									break
							else:
								#单吊
								removeSingleCraneDict = utility.getRemoveSingleCraneDict(handTilesButKing, finalTile, self.kingTiles)
								for key in removeSingleCraneDict:
									useKingNum = removeSingleCraneDict[key]
									if removeCheckOnlyWin(handTilesButKing, key, useKingNum, kingTilesNum):
										stand += 1
										result[21] = 1
										DEBUG_MSG("dandiao: 1")
										break 
								else:
									# 胡两头
									isGiveWin = False
									if (isSitWind + isWordColor) >= 2 or (isSitWind > 0 and sit_wind == const.WIND_EAST) or friend_win:
										isGiveWin = True
										DEBUG_MSG("hu liangtou: 1")
									else:
										DEBUG_MSG("buneng hu liangtou")			

			#无搭， 一搭，二搭，三百搭， 三花三百搭
			if kingTilesNum == 0:
				stand += 1
				result[12] = 1
				DEBUG_MSG("wuda: 1")
			elif kingTilesNum == 1:
				stand += 1
				result[13] = 1
				DEBUG_MSG("yida: 1")
			elif kingTilesNum == 2:
				stand += 2
				result[14] = 1
				DEBUG_MSG("erda: 1")
			elif kingTilesNum == 3:
				if self.kingTiles[0] in const.SEASON or self.kingTiles[0] in const.FLOWER:
					quantity += 300
					result[43] = 1
					DEBUG_MSG("san hua sanbaida: 300")
				else:
					quantity += 150
					result[42] = 1
					DEBUG_MSG("san baida: 150")

			# 花 手牌 桌牌 非胡台数
			quantities, stands, four_flower= utility.getWreathQuantity(wreaths, p_wind)
			quantity += quantities
			stand += stands
			if four_flower:
				result[44] = 1
			DEBUG_MSG("wreaths quantity:{0}, stand: {1}".format(quantities, stands))

			# 抢杠胡
			if win_op == const.OP_KONG_WIN:
				quantity += 100
				result[32] = 1
				DEBUG_MSG("qiangganghu: 100" )

		#判断台数
		DEBUG_MSG("quantity: {0}, stand: {1}, {2}".format(quantity, stand, isHunadaWin))
		tatal_stands = quantity + stand
		if isGiveWin and isHunadaWin == False and tatal_stands >= self.win_quantity and (win_op == const.OP_GIVE_WIN or (win_op == const.OP_FINAL_WIN and idx != self.last_player_idx)):
			return True, quantity, stand, result, kongType
		elif isSelfWin:
			return True, quantity, stand, result, kongType
		else:
			return False, quantity, stand, result, kongType

