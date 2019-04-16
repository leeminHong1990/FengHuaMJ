// var UIBase = require("src/views/ui/UIBase.js")
// cc.loader.loadJs("src/views/ui/UIBase.js")
"use strict"
var CreateRoomUI = UIBase.extend({
	ctor:function() {
		this._super();
		this.resourceFilename = "res/ui/CreateRoomUI.json";
	},

	initUI:function(){
		this.pay_mode = 1; //付费方式，0代表房主支付，1代表AA支付
		this.game_mode = 0; //游戏模式，0代表冲刺模式，1代表平打模式
        this.win_num = 4; //起胡台数
		this.round_num = -1; //局数玩法，-1代表冲刺模式的200底分，4、8、16分别代表平打模式的4局、8局、16局
		this.createroom_panel = this.rootUINode.getChildByName("createroom_panel");
		this.initCreateRoomPanel();

		this.initCreateRoom();

		this.updateCardDiamond(this.pay_mode, this.game_mode, this.round_num);
        this.updateRoundNum(this.game_mode);
	},

	updateCardDiamond:function(pay_mode, game_mode, round_num){
		var tips_label = this.rootUINode.getChildByName("createroom_panel").getChildByName("tips_label");
		if(pay_mode == 0) {
			if(game_mode == 0) {
                tips_label.setString("游戏开始后，房主扣除200钻石");
            }else {
                tips_label.setString("游戏开始后，房主扣除"+ round_num * 25 +"钻石");
			}
        }else {
            if(game_mode == 0) {
                tips_label.setString("游戏开始后，每人扣除50钻石");
            }else {
                tips_label.setString("游戏开始后，每人扣除"+ round_num * 25 / 4 +"钻石");
            }
		}
	},

	initCreateRoomPanel:function(){
		var self = this;
		var return_btn = ccui.helper.seekWidgetByName(this.createroom_panel, "return_btn");
		function return_btn_event(sender, eventType){
			if (eventType == ccui.Widget.TOUCH_ENDED) {
				self.hide();
			}
		}
		return_btn.addTouchEventListener(return_btn_event);

		//付费方式
		this.pay_mode_chx_list = []
		function pay_mode_event(sender,eventType) {
			if(eventType == ccui.CheckBox.EVENT_SELECTED || eventType == ccui.CheckBox.EVENT_UNSELECTED){
				for(var i = 0; i < self.pay_mode_chx_list.length; i++){
					if(sender != self.pay_mode_chx_list[i]){
						self.pay_mode_chx_list[i].setSelected(false);
						self.pay_mode_chx_list[i].setTouchEnabled(true);
					}else {
						self.pay_mode = i;
						sender.setSelected(true);
						sender.setTouchEnabled(false);
						cc.log("pay_mode:",self.pay_mode);
						self.updateCardDiamond(self.pay_mode, self.game_mode, self.round_num);
					}
				}
			}
        }
        for(var i = 0; i < 2; i++){
			var pay_mode_chx = ccui.helper.seekWidgetByName(this.createroom_panel, "pay_mode_chx_" + String(i + 1));
			this.pay_mode_chx_list.push(pay_mode_chx);
			pay_mode_chx.addTouchEventListener(pay_mode_event);
		}
		this.pay_mode_chx_list[1].setTouchEnabled(false);
        cc.log("pay_mode:",self.pay_mode);

        //游戏模式
		this.game_mode_chx_list = [];
		function game_mode_event(sender, eventType) {
			if(eventType == ccui.CheckBox.EVENT_SELECTED || eventType == ccui.CheckBox.EVENT_UNSELECTED){
				for(var i = 0; i < self.game_mode_chx_list.length; i++){
					if(sender != self.game_mode_chx_list[i]){
						self.game_mode_chx_list[i].setSelected(false);
						self.game_mode_chx_list[i].setTouchEnabled(true);
					}else {
						self.game_mode = i;
						if(self.game_mode == 0){
							self.round_num = -1;
						}else {
							self.round_num = 4;
						}
						sender.setSelected(true);
						sender.setTouchEnabled(false);
						cc.log("game_mode:",self.game_mode);
                        self.updateRoundNum(self.game_mode);
                        self.updateCardDiamond(self.pay_mode, self.game_mode, self.round_num);
					}
				}
			}
        }
        for(var i = 0; i < 2; i++){
			var game_mode_chx = ccui.helper.seekWidgetByName(this.createroom_panel, "game_mode_chx_" + String( i + 1));
			this.game_mode_chx_list.push(game_mode_chx);
			game_mode_chx.addTouchEventListener(game_mode_event);
		}
		this.game_mode_chx_list[0].setTouchEnabled(false);
		cc.log("game_mode:",self.game_mode);

		//起胡台数
		this.win_num_chx_list = [];
		function win_num_event(sender, eventType){
			if (eventType == ccui.CheckBox.EVENT_SELECTED || eventType == ccui.CheckBox.EVENT_UNSELECTED) {
				for (var i = 0; i < self.win_num_chx_list.length; i++) {
					if (sender != self.win_num_chx_list[i]) {
						self.win_num_chx_list[i].setSelected(false);
						self.win_num_chx_list[i].setTouchEnabled(true);
					}else{
						self.win_num = 4 + i;
                        sender.setSelected(true);
						sender.setTouchEnabled(false);
						cc.log("win_num:", self.win_num);
					}
				}
			}
		}
		for (var i = 0; i < 1; i++) {
			var win_num_chx = ccui.helper.seekWidgetByName(this.createroom_panel, "win_num_chx_" + String(i+1));
			this.win_num_chx_list.push(win_num_chx);
			win_num_chx.addTouchEventListener(win_num_event);
		}
		this.win_num_chx_list[0].setTouchEnabled(false);
		cc.log("win_num:", this.win_num);

		//局数选择
		this.round_num_chx_list = [];
		function round_num_event(sender, eventType){
			if (eventType == ccui.CheckBox.EVENT_SELECTED || eventType == ccui.CheckBox.EVENT_UNSELECTED) {
				for (var i = 0; i < self.round_num_chx_list.length; i++) {
					if (sender != self.round_num_chx_list[i]) {
						self.round_num_chx_list[i].setSelected(false);
						self.round_num_chx_list[i].setTouchEnabled(true);
					}else{
						self.round_num = Math.pow(2, i + 2);
                        sender.setSelected(true);
						sender.setTouchEnabled(false);
						cc.log("round_num:", self.round_num);
                        self.updateCardDiamond(self.pay_mode, self.game_mode, self.round_num);
					}
				}
			}
		}
		for (var i = 0; i < 3; i++) {
			var round_num_chx = ccui.helper.seekWidgetByName(this.createroom_panel, "round_chx_" + String(i+1));
			this.round_num_chx_list.push(round_num_chx);
			round_num_chx.addTouchEventListener(round_num_event);
		}
		this.round_num_chx_list[0].setTouchEnabled(false);
		cc.log("round_num:", this.round_num);
	},

	updateRoundNum:function (game_mode) {
		var round_num_chx_1 = ccui.helper.seekWidgetByName(this.createroom_panel, "round_chx_1");
		var round_num_chx_2 = ccui.helper.seekWidgetByName(this.createroom_panel, "round_chx_2");
		var round_num_chx_3 = ccui.helper.seekWidgetByName(this.createroom_panel, "round_chx_3");
		var round_num_label_1 = ccui.helper.seekWidgetByName(this.createroom_panel, "round_num_label_1");
		var round_num_label_2 = ccui.helper.seekWidgetByName(this.createroom_panel, "round_num_label_2");
		var round_num_label_3 = ccui.helper.seekWidgetByName(this.createroom_panel, "round_num_label_3");
		if(game_mode == 0) {
			round_num_label_1.setString("(1冲200)");
			round_num_chx_1.setSelected(true);
			round_num_chx_2.setSelected(false);
			round_num_chx_3.setSelected(false);
			round_num_chx_1.setTouchEnabled(false);
			round_num_chx_2.setTouchEnabled(true);
			round_num_chx_3.setTouchEnabled(true);
			round_num_chx_2.setVisible(false);
			round_num_chx_3.setVisible(false);
			round_num_label_2.setVisible(false);
			round_num_label_3.setVisible(false);
		}else {
			round_num_label_1.setString("4局");
			round_num_chx_2.setVisible(true);
			round_num_chx_3.setVisible(true);
			round_num_label_2.setVisible(true);
			round_num_label_3.setVisible(true);
		}
    },


	initCreateRoom:function(){
		var self = this;
		var create_btn = ccui.helper.seekWidgetByName(this.createroom_panel, "create_btn");
		function create_btn_event(sender, eventType){
			if (eventType == ccui.Widget.TOUCH_ENDED) {
				cutil.lock_ui();
                cc.log("pay_mode:",self.pay_mode);
                cc.log("game_mode:",self.game_mode);
                cc.log("win_num:",self.win_num);
                cc.log("round_num:",self.round_num);
                h1global.entityManager.player().createRoom(4, self.win_num, self.round_num, 1, self.pay_mode, self.game_mode, 0);
				self.hide();
			}
		}
		create_btn.addTouchEventListener(create_btn_event);
	}
});