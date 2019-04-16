"use strict";
/*-----------------------------------------------------------------------------------------
 interface
 -----------------------------------------------------------------------------------------*/
var impGameRules = impGameOperation.extend({
    __init__: function () {
        this._super();
        this.allTiles = const_val.CHARACTER.concat(const_val.BAMBOO);
        this.allTiles = this.allTiles.concat(const_val.DOT);
        this.allTiles.push(const_val.DRAGON_RED);
        // this.meld_history = {};
        KBEngine.DEBUG_MSG("Create impGameRules");
    },

    getCanWinTiles: function () {
        return [];
        //听牌提示
        var canWinTiles = [];
        for (var i = 0; i < this.allTiles.length; i++) {
            var handTiles = this.curGameRoom.handTilesList[this.serverSitNum].concat([this.allTiles[i]]);
            if (this.canWin(handTiles)) {
                canWinTiles.push(this.allTiles[i]);
            }
        }
        return canWinTiles;
    },

    canConcealedKong: function (tiles) {
        //暗杠
        if (this.getOneConcealedKongNum(tiles) > 0) {
            return true;
        } else {
            return false;
        }
    },

    getOneConcealedKongNum: function (tiles) {
        var hashDict = {};
        for (var i = 0; i < tiles.length; i++) {
            if (this.curGameRoom.kingTiles.indexOf(tiles[i]) >= 0) {
                continue;
            }
            if (hashDict[tiles[i]]) {
                hashDict[tiles[i]]++;
                if (hashDict[tiles[i]] >= 4) {
                    return tiles[i];
                }
            } else {
                hashDict[tiles[i]] = 1;
            }
        }
        return 0;
    },

    canExposedKong: function (tiles, lastTile) {
        if (this.curGameRoom.kingTiles.indexOf(lastTile) >= 0) {
            return false;
        }
        var tile = 0;
        for (var i = 0; i < tiles.length; i++) {
            if (tiles[i] == lastTile) {
                tile++;
            }
        }
        if (tile >= 3) {
            return true;
        }
        return false;
    },

    canSelfExposedKong: function (upTilesList, drawTile) {
        if (this.getSelfExposedKongIdx(upTilesList, drawTile) >= 0) {
            return true;
        }
        return false;
    },

    getSelfExposedKongIdx: function (upTilesList, drawTile) {
        if (this.curGameRoom.kingTiles.indexOf(drawTile) >= 0) {
            return -1;
        }
        for (var i = 0; i < upTilesList.length; i++) {
            if (upTilesList[i].length == 3 && drawTile == upTilesList[i][0] &&
                upTilesList[i][0] == upTilesList[i][1] && upTilesList[i][1] == upTilesList[i][2]) {
                return i;
            }
        }
        return -1;
    },

    canSelfRiskKong: function (upTilesList, handTiles) {
        if (upTilesList.length == 0) {return -1;}
        var upKongTile = [];
        for (var i = 0; i < upTilesList.length; i++) {
            if (upTilesList[i].length == 3 && upTilesList[i][0] == upTilesList[i][1] && upTilesList[i][1] == upTilesList[i][2]) {
                upKongTile.push(upTilesList[i][0]);
            }
        }

        if (upKongTile.length == 0) {
            return -1;
        }else{
            for (var i = 0; i < handTiles.length; i++) {
                if (upKongTile.indexOf(handTiles[i]) >= 0) {
                    return i;
                }
            }
        }
        return -1;
    },

    canPong: function (tiles, lastTile) {
        if (this.curGameRoom.kingTiles.indexOf(lastTile) >= 0) {
            return false;
        }
        // 正常碰牌逻辑
        var tile = 0;
        for (var i = 0; i < tiles.length; i++) {
            if (tiles[i] == lastTile) {
                tile++;
            }
        }
        if (tile >= 2) {
            return true;
        }
        return false;
    },

    getCanChowTilesList: function (lastTile) {
        var chowTilesList = [];
        // 下面两行其实加不加都行，该方法仅在canChow返回值为true时才会被调用
        // if (!this.canOperationByTimesLimit()) {return []}
        // if (!this.canOperationByKingTile()) {return []}
        if (lastTile == this.curGameRoom.kingTile) {return []}
        if (lastTile >= 30) {
            return chowTilesList;
        }
        var tiles = this.curGameRoom.handTilesList[this.serverSitNum];
        var neighborTileNumList = [0, 0, 1, 0, 0];
        for (var i = 0; i < tiles.length; i++) {
            if (tiles[i] - lastTile >= -2 && tiles[i] - lastTile <= 2 && tiles[i] != this.curGameRoom.kingTile) {
                neighborTileNumList[tiles[i] - lastTile + 2]++;
            }
        }
        for (var i = 0; i < 3; i++) {
            var tileList = [];
            for (var j = i; j < i + 3; j++) {
                if (neighborTileNumList[j] > 0) {
                    tileList.push(lastTile - 2 + j);
                } else {
                    break;
                }
            }
            // 三张连续的牌
            if (tileList.length >= 3) {
                chowTilesList.push(tileList);
            }
        }
        return chowTilesList;
    },

    canChow: function (tiles, lastTile, seatNum) {
        // if (!this.canOperationByTimesLimit()) {return false}
        // if (!this.canOperationByKingTile()) {return false}
        if (lastTile == this.curGameRoom.kingTile) {return false}
        if (this.curGameRoom.lastDiscardTileFrom != (seatNum + 3) % 4) {
            return false
        }
        if (lastTile >= 30) {return false;}
        var neighborTileNumList = [0, 0, 1, 0, 0];
        for (var i = 0; i < tiles.length; i++) {
            if (tiles[i] - lastTile >= -2 && tiles[i] - lastTile <= 2 && tiles[i] != this.curGameRoom.kingTile) {
                neighborTileNumList[tiles[i] - lastTile + 2]++;
            }
        }
        for (var i = 0; i < 3; i++) {
            var tileNum = 0
            for (var j = i; j < i + 3; j++) {
                if (neighborTileNumList[j] > 0) {
                    tileNum++;
                } else {
                    break;
                }
            }
            // 三张连续的牌
            if (tileNum >= 3) {
                return true;
            }
        }
        return false;
    },

    canWin: function (handTiles, finalTile, win_op) {
        var isDrawWin = (win_op == const_val.OP_DRAW_WIN || (win_op == const_val.OP_FINAL_WIN && this.curGameRoom.lastDiscardTileFrom == this.serverSitNum)) ? true : false 
        var isGunWin = (win_op == const_val.OP_GIVE_WIN || (win_op == const_val.OP_FINAL_WIN && this.curGameRoom.lastDiscardTileFrom != this.serverSitNum)) ? true : false 
        var handCopyTile = handTiles.concat([])
        handCopyTile.splice(handCopyTile.indexOf(finalTile), 1)
        // if (isGiveWin && handTiles.length == 2 && this.curGameRoom.kingTiles.indexOf(handCopyTile[0]) >= 0) {
        //     return false
        // }

        if (finalTile == this.curGameRoom.kingTiles[0] && isGunWin) {
            return false
        }

        for (var i = 0; i < handTiles.length; i++) {
            var tile = handTiles[i]
            if (const_val.SEASON.indexOf(tile) >= 0 && const_val.FLOWER.indexOf(tile) >= 0) {
                cc.log("can not win,bcz of have season or flower.")
                return false
            }
        }
        var copyTiles = handTiles.concat([]).sort(function (a, b) {
            return a - b;
        })
        var results = this.getCanWinQuantity(copyTiles, finalTile, win_op, isDrawWin, isGunWin)
        return results;
    },

    getCanWinQuantity: function (handTiles, finalTile, win_op, isDrawWin, isGunWin) {

        //测试样例
        // this.curGameRoom.kingTiles = [24]
        // handTiles = [24,2,4,4,4,4,6,7,7,12,12,21,21,6]
        // var discardTilesList = this.curGameRoom.discardTilesList
        // var upTilesOpsList = this.curGameRoom.upTilesOpsList
        // var cutIdxsList = this.curGameRoom.cutIdxsList
        // var wreaths = this.curGameRoom.wreathsList[this.serverSitNum]
        // var p_wind = this.curGameRoom.playerWindList[this.serverSitNum]
        // var prevailing_wind = this.curGameRoom.prevailing_wind
        // var uptiles = []
        // var isGiveWin = false  //是否能放炮胡
        // var isSelfWin = false // 是否自摸
        // var isHuandaWin = false //是否还搭

        cc.log(handTiles, finalTile, win_op)
        var discardTilesList = this.curGameRoom.discardTilesList
        var upTilesOpsList = this.curGameRoom.upTilesOpsList
        var cutIdxsList = this.curGameRoom.cutIdxsList
        var wreaths = this.curGameRoom.wreathsList[this.serverSitNum]
        var p_wind = this.curGameRoom.playerWindList[this.serverSitNum]
        var prevailing_wind = this.curGameRoom.prevailing_wind
        var uptiles = this.curGameRoom.upTilesList[this.serverSitNum]
        var isGiveWin = false  //是否能放炮胡
        var isSelfWin = false // 是否自摸
        var isHuandaWin = false //是否还搭

        function removeCheckPairWin(handTilesButKing, removeList, useKingNum, kingTilesNum) {
            if (useKingNum <= kingTilesNum) {
                var tryHandTilesButKing = handTilesButKing.concat([])
                for (var i = 0; i < removeList.length; i++) {
                    var t = removeList[i]
                    if (t != -1) {
                        tryHandTilesButKing.splice(tryHandTilesButKing.indexOf(t), 1)
                    }
                }
                if (cutil.meld_with_pair_need_num(tryHandTilesButKing, {}) <= kingTilesNum - useKingNum) {
                    return true
                }
            }
            return false
        }

        function removeCheckOnlyWin(handTilesButKing, removeList, useKingNum, kingTilesNum) {
            if (useKingNum <= kingTilesNum) {
                var tryHandTilesButKing = handTilesButKing.concat([])
                for (var i = 0; i < removeList.length; i++) {
                    var t = removeList[i]
                    if (t != -1) {
                        tryHandTilesButKing.splice(tryHandTilesButKing.indexOf(t), 1)
                    }
                }
                if (cutil.meld_only_need_num(tryHandTilesButKing, {}) <= kingTilesNum - useKingNum) {
                    return true
                }
            }
            return false
        }

        var quantity = 0 //分数
        var stand = 1 //台数 坐台为一台        
        var classifyList = cutil.classifyTiles(handTiles, this.curGameRoom.kingTiles)
        var kingTilesNum = classifyList[0].length
        var handTilesButKing = []
        var kingTile =  this.curGameRoom.kingTiles[0]
        var kingTileDict = cutil.getTileNumDict(classifyList[0])
        for (var i = 1; i < classifyList.length; i++) {
            handTilesButKing = handTilesButKing.concat(classifyList[i])
        }
        cc.log(handTilesButKing, cutil.meld_with_pair_need_num(handTilesButKing, {}), kingTilesNum)
        cc.log("坐台为 1台")
        if(kingTilesNum == 0 || kingTilesNum == 1){ //无搭和一搭加一台
            stand += 1
            cc.log("无搭和一搭 1台")
        }else if (kingTilesNum == 2){ //两搭为两台
            stand += 2
            cc.log("两搭 2台")
        }
        if (win_op == const_val.OP_WREATH_WIN) { //8 张花
            if (wreaths.length == 8) {                
                cc.log('8张花胡')
                var wreathsStands = cutil.getWreathQuantity(wreaths, p_wind)
                quantity += wreathsStands[0]
                stand += wreathsStands[1]
                cc.log('花台数 quantity:' + String(wreathsStands[0]) + "  stand: " + String(wreathsStands[1]))
            }
        } else if (handTiles.length % 3 == 2) { //其他3X2胡

            //抛百搭不能放炮胡
            if (isGunWin && kingTilesNum > 0 && this.curGameRoom.leftTileNum > 1){
                if (cutil.getCheckWinThorw(handTiles, finalTile, this.curGameRoom.kingTiles)){
                    cc.log("抛百搭不能放炮胡")
                    return false
                }
            }

            cc.log("七星：",cutil.getStarType(handTilesButKing, kingTileDict, finalTile, isDrawWin))
            //清老头
            if(cutil.getTileColorType(handTilesButKing, uptiles) == const_val.SAME_HONOR
                && (cutil.meld_with_pair_need_num(handTilesButKing, {}) <= kingTilesNum || cutil.is7DoubleWin(handTiles, handTilesButKing, kingTilesNum))) {
                quantity += 1000;
                isGiveWin = true;
                isSelfWin = true;
                cc.log("清老头,台数:" + String(quantity))
            } else if(cutil.getAllColorType(uptiles, handTilesButKing)){//乱老头
                quantity += 500;
                isGiveWin = true;
                isSelfWin = true;
                cc.log("乱老头,台数:" + String(quantity))
            }else if(cutil.is7DoubleWin(handTiles, handTilesButKing, kingTilesNum)){
                if(kingTilesNum > 0){
                    quantity += 70
                }else{
                    quantity += 170
                }
                isGiveWin = true;
                isSelfWin = true;
                cc.log('七对头, 台数 70+')
            }else if ((cutil.getStarType(handTilesButKing, kingTileDict, finalTile, isDrawWin)).length > 0){
                quantity += 50
                isGiveWin = true;
                isSelfWin = true;
                cc.log('十三不搭, 台数 50+')
            }else if (cutil.meld_with_pair_need_num(handTilesButKing, {}) <= kingTilesNum) {
                //碰碰胡?
                var isPongPongWin = cutil.checkIsPongPongWin(handTilesButKing, uptiles, kingTilesNum)
                if (isPongPongWin) {
                    if(kingTilesNum > 0){
                        quantity += 50
                    }else{
                        quantity += 100
                    }
                    isGiveWin = true
                    cc.log('碰碰胡,台数 50+')
                }
                // 天胡
                var discardNum = cutil.getDiscardNum(discardTilesList, upTilesOpsList, cutIdxsList, this.serverSitNum)
                if (discardNum <= 0 && this.serverSitNum == this.curGameRoom.dealerIdx) {
                    quantity += 150
                    cc.log('天胡,台数 150')
                }else{
                    quantity += 150                    
                    isSelfWin = true;
                    cc.log('地胡,台数 150')
                }
                
                //杠上开花
                if (win_op == const_val.OP_DRAW_WIN && cutil.getNearlyKongType(upTilesOpsList, discardTilesList, cutIdxsList, this.serverSitNum) > 0) {
                    quantity += 50
                    cc.log('杠上开花,台数 50+')
                }

                //海捞
                if (this.curGameRoom.leftTileNum <= 0) {
                    quantity += 150
                    isGiveWin = true
                    cc.log('海捞胡,台数 150台')
                }
                //大吊
                if (handTiles.length == 2) {
                    if(kingTilesNum > 0){
                        quantity += 50
                    }else{
                        quantity += 100
                    }
                    isGiveWin = true
                    cc.log('大吊,台数 50+')
                }
                //清一色 混一色
                var colorType = cutil.getTileColorType(handTilesButKing, uptiles)
                if (colorType == const_val.SAME_SUIT) {
                    quantity += 150
                    isGiveWin = true
                    cc.log("清一色,台数 150")
                } else if (colorType == const_val.MIXED_ONE_SUIT) {
                    quantity += 70
                    isGiveWin = true
                    cc.log("混一色,台数 70")
                }

                // 座风三个为一台               
                var sit_wind = const_val.WINDS[(this.serverSitNum - this.curGameRoom.dealerIdx + 4)%4];
                var isSitWind = cutil.checkIsSitWind(sit_wind, uptiles, handTiles, handTilesButKing, kingTilesNum, this.curGameRoom.kingTiles);
                if (isSitWind > 0){
                    if (this.curGameRoom.game_mode == 0){
                        stand += 2;
                    }else if(this.curGameRoom.game_mode == 1){
                        stand += 1;
                    }
                    isGiveWin = true;
                    cc.log("座风 台数: 1 or 2台")
                }

                //东风碰出或暗刻
                var isEastWind = cutil.checkIsEastWind(const_val.WIND_EAST, uptiles, handTiles, handTilesButKing, kingTilesNum, this.curGameRoom.kingTiles);
                if (isEastWind > 0 && sit_wind != const_val.WIND_EAST) {
                    stand += 1;
                    isGiveWin = true;
                    cc.log("碰出东风 台数: 1台")
                }

                // 中发白
                var isWordColor = cutil.checkIsWordColor(uptiles, handTiles, handTilesButKing, kingTilesNum, this.curGameRoom.kingTiles);
                if (isWordColor > 0){
                    stand += 1;
                    isGiveWin = true;
                    cc.log("中发白: 1台");
                }

                //还搭  朋胡 抛百搭
                var friend_win = false
                if (kingTilesNum > 0 && kingTilesNum < 3) {
                    //还搭  抛百搭
                    if (cutil.meld_with_pair_need_num(handTilesButKing, {}) < kingTilesNum){
                        stand += 1
                        isHuandaWin = true
                        cc.log("huan da: 1")                       
                    }

                    var series_win = true
                    var seriesDict = cutil.getRemoveMatchOrderDict(handTilesButKing, finalTile, this.curGameRoom.kingTiles)
                    for (var key in seriesDict) {
                        key = eval("[" + key + "]")
                        var seriesNum = seriesDict[key]
                        if (removeCheckPairWin(handTilesButKing, key, seriesNum, kingTilesNum)) {
                            series_win = false;
                            cc.log("对倒");
                            break
                        }
                    }

                    if (series_win && cutil.getFriendWin(uptiles, handTiles, handTilesButKing, kingTilesNum, sit_wind, this.curGameRoom.game_mode, prevailing_wind)){
                        stand += 1;
                        friend_win = true;
                        cc.log("peng hu: 1");
                    }
                }

                // //胡两头
                // if (finalTile < 30) {
                //     var isWinTwoSides = cutil.getRemoveTwoSides(handTilesButKing, finalTile, kingTilesNum,this.curGameRoom.kingTiles);
                //     cc.log("isSitWind: " + isSitWind + " isWordColor: " + isWordColor + "  isWinTwoSides:" + isWinTwoSides);
                //     if (isWinTwoSides){
                //         if ((isSitWind + isWordColor) >= 2 || (isSitWind > 0 && sit_wind == const_val.WIND_EAST) || friend_win){
                //             isGiveWin = true
                //             cc.log("胡两头 1台");
                //         }else{
                //             // isGiveWin = false
                //             cc.log("胡两头 不能胡");
                //         }
                //     }
                // }

                //对倒 边 夹 单吊
                //对倒
                var removeMatchOrderDict = cutil.getRemoveMatchOrderDict(handTilesButKing, finalTile, this.curGameRoom.kingTiles)
                var isMatchOrder = false
                for (var key in removeMatchOrderDict) {
                    key = eval("[" + key + "]")
                    var useKingNum = removeMatchOrderDict[key]
                    if (removeCheckPairWin(handTilesButKing, key, useKingNum, kingTilesNum)) {
                        stand += 1
                        isMatchOrder = true
                        isGiveWin = true
                        cc.log("对倒,台数 1台")
                        break
                    }
                }
                if (!isPongPongWin && !isMatchOrder) {
                    //边
                    var removeEdgeDict = cutil.getRemoveEdgeDict(handTilesButKing, finalTile, this.curGameRoom.kingTiles)
                    var isEdge = false
                    for (var key in removeEdgeDict) {
                        key = eval("[" + key + "]")
                        useKingNum = removeEdgeDict[key]
                        if (removeCheckPairWin(handTilesButKing, key, useKingNum, kingTilesNum)) {
                            stand += 1
                            isEdge = true
                            cc.log("边,台数 1台")
                            break
                        }
                    }
                    // 夹
                    var isMid = false
                    if (!isEdge) {
                        var removeMidDict = cutil.getRemoveMidDict(handTilesButKing, finalTile, this.curGameRoom.kingTiles)
                        for (var key in removeMidDict) {
                            key = eval("[" + key + "]")
                            useKingNum = removeMidDict[key]
                            if (removeCheckPairWin(handTilesButKing, key, useKingNum, kingTilesNum)) {
                                stand += 1
                                isMid = true
                                cc.log("夹,台数 1台")
                                break
                            }
                        }
                    }
                    // 单吊
                    var isSingle = false;
                    if (!isEdge && !isMid) {
                        var removeSingleCraneDict = cutil.getRemoveSingleCraneDict(handTilesButKing, finalTile, this.curGameRoom.kingTiles)
                        for (var key in removeSingleCraneDict) {
                            key = eval("[" + key + "]")
                            useKingNum = removeSingleCraneDict[key]
                            if (removeCheckOnlyWin(handTilesButKing, key, useKingNum, kingTilesNum)) {
                                stand += 1
                                isSingle = true
                                cc.log("单吊,台数 1台")
                                break
                            }
                        }
                    }

                    // 胡两头
                    if (!isEdge && !isMid && !isSingle) {
                        isGiveWin = false
                        if ((isSitWind + isWordColor) >= 2 || (isSitWind > 0 && sit_wind == const_val.WIND_EAST) || friend_win){
                            isGiveWin = true
                            cc.log("胡两头 1台");
                        }else{
                            cc.log("胡两头 不能胡");
                        }
                    }
                }
                //花 手牌 桌牌 非胡台数
                var wreathsStands = cutil.getWreathQuantity(wreaths, p_wind)
                quantity += wreathsStands[0]
                stand += wreathsStands[1]
                cc.log('花台数 quantity:' + String(wreathsStands[0]) + "  stand: " + String(wreathsStands[1]))

                //自摸
                if (isDrawWin) {
                    stand += 1
                    isSelfWin = true;
                    cc.log('自摸胡,台数 1台')
                }

                if (win_op == const_val.OP_KONG_WIN) {
                    isSelfWin = true;
                    cc.log('抢杠胡')
                }
            }

            if (win_op == const_val.OP_KONG_WIN) {
                quantity += 100
                cc.log('抢杠胡,台数 100台')
            }
        }
        cc.log("quantity :" + quantity + "  stand : "+ stand + " isGiveWin: " + isGiveWin + " isHuandaWin: " + isHuandaWin);
        var quantities = quantity + stand;      
        if (isGiveWin && !isHuandaWin && quantities >= 4 && (win_op == const_val.OP_GIVE_WIN || (win_op == const_val.OP_FINAL_WIN && this.curGameRoom.lastDiscardTileFrom != this.serverSitNum))) {
            cc.log("canWin 放炮胡")
            return true;
        }else if (isSelfWin){
            cc.log("canWin 自模糊")
            return true; 
        }else{
            return false;
        } 
    },

});
