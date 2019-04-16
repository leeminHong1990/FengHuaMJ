"use strict";

var GameRoomEntity = KBEngine.Entity.extend({
	ctor : function(player_num)
	{
		cc.log(player_num)
		cc.log("==================")
		this._super();
		this.roomID = undefined;
		this.curRound = 0;
		this.maxRound = 4;
		this.luckyTileNum = 0;
		this.ownerId = undefined;
		this.dealerIdx = 0;
		this.isAgent = false;
		this.king_num = 1;
  		this.player_num = player_num;
  		this.win_quantity = 4;
  		this.pay_mode = 0;
  		this.game_mode = 0;

		this.agentInfo = {};
		if (player_num == 3) {
			this.playerInfoList = [null, null, null];
			this.playerStateList = [0, 0, 0];
			this.handTilesList = [[], [], []];
			this.upTilesList = [[], [], []];
			this.upTilesOpsList = [[], [], []];
			this.discardTilesList = [[], [], []];
			this.cutIdxsList = [[], [], []];
			this.wreathsList = [[], [], []];
		} else {
			this.playerInfoList = [null, null, null, null];
			this.playerStateList = [0, 0, 0, 0];
			this.handTilesList = [[], [], [], []];
			this.upTilesList = [[], [], [], []];
			this.upTilesOpsList = [[], [], [], []];
			this.discardTilesList = [[], [], [], []];
			this.cutIdxsList = [[], [], [], []];
			this.wreathsList = [[], [], [], []];
		}
		

		this.prevailing_wind = const_val.WIND_EAST
		this.playerWindList = [const_val.WIND_EAST, const_val.WIND_SOUTH, const_val.WIND_WEST, const_val.WIND_NORTH]
		this.curPlayerSitNum = 0;
		this.isPlayingGame = 0;
		this.lastDiscardTile = 0;
		this.lastDrawTile = -1
		this.lastDiscardTileFrom = -1;
		this.leftTileNum = 60;
		this.finalTileWaitIdx = -1

		this.kingTiles = [];	// 财神(多个)

		this.applyCloseLeftTime = 0;
		this.applyCloseFrom = 0;
		if (player_num == 3) {
			this.applyCloseStateList = [0, 0, 0];
		}else {
			this.applyCloseStateList = [0, 0, 0, 0];
		}

		this.waitAidList = []; // 玩家操作列表，[]表示没有玩家操作
		this.createRoomTime = 0;
		this.prepareLeftTime = 0;

		// 每局不清除的信息
		if (player_num == 3) {
			this.playerScoreList = [0, 0, 0];
		}else{
			this.playerScoreList = [0, 0, 0, 0];
		}
	    KBEngine.DEBUG_MSG("Create GameRoomEntity")
  	},

  	reconnectRoomData : function(recRoomInfo){
  		cc.log("reconnectRoomData",recRoomInfo)
  		this.curPlayerSitNum = recRoomInfo["curPlayerSitNum"];
  		this.isPlayingGame = recRoomInfo["isPlayingGame"];
  		this.playerStateList = recRoomInfo["player_state_list"];
  		this.lastDiscardTile = recRoomInfo["lastDiscardTile"];
  		this.lastDrawTile = recRoomInfo["lastDrawTile"]
  		this.lastDiscardTileFrom = recRoomInfo["lastDiscardTileFrom"];
  		this.leftTileNum = recRoomInfo["leftTileNum"];
  		this.kingTiles = recRoomInfo["kingTiles"];
  		this.prevailing_wind = recRoomInfo["prevailing_wind"];
  		this.finalTileWaitIdx = recRoomInfo["finalTileWaitIdx"];
  		for(var i = 0; i < recRoomInfo["player_advance_info_list"].length; i++){

  			var curPlayerInfo = recRoomInfo["player_advance_info_list"][i];
  			this.wreathsList[i] = curPlayerInfo["wreaths"];
  			this.playerWindList[i] = curPlayerInfo["wind"];

  			this.handTilesList[i] = curPlayerInfo["tiles"];
  			this.discardTilesList[i] = curPlayerInfo["discard_tiles"];
  			this.cutIdxsList[i] = curPlayerInfo["cut_idxs"];
 
  			for(var j = 0; j < curPlayerInfo["op_list"].length; j++){
  				var op_info = curPlayerInfo["op_list"][j]; //[opId, [tile]]
  				if(op_info["opId"] == const_val.OP_PONG){
  					this.upTilesList[i].push([op_info["tiles"][0], op_info["tiles"][0], op_info["tiles"][0]]);
  					this.upTilesOpsList[i].push([op_info]);
  				} else if(op_info["opId"] == const_val.OP_EXPOSED_KONG){
  					// 检查是否有碰过相同的牌
  					var kongIdx = h1global.entityManager.player().getSelfExposedKongIdx(this.upTilesList[i], op_info["tiles"][0]);
  					if(kongIdx >= 0){
  						// 已经碰过相同的牌，说明为自摸杠
	  					this.upTilesList[i][kongIdx].push(op_info["tiles"][0]);
	  					this.upTilesOpsList[i][kongIdx].push(op_info);
	  				} else {
	  					// 否则为普通杠
	  					this.upTilesList[i].push([op_info["tiles"][0], op_info["tiles"][0], op_info["tiles"][0], op_info["tiles"][0]]);
	  					this.upTilesOpsList[i].push([op_info]);
	  				}
  				} else if(op_info["opId"] == const_val.OP_CONCEALED_KONG){
  					this.upTilesList[i].push([0, 0, 0, op_info["tiles"][0]]);
  					this.upTilesOpsList[i].push([op_info]);
  				} else if(op_info["opId"] == const_val.OP_CHOW){
  					this.upTilesList[i].push((op_info["tiles"].concat()).sort(cutil.tileSortFunc));
  					this.upTilesOpsList[i].push([op_info]);
  				}
  			}
  		}

  		this.applyCloseLeftTime = recRoomInfo["applyCloseLeftTime"];
  		this.applyCloseFrom = recRoomInfo["applyCloseFrom"];
		this.applyCloseStateList = recRoomInfo["applyCloseStateList"];
		if(this.applyCloseLeftTime > 0){
			onhookMgr.setApplyCloseLeftTime(this.applyCloseLeftTime);
		}
		this.waitAidList = recRoomInfo["waitAidList"];

		this.updateRoomData(recRoomInfo["init_info"]);
		for(var i = 0; i < recRoomInfo["player_advance_info_list"].length; i++){
			var curPlayerInfo = recRoomInfo["player_advance_info_list"][i];
			this.playerInfoList[i]["score"] = curPlayerInfo["score"]
			this.playerInfoList[i]["total_score"] = curPlayerInfo["total_score"]
		}

		this.createRoomTime = recRoomInfo['createRoomTime']
		if (this.createRoomTime > 0) {
			onhookMgr.setCreateRoomLeftTime(this.createRoomTime);
		}

		this.prepareLeftTime = recRoomInfo['prepareTime']
		if (this.prepareLeftTime > 0) {
			onhookMgr.setCreateRoomLeftTime(this.prepareLeftTime);
		}
  	},

  	updateRoomData : function(roomInfo){
  		cc.log('updateRoomData:',roomInfo)
  		this.roomID = roomInfo["roomID"];
  		this.ownerId = roomInfo["ownerId"];
  		this.dealerIdx = roomInfo["dealerIdx"];
  		this.curRound = roomInfo["curRound"]
  		this.maxRound = roomInfo["maxRound"];
  		this.king_num = roomInfo["king_num"];
  		this.player_num = roomInfo["player_num"];
  		this.win_quantity = roomInfo["win_quantity"];
  		this.pay_mode = roomInfo["pay_mode"];
  		this.game_mode = roomInfo["game_mode"];
  		this.isAgent = roomInfo["isAgent"];
		this.agentInfo = roomInfo["agentInfo"];		

  		for(var i = 0; i < roomInfo["player_base_info_list"].length; i++){
  			this.updatePlayerInfo(roomInfo["player_base_info_list"][i]["idx"], roomInfo["player_base_info_list"][i]);
		}

		var self = this;
        if(!((cc.sys.os == cc.sys.OS_IOS && cc.sys.isNative) || (cc.sys.os == cc.sys.OS_ANDROID && cc.sys.isNative)) || switches.TEST_OPTION){
			wx.onMenuShareAppMessage({
                title: '房間號【' + self.roomID.toString() + '】', // 分享标题
                desc: '我在[奉化麻将]开了' + self.maxRound.toString() + '局的房间，快来一起玩吧', // 分享描述
                link: switches.h5entrylink, // 分享链接
			    imgUrl: '', // 分享图标
			    type: '', // 分享类型,music、video或link，不填默认为link
			    dataUrl: '', // 如果type是music或video，则要提供数据链接，默认为空
			    success: function () { 
			        // 用户确认分享后执行的回调函数
			        cc.log("ShareAppMessage Success!");
			    },
			    cancel: function () { 
			        // 用户取消分享后执行的回调函数
			        cc.log("ShareAppMessage Cancel!");
			    },
			    fail: function() {
			    	cc.log("ShareAppMessage Fail")
			    },
			});
			wx.onMenuShareTimeline({
                title: '房間號【' + self.roomID.toString() + '】', // 分享标题
                desc: '我在[奉化麻将]开了' + self.maxRound.toString() + '局的房间，快来一起玩吧', // 分享描述
                link: switches.h5entrylink, // 分享链接
			    imgUrl: '', // 分享图标
			    type: '', // 分享类型,music、video或link，不填默认为link
			    dataUrl: '', // 如果type是music或video，则要提供数据链接，默认为空
			    success: function () { 
			        // 用户确认分享后执行的回调函数
			        cc.log("onMenuShareTimeline Success!");
			    },
			    cancel: function () { 
			        // 用户取消分享后执行的回调函数
			        cc.log("onMenuShareTimeline Cancel!");
			    },
			    fail: function() {
			    	cc.log("onMenuShareTimeline Fail")
			    },
			});
		}
  	},

  	updatePlayerInfo : function(serverSitNum, playerInfo){
  		this.playerInfoList[serverSitNum] = playerInfo;
  	},

  	updatePlayerState : function(serverSitNum, state){
  		this.playerStateList[serverSitNum] = state;
  	},

  	updatePlayerOnlineState : function(serverSitNum, state){
  		this.playerInfoList[serverSitNum]["online"] = state;
  	},

  	startGame : function(kingTiles, wreathsList){
  		this.curRound = this.curRound + 1;
  		this.isPlayingGame = 1;
  		this.wreathsList = wreathsList
  		this.kingTiles = kingTiles
  		this.finalTileWaitIdx = -1
		var wreathsNum = 0
		for (var i = 0; i < wreathsList.length; i++) {
			wreathsNum += wreathsList[i].length
		}
  		if (this.player_num == 3) {
  			this.handTilesList = [	[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
								[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
								[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]];
			this.upTilesList = [[], [], []];
			this.upTilesOpsList = [[], [], []];
			this.discardTilesList = [[], [], []];
			this.cutIdxsList = [[], [], []];
			this.leftTileNum = 104 - wreathsNum;
  		} else {
  			this.handTilesList = [	[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
								[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
								[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
								[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]];
			this.upTilesList = [[], [], [], []];
			this.upTilesOpsList = [[], [], [], []];
			this.discardTilesList = [[], [], [], []];
			this.cutIdxsList = [[], [], [], []];
			this.leftTileNum = 91 - wreathsNum;
  		}	
  	},

  	endGame : function(){
  		// 重新开始准备
  		this.isPlayingGame = 0;
  		if (this.player_num == 3) {
  			this.playerStateList = [0, 0, 0];
  		} else {
  			this.playerStateList = [0, 0, 0, 0];
  		}
  	},
});