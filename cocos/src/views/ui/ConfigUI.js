// var UIBase = require("src/views/ui/UIBase.js")
// cc.loader.loadJs("src/views/ui/UIBase.js")
var ConfigUI = UIBase.extend({
	ctor:function() {
		this._super();
		this.resourceFilename = "res/ui/ConfigUI.json";
	},

	initUI:function(){
		this.gameconfig_panel = this.rootUINode.getChildByName("gameconfig_panel");
		var player = h1global.entityManager.player();
		var self = this;
		this.gameconfig_panel.getChildByName("return_btn").addTouchEventListener(function(sender, eventType){
			if(eventType == ccui.Widget.TOUCH_ENDED){
				self.hide();
			}
		});

		this.gameconfig_panel.getChildByName("music_slider").addTouchEventListener(function(sender, eventType){
			if(eventType == ccui.Widget.TOUCH_ENDED){
			// if(eventType == ccui.Slider.EVENT_PERCENT_CHANGED){
				cc.audioEngine.setMusicVolume(sender.getPercent()*0.01);
				cc.sys.localStorage.setItem("MUSIC_VOLUME", sender.getPercent());
			}
		});
		this.gameconfig_panel.getChildByName("music_slider").setPercent(cc.sys.localStorage.getItem("MUSIC_VOLUME") * 100);

		this.gameconfig_panel.getChildByName("effect_slider").addTouchEventListener(function(sender, eventType){
			if(eventType == ccui.Widget.TOUCH_ENDED){
			// if(eventType == ccui.Slider.EVENT_PERCENT_CHANGED){
				cc.audioEngine.setEffectsVolume(sender.getPercent()*0.01);
				cc.sys.localStorage.setItem("EFFECT_VOLUME", sender.getPercent());
			}
		});
		this.gameconfig_panel.getChildByName("effect_slider").setPercent(cc.sys.localStorage.getItem("EFFECT_VOLUME") * 100);

		this.gameconfig_panel.getChildByName("logout_btn").addTouchEventListener(function(sender, eventType){
			if(eventType == ccui.Widget.TOUCH_ENDED){
				cutil.lock_ui();
				player.logout();
			}
		});
	},
});