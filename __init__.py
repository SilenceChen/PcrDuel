import asyncio
import base64
import os
import random
import sqlite3
import math
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from hoshino import Service, priv
from hoshino.modules.priconne import _pcr_data_duel
from hoshino.modules.priconne import chara_duel as chara
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter
import copy
import json

sv = Service('pcr-duel', enable_on_default=True)
DUEL_DB_PATH = os.path.expanduser('~/.hoshino/pcr_duel.db')
SCORE_DB_PATH = os.path.expanduser('~/.hoshino/pcr_running_counter.db')
BLACKLIST_ID = [1000, 1072, 4031, 9000, 1069, 1073,1907,1910,1913,1914,1915,1916,1917,1919,9601,9602,9603,9604] # 黑名单ID
WAIT_TIME = 30 # 对战接受等待时间
WAIT_TIME_jy = 30 # 交易接受等待时间
DUEL_SUPPORT_TIME = 30 # 赌钱等待时间
DB_PATH = os.path.expanduser("~/.hoshino/pcr_duel.db")

#这里是参数设置区
SIGN_DAILY_LIMIT = 1  # 机器人每天签到的次数
DUEL_DAILY_LIMIT = 999 #每个人每日发起决斗上限
RESET_HOUR = 0  # 每日使用次数的重置时间，0代表凌晨0点，1代表凌晨1点，以此类推
GACHA_COST = 500  # 抽老婆需求
GACHA_COST_Fail = 200 #抽老婆失败补偿量
ZERO_GET_AMOUNT = 150  # 没钱补给量
WIN_NUM = 2 #下注获胜赢得的倍率

SHANGXIAN_NUM = 100000 #增加女友上限所需金币
WAREHOUSE_NUM = 10 #仓库增加上限
SHANGXIAN_SW = 500 #扩充女友上限，需要的声望值

BREAK_UP_SWITCH = True #分手系统开关
Zhuan_Need = 0.5 #转账所需的手续费比例
WinSWBasics = 400 #赢了获得的基础声望
LoseSWBasics = 150 #输了掉的基础声望

Remake_allow = False #是否允许重开

SW_COST = 500 #声望招募的声望需求量
DJ_NEED_SW = 2500 #加冕称帝消耗的声望
DJ_NEED_GOLD = 20000 #加冕称帝消耗的金币
FS_NEED_SW = 4000 #飞升所需的声望
FS_NEED_GOLD = 30000 #飞升所需的金币
DATE_DAILY_LIMIT = 1 #每天女友约会次数上限
GIFT_DAILY_LIMIT = 5 #每日购买礼物次数上限 
WAIT_TIME_CHANGE = 30 #礼物交换等待时间
NEED_favor = 300 #成为妻子所需要的好感，为0表示关闭
favor_reduce = 50 #当输掉女友时，损失的好感度

Suo_allow = True #是否允许梭哈
Suo = 2 #梭哈额外获取的金币倍率


#这里是庆典设置区 ~~开关类，1为开，0为关~~
Show_Cele_Not = True #查询庆典时，显示未开放的庆典
#金币庆典
Gold_Cele = 1 #群庆典初始化时，是否开启金币庆典
Gold_Cele_Num = 2 #金币庆典倍率，实际获得金币倍率为金币庆典倍率*基础倍率
#贵族签到庆典
QD_Cele = 1 #群庆典初始化时，是否开启贵族签到庆典
QD_Gold_Cele_Num = 3 #签到庆典金币倍率
QD_SW_Cele_Num = 2 #签到庆典声望倍率
#梭哈庆典
Suo_Cele = 1 #群庆典初始化时，是否开启梭哈倍率庆典
Suo_Cele_Num = 1 #梭哈额外倍率，实际获得梭哈倍率为梭哈庆典倍率*基础倍率
#免费招募庆典
FREE_DAILY = 1 #群庆典初始化时，是否开启免费招募庆典
FREE_DAILY_LIMIT = 1  # 每天免费招募的次数
#限时开放声望招募
SW_add = 0 #群庆典初始化时，是否开启无限制等级声望招募

FILE_PATH = os.path.dirname(__file__)#用于加载dlcjson
LEVEL_GIRL_NEED = {
        "1": 2,
        "2": 3,
        "3": 4,
        "4": 6,
        "5": 8,
        "6": 10,
        "7": 11,
        "8": 13,
        "9": 15,
        "10": 16,
        "20": 99
    } # 升级所需要的老婆，格式为["等级“: 需求]
LEVEL_COST_DICT = {
        "1": 0,
        "2": 100,
        "3": 300,
        "4": 500,
        "5": 1000,
        "6": 3000,
        "7": 5000,
        "8": 10000,
        "9": 15000
    } # 升级所需要的钱钱，格式为["等级“: 需求]
LEVEL_SW_NEED = {
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0,
        "6": 0,
        "7": 1000,
        "8": 1500,
        "9": 2000
    } # 升级所需要的声望，格式为["等级“: 需求]
    
RELATIONSHIP_DICT = {
        0:["初见","浣花溪上见卿卿，脸波明，黛眉轻。"],
        30:["相识","有美一人，清扬婉兮。邂逅相遇，适我愿兮。"],
        60:["熟悉","夕阳谁唤下楼梯，一握香荑。回头忍笑阶前立，总无语，也依依。"],
        100:["朋友","锦幄初温，兽烟不断，相对坐调笙。"],
        150:["朦胧","和羞走，倚门回首，却把青梅嗅。"],
        200:["喜欢","夜月一帘幽梦，春风十里柔情。"],
        300:["依恋","愿我如星君如月，夜夜流光相皎洁。"],
        500:["挚爱","江山看不尽，最美镜中人。"]
    }       

GIFT_DICT = {
        "玩偶"    :0,
        "礼服"    :1,
        "歌剧门票":2,
        "水晶球"  :3,
        "耳环"    :4,
        "发饰"    :5,
        "小裙子"  :6,
        "热牛奶"  :7,
        "书"      :8,
        "鲜花"    :9  
    }  

GIFTCHOICE_DICT={
        0:[0,2,1],
        1:[1,0,2],
        2:[2,1,0],
}    




Gift10=[
    "这个真的可以送给我吗，谢谢(害羞的低下了头)。",
    "你是专门为我准备的吗，你怎么知道我喜欢这个呀，谢谢你！",
    "啊，我最喜欢这个，真的谢谢你。"
]

Gift5=[
    "谢谢送我这个，我很开心。",
    "这个我很喜欢，谢谢。",
    "你的礼物我都很喜欢哦，谢谢。"
]

Gift2=[
    "送我的吗，谢谢你。",
    "谢谢你的礼物。",
    "为我准备了礼物吗，谢谢。"    
]

Gift1=[
    "不用为我特意准备礼物啦，不过还是谢谢你哦。",
    "嗯，谢谢。",
    "嗯，我收下了，谢谢你。"
]




Addgirlfail = [
    '你参加了一场贵族舞会，热闹的舞会场今天竟然没人同你跳舞。',
    '你邀请到了心仪的女友跳舞，可是跳舞时却踩掉了她的鞋，她生气的离开了。',
    '你为这次舞会准备了很久，结果一不小心在桌子上睡着了，醒来时只看到了过期的邀请函。',
    '你参加了一场贵族舞会，可是舞会上只有一名男性向你一直眨眼。',
    '你准备参加一场贵族舞会，可惜因为忘记穿礼服，被拦在了门外。',
    '你沉浸在舞会的美食之中，忘了此行的目的。',
    '你本准备参加舞会，却被会长拉去出了一晚上刀。',
    '舞会上你和另一个贵族发生了争吵，你一拳打破了他的鼻子，两人都被请出了舞会。',
    '舞会上你很快约到了一名女伴跳舞，但是她不是你喜欢的类型。',
    '你约到了一位心仪的女伴，但是她拒绝了与你回家，说想再给你一个考验。',
    '你和另一位贵族同时看中了一个女孩，但是在三人交谈时，你渐渐的失去了话题。'
]
Addgirlsuccess = [
    '你参加了一场贵族舞会，你优雅的舞姿让每位年轻女孩都望向了你。',
    '你参加了一场贵族舞会，你的帅气使你成为了舞会的宠儿。',
    '你在舞会门口就遇到了一位女孩，你挽着她的手走进了舞会。',
    '你在舞会的闲聊中无意中谈到了自己显赫的家室，你成为了舞会的宠儿。',
    '没有人比你更懂舞会，每一个女孩都为你的风度倾倒。',
    '舞会上你没有约到女伴，但是舞会后却有个女孩偷偷跟着你回了家。',
    '舞会上你和另一个贵族发生了争吵，一位女孩站出来为你撑腰，你第一次的注意到了这个可爱的女孩。',
    '你强壮的体魄让女孩们赞叹不已，她们纷纷来问你是不是一位军官。',
    '你擅长在舞会上温柔地对待每一个人，女孩们也向你投来了爱意。',
    '一个可爱的女孩一直在舞会上望着你，你犹豫了一会，向她发出了邀请。'
  
]

Login100 =[
    '今天是练习击剑的一天，不过你感觉你的剑法毫无提升。',
    '优雅的贵族从不晚起，可是你今天一直睡到了中午。',
    '今天你点了一份豪华的午餐却忘记了带钱，窘迫的你毫无贵族的姿态。',
    '今天你在路上看上了别人的女友，却没有鼓起勇气向他决斗。',
    '今天你十分抑郁，因为发现自己最近上升的只有体重。'

]

Login200 =[
    '今天是练习击剑的一天，你感觉到了你的剑法有所提升。',
    '早起的你站在镜子前许久，天底下竟然有人可以这么帅气。',
    '今天你搞到了一瓶不错的红酒，你的酒窖又多了一件存货。',
    '今天巡视领地时，一个小孩子崇拜地望着你，你感觉十分开心。',
    '今天一个朋友送你一张音乐会的门票，你打算邀请你的女友同去。',
    '今天一位国王的女友在路上向你抛媚眼，也许这就是个人魅力吧。'
    
]


Login300 =[
    '今天是练习击剑的一天，你感觉到了你的剑法大有长进。',
    '今天你救下了一个落水的小孩，他的家人说什么也要你收下一份心意。',
    '今天你巡视领地时，听到几个小女孩说想长大嫁给帅气的领主，你心里高兴极了。',
    '今天你打猎时猎到了一只鹿，你骄傲的把鹿角加入了收藏。',
    '今天你得到了一匹不错的马，说不定可以送去比赛。'
    
]

Login600 =[
    '今天是练习击剑的一天，你觉得自己已经可谓是当世剑圣。',
    '今天你因为领地治理有方，获得了皇帝的嘉奖。',
    '今天你的一位叔叔去世了，无儿无女的他，留给了你一大笔遗产。',
    '今天你在比武大会上获得了优胜，获得了全场的喝彩。',
    '今天你名下的马夺得了赛马的冠军，你感到无比的自豪。'
    
    
]

Date5 =[
    '你比约会的时间晚到了十分钟，嘟着嘴的她看起来不太满意。',
    '一向善于言辞的你，今天的约会却不时冷场，她看起来不是很开心。',
    '今天的约会上你频频打哈欠，被她瞪了好几次，早知道昨晚不该晚睡的。',
    '“为您旁边的这个姐姐买朵花吧。”你们被卖花的男孩拦下，你本想买花却发现自己忘记了带钱，她看起来不是很开心。'
]

Date10 =[
    '你带她去熟悉的餐厅吃饭，她觉得今天过得很开心。',
    '你带她去看了一场马术表演，并约她找机会一起骑马出去，她愉快的答应了。',
    '“为您旁边的这个姐姐买朵花吧。”你们被卖花的男孩拦下，你买了一束花还给了小孩一笔小费，你的女友看起来很开心。',
    '你邀请她去看一场歌剧，歌剧中她不时微笑，看起来十分开心。'
]

Date15 =[
    '你和她一同骑马出行，两个人一同去了很多地方，度过了愉快的一天。',
    '你新定做了一件最新款的礼服，约会中她称赞你比往常更加帅气。',
    '你邀请她共赴一场宴会，宴会上你们无所不谈，彼此间的了解增加了。',
    '你邀请她去看一场歌剧，歌剧中她一直轻轻地握着你的手。'  
]

Date20 =[
    '你邀请她共赴一场宴会，宴会中她亲吻了你的脸颊后，害羞的低下了头，这必然是你和她难忘的一天。',
    '约会中你们被一群暴民劫路，你为了保护她手臂受了伤。之后她心疼的抱住了你，并为你包扎了伤口。',
    '你邀请她去看你的赛马比赛，你骑着爱马轻松了夺取了第一名，冲过终点后，你大声地向着看台喊出了她的名字，她红着脸低下了头。',
    '你和她共同参加了一场盛大的舞会，两人的舞步轻盈而优雅，被评为了舞会第一名，上台时你注视着微笑的她，觉得她今天真是美极了。'
]


@sv.on_fullmatch(['贵族决斗帮助','贵族帮助','贵族指令'])
async def duel_help(bot, ev: CQEvent):
    msg='''
╔                                       ╗    
        贵族决斗相关指令

   1.贵族签到(每日一次)
   2.查询贵族
   3.贵族决斗+艾特
   4.领金币/查金币
   5.贵族舞会(招募女友)
   6.查女友+角色名
   7.升级贵族
   8.重置金币+qq (限群主)
   9.重置角色+qq (限群主) 
   10.重置决斗(限管理，决
   斗卡住时用)
   11.分手+角色名(需分手费)
   12.贵族等级表
   13.兑换声望+数量(兑换比例1：10000)
   14.转账(为@qq转账xxx金币)
   15.女友交易(用xxx金币与@qq交易女友+角色名)，需要收10%交易手续费
   16.dlc帮助(增加dlc角色)
   
  一个女友只属于一位群友

  
  声望系统国王后开启，
  具体指令发送:
  声望系统帮助
╚                                        ╝
'''  
    await bot.send(ev, msg)

    
blhxlist = range(6000,6106)
blhxlist2 = range(6106,6206)
blhxlist3 = range(6206,6306)
blhxlist4 = range(6306,6406)
blhxlist5 = range(6406,6506)
yozilist = range(1523,1544)
genshinlist = range(7001,7020)
bangdreamlist = range(1601,1636)
millist = range(3001,3055)
collelist = range(4001,4639)
koilist = range(7100,7104)
sakulist = range(7200,7204)
cloverlist = range(7300,7307)
majsoullist = range(7400,7476)
noranekolist = range(7500,7510)
fgolist = range(8001,8301)


#这里记录dlc名字和对应列表
dlcdict = {
        'blhx':blhxlist,
        'blhx2':blhxlist2,
        'blhx3':blhxlist3,
        'blhx4':blhxlist4,
        'blhx5':blhxlist5,
        'yozi':yozilist,
        'genshin':genshinlist,
        'bangdream':bangdreamlist,
        'million':millist,
        'kancolle':collelist,
        'koikake':koilist,
        'sakukoi':sakulist,
        'cloverdays':cloverlist,
        'majsoul':majsoullist,
        'noraneko':noranekolist,
        'fgo':fgolist
        }


#这里记录每个dlc的介绍
dlcintro = {
        'blhx':'碧蓝航线手游角色包。',
        'blhx2':'碧蓝航线手游角色包2。',
        'blhx3':'碧蓝航线手游角色包3。',
        'blhx4':'碧蓝航线手游角色包4。',
        'blhx5':'碧蓝航线手游角色包5。',
        'yozi':'柚子社部分角色包。',
        'genshin':'原神角色包。',
        'bangdream':'邦邦手游角色包。',
        'million':'偶像大师百万剧场角色包',
        'kancolle':'舰队collection角色包',
        'koikake':'恋×シンアイ彼女角色包',
        'sakukoi':'桜ひとひら恋もよう角色包',
        'cloverdays':'Clover Days角色包',
        'majsoul':'雀魂角色包',
        'noraneko':'ノラと皇女と野良猫ハート角色包' ,
        'fgo':'FGO手游角色包'        
        
        }




# 这个字典保存保存每个DLC开启的群列表，pcr默认一直开启。
dlc_switch={}

with open(os.path.join(FILE_PATH,'dlc_config.json'),'r',encoding='UTF-8') as f:
    dlc_switch = json.load(f, strict=False)
def save_dlc_switch():
    with open(os.path.join(FILE_PATH,'dlc_config.json'),'w',encoding='UTF-8') as f:
        json.dump(dlc_switch,f,ensure_ascii=False)



@sv.on_prefix(['加载dlc','加载DLC','开启dlc','开启DLC'])
async def add_dlc(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.OWNER):
        await bot.finish(ev, '只有群主才能加载dlc哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args)>= 2:
        await bot.finish(ev, '指令格式错误。', at_sender=True)
    if len(args)==0:
        await bot.finish(ev, '请输入加载dlc+dlc名。', at_sender=True)
    dlcname = args[0]
    if dlcname not in dlcdict.keys():
        await bot.finish(ev, 'DLC名填写错误。', at_sender=True)        

    if gid in dlc_switch[dlcname]:
        await bot.finish(ev, '本群已开启此dlc哦。', at_sender=True)
    dlc_switch[dlcname].append(gid)
    save_dlc_switch()
    await bot.finish(ev, f'加载dlc {dlcname}  成功!', at_sender=True)
        
    

@sv.on_prefix(['卸载dlc','卸载DLC','关闭dlc','关闭DLC'])
async def delete_dlc(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.OWNER):
        await bot.finish(ev, '只有群主才能卸载dlc哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args)>= 2:
        await bot.finish(ev, '指令格式错误', at_sender=True)
    if len(args)==0:
        await bot.finish(ev, '请输入卸载dlc+dlc名。', at_sender=True)
    dlcname = args[0]
    if dlcname not in dlcdict.keys():
        await bot.finish(ev, 'DLC名填写错误', at_sender=True)        

    if gid not in dlc_switch[dlcname]:
        await bot.finish(ev, '本群没有开启此dlc哦。', at_sender=True)
    dlc_switch[dlcname].remove(gid)
    save_dlc_switch()
    await bot.finish(ev, f'卸载dlc {dlcname}  成功!', at_sender=True)
    


@sv.on_fullmatch(['dlc列表','DLC列表','dlc介绍','DLC介绍'])
async def intro_dlc(bot, ev: CQEvent):
    msg = '可用DLC列表：\n\n'
    i=1
    for dlc in dlcdict.keys():
        msg+=f'{i}.{dlc}:\n'
        intro = dlcintro[dlc]
        msg+=f'介绍:{intro}\n'
        num = len(dlcdict[dlc])
        msg+=f'共有{num}名角色\n\n'
        i+=1
    msg+= '发送 加载\卸载dlc+dlc名\n可加载\卸载dlc\n卸载的dlc不会被抽到，但是角色仍留在玩家仓库，可以被抢走。'    
        
    await bot.finish(ev, msg)

@sv.on_fullmatch(['dlc帮助','DLC帮助','dlc指令','DLC指令'])
async def help_dlc(bot, ev: CQEvent):
    msg = '''
╔                                 ╗
         DLC帮助
      
  1.加载\卸载dlc+dlc名
  2.dlc列表(查看介绍)
  
  卸载的dlc不会被抽到
  但是角色仍留在仓库
  可以被他人抢走
  
╚                                 ╝    
'''
    await bot.finish(ev, msg)




#取得该群未开启的dlc所形成的黑名单
def get_dlc_blacklist(gid):

    dlc_blacklist=[]
    for dlc in dlcdict.keys():
        if gid not in dlc_switch[dlc]:
            dlc_blacklist += dlcdict[dlc]
    return dlc_blacklist

#检查有没有没加到json里的dlc
def check_dlc():
    for dlc in dlcdict.keys():
        if dlc not in dlc_switch.keys():
            dlc_switch[dlc]=[]
    save_dlc_switch()
            
check_dlc()





@sv.on_fullmatch(['贵族表','贵族等级表'])
async def duel_biao(bot, ev: CQEvent):
    msg='''"1": "平民",  最多可持有1名女友，每日签到额外获得100金币，初始等级。
"2": "骑士",  升级需要100金币，最多可持有2名女友，每日签到额外获得200金币，保持等级最少持有1名女友。
"3": "准男爵", 升级需要300金币，最多可持有3名女友，每日签到额外获得300金币，保持等级最少持有2名女友。
"4": "男爵",升级需要500金币，最多可持有5名女友，每日签到额外获得400金币，保持等级最少持有3名女友。
"5": "子爵",升级需要1000金币，最多可持有7名女友，每日签到额外获得500金币，保持等级最少持有5名女友。
"6": "伯爵",升级需要3000金币，最多可持有9名女友，每日签到额外获得600金币，保持等级最少持有7名女友。
"7": "侯爵",升级需要1000声望和5000金币，最多可持有10名女友，每日签到额外获得700金币，保持等级最少持有9名女友。
"8": "公爵",升级需要1500声望和10000金币，最多可持有12名女友，每日签到额外获得800金币，不再会掉级，可拥有一名妻子。
"9": "国王",升级需要2000声望和15000金币，最多可持有14名女友，每日签到额外获得900金币，不再会掉级，可拥有一名妻子。
"10": "皇帝"升级需要2500声望和20000金币，最多可持有15名女友，每日签到额外获得1000金币，不再会掉级，可拥有一名妻子。
"11": "神"升级需要4000声望和30000金币，最多可持有99名女友，每日签到额外获得2000金币，当输光女友时贬为平民，可拥有一名妻子。
'''  
    await bot.send(ev, msg)


# noinspection SqlResolve
class RecordDAO:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS limiter"
                "(key TEXT NOT NULL, num INT NOT NULL, date INT, PRIMARY KEY(key))"
            )

    def exist_check(self, key):
        try:
            key = str(key)
            with self.connect() as conn:
                conn.execute("INSERT INTO limiter (key,num,date) VALUES (?, 0,-1)", (key,), )
            return
        except:
            return

    def get_num(self, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            r = conn.execute(
                "SELECT num FROM limiter WHERE key=? ", (key,)
            ).fetchall()
            r2 = r[0]
        return r2[0]

    def clear_key(self, key):
        key = str(key)
        self.exist_check(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET num=0 WHERE key=?", (key,), )
        return

    def increment_key(self, key, num):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET num=num+? WHERE key=?", (num, key,))
        return

    def get_date(self, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            r = conn.execute(
                "SELECT date FROM limiter WHERE key=? ", (key,)
            ).fetchall()
            r2 = r[0]
        return r2[0]

    def set_date(self, date, key):
        print(date)
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET date=? WHERE key=?", (date, key,), )
        return


db = RecordDAO(DB_PATH)


class DailyAmountLimiter(DailyNumberLimiter):
    def __init__(self, types, max_num, reset_hour):
        super().__init__(max_num)
        self.reset_hour = reset_hour
        self.type = types

    def check(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != db.get_date(key):
            db.set_date(day, key)
            db.clear_key(key)
        return bool(db.get_num(key) < self.max)

    def check10(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != db.get_date(key):
            db.set_date(day, key)
            db.clear_key(key)
        return bool(db.get_num(key) < 10)

    def get_num(self, key):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        return db.get_num(key)

    def increase(self, key, num=1):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        db.increment_key(key, num)

    def reset(self, key):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        db.clear_key(key)


daily_sign_limiter = DailyAmountLimiter("sign", SIGN_DAILY_LIMIT, RESET_HOUR)
daily_free_limiter = DailyAmountLimiter("free", FREE_DAILY_LIMIT, RESET_HOUR)
daily_duel_limiter = DailyAmountLimiter("duel", DUEL_DAILY_LIMIT, RESET_HOUR)
daily_date_limiter = DailyAmountLimiter("date", DATE_DAILY_LIMIT, RESET_HOUR)
daily_gift_limiter = DailyAmountLimiter("gift", GIFT_DAILY_LIMIT, RESET_HOUR)

# 用于与赛跑金币互通
class ScoreCounter2:
    def __init__(self):
        os.makedirs(os.path.dirname(SCORE_DB_PATH), exist_ok=True)
        self._create_table()
        self._create_pres_table()
    def _connect(self):
        return sqlite3.connect(SCORE_DB_PATH)

    def _create_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS SCORECOUNTER
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           SCORE           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建表发生错误')

    def _add_score(self, gid, uid, score):
        try:
            current_score = self._get_score(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                VALUES (?,?,?)", (gid, uid, current_score + score))
            conn.commit()
        except:
            raise Exception('更新表发生错误')

    def _reduce_score(self, gid, uid, score):
        try:
            current_score = self._get_score(gid, uid)
            if current_score >= score:
                conn = self._connect()
                conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                VALUES (?,?,?)", (gid, uid, current_score - score))
                conn.commit()
            else:
                conn = self._connect()
                conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                VALUES (?,?,?)", (gid, uid, 0))
                conn.commit()
        except:
            raise Exception('更新表发生错误')

    def _get_score(self, gid, uid):
        try:
            r = self._connect().execute("SELECT SCORE FROM SCORECOUNTER WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找表发生错误')

    # 判断金币是否足够下注
    def _judge_score(self, gid, uid, score):
        try:
            current_score = self._get_score(gid, uid)
            if current_score >= score:
                return 1
            else:
                return 0
        except Exception as e:
            raise Exception(str(e))

    #记录国王声望数据
    def _create_pres_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS PRESTIGECOUNTER
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           PRESTIGE           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建表发生错误')

    def _set_prestige(self, gid, uid, prestige):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO PRESTIGECOUNTER (GID, UID, PRESTIGE) VALUES (?, ?, ?)",
                (gid, uid, prestige),
            )

    def _get_prestige(self, gid, uid):
        try:
            r = self._connect().execute("SELECT PRESTIGE FROM PRESTIGECOUNTER WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            if r is None:
               score_counter = ScoreCounter2()
               score_counter._set_prestige(gid,uid,0)
               return 0
            return r[0]
        except Exception as e:
            raise Exception('错误:\n' + str(e))
            return 0

    def _add_prestige(self, gid, uid, num):
        prestige = self._get_prestige(gid, uid)
        prestige += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO PRESTIGECOUNTER (GID, UID, PRESTIGE) VALUES (?, ?, ?)",
                (gid, uid, prestige),
            )

    def _reduce_prestige(self, gid, uid, num):
        prestige = self._get_prestige(gid, uid)
        prestige -= num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO PRESTIGECOUNTER (GID, UID, PRESTIGE) VALUES (?, ?, ?)",
                (gid, uid, prestige),
            )





   
# 记录贵族相关数据

class DuelCounter:
    def __init__(self):
        os.makedirs(os.path.dirname(DUEL_DB_PATH), exist_ok=True)
        self._create_charatable()
        self._create_uidtable()
        self._create_leveltable()
        self._create_queentable()
        self._create_warehousetable()
        self._create_favortable()
        self._create_gifttable()
        self._create_SWITCH()

    def _connect(self):
        return sqlite3.connect(DUEL_DB_PATH)


    def _create_warehousetable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS WAREHOUSE
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建仓库上限表发生错误')
            
    def _create_charatable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS CHARATABLE
                          (GID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           PRIMARY KEY(GID, CID));''')
        except:
            raise Exception('创建角色表发生错误')


    def _create_uidtable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS UIDTABLE
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           CID           INT    NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID, CID));''')
        except:
            raise Exception('创建UID表发生错误')

    def _create_leveltable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS LEVELTABLE
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           LEVEL           INT    NOT NULL,
                           
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建UID表发生错误')

    def _get_card_owner(self, gid, cid):
        try:
            r = self._connect().execute("SELECT UID FROM CHARATABLE WHERE GID=? AND CID=?", (gid, cid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找角色归属发生错误')

    def _set_card_owner(self, gid, cid, uid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO CHARATABLE (GID, CID, UID) VALUES (?, ?, ?)",
                (gid, cid, uid),
            )

    def _delete_card_owner(self, gid, cid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM CHARATABLE  WHERE GID=? AND CID=?",
                (gid, cid),
            )


# 查询已被邀请的女友列表

    def _get_card_list(self, gid):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT CID FROM CHARATABLE WHERE GID={gid}").fetchall()
            return [c[0] for c in r] if r else {}

    def _get_warehouse(self, gid, uid):
        try:
            r = self._connect().execute("SELECT NUM FROM WAREHOUSE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找上限发生错误')
            
    def _add_warehouse(self, gid, uid, increment=1):
        housenum = self._get_warehouse(gid, uid)
        housenum += increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO WAREHOUSE (GID, UID, NUM) VALUES (?, ?, ?)",
                (gid, uid, housenum),
            )
            
    def _get_level(self, gid, uid):
        try:
            r = self._connect().execute("SELECT LEVEL FROM LEVELTABLE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找等级发生错误')

    def _get_cards(self, gid, uid):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT CID, NUM FROM UIDTABLE WHERE GID=? AND UID=? AND NUM>0", (gid, uid)
            ).fetchall()
        return [c[0] for c in r] if r else {}

    def _get_card_num(self, gid, uid, cid):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT NUM FROM UIDTABLE WHERE GID=? AND UID=? AND CID=?", (gid, uid, cid)
            ).fetchone()
            return r[0] if r else 0

    def _add_card(self, gid, uid, cid, increment=1):
        num = self._get_card_num(gid, uid, cid)
        num += increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO UIDTABLE (GID, UID, CID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, num),
            )
        if cid !=9999:
            self._set_card_owner(gid, cid, uid)
            self._set_favor(gid,uid,cid,0)

    def _delete_card(self, gid, uid, cid, increment=1):
        num = self._get_card_num(gid, uid, cid)
        num -= increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO UIDTABLE (GID, UID, CID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, num),
            )
        self._delete_card_owner(gid, cid)
        self._delete_favor(gid,uid,cid)

    def _add_level(self, gid, uid, increment=1):
        level = self._get_level(gid, uid)
        level += increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO LEVELTABLE (GID, UID, LEVEL) VALUES (?, ?, ?)",
                (gid, uid, level),
            )

    def _reduce_level(self, gid, uid, increment=1):
        level = self._get_level(gid, uid)
        level -= increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO LEVELTABLE (GID, UID, LEVEL) VALUES (?, ?, ?)",
                (gid, uid, level),
            )

    def _set_level(self, gid, uid, level):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO LEVELTABLE (GID, UID, LEVEL) VALUES (?, ?, ?)",
                (gid, uid, level),
            )
            
    def _get_level_num(self, gid, level):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT COUNT(UID) FROM LEVELTABLE WHERE GID=? AND LEVEL=? ", (gid, level)
            ).fetchone()
            return r[0] if r else 0    
#开关部分
    def _create_SWITCH(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS SWITCH
                          (GID             INT    NOT NULL,
                           GC             INT    NULL,
                           QC           INT    NULL,
                           FREE           INT    NULL,
                           SW           INT    NULL,
                           SUO           INT    NULL,
                           PRIMARY KEY(GID));''')
        except:
            raise Exception('创建开关表发生错误')
            
    def _get_GOLD_CELE(self, gid):
        with self._connect() as conn:
            r = conn.execute("SELECT GC FROM SWITCH WHERE GID=?", (gid,)).fetchone()
            return None if r is None else r[0]
    
    def _get_SUO_CELE(self, gid):
        with self._connect() as conn:
            r = conn.execute("SELECT SUO FROM SWITCH WHERE GID=?", (gid,)).fetchone()
            return None if r is None else r[0]
            
    def _get_QC_CELE(self, gid):
        with self._connect() as conn:
            r = conn.execute("SELECT QC FROM SWITCH WHERE GID=?", (gid,)).fetchone()
            return None if r is None else r[0]
    
    def _get_FREE_CELE(self, gid):
        with self._connect() as conn:
            r = conn.execute("SELECT FREE FROM SWITCH WHERE GID=?", (gid,)).fetchone()
            return None if r is None else r[0]
    
    def _get_SW_CELE(self, gid):
        with self._connect() as conn:
            r = conn.execute("SELECT SW FROM SWITCH WHERE GID=?", (gid,)).fetchone()
            return None if r is None else r[0]
            
    def _initialization_CELE(self, gid, GC, QC, SUO, SW, FREE):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO SWITCH (GID, GC, QC, SUO, SW, FREE) VALUES (?, ?, ?, ?, ?, ?)",
                (gid, GC, QC, SUO, SW, FREE),
            )
#妻子部分

    def _create_queentable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS QUEENTABLE
                          (GID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           PRIMARY KEY(GID, CID));''')
        except:
            raise Exception('创建妻子表发生错误')

    def _get_queen_owner(self, gid, cid):
        try:
            r = self._connect().execute("SELECT UID FROM QUEENTABLE WHERE GID=? AND CID=?", (gid, cid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找妻子归属发生错误')

    def _set_queen_owner(self, gid, cid, uid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO QUEENTABLE (GID, CID, UID) VALUES (?, ?, ?)",
                (gid, cid, uid),
            )

    def _delete_queen_owner(self, gid, cid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM QUEENTABLE  WHERE GID=? AND CID=?",
                (gid, cid),
            )
    def _get_queen_list(self, gid):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT CID FROM QUEENTABLE WHERE GID={gid}").fetchall()
            return [c[0] for c in r] if r else {}
#查询某人的妻子，无则返回0
    def _search_queen(self,gid,uid):
        try:
            r = self._connect().execute("SELECT CID FROM QUEENTABLE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找妻子发生错误')    

#好感度部分
    def _create_favortable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS FAVORTABLE
                          (
                           GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           FAVOR           INT    NOT NULL,
                           PRIMARY KEY(GID, UID, CID));''')
        except:
            raise Exception('创建好感表发生错误')


    def _set_favor(self, gid, uid, cid, favor):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO FAVORTABLE (GID, UID, CID, FAVOR) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, favor),
            )

    def _get_favor(self, gid, uid, cid):
        try:
            r = self._connect().execute("SELECT FAVOR FROM FAVORTABLE WHERE GID=? AND UID=? AND CID=?", (gid, uid, cid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找好感发生错误')

    def _add_favor(self, gid, uid, cid, num):
        favor = self._get_favor(gid, uid, cid)
        if favor == None:
            favor = 0
        favor += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO FAVORTABLE (GID, UID, CID, FAVOR) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, favor),
            )

    def _reduce_favor(self, gid, uid, cid, num):
        favor = self._get_favor(gid, uid, cid)
        favor -= num
        favor = max(favor,0)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO FAVORTABLE (GID, UID, CID, FAVOR) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, favor),
            )

    def _delete_favor(self, gid, uid, cid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM FAVORTABLE  WHERE GID=? AND UID=? AND CID=?",
                (gid, uid, cid),
            )
#礼物仓库部分

    def _create_gifttable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS GIFTTABLE
                          (
                           GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           GFID             INT    NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID, GFID));''')
        except:
            raise Exception('创建礼物表发生错误')

    def _get_gift_num(self, gid, uid, gfid):
        try:
            r = self._connect().execute("SELECT NUM FROM GIFTTABLE WHERE GID=? AND UID=? AND GFID=?", (gid, uid, gfid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找礼物发生错误')

    def _add_gift(self, gid, uid, gfid, num=1):
        giftnum = self._get_gift_num(gid, uid, gfid)
        if giftnum == None:
            giftnum = 0
        giftnum += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO GIFTTABLE (GID, UID, GFID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, gfid, giftnum),
            )    

    def _reduce_gift(self, gid, uid, gfid, num=1):
        giftnum = self._get_gift_num(gid, uid, gfid)
        giftnum -= num
        giftnum = max(giftnum,0)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO GIFTTABLE (GID, UID, GFID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, gfid, giftnum),
            ) 




# 记录决斗和下注数据


class DuelJudger:
    def __init__(self):
        self.on = {}
        self.accept_on = {}
        self.support_on = {}
        self.fire_on = {}
        self.deadnum = {}
        self.support = {}
        self.turn = {}
        self.duelid = {}
        self.isaccept = {}
        self.hasfired_on = {}

    def set_support(self, gid):
        self.support[gid] = {}

    def get_support(self, gid):
        return self.support[gid] if self.support.get(gid) is not None else 0

    def add_support(self, gid, uid, id, score):
        self.support[gid][uid] = [id, score]

    def get_support_id(self, gid, uid):
        if self.support[gid].get(uid) is not None:
            return self.support[gid][uid][0]
        else:
            return 0

    def get_support_score(self, gid, uid):
        if self.support[gid].get(uid) is not None:
            return self.support[gid][uid][1]
        else:
            return 0

    # 五个开关：决斗，接受，下注， 开枪, 是否已经开枪

    def get_on_off_status(self, gid):
        return self.on[gid] if self.on.get(gid) is not None else False

    def turn_on(self, gid):
        self.on[gid] = True

    def turn_off(self, gid):
        self.on[gid] = False

    def get_on_off_accept_status(self, gid):
        return self.accept_on[gid] if self.accept_on.get(gid) is not None else False

    def turn_on_accept(self, gid):
        self.accept_on[gid] = True

    def turn_off_accept(self, gid):
        self.accept_on[gid] = False

    def get_on_off_support_status(self, gid):
        return self.support_on[gid] if self.support_on.get(gid) is not None else False

    def turn_on_support(self, gid):
        self.support_on[gid] = True

    def turn_off_support(self, gid):
        self.support_on[gid] = False

    def get_on_off_fire_status(self, gid):
        return self.fire_on[gid] if self.fire_on.get(gid) is not None else False

    def turn_on_fire(self, gid):
        self.fire_on[gid] = True

    def turn_off_fire(self, gid):
        self.fire_on[gid] = False

    def get_on_off_hasfired_status(self, gid):
        return self.hasfired_on[gid] if self.hasfired_on.get(gid) is not None else False

    def turn_on_hasfired(self, gid):
        self.hasfired_on[gid] = True

    def turn_off_hasfired(self, gid):
        self.hasfired_on[gid] = False

    # 记录决斗者id
    def init_duelid(self, gid):
        self.duelid[gid] = []

    def set_duelid(self, gid, id1, id2):
        self.duelid[gid] = [id1, id2]

    def get_duelid(self, gid):
        return self.duelid[gid] if self.accept_on.get(gid) is not None else [0, 0]
        
    # 查询一个决斗者是1号还是2号
    def get_duelnum(self, gid, uid):
        return self.duelid[gid].index(uid) + 1

    # 记录由谁开枪
    def init_turn(self, gid):
        self.turn[gid] = 1

    def get_turn(self, gid):
        return self.turn[gid] if self.turn[gid] is not None else 0

    def change_turn(self, gid):
        if self.get_turn(gid) == 1:
            self.turn[gid] = 2
            return 2
        else:
            self.turn[gid] = 1
            return 1

    # 记录子弹位置
    def init_deadnum(self, gid):
        self.deadnum[gid] = None

    def set_deadnum(self, gid, num):
        self.deadnum[gid] = num

    def get_deadnum(self, gid):
        return self.deadnum[gid] if self.deadnum[gid] is not None else False

    # 记录是否接受
    def init_isaccept(self, gid):
        self.isaccept[gid] = False

    def on_isaccept(self, gid):
        self.isaccept[gid] = True

    def off_isaccept(self, gid):
        self.isaccept[gid] = False

    def get_isaccept(self, gid):
        return self.isaccept[gid] if self.isaccept[gid] is not None else False

class GiftChange:
    def __init__(self):    
        self.giftchange_on={}
        self.waitchange={}
        self.isaccept = {}
        self.changeid = {}

 #礼物交换开关
    def get_on_off_giftchange_status(self, gid):
        return self.giftchange_on[gid] if self.giftchange_on.get(gid) is not None else False

    def turn_on_giftchange(self, gid):
        self.giftchange_on[gid] = True

    def turn_off_giftchange(self, gid):
        self.giftchange_on[gid] = False
    #礼物交换发起开关   
    def get_on_off_waitchange_status(self, gid):
        return self.waitchange[gid] if self.waitchange.get(gid) is not None else False

    def turn_on_waitchange(self, gid):
        self.waitchange[gid] = True

    def turn_off_waitchange(self, gid):
        self.waitchange[gid] = False
    #礼物交换是否接受开关
    def turn_on_accept_giftchange(self, gid):
        self.isaccept[gid] = True

    def turn_off_accept_giftchange(self, gid):
        self.isaccept[gid] = False

    def get_isaccept_giftchange(self, gid):
        return self.isaccept[gid] if self.isaccept[gid] is not None else False
    #记录礼物交换请求接收者id
    def init_changeid(self, gid):
        self.changeid[gid] = []

    def set_changeid(self, gid, id2):
        self.changeid[gid] = id2

    def get_changeid(self, gid):
        return self.changeid[gid] if self.changeid.get(gid) is not None else 0




duel_judger = DuelJudger()
gift_change = GiftChange()

class NvYouJiaoYi:
    def __init__(self):
        self.jiaoyion = {}
        self.jiaoyiflag = {}
        self.jiaoyiid = {}
        self.jiaoyiname = {}
        self.jiaoyi_on = {}
        
    def get_jiaoyi_on_off_status(self, gid):
        return self.jiaoyion[gid] if self.jiaoyion.get(gid) is not None else False
    # 记录群交易开关
    def turn_jiaoyion(self, gid):
        self.jiaoyion[gid] = True

    def turn_jiaoyioff(self, gid):
        self.jiaoyion[gid] = False
    
    # 记录群交易是否接受开关
    def turn_on_jiaoyi(self, gid):
        self.jiaoyi_on[gid] = True

    def turn_off_jiaoyi(self, gid):
        self.jiaoyi_on[gid] = False
    
    # 记录交易者id
    def init_jiaoyiid(self, gid):
        self.jiaoyiid[gid] = []

    def set_jiaoyiid(self, gid, id1, id2, cid):
        self.jiaoyiid[gid] = [id1, id2, cid]

    def get_jiaoyiid(self, gid):
        return self.jiaoyiid[gid] if self.jiaoyi_on.get(gid) is not None else [0, 0, 0]
    # 记录是否接受交易
    def init_jiaoyiflag(self, gid):
        self.jiaoyiflag[gid] = False

    def on_jiaoyiflag(self, gid):
        self.jiaoyiflag[gid] = True

    def off_jiaoyiflag(self, gid):
        self.jiaoyiflag[gid] = False

    def get_jiaoyiflag(self, gid):
        return self.jiaoyiflag[gid] if self.jiaoyiflag[gid] is not None else False
        
        
duel_jiaoyier = NvYouJiaoYi()

# 随机生成一个pcr角色id，应该已经被替代了。
def get_pcr_id():
    chara_id_list = list(_pcr_data_duel.CHARA_NAME.keys())
    while True:
        random.shuffle(chara_id_list)
        if chara_id_list[0] not in BLACKLIST_ID: break
    return chara_id_list[0]


# 生成没被约过的角色列表
def get_newgirl_list(gid):
    chara_id_list = list(_pcr_data_duel.CHARA_NAME.keys())
    duel = DuelCounter()
    old_list = duel._get_card_list(gid)
    dlc_blacklist = get_dlc_blacklist(gid)
    new_list = []
    for card in chara_id_list:
        if card not in BLACKLIST_ID and card not in old_list and card not in dlc_blacklist:
            new_list.append(card)
    return new_list


# 取爵位名
def get_noblename(level: int):
    namedict = {
        "1": "平民",
        "2": "骑士",
        "3": "准男爵",
        "4": "男爵",
        "5": "子爵",
        "6": "伯爵",
        "7": "侯爵",
        "8": "公爵",
        "9": "国王",
        "10": "皇帝",
        "20": "已成神"
    }
    return namedict[str(level)]


# 返回爵位对应的女友数
def get_girlnum(level: int):
    numdict = LEVEL_GIRL_NEED
    return numdict[str(level)]

# 返回对应的女友上限
def get_girlnum_buy(gid,uid):
    numdict = LEVEL_GIRL_NEED
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    num = duel._get_warehouse(gid, uid)
    housenum = int(numdict[str(level)])+num
    return housenum

# 返回升级到爵位所需要的金币数
def get_noblescore(level: int):
    numdict = LEVEL_COST_DICT
    return numdict[str(level)]

# 返回升级到爵位所需要的声望数
def get_noblesw(level: int):
    numdict = LEVEL_SW_NEED
    return numdict[str(level)]

# 判断当前女友数是否大于于上限
def girl_outlimit(gid,uid):
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    girlnum = get_girlnum_buy(gid, uid)
    cidlist = duel._get_cards(gid, uid)
    cidnum = len(cidlist) 
    if cidnum > girlnum:
        return True
    else: 
        return False
        
        
#魔改图片拼接 
def concat_pic(pics, border=0):
    num = len(pics)
    w= pics[0].size[0]
    h_sum = 0
    for pic in pics:
        h_sum += pic.size[1]
    des = Image.new('RGBA', (w, h_sum + (num-1) * border), (255, 255, 255, 255))
    h = 0
    for i, pic in enumerate(pics):
        des.paste(pic, (0, (h + i*border)), pic)
        h += pic.size[1]        
    return des

def get_nv_icon(cid):
    c = chara.fromid(cid)
    mes = c.icon.cqcode
    PIC_PATH = os.path.join(FILE_PATH,'fullcard')
    path = os.path.join(PIC_PATH,f'{cid}31.png')
    if  os.path.exists(path):
        img = Image.open(path)
        bio = BytesIO()
        img.save(bio, format='PNG')
        base64_str = 'base64://' + base64.b64encode(bio.getvalue()).decode()
        mes = f"[CQ:image,file={base64_str}]"   
    return mes

@sv.on_rex(f'^用(\d+)金币与(.*)交易女友(.*)$')
async def nobleduel(bot, ev: CQEvent):
    if duel_jiaoyier.get_jiaoyi_on_off_status(ev.group_id):
        await bot.send(ev, "此轮交易还没结束，请勿重复使用指令。")
        return
    gid = ev.group_id
    match = ev['match']
    try:
        id2 = int(match.group(2))
    except ValueError:
        id2 = int(ev.message[1].data['qq'])
    except:
        await bot.finish(ev, '参数格式错误')
    name = str(match.group(3))
    num = int(match.group(1))
    duel_jiaoyier.turn_jiaoyion(gid)
    id1 = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    level2 = duel._get_level(gid, id2)
    noblename = get_noblename(level2)
    is_overtime = 0
    num2 = 500
    if duel._get_level(gid, id2) < 7:
        msg = f'该用户等级较低，交易需要扣除您双倍声望喔'
        num2 = 1000
        await bot.send(ev, msg, at_sender=True)
    score = score_counter._get_score(gid, id1)
    prestige = score_counter._get_prestige(gid,id1)
    if score < num:
        msg = f'您的金币不足{num}，无法交易哦。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg, at_sender=True)
        return
    if prestige < num2:
        msg = f'您的声望不足{num2}，无法交易哦。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg, at_sender=True)
        return         
    if id2 == id1:
        await bot.send(ev, "不能和自己交易！", at_sender=True)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        return 
    if girl_outlimit(gid,id1):
        await bot.send(ev, "您的女友超过了爵位上限，无法进行交易哦！", at_sender=True)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        return 
    
    if duel._get_level(gid, id1) == 0:
        msg = f'[CQ:at,qq={id1}]交易发起者还未在创建过贵族\n请发送 创建贵族 开始您的贵族之旅。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg)
        return
    if duel._get_cards(gid, id1) == {}:
        msg = f'[CQ:at,qq={id1}]您没有女友，不能参与交易哦。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg)
        return

    if duel._get_level(gid, id2) == 0:
        msg = f'[CQ:at,qq={id2}]被交易者还未在本群创建过贵族\n请发送 创建贵族 开始您的贵族之旅。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg)
        return
    if duel._get_cards(gid, id2) == {}:
        msg = f'[CQ:at,qq={id2}]您没有女友，不能参与交易哦。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg)
        return
        
    if not name:
        await bot.send(ev, '请输入查女友+pcr角色名。', at_sender=True)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        return
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        return
    owner = duel._get_card_owner(gid, cid)
    c = chara.fromid(cid)
    #判断是否是妻子。
    if duel._get_queen_owner(gid,cid) !=0 :
        owner = duel._get_queen_owner(gid,cid)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.finish(ev, f'\n{c.name}现在是\n[CQ:at,qq={owner}]的妻子，无法交易哦。', at_sender=True)

    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。', at_sender=True)
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        return
    if id2!=owner:
        msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦，您需要与此人进行交易哦。'
        duel_jiaoyier.turn_jiaoyioff(ev.group_id)
        await bot.send(ev, msg)
        return
    duel_jiaoyier.init_jiaoyiflag(gid)
    duel_jiaoyier.set_jiaoyiid(gid, id1, id2, cid)
    duel_jiaoyier.turn_on_jiaoyi(gid)
    msg = f'[CQ:at,qq={id2}]尊敬的{noblename}您好\n[CQ:at,qq={id1}]试图以{num}金币的价格购买您的女友{c.name}，请在{WAIT_TIME_jy}秒内[接受交易/拒绝交易]，女友交易需要收5%手续费哦。'
    await bot.send(ev, msg)
    
    await asyncio.sleep(WAIT_TIME_jy)
    duel_jiaoyier.turn_off_jiaoyi(gid)
    if duel_jiaoyier.get_jiaoyiflag(gid) is False:
        msg = '交易被拒绝。'
        duel_jiaoyier.turn_jiaoyioff(gid)
        await bot.send(ev, msg, at_sender=True)
        return
        
    duel = DuelCounter()
    get_num=num*0.95
    score_counter._add_score(gid, id2, get_num)
    score = score_counter._get_score(gid, id2)
    
    score_counter._reduce_score(gid, id1, num)
    scoreyou = score_counter._get_score(gid, id1)
    duel._delete_card(gid, id2, cid)
    duel._add_card(gid, id1, cid)
    duel_jiaoyier.turn_jiaoyioff(gid)
    nvmes = get_nv_icon(cid)
    score_counter._reduce_prestige(gid,id1,num2)
    msg = f'[CQ:at,qq={id1}]以{num}金币的价格购买了[CQ:at,qq={id2}]的女友{c.name}，交易成功\n[CQ:at,qq={id1}]您失去了{num}金币，{num2}声望，剩余{scoreyou}金币\n[CQ:at,qq={id2}]扣除5%手续费，您能得到了{get_num}金币，剩余{score}金币。{nvmes}'
    await bot.send(ev, msg)


@sv.on_fullmatch('接受交易')
async def duelaccept(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_jiaoyier.get_jiaoyi_on_off_status(gid):
        if ev.user_id == duel_jiaoyier.get_jiaoyiid(gid)[1]:
            gid = ev.group_id
            msg = '交易接受成功，请耐心等待交易开始。'
            await bot.send(ev, msg, at_sender=True)
            duel_jiaoyier.turn_off_jiaoyi(gid)
            duel_jiaoyier.on_jiaoyiflag(gid)
        else:
            print('不是被交易者')
    else:
        print('现在不在交易期间')


@sv.on_fullmatch('重置交易')
async def init_duel(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能使用重置交易哦。', at_sender=True)
    duel_jiaoyier.turn_jiaoyioff(ev.group_id)
    msg = '已重置本群交易状态！'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch('拒绝交易')
async def duelrefuse(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_jiaoyier.get_jiaoyi_on_off_status(gid):
        if ev.user_id == duel_jiaoyier.get_jiaoyiid(gid)[1]:
            gid = ev.group_id
            msg = '您已拒绝女友交易。'
            await bot.send(ev, msg, at_sender=True)
            duel_jiaoyier.turn_off_jiaoyi(gid)
            duel_jiaoyier.off_jiaoyiflag(gid)

@sv.on_fullmatch('贵族签到')
async def noblelogin(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    guid = gid, uid
    if not daily_sign_limiter.check(guid):
        await bot.send(ev, '今天已经签到过了哦，明天再来吧。', at_sender=True)
        return
    duel = DuelCounter()
    
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    #根据概率随机获得收益。 
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid,uid)
    if prestige == None :
       score_counter._set_prestige(gid,uid,0)
    daily_sign_limiter.increase(guid)    
    loginnum_ = ['1','2', '3', '4']  
    r_ = [0.3, 0.4, 0.2, 0.1]  
    sum_ = 0
    ran = random.random()
    for num, r in zip(loginnum_, r_):
        sum_ += r
        if ran < sum_ :break
    Bonus = {'1':[200,Login100],
             '2':[500,Login200],
             '3':[700,Login300],    
             '4':[1000,Login600]
            }             
    score1 = Bonus[num][0]
    score1 = 3 * score1
    text1 = random.choice(Bonus[num][1])
    
    #根据爵位的每日固定收入
    level = duel._get_level(gid, uid)
    score2 = 300*level
    SW2 = 100*level
    scoresum = score1+score2
    noblename = get_noblename(level)
    score = score_counter._get_score(gid, uid)  
    if duel._get_QC_CELE(gid) == 1:
     scoresum = scoresum * QD_Gold_Cele_Num
     SW2 = SW2 * QD_SW_Cele_Num
     msg = f'\n{text1}\n签到成功！\n[庆典举办中]\n您领取了：\n\n{score1}金币(随机)和\n{score2}金币以及{SW2}声望({noblename}爵位)'
    else:
     msg = f'\n{text1}\n签到成功！\n您领取了：\n\n{score1}金币(随机)和\n{score2}金币以及{SW2}声望({noblename}爵位)'
    score_counter._add_prestige(gid,uid,SW2)
    score_counter._add_score(gid, uid, scoresum)
    cidlist = duel._get_cards(gid, uid)
    cidnum = len(cidlist)
    
    if cidnum > 0:
        cid = random.choice(cidlist)
        c = chara.fromid(cid)
        nvmes = get_nv_icon(cid)
        msg +=f'\n\n今天向您请安的是\n{c.name}{nvmes}'   
    #随机获得一件礼物
    select_gift = random.choice(list(GIFT_DICT.keys()))
    gfid = GIFT_DICT[select_gift]
    duel._add_gift(gid,uid,gfid)
    msg +=f'\n随机获得了礼物[{select_gift}]'
    await bot.send(ev, msg, at_sender=True)
    
@sv.on_fullmatch('免费招募')
async def noblelogin(bot, ev: CQEvent):
   gid = ev.group_id
   uid = ev.user_id
   duel = DuelCounter()  
   if duel._get_FREE_CELE(gid) != 1:
    await bot.send(ev, '当前未开放免费招募庆典！', at_sender=True)
    return
   else:
    guid = gid, uid
    if not daily_free_limiter.check(guid):
        await bot.send(ev, '今天已经免费招募过了喔，明天再来吧。(免费招募次数每天0点刷新)', at_sender=True)
        return 
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return  
    score_counter = ScoreCounter2()
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再参加舞会吧。'
        await bot.send(ev, msg, at_sender=True)
        return             
    else:
        # 防止女友数超过上限
        level = duel._get_level(gid, uid)
        noblename = get_noblename(level)
        girlnum = get_girlnum_buy(gid,uid)
        cidlist = duel._get_cards(gid, uid)
        cidnum = len(cidlist)
        if cidnum >= girlnum:
            msg = '您的女友已经满了哦，您转为获得500声望。'
            score_counter._add_prestige(gid, uid, 500)
            daily_free_limiter.increase(guid)  
            await bot.send(ev, msg, at_sender=True)
            return
        score = score_counter._get_score(gid, uid)
        prestige = score_counter._get_prestige(gid,uid)
        if prestige == None:
           score_counter._set_prestige(gid,uid,0)
        newgirllist = get_newgirl_list(gid)
        # 判断女友是否被抢没和该用户是否已经没有女友
        if len(newgirllist) == 0:
            if cidnum!=0:
                await bot.send(ev, '这个群已经没有可以约到的新女友了哦。', at_sender=True)
                return        
            else : 
                score_counter._reduce_score(gid, uid, GACHA_COST)
                cid = 9999
                c = chara.fromid(1059)
                duel._add_card(gid, uid, cid)
                msg = f'本群已经没有可以约的女友了哦，一位神秘的可可萝在你孤单时来到了你身边。{c.icon.cqcode}。'
                await bot.send(ev, msg, at_sender=True)
                return

        # 招募女友成功
        daily_free_limiter.increase(guid)  
        cid = random.choice(newgirllist)
        c = chara.fromid(cid)
        nvmes = get_nv_icon(cid)
        duel._add_card(gid, uid, cid)
        wintext = random.choice(Addgirlsuccess)
        msg = f'\n{wintext}\n招募女友成功！\n新招募的女友为：{c.name}{nvmes}'
        await bot.send(ev, msg, at_sender=True)
       
@sv.on_fullmatch(['本群贵族状态','查询本群贵族','本群贵族'])
async def group_noble_status(bot, ev: CQEvent):
    gid = ev.group_id
    duel = DuelCounter()
    newgirllist = get_newgirl_list(gid)
    newgirlnum = len(newgirllist)
    l1_num = duel._get_level_num(gid,1)
    l2_num = duel._get_level_num(gid,2)
    l3_num = duel._get_level_num(gid,3)
    l4_num = duel._get_level_num(gid,4)
    l5_num = duel._get_level_num(gid,5)
    l6_num = duel._get_level_num(gid,6)
    l7_num = duel._get_level_num(gid,7)
    l8_num = duel._get_level_num(gid,8)
    l9_num = duel._get_level_num(gid,9)
    lA_num = duel._get_level_num(gid,10)
    lB_num = duel._get_level_num(gid,20)
    dlctext=''
    for dlc in dlcdict.keys():
        if gid in dlc_switch[dlc]:
            dlctext += f'{dlc},'
    msg=f'''
╔                          ╗
         本群贵族
    神：{lB_num}名  
  皇帝：{lA_num}名  
  国王：{l9_num}名  
  公爵：{l8_num}名  
  侯爵：{l7_num}名
  伯爵：{l6_num}名
  子爵：{l5_num}名
  男爵：{l4_num}名
  准男爵：{l3_num}名
  骑士：{l2_num}名
  平民：{l1_num}名
  已开启DLC:
  {dlctext}
  还有{newgirlnum}名单身女友 
╚                          ╝
'''
    await bot.send(ev, msg)
    
@sv.on_fullmatch('创建贵族')
async def add_noble(bot, ev: CQEvent):
    try:
        gid = ev.group_id
        uid = ev.user_id
        duel = DuelCounter()
        if duel._get_level(gid, uid) != 0:
            msg = '您已经在本群创建过贵族了，请发送 查询贵族 查询。'
            await bot.send(ev, msg, at_sender=True)
            return
        
        #判定本群女友是否已空，如果空则分配一个复制人可可萝。
        newgirllist = get_newgirl_list(gid)
        if len(newgirllist) == 0:
            cid = 9999
            c = chara.fromid(1059)
            girlmsg = f'本群已经没有可以约的女友了哦，一位神秘的可可萝在你孤单时来到了你身边。{c.icon.cqcode}。'
        else:
            cid = random.choice(newgirllist)
            c = chara.fromid(cid)
            girlmsg = f'为您分配的初始女友为：{c.name}{c.icon.cqcode}'
        duel._add_card(gid, uid, cid)
        duel._set_level(gid, uid, 1)
        msg = f'\n创建贵族成功！\n您的初始爵位是平民\n可以拥有1名女友。\n初始金币为1000，初始声望为0\n{girlmsg}'
        score_counter = ScoreCounter2()
        score_counter._set_prestige(gid,uid,0)
        score_counter._add_score(gid, uid, 1000)
        
        await bot.send(ev, msg, at_sender=True)        
            

    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))


@sv.on_fullmatch(['增加容量', '增加女友上限'])
async def add_warehouse(bot, ev: CQEvent):
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    gid = ev.group_id
    uid = ev.user_id
    current_score = score_counter._get_score(gid, uid)
    prestige = score_counter._get_prestige(gid,uid)
    if duel._get_level(gid, uid) <= 9:
        msg = '只有成为皇帝后，才能扩充女友上限喔'
        await bot.send(ev, msg, at_sender=True)
        return
    if prestige < SHANGXIAN_SW:
        msg = '扩充女友上限，需要{SHANGXIAN_SW}声望，您的声望不足喔'
        await bot.send(ev, msg, at_sender=True)
        return
    if current_score < SHANGXIAN_NUM:
        msg = f'增加女友上限需要消耗{SHANGXIAN_NUM}金币，您的金币不足哦'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        housenum=duel._get_warehouse(gid, uid)
        if housenum>=WAREHOUSE_NUM:
            msg = f'您已增加{WAREHOUSE_NUM}次上限，无法继续增加了哦'
            await bot.send(ev, msg, at_sender=True)
            return
        duel._add_warehouse(gid, uid, 1)
        score_counter._reduce_score(gid, uid, SHANGXIAN_NUM)
        score_counter._reduce_prestige(gid, uid, SHANGXIAN_SW)
        last_score = current_score-SHANGXIAN_NUM
        myhouse = get_girlnum_buy(gid, uid)
        msg = f'您消耗了{SHANGXIAN_NUM}金币，{SHANGXIAN_SW}声望，增加了1个女友上限，目前的女友上限为{myhouse}名'
        await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['查询贵族', '贵族查询', '我的贵族'])
async def inquire_noble(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    level = duel._get_level(gid, uid)
    noblename = get_noblename(level)
    girlnum = get_girlnum_buy(gid,uid)
    score = score_counter._get_score(gid, uid)
    charalist = []

    cidlist = duel._get_cards(gid, uid)
    cidnum = len(cidlist)
    prestige = score_counter._get_prestige(gid,uid)
    if prestige == None:
       prestige = 0
       partmsg = f'您的声望为{prestige}点'
    else:
       partmsg = f'您的声望为{prestige}点'
    nv_names=''
    if cidnum == 0:
        msg = f'''
╔                          ╗
  您的爵位为{noblename}
  您的金币为{score}
  {partmsg}
  您共可拥有{girlnum}名女友
  您目前没有女友。
  发送[贵族约会]
  可以招募女友哦。
  
╚                          ╝
'''
        await bot.send(ev, msg, at_sender=True)

    else:
        shuzi_flag=0
        for cid in cidlist:
            #替换复制人可可萝
            if cid == 9999:
                cid = 1059
            charalist.append(chara.Chara(cid, 0, 0))
            c = chara.fromid(cid)
            shuzi_flag=shuzi_flag+1
            nv_names=nv_names+c.name+' '
            if shuzi_flag==6:
                nv_names=nv_names+'\n'
                shuzi_flag=0
            
            
        #制图部分，六个一行
        num = copy.deepcopy(cidnum)
        position = 6
        if num <= 6:
            res = chara.gen_team_pic(charalist, star_slot_verbose=False)
        else:
            num -= 6
            res = chara.gen_team_pic(charalist[0:position], star_slot_verbose=False)
            while(num > 0):
                if num>=6:
                    res1 = chara.gen_team_pic(charalist[position:position+6], star_slot_verbose=False)
                else: 
                    res1 = chara.gen_team_pic(charalist[position:], star_slot_verbose=False)
                res = concat_pic([res, res1])
                position +=6
                num -= 6
            

        bio = BytesIO()
        res.save(bio, format='PNG')
        base64_str = 'base64://' + base64.b64encode(bio.getvalue()).decode()
        mes = f"[CQ:image,file={base64_str}]"
        
        #判断是否开启声望

        
        
        
        
        
        msg = f'''
╔                          ╗
  您的爵位为{noblename}
  您的金币为{score}
  {partmsg}
  您共可拥有{girlnum}名女友
  您已拥有{cidnum}名女友
  她们是：
  {nv_names}
    {mes}   
╚                          ╝
'''
        #判断有无妻子
        queen = duel._search_queen(gid,uid)
        if queen != 0:
            c = chara.fromid(queen)
            
            msg = f'''
╔                          ╗
  您的爵位为{noblename}
  您的金币为{score}
  {partmsg}
  您的妻子是{c.name}
  您共可拥有{girlnum}名女友
  您已拥有{cidnum}名女友
  她们是：
  {nv_names}
    {mes}  
    
╚                          ╝
'''


        await bot.send(ev, msg, at_sender=True)


@sv.on_fullmatch(['招募女友', '贵族舞会'])
async def add_girl(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再参加舞会吧。'
        await bot.send(ev, msg, at_sender=True)
        return            
    if duel._get_level(gid, uid) == 20:
        msg = '你已成神，神不能招募女友。'
        await bot.send(ev, msg, at_sender=True)
        return      
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        # 防止女友数超过上限
        level = duel._get_level(gid, uid)
        noblename = get_noblename(level)
        girlnum = get_girlnum_buy(gid,uid)
        cidlist = duel._get_cards(gid, uid)
        cidnum = len(cidlist)
        if cidnum >= girlnum:
            msg = '您的女友已经满了哦，快点发送[升级贵族]进行升级吧。'
            await bot.send(ev, msg, at_sender=True)
            return
        score = score_counter._get_score(gid, uid)
        if score < GACHA_COST:
            msg = f'您的金币不足{GACHA_COST}哦。'
            await bot.send(ev, msg, at_sender=True)
            return
        prestige = score_counter._get_prestige(gid,uid)
        if prestige == None:
           score_counter._set_prestige(gid,uid,0)
        if prestige < 0 and level >7:
            msg = f'您现在身败名裂（声望为负），无法招募女友！。'
            await bot.send(ev, msg, at_sender=True)
            return
        newgirllist = get_newgirl_list(gid)
        # 判断女友是否被抢没和该用户是否已经没有女友
        if len(newgirllist) == 0:
            if cidnum!=0:
                await bot.send(ev, '这个群已经没有可以约到的新女友了哦。', at_sender=True)
                return        
            else : 
                score_counter._reduce_score(gid, uid, GACHA_COST)
                cid = 9999
                c = chara.fromid(1059)
                duel._add_card(gid, uid, cid)
                msg = f'本群已经没有可以约的女友了哦，一位神秘的可可萝在你孤单时来到了你身边。{c.icon.cqcode}。'
                await bot.send(ev, msg, at_sender=True)
                return

        score_counter._reduce_score(gid, uid, GACHA_COST)

        # 招募女友失败
        if random.random() < 0.4:
            losetext = random.choice(Addgirlfail)
            msg = f'\n{losetext}\n您花费了{GACHA_COST}金币，但是没有约到新的女友。获得了{GACHA_COST_Fail}金币补偿。'
            score_counter._add_score(gid, uid, GACHA_COST_Fail)
            score = score_counter._get_score(gid, uid)
            await bot.send(ev, msg, at_sender=True)
            return

        # 招募女友成功
        cid = random.choice(newgirllist)
        c = chara.fromid(cid)
        nvmes = get_nv_icon(cid)
        duel._add_card(gid, uid, cid)
        wintext = random.choice(Addgirlsuccess)
        
        msg = f'\n{wintext}\n招募女友成功！\n您花费了{GACHA_COST}金币\n新招募的女友为：{c.name}{nvmes}'
        await bot.send(ev, msg, at_sender=True)
    
@sv.on_fullmatch('声望招募')
async def add_girl(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel._get_SW_CELE(gid) != 1 and duel._get_level(gid, uid) != 20:
        msg = '目前不在限时开放声望招募期间，只有神能参与！'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg, at_sender=True)
        return
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再参加舞会吧。'
        await bot.send(ev, msg, at_sender=True)
        return                  
    else:
        # 防止女友数超过上限
        level = duel._get_level(gid, uid)
        noblename = get_noblename(level)
        girlnum = get_girlnum_buy(gid,uid)
        cidlist = duel._get_cards(gid, uid)
        cidnum = len(cidlist)
        score = score_counter._get_score(gid, uid)
        needSW2 = SW_COST
        prestige = score_counter._get_prestige(gid,uid)
        if prestige == None:
           score_counter._set_prestige(gid,uid,0)
        if prestige < needSW2:
            msg = f'您的声望不足{needSW2}哦。'
            await bot.send(ev, msg, at_sender=True)
            return


        newgirllist = get_newgirl_list(gid)
        # 判断女友是否被抢没和该用户是否已经没有女友
        if len(newgirllist) == 0:
            if cidnum!=0:
                await bot.send(ev, '这个群已经没有可以约到的新女友了哦。', at_sender=True)
                return        
            else : 
                score_counter._reduce_prestige(gid, uid, needSW2)
                cid = 9999
                c = chara.fromid(1059)
                duel._add_card(gid, uid, cid)
                msg = f'本群已经没有可以约的女友了哦，一位神秘的可可萝在你孤单时来到了你身边。{c.icon.cqcode}。'
                await bot.send(ev, msg, at_sender=True)
                return

        score_counter._reduce_prestige(gid, uid, needSW2)
        # 招募女友成功
        cid = random.choice(newgirllist)
        c = chara.fromid(cid)
        nvmes = get_nv_icon(cid)
        duel._add_card(gid, uid, cid)
        wintext = random.choice(Addgirlsuccess)
        
        msg = f'\n{wintext}\n招募女友成功！\n您花费了{needSW2}声望\n新招募的女友为：{c.name}{nvmes}'
        await bot.send(ev, msg, at_sender=True)



@sv.on_fullmatch(['升级爵位', '升级贵族','贵族升级'])
async def add_girl(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    score = score_counter._get_score(gid, uid)
    level = duel._get_level(gid, uid)
    noblename = get_noblename(level)
    girlnum = get_girlnum(level)
    cidlist = duel._get_cards(gid, uid)
    cidnum = len(cidlist)

    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再升级爵位吧。'
        await bot.send(ev, msg, at_sender=True)
        return  
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return    
    if level == 9:
        msg = f'您已经是国王了， 需要通过声望加冕称帝哦。'
        await bot.send(ev, msg, at_sender=True)
        return

    if level == 10:
        msg = f'您是本群的皇帝， 再往前一步就能成神了，请飞升成神。'
        await bot.send(ev, msg, at_sender=True)
        return

    if level == 20:
        msg = f'您已经到达了世界的巅峰， 无法再继续提升了。'
        await bot.send(ev, msg, at_sender=True)
        return
        
    if cidnum < girlnum:
        msg = f'您的女友没满哦。\n需要达到{girlnum}名女友\n您现在有{cidnum}名。'
        await bot.send(ev, msg, at_sender=True)
        return
    prestige = score_counter._get_prestige(gid,uid)    
    needscore = get_noblescore(level + 1)
    futurename = get_noblename(level + 1)
    needSW = get_noblesw(level + 1)
    if score < needscore:
        msg = f'您的金币不足哦。\n升级到{futurename}需要{needscore}金币'
        await bot.send(ev, msg, at_sender=True)
        return
    
    if level > 5 :
        if prestige == None:
            score_counter._set_prestige(gid,uid,0)
            await bot.finish(ev, '您还未开启声望系统哦，已为您开启！', at_sender=True)
            
        if prestige < needSW: 
            await bot.finish(ev, '您的声望不足哦。', at_sender=True)

        score_counter._reduce_prestige(gid, uid, needSW)
    score_counter._reduce_score(gid, uid, needscore)
    duel._add_level(gid, uid)
    newlevel = duel._get_level(gid, uid)
    newnoblename = get_noblename(newlevel)
    newgirlnum = get_girlnum_buy(gid,uid)
    msg = f'花费了{needscore}金币和{needSW}声望\n您成功由{noblename}升到了{newnoblename}\n可以拥有{newgirlnum}名女友了哦。'
    await bot.send(ev, msg, at_sender=True)


@sv.on_prefix('贵族决斗')
async def nobleduel(bot, ev: CQEvent):
    if ev.message[0].type == 'at':
        id2 = int(ev.message[0].data['qq'])
    else:
        await bot.finish(ev, '参数格式错误, 请重试')
    if duel_judger.get_on_off_status(ev.group_id):
        await bot.send(ev, "此轮决斗还没结束，请勿重复使用指令。")
        return
        
    gid = ev.group_id
    duel_judger.turn_on(gid)
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    id1 = ev.user_id
    duel = DuelCounter()
    is_overtime = 0
    prestige = score_counter._get_prestige(gid,id1)
    prestige2 = score_counter._get_prestige(gid,id2)
    level1 = duel._get_level(gid, id1)
    level2 = duel._get_level(gid, id2)
    if id2 == id1:
        await bot.send(ev, "不能和自己决斗！", at_sender=True)
        duel_judger.turn_off(ev.group_id)
        return 

    if duel._get_level(gid, id1) == 0:
        msg = f'[CQ:at,qq={id1}]决斗发起者还未在创建过贵族\n请发送 创建贵族 开始您的贵族之旅。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return
    if duel._get_cards(gid, id1) == {}:
        msg = f'[CQ:at,qq={id1}]您没有女友，不能参与决斗哦。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return

    if duel._get_level(gid, id2) == 0:
        msg = f'[CQ:at,qq={id2}]被决斗者还未在本群创建过贵族\n请发送 创建贵族 开始您的贵族之旅。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return
    if duel._get_cards(gid, id2) == {}:
        msg = f'[CQ:at,qq={id2}]您没有女友，不能参与决斗哦。'
        duel_judger.turn_off(ev.group_id)
        await bot.send(ev, msg)
        return
    #判定每日上限
    guid = gid ,id1
    if not daily_duel_limiter.check(guid):
        await bot.send(ev, '今天的决斗次数已经超过上限了哦，明天再来吧。', at_sender=True)
        duel_judger.turn_off(ev.group_id)
        return
    daily_duel_limiter.increase(guid)



    # 判定双方的女友是否已经超过上限

    # 这里设定大于才会提醒，就是可以超上限1名，可以自己改成大于等于。
    if girl_outlimit(gid,id1):
        msg = f'[CQ:at,qq={id1}]您的女友超过了爵位上限，本次决斗获胜只能获得金币哦。'
        await bot.send(ev, msg)
    if girl_outlimit(gid,id2):
        msg = f'[CQ:at,qq={id2}]您的女友超过了爵位上限，本次决斗获胜只能获得金币哦。'
        await bot.send(ev, msg)
    duel_judger.init_isaccept(gid)
    duel_judger.set_duelid(gid, id1, id2)
    duel_judger.turn_on_accept(gid)
    msg = f'[CQ:at,qq={id2}]对方向您发起了优雅的贵族决斗，请在{WAIT_TIME}秒内[接受/拒绝]。'

    await bot.send(ev, msg)
    await asyncio.sleep(WAIT_TIME)
    duel_judger.turn_off_accept(gid)
    if duel_judger.get_isaccept(gid) is False:
        msg = '决斗被拒绝。'
        duel_judger.turn_off(gid)
        await bot.send(ev, msg, at_sender=True)
        return
    duel = DuelCounter()
    level1 = duel._get_level(gid, id1)
    noblename1 = get_noblename(level1)
    level2 = duel._get_level(gid, id2)
    noblename2 = get_noblename(level2)
    if duel._get_GOLD_CELE(gid) == 1:
     msg = f'''对方接受了决斗！    
1号：[CQ:at,qq={id1}]
爵位为：{noblename1}
2号：[CQ:at,qq={id2}]
爵位为：{noblename2}
其他人请在{DUEL_SUPPORT_TIME}秒选择支持的对象
[庆典举办中]支持成功时，金币的获取量将会变为{Gold_Cele_Num * WIN_NUM}倍！
[支持1/2号xxx金币]'''
    else:
     msg = f'''对方接受了决斗！    
1号：[CQ:at,qq={id1}]
爵位为：{noblename1}
2号：[CQ:at,qq={id2}]
爵位为：{noblename2}
其他人请在{DUEL_SUPPORT_TIME}秒选择支持的对象
支持成功时，金币的获取量将会变为{WIN_NUM}倍！
[支持1/2号xxx金币]'''

    await bot.send(ev, msg)
    duel_judger.turn_on_support(gid)
    deadnum = int(math.floor( random.uniform(1,7) ))
    print ("死的位置是", deadnum)
    duel_judger.set_deadnum(gid, deadnum)
    await asyncio.sleep(DUEL_SUPPORT_TIME)
    duel_judger.turn_off_support(gid)
    duel_judger.init_turn(gid)
    duel_judger.turn_on_fire(gid)
    duel_judger.turn_off_hasfired(gid)
    msg = f'支持环节结束，下面请决斗双方轮流[开枪]。\n[CQ:at,qq={id1}]先开枪，30秒未开枪自动认输'

    await bot.send(ev, msg)
    n = 1
    while (n <= 6):
        wait_n = 0
        while (wait_n < 30):
            if duel_judger.get_on_off_hasfired_status(gid):
                break

            wait_n += 1
            await asyncio.sleep(1)
        if wait_n >= 30:
            # 超时未开枪的胜负判定
            loser = duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]
            winner = duel_judger.get_duelid(gid)[2 - duel_judger.get_turn(gid)]
            msg = f'[CQ:at,qq={loser}]\n你明智的选择了认输。'
            await bot.send(ev, msg)
            
            #记录本局为超时局。
            is_overtime = 1
            
            
            break
        else:
            if n == duel_judger.get_deadnum(gid):
                # 被子弹打到的胜负判定
                loser = duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]
                winner = duel_judger.get_duelid(gid)[2 - duel_judger.get_turn(gid)]
                msg = f'[CQ:at,qq={loser}]\n砰！你死了。'
                await bot.send(ev, msg)
                break
            else:
                id = duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]
                id2 = duel_judger.get_duelid(gid)[2 - duel_judger.get_turn(gid)]
                msg = f'[CQ:at,qq={id}]\n砰！松了一口气，你并没有死。\n[CQ:at,qq={id2}]\n轮到你开枪了哦。'
                await bot.send(ev, msg)
                n += 1
                duel_judger.change_turn(gid)
                duel_judger.turn_off_hasfired(gid)
                duel_judger.turn_on_fire(gid)
    score_counter = ScoreCounter2()
    cidlist = duel._get_cards(gid, loser)
    selected_girl = random.choice(cidlist)
    queen = duel._search_queen(gid,loser)

    #判定被输掉的是否是复制人可可萝，是则换成金币。
    if selected_girl==9999:
        score_counter._add_score(gid, winner, 300)
        c = chara.fromid(1059)
        nvmes = get_nv_icon(1059)
        duel._delete_card(gid, loser, selected_girl)
        msg = f'[CQ:at,qq={winner}]\n您赢得了神秘的可可萝，但是她微笑着消失了。\n本次决斗获得了300金币。'
        await bot.send(ev, msg)
        msg = f'[CQ:at,qq={loser}]\n您输掉了贵族决斗，被抢走了女友\n{c.name}，\n只要招募，她就还会来到你的身边哦。{nvmes}'
        await bot.send(ev, msg)

    #判断被输掉的是否为妻子。    
    elif selected_girl==queen:
        score_counter._add_score(gid, winner, 1000)
        msg = f'[CQ:at,qq={winner}]您赢得的角色为对方的妻子，\n您改为获得1000金币。'
        await bot.send(ev, msg)
        score_counter._reduce_prestige(gid,loser,300)
        msg = f'[CQ:at,qq={loser}]您差点输掉了妻子，额外失去了300声望。'
        await bot.send(ev, msg)


    elif girl_outlimit(gid,winner):
        score_counter._add_score(gid, winner, 1000)
        msg = f'[CQ:at,qq={winner}]您的女友超过了爵位上限，\n本次决斗获得了300金币。'
        c = chara.fromid(selected_girl)
        #判断好感是否足够，足够则扣掉好感
        favor = duel._get_favor(gid,loser,selected_girl)
        if favor>=favor_reduce:
            c = chara.fromid(selected_girl)
            duel._reduce_favor(gid,loser,selected_girl,favor_reduce)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗，您与{c.name}的好感下降了50点。\n{c.icon.cqcode}'
            await bot.send(ev, msg)            
        else:
            duel._delete_card(gid, loser, selected_girl)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗且对方超过了爵位上限，您的女友恢复了单身。\n{c.name}{c.icon.cqcode}'
            await bot.send(ev, msg)

    else:
        #判断好感是否足够，足够则扣掉好感
        favor = duel._get_favor(gid,loser,selected_girl)    
        if favor>=favor_reduce:
            duel._reduce_favor(gid,loser,selected_girl,favor_reduce)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗，您与{c.name}的好感下降了50点。\n{c.icon.cqcode}'
            await bot.send(ev, msg)      
            score_counter._add_score(gid, winner, 300)
            msg = f'[CQ:at,qq={winner}]您赢得了决斗，对方女友仍有一定好感。\n本次决斗获得了300金币。'
            await bot.send(ev, msg)  
        else:
            c = chara.fromid(selected_girl)
            duel._delete_card(gid, loser, selected_girl)
            duel._add_card(gid, winner, selected_girl)
            msg = f'[CQ:at,qq={loser}]您输掉了贵族决斗，您被抢走了女友\n{c.name}{c.icon.cqcode}'
            await bot.send(ev, msg)
        #判断赢家的角色列表里是否有复制人可可萝。
            wincidlist = duel._get_cards(gid, winner)
            if 9999 in wincidlist:
                duel._delete_card(gid, winner, 9999)
                score_counter._add_score(gid, winner, 300)
                msg = f'[CQ:at,qq={winner}]\n“主人有了女友已经不再孤单了，我暂时离开了哦。”\n您赢得了{c.name},可可萝微笑着消失了。\n您获得了300金币。'
                await bot.send(ev, msg)

    #判断胜者败者是否需要增减声望
    level_loser = duel._get_level(gid, loser)
    level_winner = duel._get_level(gid, winner)
    wingold = 800 + (level_loser * 100)
    if is_overtime == 1:
         if n !=6:
           wingold = 100
    score_counter._add_score(gid, winner, wingold)
    msg = f'[CQ:at,qq={winner}]本次决斗胜利获得了{wingold}金币。'
    await bot.send(ev, msg)
    winprestige = score_counter._get_prestige(gid,winner)
    if winprestige == None:
       winprestige == 0
    if winprestige != None:
        level_cha = level_loser - level_winner
        level_zcha = max(level_cha,0)
        winSW = WinSWBasics + (level_zcha * 20)
        if is_overtime == 1:
         if n !=6:
            if level_loser < 6:
               winSW = 0
            else:
               winSW = 150
        score_counter._add_prestige(gid,winner,winSW)
        msg = f'[CQ:at,qq={winner}]决斗胜利使您的声望上升了{winSW}点。'
        await bot.send(ev, msg)
    loseprestige = score_counter._get_prestige(gid,loser)
    if loseprestige == -1:
       loseprestige == 0
    if loseprestige != -1:
        level_cha = level_loser - level_winner
        level_zcha = max(level_cha,0)
        LOSESW = LoseSWBasics + (level_zcha * 10)
        score_counter._reduce_prestige(gid,loser,LOSESW)
        msg = f'[CQ:at,qq={loser}]决斗失败使您的声望下降了{LOSESW}点。'
        await bot.send(ev, msg)


    #判定败者是否掉爵位，皇帝不会因为决斗掉爵位。
    level_loser = duel._get_level(gid, loser)
    if level_loser > 1 and level_loser < 8:
        noblename_loser = get_noblename(level_loser)
        girlnum_loser = get_girlnum(level_loser - 1)
        cidlist_loser = duel._get_cards(gid, loser)
        cidnum_loser = len(cidlist_loser)
        if cidnum_loser < girlnum_loser:
            duel._reduce_level(gid, loser)
            new_noblename = get_noblename(level_loser - 1)
            msg = f'[CQ:at,qq={loser}]\n您的女友数为{cidnum_loser}名\n小于爵位需要的女友数{girlnum_loser}名\n您的爵位下降到了{new_noblename}'
            await bot.send(ev, msg)

    #结算下注金币，判定是否为超时局。
    if is_overtime == 1:
     if n !=6:
        if level_loser < 6:
          msg = '认输警告！本局为超时局/认输局，不进行金币结算，支持的金币全部返还。胜者获得的声望为0，金币大幅减少。'
        else:
          msg = '认输警告！本局为超时局/认输局，不进行金币结算，支持的金币全部返还。胜者获得的声望减半，金币大幅减少，不计等级差。'
        await bot.send(ev, msg)
        duel_judger.set_support(ev.group_id)
        duel_judger.turn_off(ev.group_id)
        return
    
    support = duel_judger.get_support(gid)
    winuid = []
    supportmsg = '金币结算:\n'
    winnum = duel_judger.get_duelnum(gid, winner)

    if support != 0:
        for uid in support:
            support_id = support[uid][0]
            support_score = support[uid][1]
            if support_id == winnum:
                winuid.append(uid)
                #这里是赢家获得的金币结算，可以自己修改倍率。
                if duel._get_GOLD_CELE(gid) == 1:
                 winscore = support_score * WIN_NUM * Gold_Cele_Num
                else:
                 winscore = support_score * WIN_NUM
                score_counter._add_score(gid, uid, winscore)
                supportmsg += f'[CQ:at,qq={uid}]+{winscore}金币\n'
            else:
                score_counter._reduce_score(gid, uid, support_score)
                supportmsg += f'[CQ:at,qq={uid}]-{support_score}金币\n'
    await bot.send(ev, supportmsg)
    duel_judger.set_support(ev.group_id)
    duel_judger.turn_off(ev.group_id)
    return


@sv.on_fullmatch('接受')
async def duelaccept(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_judger.get_on_off_accept_status(gid):
        if ev.user_id == duel_judger.get_duelid(gid)[1]:
            gid = ev.group_id
            msg = '贵族决斗接受成功，请耐心等待决斗开始。'
            await bot.send(ev, msg, at_sender=True)
            duel_judger.turn_off_accept(gid)
            duel_judger.on_isaccept(gid)
        else:
            print('不是被决斗者')
    else:
        print('现在不在决斗期间')


@sv.on_fullmatch('拒绝')
async def duelrefuse(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_judger.get_on_off_accept_status(gid):
        if ev.user_id == duel_judger.get_duelid(gid)[1]:
            gid = ev.group_id
            msg = '您已拒绝贵族决斗。'
            await bot.send(ev, msg, at_sender=True)
            duel_judger.turn_off_accept(gid)
            duel_judger.off_isaccept(gid)


@sv.on_fullmatch('开枪')
async def duelfire(bot, ev: CQEvent):
    gid = ev.group_id
    if duel_judger.get_on_off_fire_status(gid):
        if ev.user_id == duel_judger.get_duelid(gid)[duel_judger.get_turn(gid) - 1]:
            duel_judger.turn_on_hasfired(gid)
            duel_judger.turn_off_fire(gid)


@sv.on_rex(r'^支持(1|2)号(\d+)(金币|币)$')
async def on_input_duel_score(bot, ev: CQEvent):
    try:
        if duel_judger.get_on_off_support_status(ev.group_id):
            gid = ev.group_id
            uid = ev.user_id

            match = ev['match']
            select_id = int(match.group(1))
            input_score = int(match.group(2))
            print(select_id, input_score)
            score_counter = ScoreCounter2()
            # 若下注该群下注字典不存在则创建
            if duel_judger.get_support(gid) == 0:
                duel_judger.set_support(gid)
            support = duel_judger.get_support(gid)
            # 检查是否重复下注
            if uid in support:
                msg = '您已经支持过了。'
                await bot.send(ev, msg, at_sender=True)
                return
            # 检查是否是决斗人员
            duellist = duel_judger.get_duelid(gid)
            if uid in duellist:
                msg = '决斗参与者不能支持。'
                await bot.send(ev, msg, at_sender=True)
                return

                # 检查金币是否足够下注
            if score_counter._judge_score(gid, uid, input_score) == 0:
                msg = '您的金币不足。'
                await bot.send(ev, msg, at_sender=True)
                return
            else:
                duel_judger.add_support(gid, uid, select_id, input_score)
                msg = f'支持{select_id}号成功。'
                await bot.send(ev, msg, at_sender=True)
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))

@sv.on_rex(r'^梭哈支持(1|2)号$')
async def on_input_duel_score2(bot, ev: CQEvent):
    try:
        if duel_judger.get_on_off_support_status(ev.group_id):
            gid = ev.group_id
            duel = DuelCounter()
            uid = ev.user_id
            if Suo_allow != True:
                msg = '管理员禁止梭哈。'
                await bot.send(ev, msg, at_sender=True)
                return
            score_counter = ScoreCounter2()
            match = ev['match']
            select_id = int(match.group(1))
            current_score = score_counter._get_score(gid, uid)
            input_score = current_score
            print(select_id, input_score)
            score_counter = ScoreCounter2()
            # 若下注该群下注字典不存在则创建
            if duel_judger.get_support(gid) == 0:
                duel_judger.set_support(gid)
            support = duel_judger.get_support(gid)
            # 检查是否重复下注
            if uid in support:
                msg = '您已经支持过了。'
                await bot.send(ev, msg, at_sender=True)
                return
            # 检查是否是决斗人员
            duellist = duel_judger.get_duelid(gid)
            if uid in duellist:
                msg = '决斗参与者不能支持。'
                await bot.send(ev, msg, at_sender=True)
                return
                # 检查金币是否足够下注
            if score_counter._judge_score(gid, uid, input_score) == 0:
                msg = '您的金币不足。'
                await bot.send(ev, msg, at_sender=True)
                return
            else:
             if duel._get_SUO_CELE(gid) == 1:
                input_score =  Suo * current_score * Suo_Cele_Num
                duel_judger.add_support(gid, uid, select_id, input_score)
                msg = f'梭哈支持{select_id}号{current_score}金币成功，[庆典举办中]胜利时，将获得相对于平常值{Suo*Suo_Cele_Num}倍的金币！'
                await bot.send(ev, msg, at_sender=True)
             else:
                input_score =  Suo * current_score
                duel_judger.add_support(gid, uid, select_id, input_score)
                msg = f'梭哈支持{select_id}号{current_score}金币成功，胜利时，将获得相对于平常值{Suo}倍的金币！'
                await bot.send(ev, msg, at_sender=True)
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))


# 以下部分与赛跑的重合，有一个即可，两个插件都装建议注释掉。

@sv.on_prefix(['领金币', '领取金币'])
async def add_score(bot, ev: CQEvent):
    try:
        score_counter = ScoreCounter2()
        gid = ev.group_id
        uid = ev.user_id

        current_score = score_counter._get_score(gid, uid)
        if current_score == 0:
            score_counter._add_score(gid, uid, ZERO_GET_AMOUNT)
            msg = f'您已领取{ZERO_GET_AMOUNT}金币'
            await bot.send(ev, msg, at_sender=True)
            return
        else:
            msg = '金币为0才能领取哦。'
            await bot.send(ev, msg, at_sender=True)
            return
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))


@sv.on_prefix(['查金币', '查询金币', '查看金币'])
async def get_score(bot, ev: CQEvent):
    try:
        score_counter = ScoreCounter2()
        gid = ev.group_id
        uid = ev.user_id

        current_score = score_counter._get_score(gid, uid)
        msg = f'您的金币为{current_score}'
        await bot.send(ev, msg, at_sender=True)
        return
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))
        


@sv.on_rex(f'^为(.*)充值(\d+)金币$')
async def cheat_score(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '不要想着走捷径哦。', at_sender=True)
    gid = ev.group_id
    match = ev['match']
    try:
        id = int(match.group(1))
    except ValueError:
        id = int(ev.message[1].data['qq'])
    except:
        await bot.finish(ev, '参数格式错误')
    num = int(match.group(2))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel._get_level(gid, id) == 0:
        await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
    score_counter._add_score(gid, id, num)
    score = score_counter._get_score(gid, id)
    msg = f'已为[CQ:at,qq={id}]充值{num}金币。\n现在共有{score}金币。'
    await bot.send(ev, msg)
    
@sv.on_rex(f'^设定群(.*)为(\d+)号死$')
async def cheat_num(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '不要想着走捷径哦。', at_sender=True)
    match = ev['match']
    try:
        gid = int(match.group(1))
    except ValueError:
        gid = int(ev.message[1].data['qq'])
    except:
        await bot.finish(ev, '参数格式错误')
    deadnum = int(match.group(2))
    duel_judger.set_deadnum(gid, deadnum)
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    msg = f'已将群{gid}本次决斗死亡位置修改为{deadnum}号。\n'
    print ("死的位置是", duel_judger.get_deadnum(gid))
    await bot.send(ev, msg)
    self.deadnum[gid] = deadnum
    
@sv.on_rex(f'^为(.*)转账(\d+)金币$')
async def cheat_score(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    try:
        id = int(match.group(1))
    except ValueError:
        id = int(ev.message[1].data['qq'])
    except:
        await bot.finish(ev, '参数格式错误')
    num = int(match.group(2))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel._get_level(gid, id) == 0:
        await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
    if duel._get_level(gid, id) < 7:
        await bot.finish(ev, '该用户等级过低，无法接受转账喔（接受转账需要等级达到伯爵）。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < num:
        msg = f'您的金币不足{num}哦。'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        score_counter._reduce_score(gid, uid, num)
        scoreyou = score_counter._get_score(gid, uid)
        num2 = num * (1-Zhuan_Need)
        score_counter._add_score(gid, id, num2)
        score = score_counter._get_score(gid, id)
        msg = f'已为[CQ:at,qq={id}]转账{num}金币。\n扣除{Zhuan_Need*100}%手续费，您的金币剩余{scoreyou}金币，对方金币剩余{score}金币。'
        await bot.send(ev, msg)


@sv.on_fullmatch('重置决斗')
async def init_duel(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能使用重置决斗哦。', at_sender=True)
    duel_judger.turn_off(ev.group_id)
    msg = '已重置本群决斗状态！'
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(['查女友', '查询女友', '查看女友'])
async def search_girl(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    if not args:
        await bot.send(ev, '请输入查女友+pcr角色名。', at_sender=True)
        return
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.send(ev, '请输入正确的pcr角色名。', at_sender=True)
        return
    duel = DuelCounter()
    owner = duel._get_card_owner(gid, cid)
    c = chara.fromid(cid)
    #判断是否是妻子。
    print(duel._get_queen_owner(gid,cid))
    nvmes = get_nv_icon(cid)
    if duel._get_queen_owner(gid,cid) !=0 :
        owner = duel._get_queen_owner(gid,cid)
        await bot.finish(ev, f'\n{c.name}现在是\n[CQ:at,qq={owner}]的妻子哦。{nvmes}', at_sender=True)

    if owner == 0:
        await bot.send(ev, f'{c.name}现在还是单身哦，快去约到她吧。{nvmes}', at_sender=True)
        return
    else:
        msg = f'{c.name}现在正在\n[CQ:at,qq={owner}]的身边哦。{nvmes}'
        await bot.send(ev, msg)


#重置某一用户的金币，只用做必要时删库用。
@sv.on_prefix('重置金币')
async def reset_score(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.OWNER):
        await bot.finish(ev, '只有群主才能使用重置金币功能哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args)>=2:
        await bot.finish(ev, '指令格式错误', at_sender=True)
    if len(args)==0:
        await bot.finish(ev, '请输入重置金币+被重置者QQ', at_sender=True)
    else :
        id = args[0]
        duel = DuelCounter()
        if duel._get_level(gid, id) == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        score_counter = ScoreCounter2()    
        current_score = score_counter._get_score(gid, id)
        score_counter._reduce_score(gid, id,current_score)
        await bot.finish(ev, f'已清空用户{id}的金币。', at_sender=True)
        
#注意会清空此人的角色以及贵族等级，只用做必要时删库用。 
@sv.on_prefix('重置角色')
async def reset_chara(bot, ev: CQEvent):
    gid = ev.group_id
    if not priv.check_priv(ev, priv.OWNER):
        await bot.finish(ev, '只有群主才能使用重置角色功能哦。', at_sender=True)
    args = ev.message.extract_plain_text().split()
    if len(args)>=2:
        await bot.finish(ev, '指令格式错误', at_sender=True)
    if len(args)==0:
        await bot.finish(ev, '请输入重置角色+被重置者QQ', at_sender=True)
    else :
        id = args[0]
        duel = DuelCounter()
        if duel._get_level(gid, id) == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        cidlist = duel._get_cards(gid, id)
        for cid in cidlist:
            duel._delete_card(gid, id, cid)
        score_counter = ScoreCounter2()    
        current_score = score_counter._get_score(gid, id)
        score_counter._reduce_score(gid, id,current_score)
        queen = duel._search_queen(gid,id)
        duel._delete_queen_owner(gid,queen)
        duel._set_level(gid, id, 0)    
        await bot.finish(ev, f'已清空用户{id}的女友和贵族等级。', at_sender=True)


@sv.on_prefix('确认重开')
async def reset_CK(bot, ev: CQEvent):
        gid = ev.group_id
        uid = ev.user_id
        if Remake_allow == False:
         await bot.finish(ev, '管理员不允许自行重开。', at_sender=True)
        duel = DuelCounter()
        score_counter = ScoreCounter2()
        prestige = score_counter._get_prestige(gid,uid)
        if prestige < 0:
            await bot.finish(ev, '您现在身败名裂（声望为负），无法重开！请联系管理员重开！', at_sender=True)
        if duel._get_level(gid, uid) == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        cidlist = duel._get_cards(gid, uid)
        for cid in cidlist:
            duel._delete_card(gid, uid, cid)
        score_counter = ScoreCounter2()    
        current_score = score_counter._get_score(gid, uid)
        score_counter._reduce_score(gid, uid,current_score)
        queen = duel._search_queen(gid,uid)
        duel._delete_queen_owner(gid,queen)
        duel._set_level(gid, uid, 0)    
        await bot.finish(ev, f'已清空您的女友和贵族等级，金币等。', at_sender=True)

@sv.on_prefix('分手')
async def breakup(bot, ev: CQEvent):
    if BREAK_UP_SWITCH == True:
        args = ev.message.extract_plain_text().split()
        gid = ev.group_id
        uid = ev.user_id
        duel = DuelCounter()
        level = duel._get_level(gid, uid)
        if duel_judger.get_on_off_status(ev.group_id):
                msg = '现在正在决斗中哦，请决斗后再来谈分手事宜吧。'
                await bot.finish(ev, msg, at_sender=True)
        if level == 0:
            await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
        if not args:
            await bot.finish(ev, '请输入分手+pcr角色名。', at_sender=True)
        name = args[0]
        cid = chara.name2id(name)
        if cid == 1000:
            await bot.finish(ev, '请输入正确的pcr角色名。', at_sender=True)
        score_counter = ScoreCounter2()
        needscore = 400+level*100
        needSW = 100+level*15
        if level == 20:
            needSW = 600
        score = score_counter._get_score(gid, uid)
        prestige = score_counter._get_prestige(gid,uid)
        cidlist = duel._get_cards(gid, uid)
        if cid not in cidlist:
            await bot.finish(ev, '该角色不在你的身边哦。', at_sender=True)
        #检测是否是妻子
        queen = duel._search_queen(gid,uid)
        if cid==queen:
            await bot.finish(ev, '不可以和您的妻子分手哦。', at_sender=True)
        if score < needscore:
            msg = f'您的爵位分手一位女友需要{needscore}金币和{needSW}声望哦。\n分手不易，做好准备再来吧。'
            await bot.finish(ev, msg, at_sender=True)
        if prestige < needSW:
            msg = f'您的爵位分手一位女友需要{needscore}金币和{needSW}声望哦。\n分手不易，做好准备再来吧。'
            await bot.finish(ev, msg, at_sender=True)
        score_counter._reduce_score(gid, uid, needscore)
        score_counter._reduce_prestige(gid, uid, needSW)
        duel._delete_card(gid, uid, cid)
        c = chara.fromid(cid)
        msg = f'\n“真正离开的那次，关门声最小。”\n你和{c.name}分手了。失去了{needscore}金币分手费,声望减少了{needSW}。\n{c.icon.cqcode}'
        await bot.send(ev, msg, at_sender=True)
     
     


#国王以上声望部分。

@sv.on_fullmatch('开启声望系统')
async def open_prestige(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid,uid)
    if prestige != None:
        await bot.finish(ev, '您已经开启了声望系统哦。', at_sender=True)      
    score_counter._set_prestige(gid,uid,0)
    msg = '成功开启声望系统！殿下，向着成为皇帝的目标进发吧。'
    await bot.send(ev, msg, at_sender=True)
    
@sv.on_fullmatch('声望系统帮助')
async def prestige_help(bot, ev: CQEvent):
    msg='''
成为伯爵后才可以开启声望系统
开启后可以通过决斗等方式获取声望
声望系统相关指令如下
1. 开启声望系统
2. 查询声望
3. 加冕仪式(需要4000声望，20000金币）
4. 皇室婚礼+角色名(需5000金币，公爵以上)

决斗胜利+300声望
决斗失败-100声望
皇室婚礼需公爵才能举办
每个人只能举办一次
妻子不会因决斗被抢走

 '''  
    await bot.send(ev, msg)

@sv.on_fullmatch('查询声望')
async def inquire_prestige(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid,uid)
    if prestige == None:
        await bot.finish(ev, '您还未开启声望系统哦。', at_sender=True)
    msg = f'您的声望为{prestige}点。'    
    await bot.send(ev, msg, at_sender=True)    
        
@sv.on_fullmatch(['加冕称帝','加冕仪式'])
async def be_emperor(bot, ev: CQEvent): 
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()  
    prestige = score_counter._get_prestige(gid,uid)
    
    if prestige == None:
        await bot.finish(ev, '您还未开启声望系统哦。', at_sender=True)
    if level!=9:
        await bot.finish(ev, '只有国王才能进行加冕仪式哦。', at_sender=True)
    if prestige < DJ_NEED_SW: 
        await bot.finish(ev, f'加冕仪式需要{DJ_NEED_SW}声望，您的声望不足哦。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < DJ_NEED_GOLD:
        await bot.finish(ev, f'加冕仪式需要{DJ_NEED_GOLD}金币，您的金币不足哦。', at_sender=True)
    score_counter._reduce_score(gid,uid,DJ_NEED_GOLD)
    score_counter._reduce_prestige(gid,uid,DJ_NEED_SW)
    duel._set_level(gid, uid, 10)
    msg = f'\n礼炮鸣响，教皇领唱“感恩赞美歌”。“皇帝万岁！”\n在民众的欢呼声中，你加冕为了皇帝。\n花费了{DJ_NEED_SW}点声望，{DJ_NEED_GOLD}金币。'
    await bot.send(ev, msg, at_sender=True)
     
@sv.on_fullmatch(['飞升成神','成神飞升'])
async def be_feisheng(bot, ev: CQEvent): 
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()  
    prestige = score_counter._get_prestige(gid,uid)
    
    if level!=10:
        await bot.finish(ev, '只有皇帝才能飞升哦。', at_sender=True)
    if prestige < FS_NEED_SW: 
        await bot.finish(ev, f'飞升成神需要{FS_NEED_SW}声望，您的声望不足哦。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < FS_NEED_GOLD:
        await bot.finish(ev, f'飞升成神需要{FS_NEED_GOLD}金币，您的金币不足哦。', at_sender=True)
    score_counter._reduce_score(gid,uid,FS_NEED_GOLD)
    score_counter._reduce_prestige(gid,uid,FS_NEED_SW)
    duel._set_level(gid, uid, 20)
    msg = f'\n光柱冲天，你感觉无尽的力量涌入了自己的体内。\n在民众的惊讶的目光中，你飞升成神了。\n花费了{FS_NEED_SW}点声望，{FS_NEED_GOLD}金币。'
    await bot.send(ev, msg, at_sender=True)
        
    
@sv.on_prefix('皇室婚礼')
async def marry_queen(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()  
    prestige = score_counter._get_prestige(gid,uid)
    if prestige == None:
        await bot.finish(ev, '您还未开启声望系统哦。', at_sender=True)    
    if level <= 7:
        await bot.finish(ev, '只有8级(公爵)及以上才可以举办皇室婚礼哦。', at_sender=True)  
    if duel._search_queen(gid,uid)!=0:
        await bot.finish(ev, '皇帝只可以举办一次皇室婚礼哦。', at_sender=True)
    if not args:
        await bot.finish(ev, '请输入皇室婚礼+pcr角色名。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的pcr角色名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid)        
    if cid not in cidlist:
        await bot.finish(ev, '该角色不在你的身边哦。', at_sender=True)    
    if prestige < 1000:
        await bot.finish(ev, '您现在名声不好，不能结婚哦（结婚需要声望大于1000）。', at_sender=True)
    if prestige < 0:
        await bot.finish(ev, '您现在身败名裂，不能结婚哦（结婚需要声望大于1000）。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < 3000:
        await bot.finish(ev, '皇室婚礼需要3000金币，您的金币不足哦。', at_sender=True)    
    favor = duel._get_favor(gid,uid,cid)
    if favor < NEED_favor:
        await bot.finish(ev, f'举办婚礼的女友需要达到{NEED_favor}好感，您的好感不足哦。', at_sender=True)    
    score_counter._reduce_score(gid,uid,3000)    
    duel._set_queen_owner(gid,cid,uid)
    nvmes = get_nv_icon(cid)
    c = chara.fromid(cid)
    msg = f'繁杂的皇室礼仪过后\n\n{c.name}与[CQ:at,qq={uid}]\n\n正式踏上了婚礼的殿堂\n成为了他的妻子。\n让我们为他们表示祝贺！\n妻子不会因决斗被抢走了哦。\n{nvmes}'
    await bot.send(ev, msg)

#返回好感对应的关系和文本
def get_relationship(favor):
    for relation in RELATIONSHIP_DICT.keys():
        if favor >= relation:
            relationship = RELATIONSHIP_DICT[relation]
    return relationship[0],relationship[1]



@sv.on_prefix(['查好感','查询好感'])
async def girl_story(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if not args:
        await bot.finish(ev, '请输入查好感+女友名。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid) 
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)

    if duel._get_favor(gid,uid,cid)== None:
        duel._set_favor(gid,uid,cid,0)
    favor= duel._get_favor(gid,uid,cid)
    relationship,text = get_relationship(favor)
    c = chara.fromid(cid)    
    msg = f'\n{c.name}对你的好感是{favor}\n你们的关系是{relationship}\n“{text}”\n{c.icon.cqcode}'
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(['每日约会','女友约会', '贵族约会'])
async def daily_date(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if not args:
        await bot.finish(ev, '请输入贵族约会+女友名。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid) 
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)    
    guid = gid ,uid
    if not daily_date_limiter.check(guid):
        await bot.finish(ev, '今天已经和女友约会过了哦，明天再来吧。', at_sender=True)

    loginnum_ = ['1','2', '3', '4']  
    r_ = [0.2, 0.4, 0.35, 0.05]  
    sum_ = 0
    ran = random.random()
    for num, r in zip(loginnum_, r_):
        sum_ += r
        if ran < sum_ :break
    Bonus = {'1':[5,Date5],
             '2':[10,Date10],
             '3':[15,Date15],    
             '4':[20,Date20]
            }             
    favor = Bonus[num][0]
    text = random.choice(Bonus[num][1])
    duel._add_favor(gid,uid,cid,favor)
    c = chara.fromid(cid)
    current_favor = duel._get_favor(gid,uid,cid)
    relationship = get_relationship(current_favor)[0]
    msg = f'\n\n{text}\n\n你和{c.name}的好感上升了{favor}点\n她现在对你的好感是{current_favor}点\n你们现在的关系是{relationship}\n{c.icon.cqcode}'
    daily_date_limiter.increase(guid)
    await bot.send(ev, msg, at_sender=True)

#根据角色id和礼物id，返回增加的好感和文本

def check_gift(cid,giftid):
    lastnum = cid%10
    if lastnum == giftid:
        favor = 10
        text = random.choice(Gift10)
        return favor, text
    num1=lastnum%3
    num2=giftid%3
    choicelist = GIFTCHOICE_DICT[num1]

    if num2 == choicelist[0]:
        favor = 5
        text = random.choice(Gift5)
        return favor, text
    if num2 == choicelist[1]:
        favor = 2
        text = random.choice(Gift2)
        return favor, text        
    if num2 == choicelist[2]:
        favor = 1
        text = random.choice(Gift1)
        return favor, text

@sv.on_prefix(['送礼物','送礼','赠送礼物'])
async def give_gift(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    if gift_change.get_on_off_giftchange_status(ev.group_id):
        await bot.finish(ev, "有正在进行的礼物交换，礼物交换结束再来送礼物吧。")    
    if len(args)!=2:
        await bot.finish(ev, '请输入 送礼物+女友名+礼物名 中间用空格隔开。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    cidlist = duel._get_cards(gid, uid) 
    if cid not in cidlist:
        await bot.finish(ev, '该女友不在你的身边哦。', at_sender=True)    
    gift = args[1]
    if gift not in GIFT_DICT.keys():
        await bot.finish(ev, '请输入正确的礼物名。', at_sender=True)
    gfid = GIFT_DICT[gift]
    if duel._get_gift_num(gid,uid,gfid)==0:
        await bot.finish(ev, '你的这件礼物的库存不足哦。', at_sender=True)
    duel._reduce_gift(gid,uid,gfid)
    favor,text = check_gift(cid,gfid)
    duel._add_favor(gid,uid,cid,favor)
    current_favor = duel._get_favor(gid,uid,cid)
    relationship = get_relationship(current_favor)[0]
    c = chara.fromid(cid)
    msg = f'\n{c.name}:“{text}”\n\n你和{c.name}的好感上升了{favor}点\n她现在对你的好感是{current_favor}点\n你们现在的关系是{relationship}\n{c.icon.cqcode}'
    await bot.send(ev, msg, at_sender=True)    

@sv.on_fullmatch(['抽礼物','买礼物','购买礼物'])
async def buy_gift(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    guid = gid ,uid
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再来买礼物吧。'
        await bot.finish(ev, msg, at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < 300:
        await bot.finish(ev, '购买礼物需要300金币，您的金币不足哦。', at_sender=True) 
    if not daily_gift_limiter.check(guid):
        await bot.finish(ev, f'今天购买礼物已经超过{GIFT_DAILY_LIMIT}次了哦，明天再来吧。', at_sender=True)     
    select_gift = random.choice(list(GIFT_DICT.keys()))
    gfid = GIFT_DICT[select_gift]
    duel._add_gift(gid,uid,gfid)
    msg = f'\n您花费了300金币，\n买到了[{select_gift}]哦，\n欢迎下次惠顾。'
    score_counter._reduce_score(gid,uid,300)
    daily_gift_limiter.increase(guid)
    await bot.send(ev, msg, at_sender=True)    


@sv.on_fullmatch(['我的礼物','礼物仓库','查询礼物','礼物列表'])
async def my_gift(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    msg = f'\n您的礼物仓库如下:'
    giftmsg =''
    for gift in GIFT_DICT.keys():
        gfid = GIFT_DICT[gift]
        num = duel._get_gift_num(gid,uid,gfid)
        if num!=0:
        #补空格方便对齐
            length = len(gift)
            msg_part = '    '*(4-length)
            giftmsg+=f'\n{gift}{msg_part}: {num}件'
    if giftmsg == '':
        await bot.finish(ev, '您现在没有礼物哦，快去发送 买礼物 购买吧。', at_sender=True)        
    msg+=giftmsg
    await bot.send(ev, msg, at_sender=True)         

@sv.on_rex(f'^用(.*)与(.*)交换(.*)$')
async def change_gift(bot, ev: CQEvent):
    gid = ev.group_id    
    duel = DuelCounter()
    if gift_change.get_on_off_giftchange_status(ev.group_id):
        await bot.finish(ev, "有正在进行的礼物交换，请勿重复使用指令。")
    gift_change.turn_on_giftchange(gid)
    id1 = ev.user_id
    match = ev['match']
    try:
        id2 = int(match.group(2))
    except ValueError:
        id2 = int(ev.message[1].data['qq'])
    except:
        gift_change.turn_off_giftchange(ev.group_id)
        await bot.finish(ev, '参数格式错误')
    if id2 == id1:
        await bot.send(ev, "不能和自己交换礼物！", at_sender=True)
        gift_change.turn_off_giftchange(ev.group_id)
        return             
    gift1 = match.group(1)
    gift2 = match.group(3)
    if gift1 not in GIFT_DICT.keys():
        gift_change.turn_off_giftchange(ev.group_id)
        await bot.finish(ev, f'礼物1不存在。')
    if gift2 not in GIFT_DICT.keys():
        gift_change.turn_off_giftchange(ev.group_id)
        await bot.finish(ev, f'礼物2不存在。')        
    gfid1 = GIFT_DICT[gift1]
    gfid2 = GIFT_DICT[gift2] 
    if gfid2 == gfid1:
        await bot.send(ev, "不能交换相同的礼物！", at_sender=True)
        gift_change.turn_off_giftchange(ev.group_id)
        return           

    if duel._get_gift_num(gid,id1,gfid1)==0:
        gift_change.turn_off_giftchange(ev.group_id)    
        await bot.finish(ev, f'[CQ:at,qq={id1}]\n您的{gift1}的库存不足哦。')    
    if duel._get_gift_num(gid,id2,gfid2)==0:
        gift_change.turn_off_giftchange(ev.group_id)    
        await bot.finish(ev, f'[CQ:at,qq={id2}]\n您的{gift2}的库存不足哦。')  
    level2 = duel._get_level(gid, id2)
    noblename = get_noblename(level2)
    gift_change.turn_on_waitchange(gid)
    gift_change.set_changeid(gid,id2)
    gift_change.turn_off_accept_giftchange(gid)    
    msg = f'[CQ:at,qq={id2}]\n尊敬的{noblename}您好：\n\n[CQ:at,qq={id1}]试图用[{gift1}]交换您的礼物[{gift2}]。\n\n请在{WAIT_TIME_CHANGE}秒内[接受交换/拒绝交换]。'
    await bot.send(ev, msg)
    await asyncio.sleep(WAIT_TIME_CHANGE)   
    gift_change.turn_off_waitchange(gid)
    if gift_change.get_isaccept_giftchange(gid) is False:
        msg = '\n礼物交换被拒绝。'
        gift_change.init_changeid(gid)
        gift_change.turn_off_giftchange(gid)
        await bot.finish(ev, msg, at_sender=True)    
    duel._reduce_gift(gid,id1,gfid1)
    duel._add_gift(gid,id1,gfid2)    
    duel._reduce_gift(gid,id2,gfid2)
    duel._add_gift(gid,id2,gfid1)     
    msg = f'\n礼物交换成功！\n您使用[{gift1}]交换了\n[CQ:at,qq={id2}]的[{gift2}]。' 
    gift_change.init_changeid(gid)
    gift_change.turn_off_giftchange(gid)
    await bot.finish(ev, msg, at_sender=True)    



@sv.on_fullmatch('接受交换')
async def giftchangeaccept(bot, ev: CQEvent):
    gid = ev.group_id
    if gift_change.get_on_off_waitchange_status(gid):
        if ev.user_id == gift_change.get_changeid(gid):
            msg = '\n礼物交换接受成功，请耐心等待礼物交换结束。'
            await bot.send(ev, msg, at_sender=True)
            gift_change.turn_off_waitchange(gid)
            gift_change.turn_on_accept_giftchange(gid)



@sv.on_fullmatch('拒绝交换')
async def giftchangerefuse(bot, ev: CQEvent):
    gid = ev.group_id
    if gift_change.get_on_off_waitchange_status(gid):
        if ev.user_id == gift_change.get_changeid(gid):
            msg = '\n礼物交换拒绝成功，请耐心等待礼物交换结束。'
            await bot.send(ev, msg, at_sender=True)
            gift_change.turn_off_waitchange(gid)
            gift_change.turn_off_accept_giftchange(gid)



@sv.on_prefix(['购买情报','买情报'])
async def buy_information(bot, ev: CQEvent):
    args = ev.message.extract_plain_text().split()
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    if duel_judger.get_on_off_status(ev.group_id):
        msg = '现在正在决斗中哦，请决斗后再来买情报吧。'
        await bot.finish(ev, msg, at_sender=True)    
    if not args:
        await bot.finish(ev, '请输入买情报+女友名。', at_sender=True)
    name = args[0]
    cid = chara.name2id(name)
    if cid == 1000:
        await bot.finish(ev, '请输入正确的女友名。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    if score < 500:
        await bot.finish(ev, '购买女友情报需要500金币，您的金币不足哦。', at_sender=True)    
    score_counter._reduce_score(gid,uid,500)
    last_num = cid%10
    like = ''
    normal = ''
    dislike = ''
    for gift in GIFT_DICT.keys():
        if GIFT_DICT[gift]==last_num:
            favorite = gift
            continue
        num1 = last_num%3
        num2 = GIFT_DICT[gift]%3
        choicelist = GIFTCHOICE_DICT[num1]

        if num2 == choicelist[0]:
            like+=f'{gift}\n'
            continue
        if num2 == choicelist[1]:
            normal+=f'{gift}\n'
            continue
        if num2 == choicelist[2]:
            dislike+=f'{gift}\n'
            continue    
    c = chara.fromid(cid)       
    msg = f'\n花费了500金币，您买到了以下情报：\n{c.name}最喜欢的礼物是:\n{favorite}\n喜欢的礼物是:\n{like}一般喜欢的礼物是:\n{normal}不喜欢的礼物是:\n{dislike}{c.icon.cqcode}'
    await bot.send(ev, msg, at_sender=True)  

@sv.on_fullmatch(['好感系统帮助','礼物系统帮助','好感帮助','礼物帮助'])
async def gift_help(bot, ev: CQEvent):
    msg='''
╔                                        ╗  
             好感系统帮助
1. 查好感+女友名
2. 贵族约会+女友名(1天限1次)
3. 买礼物(300金币，一天限5次）
4. 送礼+女友名
5. 用xx与[艾特对象]交换xx
例: 用热牛奶与@妈宝交换书
6. 买情报+女友名(500金币，可了解女友喜好)
7. 礼物仓库(查询礼物仓库)
8. 好感列表
注:
通过约会或者送礼可以提升好感
决斗输掉某女友会扣除50好感，不够则被抢走
女友喜好与原角色无关，只是随机生成，仅供娱乐
╚                                        ╝
 '''  
    await bot.send(ev, msg)


@sv.on_fullmatch(['好感列表','女友好感列表'])
async def get_favorlist(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter() 
    if duel._get_level(gid, uid) == 0:
        msg = '您还未在本群创建过贵族，请发送 创建贵族 开始您的贵族之旅。'
        await bot.send(ev, msg, at_sender=True)
        return
    cidlist = duel._get_cards(gid, uid)
    if len(cidlist)==0:
        await bot.finish(ev, '您现在还没有女友哦。', at_sender=True)
    favorlist = []
    for cid in cidlist:
        favor = duel._get_favor(gid,uid,cid)
        if favor !=0 and favor!=None:
            favorlist.append({"cid":cid,"favor":favor})
    if len(favorlist)==0:
        await bot.finish(ev, '您的女友好感全部为0哦。', at_sender=True)        
    rows_by_favor = sorted(favorlist, key=lambda r: r['favor'],reverse=True)
    msg = '\n您好感0以上的女友的前10名如下所示:\n'
    num = min(len(rows_by_favor),10)
    for i in range(0,num):
        cid = rows_by_favor[i]["cid"]
        favor = rows_by_favor[i]["favor"]
        c = chara.fromid(cid)
        msg+=f'{c.name}:{favor}点\n'
    await bot.send(ev, msg, at_sender=True)

    
@sv.on_prefix('确认离婚')
async def lihun_queen(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    duel = DuelCounter()
    level = duel._get_level(gid, uid)
    score_counter = ScoreCounter2()  
    prestige = score_counter._get_prestige(gid,uid)
    if duel._search_queen(gid,uid) ==0:
        await bot.finish(ev, '您没有妻子！。', at_sender=True)     
    score = score_counter._get_score(gid, uid)
    if prestige < 3000: 
        await bot.finish(ev, '离婚需要3000声望，您的声望现在离婚可能身败名裂哦。', at_sender=True)
    if score < 20000:
        await bot.finish(ev, '离婚需要20000金币，您的金币不足哦。', at_sender=True)    
    score_counter._reduce_score(gid,uid,20000)    
    score_counter._reduce_prestige(gid,uid,3000)
    queen = duel._search_queen(gid,uid)
    duel._delete_card(gid, uid, queen)
    c = chara.fromid(queen)
    nvmes = get_nv_icon(queen)
    msg = f'花费了20000金币，[CQ:at,qq={uid}]总算将他的妻子{c.name}赶出家门\n，引起了众人的不满，损失3000声望。{nvmes}'
    duel._delete_queen_owner(gid,queen)
    await bot.send(ev, msg)
    
@sv.on_rex(f'^为(.*)充值(\d+)声望$')
async def cheat_SW(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '不要想着走捷径哦。', at_sender=True)
    gid = ev.group_id
    match = ev['match']
    try:
        id = int(match.group(1))
    except ValueError:
        id = int(ev.message[1].data['qq'])
    except:
        await bot.finish(ev, '参数格式错误')
    num = int(match.group(2))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid,id)
    if duel._get_level(gid, id) == 0:
        await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
    if prestige == None:
        await bot.finish(ev, '该用户尚未开启声望系统哦！。', at_sender=True)    
    score_counter._add_prestige(gid,id,num)
    msg = f'已为[CQ:at,qq={id}]充值{num}声望。'
    await bot.send(ev, msg)
    
@sv.on_rex(f'^扣除(.*)的(\d+)声望$')
async def cheat_SW2(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '不要想着走捷径哦。', at_sender=True)
    gid = ev.group_id
    match = ev['match']
    try:
        id = int(match.group(1))
    except ValueError:
        id = int(ev.message[1].data['qq'])
    except:
        await bot.finish(ev, '参数格式错误')
    num = int(match.group(2))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid,id)
    if duel._get_level(gid, id) == 0:
        await bot.finish(ev, '该用户还未在本群创建贵族哦。', at_sender=True)
    if prestige == None:
        await bot.finish(ev, '该用户尚未开启声望系统哦！。', at_sender=True)    
    score_counter._reduce_prestige(gid,id,num)
    msg = f'已扣除[CQ:at,qq={id}]的{num}声望。'
    await bot.send(ev, msg)
    
async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card']!='' else m['nickname']
    return d        

@sv.on_fullmatch(('金币排行榜', '金币排行'))
async def Race_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_counter = ScoreCounter2()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                score_dict[user_card_dict[uid]] = score_counter._get_score(gid, uid)
        group_ranking = sorted(score_dict.items(), key = lambda x:x[1], reverse = True)
        msg = '此群贵族决斗金币排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 金币: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))        
        
@sv.on_fullmatch(('声望排行榜', '声望排行'))
async def SW_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_counter = ScoreCounter2()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                score_dict[user_card_dict[uid]] = score_counter._get_prestige(gid, uid)
                if score_dict[user_card_dict[uid]] == None:
                   score_dict[user_card_dict[uid]] = 0
        group_ranking = sorted(score_dict.items(), key = lambda x:x[1], reverse = True)
        msg = '此群贵族对决声望排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 声望: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))      

@sv.on_fullmatch(('女友排行榜', '女友排行'))
async def SW_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_counter = ScoreCounter2()
        duel = DuelCounter()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                cidlist = duel._get_cards(gid, uid)
                score_dict[user_card_dict[uid]] = cidnum = len(cidlist)
        group_ranking = sorted(score_dict.items(), key = lambda x:x[1], reverse = True)
        msg = '此群贵族对决女友数排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 女友数: {group_ranking[i][1]}\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))     

@sv.on_rex(f'^用(\d+)声望兑换金币$')
async def cheat_score(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    num = int(match.group(1))
    duel = DuelCounter()
    score_counter = ScoreCounter2()
    prestige = score_counter._get_prestige(gid,uid)
    if duel._get_level(gid, uid) == 0:
        await bot.finish(ev, '您还没有在本群创建贵族哦。', at_sender=True)
    if prestige == None:
        await bot.finish(ev, '您未开启声望系统哦！。', at_sender=True)   
    if num < 200:
        await bot.finish(ev, '200声望起兑换哦！。', at_sender=True)
    score = score_counter._get_score(gid, uid)
    pay_score=num
    num2 = num * 50
    if prestige < pay_score:
        msg = f'您的声望只有{score}，无法兑换哦。'
        await bot.send(ev, msg, at_sender=True)
        return
    else:
        score_counter._reduce_prestige(gid, uid, pay_score)
        score_counter._add_score(gid,uid,num2)
        scoreyou = score_counter._get_score(gid, uid)
        prestige = score_counter._get_prestige(gid,uid)
        msg = f'使用{num}声望兑换{num2}金币成功\n您的声望剩余{prestige}，金币为{scoreyou}。'
        await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(('查询庆典','庆典状况','当前庆典'))
async def GET_Cele(bot, ev: CQEvent):
   duel = DuelCounter()
   gid = ev.group_id
   if Show_Cele_Not == True:
    if duel._get_GOLD_CELE(gid) == 1:
       msg = f'\n当前正举办押注金币庆典，当支持成功时，获得的金币将变为原来的{Gold_Cele_Num}倍\n'
    else:
       msg = f'\n当前未举办金币庆典\n'
    if duel._get_QC_CELE(gid) == 1:
       msg += f'当前正举办贵族签到庆典，签到时获取的声望将变为{QD_SW_Cele_Num}倍，金币将变为{QD_Gold_Cele_Num}倍\n'
    else:
       msg += f'当前未举办签到庆典\n'
    if duel._get_SUO_CELE(gid) == 1:
       msg += f'当前正举办梭哈倍率庆典，梭哈时的倍率将额外提升{Suo_Cele_Num}倍\n'
    else:
       msg += f'当前未举办梭哈倍率庆典\n'
    if duel._get_FREE_CELE(gid) == 1:
       msg += f'当前正举办免费招募庆典，每日可免费招募{FREE_DAILY_LIMIT}次\n'
    else:
       msg += f'当前未举办免费招募庆典\n'
    if duel._get_SW_CELE(gid) == 1:
       msg += f'当前正举办限时开启声望招募庆典'
    else:
       msg += f'当前未举办限时开启声望招募庆典'
    await bot.send(ev, msg, at_sender=True)
   else:   
    if duel._get_GOLD_CELE(gid) == 1:
       msg = f'\n当前正举办押注金币庆典，当支持成功时，获得的金币将变为原来的{Gold_Cele_Num}倍\n'
    else:
       msg = f'\n'
    if duel._get_QC_CELE(gid) == 1:
       msg += f'当前正举办贵族签到庆典，签到时获取的声望将变为{QD_SW_Cele_Num}倍，金币将变为{QD_Gold_Cele_Num}倍\n'
    if duel._get_SUO_CELE(gid) == 1:
       msg += f'当前正举办梭哈倍率庆典，梭哈时的倍率将额外提升{Suo_Cele_Num}倍\n'
    if duel._get_FREE_CELE(gid) == 1:
       msg += f'当前正举办免费招募庆典，每日可免费招募{FREE_DAILY_LIMIT}次\n'
    if duel._get_SW_CELE(gid) == 1:
       msg += f'当前正举办限时开启声望招募庆典'
    await bot.send(ev, msg, at_sender=True)
    
@sv.on_rex(r'^开启本群(金币|签到|梭哈倍率|免费招募|声望招募)庆典$')
async def ON_Cele_SWITCH(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您无权开放庆典！', at_sender=True)
    duel = DuelCounter()
    if duel._get_SW_CELE(gid) == None:
        await bot.finish(ev, '本群庆典未初始化，请先发"初始化本群庆典"初始化数据！', at_sender=True)
    match = (ev['match'])
    cele = (match.group(1))
    if cele == '金币':
        QC_Data = duel._get_QC_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,1,QC_Data,SUO_Data,SW_Data,FREE_Data)
        msg = f'已开启本群金币庆典，当支持成功时，获得的金币将变为原来的{Gold_Cele_Num}倍\n'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '签到':
        GC_Data = duel._get_GOLD_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,1,SUO_Data,SW_Data,FREE_Data)
        msg = f'已开启本群贵族签到庆典，签到时获取的声望将变为{QD_SW_Cele_Num}倍，金币将变为{QD_Gold_Cele_Num}倍\n'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '梭哈倍率':
        GC_Data = duel._get_GOLD_CELE(gid)
        QC_Data = duel._get_QC_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,QC_Data,1,SW_Data,FREE_Data)
        msg = f'已开启本群梭哈倍率庆典，梭哈时的倍率将额外提升{Suo_Cele_Num}倍\n'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '免费招募':
        GC_Data = duel._get_GOLD_CELE(gid)
        QC_Data = duel._get_QC_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,QC_Data,SUO_Data,SW_Data,1)
        msg = f'已开启本群免费招募庆典，每日可免费招募{FREE_DAILY_LIMIT}次\n'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '声望招募':
        GC_Data = duel._get_GOLD_CELE(gid)
        QC_Data = duel._get_QC_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,QC_Data,SUO_Data,1,FREE_Data)
        msg = f'已开启本群限时开启声望招募庆典\n'
        await bot.send(ev, msg, at_sender=True)
        return
    msg = f'庆典名匹配出错！请输入金币/签到/梭哈/免费招募/声望招募庆典中的一个！'
    await bot.send(ev, msg, at_sender=True)


@sv.on_rex(r'^关闭本群(金币|签到|梭哈倍率|免费招募|声望招募)庆典$')
async def OFF_Cele_SWITCH(bot, ev: CQEvent):
    gid = ev.group_id
    uid = ev.user_id
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您无权开放庆典！', at_sender=True)
    match = (ev['match'])
    cele = (match.group(1))
    duel = DuelCounter()
    if duel._get_SW_CELE(gid) == None:
        await bot.finish(ev, '本群庆典未初始化，请先发"初始化本群庆典"初始化数据！', at_sender=True)
    if cele == '金币':
        QC_Data = duel._get_QC_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,0,QC_Data,SUO_Data,SW_Data,FREE_Data)
        msg = f'\n已关闭本群金币庆典'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '签到':
        GC_Data = duel._get_GOLD_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,0,SUO_Data,SW_Data,FREE_Data)
        msg = f'\n已关闭本群贵族签到庆典'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '梭哈倍率':
        GC_Data = duel._get_GOLD_CELE(gid)
        QC_Data = duel._get_QC_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,QC_Data,0,SW_Data,FREE_Data)
        msg = f'\n已关闭本群梭哈倍率庆典'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '免费招募':
        GC_Data = duel._get_GOLD_CELE(gid)
        QC_Data = duel._get_QC_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        SW_Data = duel._get_SW_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,QC_Data,SUO_Data,SW_Data,0)
        msg = f'\n已关闭本群免费招募庆典'
        await bot.send(ev, msg, at_sender=True)
        return
    elif cele == '声望招募':
        GC_Data = duel._get_GOLD_CELE(gid)
        QC_Data = duel._get_QC_CELE(gid)
        SUO_Data = duel._get_SUO_CELE(gid)
        FREE_Data = duel._get_FREE_CELE(gid)
        duel._initialization_CELE(gid,GC_Data,QC_Data,SUO_Data,0,FREE_Data)
        msg = f'\n已关闭本群限时声望招募庆典'
        await bot.send(ev, msg, at_sender=True)
        return
    msg = f'庆典名匹配出错！请输入金币/签到/梭哈/免费招募/声望招募庆典中的一个！'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch('初始化本群庆典')
async def initialization(bot, ev: CQEvent):
    uid = ev.user_id
    gid = ev.group_id
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '您无权初始化庆典！', at_sender=True)
    duel = DuelCounter()
    duel._initialization_CELE(gid,Gold_Cele,QD_Cele,Suo_Cele,SW_add,FREE_DAILY)
    msg = f'已成功初始化本群庆典！\n您可发送查询庆典来查看本群庆典情况！\n'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch('重置礼物交换')
async def init_change(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能使用重置礼物交换哦。', at_sender=True)
    gift_change.turn_off_giftchange(ev.group_id)
    msg = '已重置本群礼物交换状态！'
    await bot.send(ev, msg, at_sender=True)
    


