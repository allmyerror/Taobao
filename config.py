from pypinyin import lazy_pinyin

# 淘宝搜索关键字
KEYWORD = '美食'

# MongoDB配置信息
MONGO_URL = 'localhost'
MONGO_DB = 'taobao'
MONGO_TABLE = ''.join(lazy_pinyin(KEYWORD))

# PhantomJS配置信息
SERVICE_ARGS = ['--load-images=false','--disk-cache=true']
