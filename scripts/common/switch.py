# -*- coding: utf-8 -*-


PUBLISH_VERSION = 0

DEBUG_BASE = 1

PHP_SERVER_URL = 'http://10.0.0.4:9981/api/'
PHP_SERVER_SECRET = "zDYnetiVvFgWCRMIBGwsAKaqPOUjfNXS"

#计算消耗
def calc_cost(game_round, game_mode, pay_mode, player_num):
	if game_mode == 0:
		if pay_mode == 0:
			return(9999, 200)
		else:
			return(9999, 50)
	else:
		if pay_mode == 0:
			if game_round == 4:
				return(9999, 100)
			elif game_round == 8:
				return(9999, 200)
			else:
				return(9999, 400)
		else:
			if game_round == 4:
				return(9999, 25)
			elif game_round == 8:
				return(9999, 50)
			else:
				return(9999, 100)
	return (9999, 9999)