var SettlementUI = UIBase.extend({
	ctor:function() {
		this._super();
		this.resourceFilename = "res/ui/SettlementUI.json";
	},
	initUI:function(){
		var player = h1global.entityManager.player();
		var self = this;
		var confirm_btn = this.rootUINode.getChildByName("confirm_btn");
		function confirm_btn_event(sender, eventType){
			if(eventType == ccui.Widget.TOUCH_ENDED){
				// TEST:
				// self.hide();
				// h1global.curUIMgr.gameroomprepare_ui.show();
				// h1global.curUIMgr.gameroom_ui.hide();
				// return;
				self.hide();

				//重新开局
				player.curGameRoom.updatePlayerState(player.serverSitNum, 1);
				h1global.curUIMgr.gameroomprepare_ui.show();
				h1global.curUIMgr.gameroom_ui.hide();
				player.roundEndCallback();
			}
		}
		confirm_btn.addTouchEventListener(confirm_btn_event);
		this.kongTilesList = [[], [], [], []];

		var settlement_panel = this.rootUINode.getChildByName("settlement_panel");
		var settlement_bg_panel = this.rootUINode.getChildByName("settlement_bg_panel");
		var show_btn = this.rootUINode.getChildByName("show_btn");
		var hide_btn = this.rootUINode.getChildByName("hide_btn");
		show_btn.addTouchEventListener(function(sender, eventType){
			if(eventType == ccui.Widget.TOUCH_ENDED){
				show_btn.setVisible(false);
				hide_btn.setVisible(true);
				settlement_panel.setVisible(true);
				settlement_bg_panel.setVisible(true);
			}
		});
		show_btn.setVisible(false);
		hide_btn.addTouchEventListener(function(sender, eventType){
			if(eventType == ccui.Widget.TOUCH_ENDED){
				show_btn.setVisible(true);
				hide_btn.setVisible(false);
				settlement_panel.setVisible(false);
				settlement_bg_panel.setVisible(false);
			}
		});
	},
	
	show_by_info:function(roundRoomInfo, confirm_btn_func){
		cc.log("结算==========>:")
		cc.log("roundRoomInfo :  ",roundRoomInfo)
		var self = this;	
		this.show(function(){
			self.player_tiles_panels = [];
			self.player_tiles_panels.push(self.rootUINode.getChildByName("settlement_panel").getChildByName("victory_item_panel1"));
			self.player_tiles_panels.push(self.rootUINode.getChildByName("settlement_panel").getChildByName("victory_item_panel2"));
			self.player_tiles_panels.push(self.rootUINode.getChildByName("settlement_panel").getChildByName("victory_item_panel3"));
			self.player_tiles_panels.push(self.rootUINode.getChildByName("settlement_panel").getChildByName("victory_item_panel4"));	
			var playerInfoList = roundRoomInfo["player_info_list"];
			for(var i = 0; i < 4; i++){
				var roundPlayerInfo = playerInfoList[i];
				if (!roundPlayerInfo) {
					self.player_tiles_panels[i].setVisible(false)
					continue
				}
				self.player_tiles_panels[i].setVisible(true)
				self.update_score(roundPlayerInfo["idx"], roundPlayerInfo["score"]);  //显示分数
                self.update_player_hand_tiles(i, roundRoomInfo["player_info_list"][i]["tiles"], roundRoomInfo["win_idx"], roundRoomInfo["finalTile"]);   //显示麻将
                self.update_player_up_tiles(i, roundRoomInfo["player_info_list"][i]["concealed_kong"]);
                self.update_player_info(roundPlayerInfo["idx"]);  //idx 表示玩家的座位号                
			}

			self.update_win_type(roundRoomInfo, roundRoomInfo["result_list"]);
			self.show_title(roundRoomInfo["win_idx"])
			self.update_player_win(roundRoomInfo["win_idx"], roundRoomInfo["result_list"]);
			
			if(confirm_btn_func){
				self.rootUINode.getChildByName("confirm_btn").addTouchEventListener(function(sender, eventType){
					if(eventType ==ccui.Widget.TOUCH_ENDED){
						self.hide();
						confirm_btn_func();
					}
				});
			}
		});
	},

	show_title:function(win_idx){
		cc.log("win_idx ",win_idx);
        var title_img = this.rootUINode.getChildByName("settlement_panel").getChildByName("title_img");
        title_img.ignoreContentAdaptWithSize(true);
        if(win_idx == -1){
        	title_img.loadTexture("res/ui/SettlementUI/dogfull_title.png")
        }else if (h1global.entityManager.player().serverSitNum == win_idx) {
            //shengli
            title_img.loadTexture("res/ui/SettlementUI/win_title.png")
        } else {
            title_img.loadTexture("res/ui/SettlementUI/fail_title.png")
        }
	},

	update_player_hand_tiles:function(serverSitNum, tileList, win_idx, finalTile){
		if(!this.is_show) {return;}
		var player = h1global.entityManager.player();
		var cur_player_tile_panel = this.player_tiles_panels[serverSitNum].getChildByName("item_hand_panel");
		if(!cur_player_tile_panel){
			return;
		}
		tileList = tileList.concat([])
		if(win_idx == serverSitNum) {
            tileList.pop();
            tileList = tileList.sort(cutil.tileSortFunc);
            tileList.push(finalTile);
        }else {
            tileList = tileList.sort(cutil.tileSortFunc);
		}
		var mahjong_hand_str = "";
        cur_player_tile_panel.setPositionX((player.curGameRoom.upTilesList[serverSitNum].length * 180) + 280);
		mahjong_hand_str = "mahjong_tile_player_hand.png";
		for(var i = 0; i < 14; i++){
			var tile_img = ccui.helper.seekWidgetByName(cur_player_tile_panel, "mahjong_bg_img" + i.toString());
			tile_img.stopAllActions();
			if(tileList[i]){
				var mahjong_img = tile_img.getChildByName("mahjong_img");
				tile_img.loadTexture("Mahjong/" + mahjong_hand_str, ccui.Widget.PLIST_TEXTURE);
				tile_img.setVisible(true);
				mahjong_img.ignoreContentAdaptWithSize(true);
				mahjong_img.loadTexture("Mahjong/mahjong_big_" + tileList[i].toString() + ".png", ccui.Widget.PLIST_TEXTURE);
				mahjong_img.setVisible(true);
                if(win_idx == serverSitNum && i == tileList.length - 1){
                    tile_img.setPositionX(tile_img.getPositionX() + 20);
                }
                if(player.curGameRoom.kingTiles == tileList[i]){
                    var kingtilemark_img = ccui.ImageView.create("res/ui/GameRoomUI/kingtilemark.png");
                    // this.handTileMarksList[serverSitNum].push(kingtilemark_img);
                    kingtilemark_img.setAnchorPoint(0.0, 1.0);
                    kingtilemark_img.setPosition(cc.p(0, 90));
                    kingtilemark_img.setScale(0.7);
                    tile_img.addChild(kingtilemark_img);
                }
			} else {
				tile_img.setVisible(false);
			}
		}
	},

	update_player_up_tiles:function(serverSitNum, concealedKongList){
		if(!this.is_show) {return;}
		var player = h1global.entityManager.player();
        var cur_player_tile_panel = this.player_tiles_panels[serverSitNum].getChildByName("item_up_panel");
		// var cur_player_tile_panel = this.rootUINode.getChildByName("settlement_panel").getChildByName("player_tile_panel").getChildByName("player_up_panel");
		if(!cur_player_tile_panel){
			return;
		}
		// var mahjong_hand_str = "";
		var mahjong_up_str = "";
		var mahjong_down_str = "";
		// var mahjong_desk_str = "";
		// if(idx == 0){
		// 	mahjong_hand_str = "mahjong_tile_player_hand.png";
		// 	mahjong_up_str = "mahjong_tile_player_up.png";
		// 	mahjong_down_str = "mahjong_tile"
		// }
		for(var i = player.curGameRoom.upTilesList[serverSitNum].length * 3; i < 12; i++){
			var tile_img = ccui.helper.seekWidgetByName(cur_player_tile_panel, "mahjong_bg_img" + i.toString());
			tile_img.setVisible(false);
		}
		for(var i = 0; i < this.kongTilesList[serverSitNum].length; i++){
			this.kongTilesList[serverSitNum][i].removeFromParent();
		}
		this.kongTilesList[serverSitNum] = [];
		// mahjong_hand_str = "mahjong_tile_player_hand.png";
		mahjong_up_str = "mahjong_tile_player_up.png";
		mahjong_down_str = "mahjong_tile_player_down.png";
		// mahjong_desk_str = "mahjong_tile_player_desk.png";
		for(var i = 0; i < player.curGameRoom.upTilesList[serverSitNum].length; i++){
			for(var j = 0; j < 3; j++){
				var tile_img = ccui.helper.seekWidgetByName(cur_player_tile_panel, "mahjong_bg_img" + (3*i + j).toString());
				// tile_img.setPositionY(0);
				tile_img.setTouchEnabled(false);
				var mahjong_img = tile_img.getChildByName("mahjong_img");
				if(player.curGameRoom.upTilesList[serverSitNum][i][j]){
					tile_img.loadTexture("Mahjong/" + mahjong_up_str, ccui.Widget.PLIST_TEXTURE);
					mahjong_img.ignoreContentAdaptWithSize(true);
					mahjong_img.loadTexture("Mahjong/mahjong_small_" + player.curGameRoom.upTilesList[serverSitNum][i][j].toString() + ".png", ccui.Widget.PLIST_TEXTURE);
					mahjong_img.setVisible(true);
				} else {
					tile_img.loadTexture("Mahjong/" + mahjong_down_str, ccui.Widget.PLIST_TEXTURE);
					mahjong_img.setVisible(false);
				}
				tile_img.setVisible(true);
                if(player.curGameRoom.kingTiles == player.curGameRoom.upTilesList[serverSitNum][i][j]){
                    var kingtilemark_img = ccui.ImageView.create("res/ui/GameRoomUI/kingtilemark.png");
                    // this.handTileMarksList[serverSitNum].push(kingtilemark_img);
                    kingtilemark_img.setAnchorPoint(0.0, 1.0);
                    kingtilemark_img.setPosition(cc.p(0, 59));
                    kingtilemark_img.setScale(0.40);
                    tile_img.addChild(kingtilemark_img);
                }
			}
			if(player.curGameRoom.upTilesList[serverSitNum][i].length > 3){
				var tile_img = ccui.helper.seekWidgetByName(cur_player_tile_panel, "mahjong_bg_img" + (3*i + 1).toString());
				var kong_tile_img = tile_img.clone();
				this.kongTilesList[serverSitNum].push(kong_tile_img);
				var mahjong_img = kong_tile_img.getChildByName("mahjong_img");
				if(player.curGameRoom.upTilesList[serverSitNum][i][3]){
					kong_tile_img.loadTexture("Mahjong/" + mahjong_up_str, ccui.Widget.PLIST_TEXTURE);
					mahjong_img.ignoreContentAdaptWithSize(true);
					mahjong_img.loadTexture("Mahjong/mahjong_small_" + player.curGameRoom.upTilesList[serverSitNum][i][j].toString() + ".png", ccui.Widget.PLIST_TEXTURE);
					mahjong_img.setVisible(true);
				} else {
					if(concealedKongList[0]){
						kong_tile_img.loadTexture("Mahjong/" + mahjong_up_str, ccui.Widget.PLIST_TEXTURE);
						mahjong_img.ignoreContentAdaptWithSize(true);
						mahjong_img.loadTexture("Mahjong/mahjong_small_" + concealedKongList[0].toString() + ".png", ccui.Widget.PLIST_TEXTURE);
						concealedKongList.splice(0, 1);
						mahjong_img.setVisible(true);
					} else {
						kong_tile_img.loadTexture("Mahjong/" + mahjong_down_str, ccui.Widget.PLIST_TEXTURE);
						mahjong_img.setVisible(false);
					}
				}
				kong_tile_img.setPositionY(kong_tile_img.getPositionY() + 16);
				kong_tile_img.setVisible(true);
				cur_player_tile_panel.addChild(kong_tile_img);
                if(player.curGameRoom.kingTiles == player.curGameRoom.upTilesList[serverSitNum][i][j]){
                    var kingtilemark_img = ccui.ImageView.create("res/ui/GameRoomUI/kingtilemark.png");
                    // this.handTileMarksList[serverSitNum].push(kingtilemark_img);
                    kingtilemark_img.setAnchorPoint(0.0, 1.0);
                    kingtilemark_img.setPosition(cc.p(0, 59));
                    kingtilemark_img.setScale(0.40);
                    tile_img.addChild(kingtilemark_img);
                }
			}
		}
	},

	update_player_info:function(serverSitNum){
		if(!this.is_show) {return;}
		cc.log("update_player_info", serverSitNum)
		var player = h1global.entityManager.player();
		var cur_player_info_panel = this.player_tiles_panels[serverSitNum];
		cc.log(cur_player_info_panel)
		if(!cur_player_info_panel){
			return;
		}
		var playerInfo = player.curGameRoom.playerInfoList[serverSitNum];
		cur_player_info_panel.getChildByName("item_name_label").setString(playerInfo["nickname"]);
		// var frame_img = ccui.helper.seekWidgetByName(cur_player_info_panel, "frame_img");
		// cur_player_info_panel.reorderChild(frame_img, 1);
		cutil.loadPortraitTexture(playerInfo["head_icon"], function(img){
			if (cur_player_info_panel.getChildByName("item_avatar_img")) {
				cur_player_info_panel.getChildByName("item_avatar_img").removeFromParent();
			}
			var portrait_sprite  = new cc.Sprite(img);
			portrait_sprite.setName("portrait_sprite");
			portrait_sprite.setScale(67 / portrait_sprite.getContentSize().width);
            portrait_sprite.x = 145;
            portrait_sprite.y = 45;
			cur_player_info_panel.addChild(portrait_sprite);
			portrait_sprite.setLocalZOrder(-1);
			// frame_img.setLocalZOrder(0);
		}, playerInfo["uuid"].toString() + ".png");
	},

	update_player_win:function(serverSitNum, result){
		if(serverSitNum < 0 || serverSitNum > 3){
			return;
		}
		var cur_player_info_panel = this.player_tiles_panels[serverSitNum];
		var win_type_img_list = []
		for (var i = 1; i <= 7; i++) {
			var img = cur_player_info_panel.getChildByName("item_card_type_img" + String(i))
			win_type_img_list.push(img)
		}
		var index = 0
		for (var i = 0; i < result.length; i++) {
			if (index >= win_type_img_list.length) {break}
			if (result[i]) {
				win_type_img_list[index].loadTexture("res/ui/SettlementUI/win_type_" + String(i) +".png")
				win_type_img_list[index].setVisible(true)
				index += 1
			}
		}
	},

	update_score:function(serverSitNum, score){
		var score_label = this.player_tiles_panels[serverSitNum].getChildByName("item_score_label");
		if(score >= 0){
			score_label.setTextColor(cc.color(62, 121, 77));
			score_label.setString("+" + score.toString());
		} else {
			score_label.setTextColor(cc.color(144, 71, 64));
			score_label.setString(score.toString());
		}
	},

	update_win_type: function(roomInfo, resultInfo){
		var from_idx = roomInfo["from_idx"];
		var win_idx = roomInfo["win_idx"];
		var win_op = roomInfo["win_op"];
		cc.log("from_idx :" + from_idx + " win_idx :" + win_idx + " win_op :" + win_op);
		if((from_idx == win_idx) && win_op == 12){
			var self_win = this.player_tiles_panels[win_idx].getChildByName("self_win");
			self_win.setVisible(true)
		}else if(win_op != -1) {
			if (resultInfo[7] != 1 ) {
				var give_gun = this.player_tiles_panels[from_idx].getChildByName("give_gun");
				give_gun.setVisible(true)
			}
			var give_win = this.player_tiles_panels[win_idx].getChildByName("give_win");
			give_win.setVisible(true)
		}
	}
});